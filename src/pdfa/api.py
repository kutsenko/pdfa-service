"""REST API providing PDF to PDF/A conversion backed by OCRmyPDF."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal
from urllib.parse import quote

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
)
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ocrmypdf import exceptions as ocrmypdf_exceptions
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import pdfa.auth
from pdfa.a11y_camera_config import A11yCameraConfig
from pdfa.auth import (
    GoogleOAuthClient,
    WebSocketAuthenticator,
    get_current_user,
    get_current_user_optional,
)
from pdfa.auth_config import AuthConfig
from pdfa.compression_config import PRESETS, CompressionConfig
from pdfa.converter import convert_to_pdfa
from pdfa.db import MongoDBConnection, ensure_indexes
from pdfa.db_config import DatabaseConfig
from pdfa.exceptions import (
    JobCancelledException,
    JobNotFoundException,
    OfficeConversionError,
    UnsupportedFormatError,
)
from pdfa.format_converter import (
    convert_office_to_pdf,
    is_image_file,
    is_office_document,
)
from pdfa.image_converter import convert_image_to_pdf, convert_images_to_pdf
from pdfa.job_manager import get_job_manager
from pdfa.logging_config import configure_logging, get_logger
from pdfa.models import UserDocument, UserPreferencesDocument
from pdfa.pairing_manager import pairing_manager
from pdfa.progress_tracker import ProgressInfo
from pdfa.repositories import (
    JobRepository,
    UserPreferencesRepository,
    UserRepository,
)
from pdfa.user_models import User
from pdfa.websocket_protocol import (
    AuthMessage,
    CancelJobMessage,
    CancelledMessage,
    CompletedMessage,
    ErrorMessage,
    JobAcceptedMessage,
    PingMessage,
    PongMessage,
    ProgressMessage,
    RegisterPairingMessage,
    SubmitJobMessage,
    SyncImageMessage,
    parse_client_message,
)

PdfaLevel = Literal["pdf", "1", "2", "3"]
CompressionProfile = Literal["balanced", "quality", "aggressive", "minimal"]

logger = get_logger(__name__)

# Load compression configuration from environment variables at startup
compression_config = CompressionConfig.from_env()
logger.info(
    f"Loaded compression config: DPI={compression_config.image_dpi}, "
    f"JPG quality={compression_config.jpg_quality}, "
    f"Optimize={compression_config.optimize}"
)

# Load accessibility camera configuration from environment variables
a11y_camera_config = A11yCameraConfig.from_env()
logger.info(
    f"Loaded a11y camera config: Debug={a11y_camera_config.debug_enabled}, "
    f"Hysteresis={a11y_camera_config.hysteresis_lower}/{a11y_camera_config.hysteresis_upper}, "
    f"FPS={a11y_camera_config.analysis_fps}"
)

# Database configuration - loaded during startup to allow testing without MongoDB
# MongoDB is required for service operation (hard migration)
db_config = None

# Progress broadcast timeout configuration
# For long-running conversions with many WebSocket clients, broadcasting progress
# updates can take longer than the default 2 seconds. Increase this if you have
# many concurrent clients or slow network conditions.
PROGRESS_BROADCAST_TIMEOUT = int(os.getenv("PROGRESS_BROADCAST_TIMEOUT", "10"))
logger.info(f"Progress broadcast timeout: {PROGRESS_BROADCAST_TIMEOUT} seconds")

# Load authentication configuration from environment variables
auth_config_instance = AuthConfig.from_env()
if auth_config_instance.enabled:
    try:
        auth_config_instance.validate()
        logger.info("Authentication ENABLED - Google OAuth + JWT")
    except ValueError as e:
        logger.error(f"Invalid auth configuration: {e}")
        raise
else:
    logger.info("Authentication DISABLED (PDFA_ENABLE_AUTH=false)")

# Set global auth config in auth module
pdfa.auth.auth_config = auth_config_instance

app = FastAPI(
    title="PDF/A Conversion Service",
    description="Convert PDFs to PDF/A using OCRmyPDF.",
    version="0.1.0",
)

# Security: Configure rate limiting to prevent DoS attacks
# Can be disabled for testing via PDFA_DISABLE_RATE_LIMITING=true
rate_limiting_enabled = (
    os.getenv("PDFA_DISABLE_RATE_LIMITING", "false").lower() != "true"
)
if rate_limiting_enabled:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting ENABLED")
else:
    # Create a no-op limiter for tests

    limiter = Limiter(key_func=get_remote_address, enabled=False)
    app.state.limiter = limiter
    logger.info("Rate limiting DISABLED (for testing)")


# Security: Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses.

    Headers added:
    - Content-Security-Policy: Restrict resource loading to prevent XSS
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Referrer-Policy: Control referrer information

    """
    response = await call_next(request)

    # Content Security Policy - restrict resource loading
    # Note: 'unsafe-inline' is needed for inline styles in web UI
    # 'unsafe-eval' is NOT allowed for better security
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Enable browser XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# Initialize job manager
job_manager = get_job_manager()

# Mount static files for modular web UI
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Mounted static files from {static_path}")
else:
    logger.warning(f"Static files directory not found at {static_path}")

# Setup Jinja2 templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))
logger.info(f"Configured Jinja2 templates from {templates_path}")

# Global auth config (loaded in startup_event)
auth_config = None


async def ensure_default_user() -> None:
    """Create default user in MongoDB when authentication is disabled.

    This function is idempotent and can be called multiple times safely.
    It only creates a default user if:
    - auth_config is loaded
    - Authentication is disabled (auth_config.enabled == False)

    The default user is created using values from auth_config:
    - default_user_id
    - default_user_email
    - default_user_name

    These values can be customized via environment variables:
    - DEFAULT_USER_ID (default: "local-default")
    - DEFAULT_USER_EMAIL (default: "local@localhost")
    - DEFAULT_USER_NAME (default: "Local User")
    """
    global auth_config

    if auth_config is None or auth_config.enabled:
        return  # Skip if auth enabled or config not loaded

    user_repo = UserRepository()
    default_user = UserDocument(
        user_id=auth_config.default_user_id,
        email=auth_config.default_user_email,
        name=auth_config.default_user_name,
        picture=None,
        created_at=datetime.now(UTC),
        last_login_at=datetime.now(UTC),
        login_count=1,
    )

    await user_repo.create_or_update_user(default_user)
    logger.info(
        f"Default user ensured: user_id={auth_config.default_user_id}, "
        f"email={auth_config.default_user_email}"
    )


@app.on_event("startup")
async def startup_event():
    """Start background tasks and connect to MongoDB on application startup."""
    global db_config, auth_config

    # Configure logging for all modules
    configure_logging()
    logger.info("Logging configured")

    # Load database configuration from environment variables
    db_config = DatabaseConfig.from_env()
    logger.info(f"Database config loaded: database={db_config.mongodb_database}")

    # Connect to MongoDB (hard migration: service will fail if MongoDB unavailable)
    logger.info(
        f"Connecting to MongoDB: database={db_config.mongodb_database}, "
        f"uri={db_config.get_safe_uri_for_logging()}"
    )
    mongo = MongoDBConnection()
    try:
        await mongo.connect(db_config.mongodb_uri, db_config.mongodb_database)
        logger.info("MongoDB connection established")

        # Create indexes (idempotent operation)
        await ensure_indexes()
        logger.info("MongoDB indexes verified")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise RuntimeError(
            "Service cannot start without MongoDB connection. "
            "Please check MONGODB_URI environment variable and ensure MongoDB is running."
        ) from e

    # Set global auth_config reference for ensure_default_user()
    auth_config = auth_config_instance

    # Create default user if authentication is disabled
    await ensure_default_user()

    logger.info("Starting background tasks...")
    job_manager.start_background_tasks()
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks and disconnect from MongoDB on application shutdown."""
    logger.info("Stopping background tasks...")
    await job_manager.stop_background_tasks()

    logger.info("Disconnecting from MongoDB...")
    mongo = MongoDBConnection()
    await mongo.disconnect()
    logger.info("Application shutdown complete")


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check() -> dict[str, str]:
    """Health check endpoint (always public, no auth required).

    Supports both GET and HEAD methods for monitoring and load balancer checks.
    Also verifies MongoDB connection health.

    Returns:
        Status dict with "status" and "database" fields

    Raises:
        HTTPException: 503 if MongoDB is unavailable

    """
    # Check MongoDB health
    mongo = MongoDBConnection()
    db_healthy = await mongo.health_check()

    if not db_healthy:
        raise HTTPException(
            status_code=503, detail="Service unavailable: database connection lost"
        )

    return {"status": "healthy", "database": "connected"}


@app.get("/api/config/a11y-camera")
async def get_a11y_camera_config() -> dict[str, Any]:
    """Get accessibility camera configuration.

    This endpoint returns the accessibility camera configuration loaded from
    environment variables. The configuration controls edge detection, audio
    feedback, and auto-capture behavior.

    Returns:
        Dictionary with accessibility camera configuration

    """
    config = A11yCameraConfig.from_env()
    # Validation happens automatically in __post_init__
    return config.to_dict()


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def web_ui() -> str:
    """Serve the web-based conversion interface with browser language detection.

    Supports both GET and HEAD methods for health checks and monitoring.
    """
    ui_path = Path(__file__).parent / "web_ui.html"
    try:
        html_content = ui_path.read_text(encoding="utf-8")
        # For root path, inject auto-detection flag
        html_content = html_content.replace(
            '<html lang="en" data-lang="en">', '<html lang="en" data-lang="auto">'
        )
        # Config is now loaded via /api/config/a11y-camera endpoint (no injection)
        return html_content
    except FileNotFoundError:
        logger.warning("Web UI file not found at %s", ui_path)
        return await web_ui_lang("en")


@app.api_route("/{lang}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def web_ui_lang(lang: str) -> str:
    """Serve the web-based conversion interface in specified language.

    Supports both GET and HEAD methods for health checks and monitoring.

    Args:
        lang: Language code (en, de, es, fr)

    """
    # Validate language code
    supported_langs = {"en", "de", "es", "fr"}
    if lang not in supported_langs:
        # For unsupported paths, let FastAPI handle it (will show 404 or other routes)
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not supported")

    ui_path = Path(__file__).parent / "web_ui.html"
    try:
        html_content = ui_path.read_text(encoding="utf-8")
        # Inject the language code into the HTML
        html_content = html_content.replace(
            '<html lang="en" data-lang="en">',
            f'<html lang="{lang}" data-lang="{lang}">',
        )
        # Inject accessibility camera configuration
        import json

        config_json = json.dumps(a11y_camera_config.to_dict(), indent=2)
        config_injection = (
            f"\n        // Accessibility camera configuration from environment variables\n"
            f"        window.a11yCameraConfig = {config_json};\n"
        )
        html_content = html_content.replace("<script>", f"<script>{config_injection}")
        return html_content
    except FileNotFoundError:
        logger.warning("Web UI file not found at %s", ui_path)
        # Fallback HTML UI (line length exceptions acceptable for HTML/CSS)
        return """
        <html>
        <head>
            <title>PDF/A Converter</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; }
                h1 { color: #333; }
                .error { color: #d32f2f; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📄 PDF/A Converter API</h1>
                <p>Web interface is not available. Use the API directly:</p>
                <p><strong>Endpoint:</strong> <code>POST /convert</code></p>
                <p><strong>API Documentation:</strong> <a href="/docs">/docs</a></p>
                <p>For detailed usage instructions, see the <a href="https://github.com/kutsenko/pdfa-service">GitHub repository</a>.</p>
            </div>
        </body>
        </html>
        """


# Authentication endpoints


@app.get("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    """Initiate Google OAuth login flow.

    Returns:
        RedirectResponse to Google OAuth consent page

    Raises:
        HTTPException: If authentication is disabled (404)

    """
    logger.info(
        f"[OAuth] Login endpoint called from {request.client.host if request.client else 'unknown'}"
    )

    if not auth_config_instance.enabled:
        logger.warning("[OAuth] Authentication is disabled - returning 404")
        raise HTTPException(status_code=404, detail="Authentication is disabled")

    logger.info("[OAuth] Authentication is enabled, initiating OAuth flow")
    logger.debug(
        f"[OAuth] Client ID configured: {auth_config_instance.google_client_id[:20]}..."
    )
    logger.debug(f"[OAuth] Redirect URI: {auth_config_instance.redirect_uri}")

    try:
        oauth_client = GoogleOAuthClient(auth_config_instance)
        response = await oauth_client.initiate_login(request)
        logger.info("[OAuth] Redirecting to Google OAuth URL")
        return response
    except Exception as e:
        logger.error(f"[OAuth] Login initiation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"OAuth initialization failed: {str(e)}"
        )


@app.get("/auth/callback")
async def oauth_callback(request: Request):
    """Handle Google OAuth callback and issue JWT token.

    When called directly from browser (OAuth redirect from Google):
    - Returns the web UI HTML page
    - JavaScript in the page will detect callback and fetch this endpoint again

    When called via fetch/AJAX (from web UI JavaScript):
    - Returns JSON with access_token and user info

    Args:
        request: Request with 'code' and 'state' query parameters

    Returns:
        HTML page or JSON with access_token depending on request type

    Raises:
        HTTPException: If authentication is disabled or callback fails

    """
    if not auth_config_instance.enabled:
        raise HTTPException(status_code=404, detail="Authentication is disabled")

    # Check if this is a fetch/AJAX request or direct browser navigation
    accept_header = request.headers.get("accept", "")
    is_json_request = "application/json" in accept_header

    # If it's a direct browser request (from Google OAuth redirect),
    # serve the web UI HTML so JavaScript can handle the callback
    if not is_json_request:
        ui_path = Path(__file__).parent / "web_ui.html"
        html_content = ui_path.read_text(encoding="utf-8")
        # Inject accessibility camera configuration
        import json

        config_json = json.dumps(a11y_camera_config.to_dict(), indent=2)
        config_injection = (
            f"\n        // Accessibility camera configuration from environment variables\n"
            f"        window.a11yCameraConfig = {config_json};\n"
        )
        html_content = html_content.replace("<script>", f"<script>{config_injection}")
        return HTMLResponse(content=html_content)

    # Otherwise, handle the OAuth callback and return JSON
    oauth_client = GoogleOAuthClient(auth_config_instance)
    user, token = await oauth_client.handle_callback(request)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
    }


@app.get("/auth/user")
async def get_user_info(current_user: User | None = Depends(get_current_user_optional)):
    """Get current user information.

    Returns:
        User information (email, name, picture) if auth is enabled
        404 if auth is disabled

    Raises:
        HTTPException:
            - 404 if auth is disabled
            - 401 if auth is enabled and user is not authenticated

    """
    # Return 404 if auth is disabled (so frontend can detect it)
    if not auth_config_instance.enabled:
        raise HTTPException(status_code=404, detail="Authentication is disabled")

    # Return 401 if auth is enabled but user is not authenticated
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
    }


# User profile and preferences endpoints


@app.get("/api/v1/user/profile")
@limiter.limit("30/minute")
async def get_user_profile(
    request: Request, current_user: User | None = Depends(get_current_user_optional)
):
    """Get comprehensive user profile including stats and activity.

    Returns profile info, login stats, job stats, and recent activity.
    Works with auth disabled (returns default user data).

    Returns:
        Dictionary containing:
        - user: Basic user information
        - login_stats: Account creation, last login, login count
        - job_stats: Conversion statistics (total, success rate, etc.)
        - recent_activity: Last 20 audit events

    """
    from pdfa.repositories import AuditLogRepository

    user_repo = UserRepository()
    job_repo = JobRepository()
    audit_repo = AuditLogRepository()

    # Get user document for login stats (if auth enabled and user exists)
    user_doc = None
    if auth_config_instance.enabled and current_user:
        user_doc = await user_repo.get_user(current_user.user_id)

    # Get job statistics (only if user is logged in)
    job_stats = {}
    recent_activity = []

    if current_user:
        job_stats = await job_repo.get_job_stats(current_user.user_id)
        # Get recent audit events (last 20)
        recent_activity = await audit_repo.get_user_events(
            current_user.user_id, limit=20
        )

    return {
        "user": {
            "user_id": current_user.user_id if current_user else "anonymous",
            "email": current_user.email if current_user else "anonymous@localhost",
            "name": current_user.name if current_user else "Anonymous User",
            "picture": current_user.picture if current_user else None,
        },
        "login_stats": {
            "created_at": user_doc.created_at.isoformat() if user_doc else None,
            "last_login_at": user_doc.last_login_at.isoformat() if user_doc else None,
            "login_count": user_doc.login_count if user_doc else None,
        },
        "job_stats": job_stats,
        "recent_activity": [
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "ip_address": event.ip_address,
                "details": event.details,
            }
            for event in recent_activity
        ],
    }


@app.get("/api/v1/user/preferences")
@limiter.limit("30/minute")
async def get_user_preferences(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get user preferences or system defaults.

    Returns user's saved conversion preferences if they exist,
    otherwise returns system default values.

    Returns:
        UserPreferencesDocument with default conversion parameters

    """
    user_prefs_repo = UserPreferencesRepository()

    # Use user_id if user is logged in, otherwise use "anonymous"
    user_id = current_user.user_id if current_user else "anonymous"

    prefs = await user_prefs_repo.get_preferences(user_id)

    if prefs:
        return prefs.model_dump()
    else:
        # Return system defaults
        return UserPreferencesDocument(user_id=user_id).model_dump()


@app.put("/api/v1/user/preferences")
@limiter.limit("30/minute")
async def update_user_preferences(
    request: Request,
    preferences: dict[str, Any],
    current_user: User | None = Depends(get_current_user_optional),
):
    """Update user preferences.

    Saves user's preferred default conversion parameters.

    Args:
        request: FastAPI request object (required for rate limiting)
        preferences: Dictionary with preference fields
        current_user: Authenticated user (injected by FastAPI)

    Returns:
        Updated UserPreferencesDocument

    """
    user_prefs_repo = UserPreferencesRepository()

    # Use user_id if user is logged in, otherwise use "anonymous"
    user_id = current_user.user_id if current_user else "anonymous"

    # Validate and create preferences document
    prefs_doc = UserPreferencesDocument(
        user_id=user_id,
        default_pdfa_level=preferences.get("default_pdfa_level", "2"),
        default_ocr_language=preferences.get("default_ocr_language", "deu+eng"),
        default_compression_profile=preferences.get(
            "default_compression_profile", "balanced"
        ),
        default_ocr_enabled=preferences.get("default_ocr_enabled", True),
        default_skip_ocr_on_tagged=preferences.get("default_skip_ocr_on_tagged", True),
    )

    updated = await user_prefs_repo.create_or_update_preferences(prefs_doc)
    return updated.model_dump()


@app.delete("/api/v1/user/account")
@limiter.limit("30/minute")
async def delete_user_account(
    request: Request,
    body: dict[str, str],
    current_user: User = Depends(get_current_user),
):
    """Delete user account and all associated data.

    Requires email confirmation to prevent accidental deletion.
    Deletes: user profile, jobs, audit logs, preferences.

    This endpoint is disabled when authentication is disabled (returns 403).

    Args:
        request: FastAPI request object
        body: Dictionary containing email_confirmation field
        current_user: Authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: 400 if email doesn't match, 403 if auth disabled

    """
    from pdfa.auth import get_client_ip
    from pdfa.repositories import AuditLogRepository

    # Verify email confirmation
    email_confirmation = body.get("email_confirmation", "")
    if email_confirmation != current_user.email:
        raise HTTPException(
            status_code=400,
            detail="Email confirmation does not match. Account deletion cancelled.",
        )

    # Initialize repositories
    user_prefs_repo = UserPreferencesRepository()
    audit_repo = AuditLogRepository()

    # Delete all user data (cascade deletion)
    from pdfa.db import get_db

    db = get_db()

    # Delete jobs
    await db.jobs.delete_many({"user_id": current_user.user_id})

    # Delete audit logs
    await db.audit_logs.delete_many({"user_id": current_user.user_id})

    # Delete preferences
    await user_prefs_repo.delete_preferences(current_user.user_id)

    # Delete user profile
    await db.users.delete_one({"user_id": current_user.user_id})

    # Log deletion event before user is gone
    from pdfa.models import AuditLogDocument

    await audit_repo.log_event(
        AuditLogDocument(
            event_type="user_logout",  # Closest available event type
            user_id=current_user.user_id,
            timestamp=datetime.now(UTC),
            ip_address=get_client_ip(request),
            details={"reason": "account_deleted"},
        )
    )

    return {"message": "Account deleted successfully"}


# ============================================================================
# Mobile Camera Page
# ============================================================================


@app.get("/mobile/camera", response_class=HTMLResponse)
async def mobile_camera_page(request: Request):
    """Mobile camera page for capturing and syncing images to desktop.

    This page provides an optimized mobile interface for:
    - Joining a desktop pairing session
    - Capturing photos with the mobile camera
    - Basic image editing (rotation)
    - Real-time sync to desktop session

    Query Parameters:
        code: Optional pairing code to pre-fill the form

    """
    return templates.TemplateResponse("mobile_camera.html", {"request": request})


# ============================================================================
# Camera Pairing API
# ============================================================================


@app.post("/api/v1/camera/pairing/create")
@limiter.limit("10/minute")
async def create_pairing_session(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    lang: str = "en",
) -> dict[str, Any]:
    """Create new mobile-desktop pairing session.

    Returns QR code data URL and pairing code for mobile linking.

    Args:
        request: FastAPI request object
        current_user: Authenticated user (optional, depends on auth config)
        lang: Language code to pass to mobile page (en, de, es, fr)

    Returns:
        Dictionary containing:
            - session_id: UUID of the pairing session
            - pairing_code: 6-character alphanumeric code
            - qr_data: Full URL for QR code (includes pairing code and language)
            - expires_at: ISO 8601 expiration timestamp
            - ttl_seconds: Time-to-live in seconds

    Note:
        This endpoint allows anonymous access even when auth is enabled,
        because the camera pairing feature should be accessible to all users.
        The session is protected by a unique pairing code.

    """
    # Allow anonymous access for camera pairing feature
    user_id = current_user.user_id if current_user else "anonymous"
    session = await pairing_manager.create_session(user_id)

    # Build QR data URL with language parameter
    # Use X-Forwarded-Proto header to determine correct scheme (http/https)
    # This ensures HTTPS URLs when behind a reverse proxy like nginx
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")
    host = request.headers.get("Host", str(request.base_url.netloc))
    base_url = f"{forwarded_proto}://{host}"
    qr_data = f"{base_url}/mobile/camera?code={session.pairing_code}&lang={lang}"

    return {
        "session_id": session.session_id,
        "pairing_code": session.pairing_code,
        "qr_data": qr_data,
        "expires_at": session.expires_at.isoformat(),
        "ttl_seconds": int((session.expires_at - session.created_at).total_seconds()),
    }


@app.post("/api/v1/camera/pairing/join")
@limiter.limit("20/minute")
async def join_pairing_session(
    request: Request,
    pairing_code: str = Form(...),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """Join existing pairing session with code.

    Mobile device uses this endpoint to join a desktop pairing session.

    Args:
        request: FastAPI request object
        pairing_code: 6-character pairing code from desktop
        current_user: Authenticated user (optional, depends on auth config)

    Returns:
        Dictionary containing:
            - session_id: UUID of the pairing session
            - status: Session status (should be "active" after join)
            - expires_at: ISO 8601 expiration timestamp

    Raises:
        HTTPException:
            - 400 if code invalid, expired, or different user

    Note:
        This endpoint allows anonymous access even when auth is enabled,
        because mobile users joining a pairing session may not be logged in.
        The session itself is protected by the pairing code.

    """
    # Allow anonymous access for mobile pairing - session is protected by code
    user_id = current_user.user_id if current_user else "anonymous"

    try:
        session = await pairing_manager.join_session(pairing_code, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "session_id": session.session_id,
        "status": session.status,
        "expires_at": session.expires_at.isoformat(),
    }


@app.get("/api/v1/camera/pairing/status/{session_id}")
@limiter.limit("60/minute")
async def get_pairing_status(
    request: Request,
    session_id: str,
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """Get current pairing session status.

    Args:
        request: FastAPI request object
        session_id: UUID of the pairing session
        current_user: Authenticated user (optional, depends on auth config)

    Returns:
        Dictionary containing:
            - session_id: UUID of the pairing session
            - status: Current session status
            - images_synced: Number of images transferred
            - expires_at: ISO 8601 expiration timestamp

    Raises:
        HTTPException:
            - 403 if user doesn't own this session
            - 404 if session not found

    """
    session = await pairing_manager.repo.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if current_user:
        if session.desktop_user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "images_synced": session.images_synced,
        "expires_at": session.expires_at.isoformat(),
    }


@app.post("/api/v1/camera/pairing/cancel/{session_id}")
@limiter.limit("30/minute")
async def cancel_pairing_session(
    request: Request,
    session_id: str,
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, str]:
    """Cancel active pairing session.

    Args:
        request: FastAPI request object
        session_id: UUID of the pairing session
        current_user: Authenticated user (optional, depends on auth config)

    Returns:
        Dictionary with status="cancelled"

    Raises:
        HTTPException:
            - 403 if user doesn't own this session
            - 404 if session not found

    """
    session = await pairing_manager.repo.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if current_user:
        if session.desktop_user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    session.status = "cancelled"
    await pairing_manager.repo.update_session(session)

    # Notify connected devices
    connections = pairing_manager.active_connections.get(session_id, {})
    for ws in connections.values():
        try:
            await ws.send_json(
                {
                    "type": "pairing_expired",
                    "session_id": session_id,
                    "reason": "cancelled",
                }
            )
        except Exception:
            pass  # Ignore if WebSocket already closed

    return {"status": "cancelled"}


# Conversion endpoints


@app.post(
    "/convert",
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"description": "Invalid input file"},
        500: {"description": "Conversion failed"},
    },
)
@limiter.limit("10/minute")
async def convert_endpoint(
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("deu+eng"),
    pdfa_level: PdfaLevel = Form("2"),
    compression_profile: CompressionProfile = Form("balanced"),
    ocr_enabled: bool = Form(True),
    skip_ocr_on_tagged_pdfs: bool = Form(True),
    current_user: User | None = Depends(get_current_user_optional),
) -> Response:
    """Convert the uploaded PDF, Office, ODF, or image file into PDF/A or plain PDF.

    Supports PDF, DOCX, PPTX, XLSX (MS Office), ODT, ODS, ODP (OpenDocument),
    and image files (JPG, PNG, TIFF, BMP, GIF). Office, ODF, and image files
    are automatically converted to PDF before PDF/A conversion.

    Args:
        request: FastAPI request object (required for rate limiting)
        file: PDF, Office, ODF, or image file to convert.
        language: Tesseract language codes for OCR (default: 'deu+eng').
        pdfa_level: PDF/A compliance level ('1', '2', '3') or 'pdf' for plain PDF
                   (default: '2'). When 'pdf' is selected with Office documents,
                   OCRmyPDF is skipped to preserve accessibility.
        compression_profile: Compression profile to use (default: 'balanced').
        ocr_enabled: Whether to perform OCR (default: True).
        skip_ocr_on_tagged_pdfs: Skip OCR for tagged PDFs (default: True).
        current_user: Authenticated user (optional, injected by FastAPI).

    """
    logger.info(
        f"Conversion request received: filename={file.filename}, "
        f"language={language}, pdfa_level={pdfa_level}, "
        f"compression_profile={compression_profile}, ocr_enabled={ocr_enabled}, "
        f"skip_ocr_on_tagged_pdfs={skip_ocr_on_tagged_pdfs}"
    )

    # Supported MIME types
    supported_types = {
        "application/pdf",
        "application/octet-stream",
        # Office document MIME types (MS Office)
        (
            "application/vnd.openxmlformats-officedocument." "wordprocessingml.document"
        ),  # docx
        (
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),  # pptx
        (
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        ),  # xlsx
        # Open Document Format (ODF) MIME types
        "application/vnd.oasis.opendocument.text",  # odt
        "application/vnd.oasis.opendocument.spreadsheet",  # ods
        "application/vnd.oasis.opendocument.presentation",  # odp
        # Image MIME types
        "image/jpeg",  # jpg, jpeg
        "image/png",  # png
        "image/tiff",  # tiff, tif
        "image/bmp",  # bmp
        "image/gif",  # gif
    }

    if file.content_type not in supported_types:
        logger.warning(
            f"Invalid file type rejected: {file.content_type} "
            f"(filename: {file.filename})"
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Supported formats: PDF, DOCX, PPTX, XLSX, "
                "ODT, ODS, ODP, JPG, PNG, TIFF, BMP, GIF"
            ),
        )

    contents = await file.read()
    if not contents:
        logger.warning(f"Empty file rejected: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.debug(f"Processing file: {file.filename} (size: {len(contents)} bytes)")

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Determine file type
        is_office = is_office_document(file.filename or "")
        is_image = is_image_file(file.filename or "")

        # Use random filename for security (don't expose user filenames in temp storage)
        # Extract original file extension
        original_ext = Path(file.filename or "").suffix.lower() if file.filename else ""
        if not original_ext:
            if is_office:
                original_ext = ".docx"
            elif is_image:
                original_ext = ".jpg"
            else:
                original_ext = ".pdf"

        # Generate random temporary filename while preserving extension
        random_filename = f"{uuid.uuid4().hex}{original_ext}"
        input_path = tmp_path / random_filename

        logger.debug(f"Storing uploaded file with random name: {random_filename}")
        input_path.write_bytes(contents)

        try:
            # Convert Office documents to PDF first if needed
            pdf_path = input_path
            if is_office:
                logger.info(
                    f"Office document detected, converting to PDF: {file.filename}"
                )
                pdf_path = tmp_path / "converted.pdf"
                # Run blocking operation in thread pool to avoid blocking event loop
                await asyncio.to_thread(convert_office_to_pdf, input_path, pdf_path)
            elif is_image:
                logger.info(f"Image file detected, converting to PDF: {file.filename}")
                pdf_path = tmp_path / "converted.pdf"
                # Run blocking operation in thread pool to avoid blocking event loop
                await asyncio.to_thread(convert_image_to_pdf, input_path, pdf_path)

            # Convert to PDF/A or plain PDF
            output_path = tmp_path / "output.pdf"
            # Select compression configuration from profile
            selected_compression = PRESETS.get(compression_profile, compression_config)
            # Run blocking OCRmyPDF operation in thread pool to allow parallel requests
            await asyncio.to_thread(
                convert_to_pdfa,
                pdf_path,
                output_path,
                language=language,
                pdfa_level=pdfa_level,
                ocr_enabled=ocr_enabled,
                skip_ocr_on_tagged_pdfs=skip_ocr_on_tagged_pdfs,
                compression_config=selected_compression,
            )

        except FileNotFoundError as error:
            logger.error(f"File not found during conversion: {error}")
            raise HTTPException(status_code=400, detail=str(error)) from error
        except UnsupportedFormatError as error:
            logger.error(f"Unsupported file format: {error}")
            raise HTTPException(status_code=400, detail=str(error)) from error
        except OfficeConversionError as error:
            logger.error(f"Office conversion failed: {error}")
            raise HTTPException(status_code=500, detail=str(error)) from error
        except ocrmypdf_exceptions.ExitCodeException as error:
            logger.error(f"OCRmyPDF conversion failed: {error}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"OCRmyPDF failed: {error}"
            ) from error
        except Exception as error:
            logger.exception(f"Unexpected error during conversion: {error}")
            raise HTTPException(
                status_code=500, detail=f"Conversion failed: {error}"
            ) from error

        output_bytes = output_path.read_bytes()

    filename = file.filename or "converted.pdf"
    if not filename.endswith(".pdf"):
        filename = f"{Path(filename).stem}.pdf"

    logger.info(
        f"Conversion successful: {file.filename} -> {filename} "
        f"(output size: {len(output_bytes)} bytes)"
    )

    # Use RFC 5987 encoding for filenames with Unicode characters
    # This ensures compatibility with all characters including umlauts, accents, etc.
    filename_encoded = quote(filename)

    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}",
    }

    return Response(content=output_bytes, headers=headers, media_type="application/pdf")


# ============================================================================
# WebSocket-based Progress Tracking Endpoints
# ============================================================================


async def process_conversion_job(job_id: str) -> None:
    """Process a conversion job asynchronously.

    Args:
        job_id: The job ID to process

    """
    try:
        # Get job - if this fails, job doesn't exist and we can't update status
        try:
            job = job_manager.get_job(job_id)
        except JobNotFoundException as e:
            logger.error(f"Job {job_id} not found in process_conversion_job: {e}")
            # Can't update status or broadcast since job doesn't exist
            return

        # Update status to processing - catch any errors here too
        try:
            await job_manager.update_job_status(job_id, "processing")
        except Exception as e:
            logger.error(
                f"Failed to update job {job_id} status to processing: {e}",
                exc_info=True,
            )
            # Try to set to failed state
            try:
                await job_manager.update_job_status(
                    job_id, "failed", error=f"Failed to start job: {e}"
                )
            except Exception:
                pass  # Nothing more we can do
            return

        # Send initial progress message to inform client that processing has started
        initial_progress = ProgressMessage(
            job_id=job_id,
            step="Starting conversion",
            current=0,
            total=100,
            percentage=0,
            message="Preparing document for conversion...",
        )
        try:
            await job_manager.broadcast_to_job(job_id, initial_progress.to_dict())
        except Exception as broadcast_error:
            logger.warning(
                f"Failed to broadcast initial progress for job {job_id}: {broadcast_error}"
            )
            # Continue anyway - this is not critical

        # Get the current event loop BEFORE entering the thread
        # This is critical because asyncio.get_event_loop() doesn't work reliably
        # from within a thread created by asyncio.to_thread()
        event_loop = asyncio.get_running_loop()

        # Progress callback that broadcasts to WebSocket
        def progress_callback(progress: ProgressInfo) -> None:
            # Log that we received a progress update
            logger.info(
                f"Progress callback called for job {job_id}: "
                f"{progress.step} - {progress.percentage}% "
                f"({progress.current}/{progress.total})"
            )

            # Send progress update to all connected clients
            message = ProgressMessage(
                job_id=job_id,
                step=progress.step,
                current=progress.current,
                total=progress.total,
                percentage=progress.percentage,
                message=progress.message,
            )
            # Schedule broadcast from thread-safe context using the captured event loop
            try:
                future = asyncio.run_coroutine_threadsafe(
                    job_manager.broadcast_to_job(job_id, message.to_dict()), event_loop
                )
                # Wait for the broadcast to complete (with timeout)
                # Increased from 2s to 10s default to handle multiple concurrent clients
                future.result(timeout=PROGRESS_BROADCAST_TIMEOUT)
                logger.info(
                    f"Successfully broadcast progress for job {job_id}: {progress.percentage}%"
                )
            except TimeoutError:
                # Broadcasting took too long - log warning but don't fail conversion
                # This can happen with many concurrent WebSocket clients or slow networks
                logger.warning(
                    f"Progress broadcast timeout ({PROGRESS_BROADCAST_TIMEOUT}s) "
                    f"for job {job_id} at {progress.percentage}%. "
                    f"Some clients may have missed this update."
                )
            except Exception as e:
                # Log any other errors but don't fail the conversion
                logger.error(
                    f"Failed to broadcast progress for job {job_id}: {e}",
                    exc_info=True,
                )

        # Event callback that logs events to MongoDB
        async def async_event_callback(event_type: str, **kwargs) -> None:
            """Log conversion events to MongoDB for job tracking."""
            try:
                # Dynamically import the appropriate logger function
                from pdfa import event_logger

                # Map event types to logger functions
                event_loggers = {
                    "format_conversion": event_logger.log_format_conversion_event,
                    "ocr_decision": event_logger.log_ocr_decision_event,
                    "compression_selected": event_logger.log_compression_selected_event,
                    "passthrough_mode": event_logger.log_passthrough_mode_event,
                    "fallback_applied": event_logger.log_fallback_applied_event,
                }

                logger_func = event_loggers.get(event_type)
                if logger_func:
                    await logger_func(job_id=job_id, **kwargs)
                else:
                    logger.warning(f"Unknown event type: {event_type}")
            except Exception as e:
                # Log errors but don't fail conversion
                logger.error(
                    f"Failed to log event {event_type} for job {job_id}: {e}",
                    exc_info=True,
                )

        # Get the current event loop to schedule coroutines from worker thread
        main_loop = asyncio.get_running_loop()

        # Create synchronous wrapper for event callback that works from
        # worker threads
        def event_callback(event_type: str, **kwargs) -> None:
            """Schedule async callback in main loop."""
            # Schedule the coroutine in the main event loop from worker thread
            future = asyncio.run_coroutine_threadsafe(
                async_event_callback(event_type, **kwargs), main_loop
            )
            # Wait for completion with timeout to avoid blocking worker thread
            try:
                future.result(timeout=5.0)  # 5 second timeout
            except Exception as e:
                logger.error(f"Event callback failed for {event_type}: {e}")

        # Determine file type and convert
        config = job.config
        pdf_path = job.input_path

        # Convert office/image to PDF if needed
        if is_office_document(job.filename):
            logger.info(f"Converting Office document for job {job_id}")
            pdf_path = job.input_path.parent / f"{job.input_path.stem}.pdf"

            # Track conversion time
            import time

            start_time = time.time()

            await asyncio.to_thread(
                convert_office_to_pdf,
                job.input_path,
                pdf_path,
                progress_callback=progress_callback,
            )

            conversion_time = time.time() - start_time

            # Log format conversion event
            await async_event_callback(
                "format_conversion",
                source_format=job.filename.rsplit(".", 1)[-1].lower(),
                target_format="pdf",
                conversion_required=True,
                converter="office_to_pdf",
                conversion_time_seconds=conversion_time,
            )

        elif is_image_file(job.filename):
            logger.info(f"Converting image to PDF for job {job_id}")
            pdf_path = job.input_path.parent / f"{job.input_path.stem}.pdf"

            # Track conversion time
            import time

            start_time = time.time()

            # Multi-image mode: combine multiple images into single PDF
            if job.input_paths and len(job.input_paths) > 1:
                logger.info(f"Multi-image job detected: {len(job.input_paths)} images")
                await asyncio.to_thread(
                    convert_images_to_pdf, job.input_paths, pdf_path
                )
            else:
                # Single-image mode (backward compatibility)
                await asyncio.to_thread(convert_image_to_pdf, job.input_path, pdf_path)

            conversion_time = time.time() - start_time

            # Log format conversion event
            num_images = len(job.input_paths) if job.input_paths else 1
            await async_event_callback(
                "format_conversion",
                source_format=job.filename.rsplit(".", 1)[-1].lower(),
                target_format="pdf",
                conversion_required=True,
                converter="multi_image_to_pdf" if num_images > 1 else "image_to_pdf",
                conversion_time_seconds=conversion_time,
                num_images=num_images,
            )
        else:
            # Direct PDF - no conversion needed
            await async_event_callback(
                "format_conversion",
                source_format="pdf",
                target_format="pdf",
                conversion_required=False,
            )

        # Convert to PDF/A
        output_path = job.input_path.parent / f"{job.input_path.stem}_pdfa.pdf"

        # Get compression config
        profile = config.get("compression_profile", "balanced")
        selected_compression = PRESETS.get(profile, PRESETS["balanced"])

        await asyncio.to_thread(
            convert_to_pdfa,
            pdf_path,
            output_path,
            language=config.get("language", "deu+eng"),
            pdfa_level=config.get("pdfa_level", "2"),
            ocr_enabled=config.get("ocr_enabled", True),
            skip_ocr_on_tagged_pdfs=config.get("skip_ocr_on_tagged_pdfs", True),
            compression_config=selected_compression,
            progress_callback=progress_callback,
            event_callback=event_callback,
            cancel_event=job.cancel_event,
        )

        # Job completed successfully
        await job_manager.update_job_status(
            job_id, "completed", output_path=output_path
        )

        # Get file size
        file_size = output_path.stat().st_size

        # Send completion message
        message = CompletedMessage(
            job_id=job_id,
            download_url=f"/download/{job_id}",
            filename=f"{job.filename.rsplit('.', 1)[0]}_pdfa.pdf",
            size_bytes=file_size,
        )
        await job_manager.broadcast_to_job(job_id, message.to_dict())

    except JobCancelledException:
        logger.info(f"Job {job_id} was cancelled")
        await job_manager.update_job_status(job_id, "cancelled")
        message = CancelledMessage(job_id=job_id)
        await job_manager.broadcast_to_job(job_id, message.to_dict())

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)

        # Try to update status and broadcast error - wrap in try/except to ensure
        # we always try to notify the client even if status update fails
        try:
            await job_manager.update_job_status(job_id, "failed", error=str(e))
        except Exception as update_error:
            logger.error(
                f"Failed to update status for job {job_id}: {update_error}",
                exc_info=True,
            )

        # Send error message to client - always try this even if status update failed
        try:
            error_code = "CONVERSION_FAILED"
            if isinstance(e, OfficeConversionError):
                error_code = "OFFICE_CONVERSION_FAILED"
            elif isinstance(e, ocrmypdf_exceptions.PriorOcrFoundError):
                error_code = "OCR_ALREADY_EXISTS"

            message = ErrorMessage(
                job_id=job_id,
                error_code=error_code,
                message=str(e),
            )
            await job_manager.broadcast_to_job(job_id, message.to_dict())
        except Exception as broadcast_error:
            logger.error(
                f"Failed to broadcast error message for job {job_id}: {broadcast_error}",
                exc_info=True,
            )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time conversion progress and mobile-desktop pairing.

    Security: Supports two authentication methods:
        1. NEW (Secure): Auth message as first WebSocket message (token not in URL)
        2. OLD (Deprecated): Token in query parameter (for backward compatibility)

    Protocol:
        Client sends: AuthMessage (first), SubmitJobMessage, CancelJobMessage, PingMessage,
                     RegisterPairingMessage, SyncImageMessage
        Server sends: JobAcceptedMessage, ProgressMessage, CompletedMessage,
                     ErrorMessage, CancelledMessage, PongMessage,
                     ImageSyncedMessage, PairingPeerStatusMessage, PairingExpiredMessage

    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    # Security: Check if auth is enabled
    current_user: User | None = None
    authenticated = False

    if auth_config_instance.enabled:
        # Try query parameter first (deprecated but backward compatible)
        token = websocket.query_params.get("token")
        if token:
            logger.warning(
                "WebSocket auth via query parameter is deprecated. "
                "Use AuthMessage instead to prevent token logging."
            )
            try:
                authenticator = WebSocketAuthenticator(auth_config_instance)
                current_user = await authenticator.authenticate_websocket(websocket)
                authenticated = True
                logger.info(f"WebSocket authenticated for user: {current_user.email}")
            except HTTPException as e:
                logger.warning(f"WebSocket authentication failed: {e.detail}")
                await websocket.close(code=1008, reason=e.detail)
                return
        # If no token in query params, expect AuthMessage as first message
        else:
            logger.info("Waiting for AuthMessage (secure auth method)")
            authenticated = False  # Will be set to True after AuthMessage

    current_job_id: str | None = None

    # Track pairing session
    current_pairing_session: str | None = None
    pairing_role: str | None = None

    try:
        async for message_data in websocket.iter_json():
            try:
                # Parse incoming message
                message = parse_client_message(message_data)

                # Security: Handle authentication message (new secure method)
                if isinstance(message, AuthMessage):
                    if not auth_config_instance.enabled:
                        logger.warning("Received AuthMessage but auth is disabled")
                        continue  # Ignore auth message if auth is disabled

                    if authenticated:
                        logger.warning("Received AuthMessage but already authenticated")
                        continue  # Already authenticated via query parameter

                    # Authenticate using token from message body
                    try:
                        from pdfa.auth import decode_jwt_token

                        current_user = decode_jwt_token(
                            message.token, auth_config_instance
                        )
                        authenticated = True
                        logger.info(
                            f"WebSocket authenticated via AuthMessage for user: {current_user.email}"
                        )
                        # Send acknowledgment (success is implicit, errors close connection)
                        continue
                    except HTTPException as e:
                        logger.warning(f"AuthMessage authentication failed: {e.detail}")
                        await websocket.close(code=1008, reason=e.detail)
                        return

                # Security: Enforce authentication for protected operations
                # Exception: Pairing messages (RegisterPairingMessage, SyncImageMessage)
                # use session-based security via pairing codes, not user auth
                is_pairing_message = isinstance(
                    message, (RegisterPairingMessage, SyncImageMessage)
                )
                if auth_config_instance.enabled and not authenticated and not is_pairing_message:
                    error_msg = ErrorMessage(
                        job_id="",
                        error_code="UNAUTHORIZED",
                        message="Authentication required. Send AuthMessage first.",
                    )
                    await websocket.send_json(error_msg.to_dict())
                    logger.warning("Unauthenticated client tried to send message")
                    continue

                if isinstance(message, SubmitJobMessage):
                    # Create new job (supports both single-file and multi-file modes)
                    if message.multi_file_mode:
                        # Multi-file mode: multiple images to single PDF
                        files_data = message.get_files_bytes()
                        job = job_manager.create_job(
                            filename="",  # Not used in multi-file mode
                            file_data=b"",  # Not used in multi-file mode
                            config=message.config or {},
                            user_id=current_user.user_id if current_user else None,
                            filenames=message.filenames,
                            files_data=files_data,
                        )
                    else:
                        # Single-file mode (backward compatibility)
                        file_data = message.get_file_bytes()
                        job = job_manager.create_job(
                            filename=message.filename,
                            file_data=file_data,
                            config=message.config or {},
                            user_id=current_user.user_id if current_user else None,
                        )
                    current_job_id = job.job_id

                    # Register WebSocket for this job
                    job_manager.register_websocket(job.job_id, websocket)

                    # Send job accepted message
                    response = JobAcceptedMessage(
                        job_id=job.job_id,
                        status="queued",
                    )
                    await websocket.send_json(response.to_dict())

                    # Start processing job in background
                    asyncio.create_task(process_conversion_job(job.job_id))

                elif isinstance(message, CancelJobMessage):
                    # Cancel job
                    try:
                        await job_manager.cancel_job(message.job_id)
                        logger.info(f"Job {message.job_id} cancel requested")
                    except JobNotFoundException:
                        error_msg = ErrorMessage(
                            job_id=message.job_id,
                            error_code="JOB_NOT_FOUND",
                            message=f"Job {message.job_id} not found",
                        )
                        await websocket.send_json(error_msg.to_dict())

                elif isinstance(message, RegisterPairingMessage):
                    # Register WebSocket for pairing session
                    session = await pairing_manager.repo.get_session(message.session_id)

                    if not session:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error_code": "INVALID_SESSION",
                                "message": "Invalid session ID",
                            }
                        )
                        continue

                    # Verify ownership based on role
                    user_id = current_user.user_id if current_user else "anonymous"

                    if message.role == "desktop":
                        if session.desktop_user_id != user_id:
                            logger.warning(
                                f"Unauthorized desktop registration attempt: "
                                f"session user {session.desktop_user_id} != {user_id}"
                            )
                            await websocket.close(code=1008, reason="Unauthorized")
                            return
                    elif message.role == "mobile":
                        if not session.mobile_user_id:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "error_code": "SESSION_NOT_JOINED",
                                    "message": "Session not yet joined",
                                }
                            )
                            continue
                        if session.mobile_user_id != user_id:
                            logger.warning(
                                f"Unauthorized mobile registration attempt: "
                                f"session user {session.mobile_user_id} != {user_id}"
                            )
                            await websocket.close(code=1008, reason="Unauthorized")
                            return

                    # Register WebSocket for pairing
                    await pairing_manager.register_websocket(
                        message.session_id, message.role, websocket
                    )
                    current_pairing_session = message.session_id
                    pairing_role = message.role

                    logger.info(
                        f"Registered {message.role} WebSocket for pairing session "
                        f"{message.session_id}"
                    )

                elif isinstance(message, SyncImageMessage):
                    # Sync image from mobile to desktop
                    try:
                        await pairing_manager.sync_image(
                            message.session_id,
                            message.image_data,
                            message.image_index,
                            message.metadata,
                        )
                        logger.info(
                            f"Synced image {message.image_index} for session "
                            f"{message.session_id}"
                        )
                    except ValueError as e:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error_code": "SYNC_FAILED",
                                "message": str(e),
                            }
                        )
                        logger.warning(f"Image sync failed: {e}")

                elif isinstance(message, PingMessage):
                    response = PongMessage()
                    await websocket.send_json(response.to_dict())

            except ValueError as e:
                # Invalid message format
                logger.error(f"Invalid WebSocket message: {e}")
                error_msg = ErrorMessage(
                    error_code="INVALID_MESSAGE",
                    message=str(e),
                )
                await websocket.send_json(error_msg.to_dict())

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Unregister WebSocket for job
        if current_job_id:
            job_manager.unregister_websocket(current_job_id, websocket)

        # Unregister WebSocket for pairing
        if current_pairing_session and pairing_role:
            await pairing_manager.unregister_websocket(
                current_pairing_session, pairing_role
            )
            logger.info(
                f"Unregistered {pairing_role} from pairing session "
                f"{current_pairing_session}"
            )

        logger.info("WebSocket connection closed")


@app.get("/api/v1/jobs/history")
async def get_job_history(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Get conversion job history for the authenticated user.

    Returns a paginated list of jobs sorted by creation date (newest first).
    This endpoint requires authentication.

    Args:
        limit: Maximum number of jobs to return (default: 50, max: 100)
        offset: Number of jobs to skip for pagination (default: 0)
        status: Filter by job status (optional): queued, processing, completed, failed, cancelled
        current_user: Authenticated user (injected by dependency)

    Returns:
        Job history with pagination info:
        - jobs: List of job objects
        - total: Total number of jobs (for current filter)
        - limit: Items per page
        - offset: Current offset

    Raises:
        HTTPException: If authentication fails (401)

    Example:
        GET /api/v1/jobs/history?limit=10&offset=0&status=completed
        Response:
        {
            "jobs": [
                {
                    "job_id": "abc123",
                    "filename": "document.pdf",
                    "status": "completed",
                    "created_at": "2024-12-12T10:30:00Z",
                    "completed_at": "2024-12-12T10:32:30Z",
                    "duration_seconds": 150.5,
                    "file_size_input": 1048576,
                    "file_size_output": 524288,
                    "compression_ratio": 0.5
                },
                ...
            ],
            "total": 42,
            "limit": 10,
            "offset": 0
        }

    """
    # Validate limit
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    # Validate status filter
    valid_statuses = ["queued", "processing", "completed", "failed", "cancelled"]
    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    # Fetch jobs from MongoDB
    job_repo = JobRepository()
    jobs = await job_repo.get_user_jobs(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
        status=status,
    )

    # Get total count for pagination (using same filters)
    # Note: This is a simplified version. For production, you might want to cache this
    # or use a more efficient counting mechanism
    all_jobs = await job_repo.get_user_jobs(
        user_id=current_user.user_id,
        limit=1000,  # Get a large number to count
        offset=0,
        status=status,
    )
    total = len(all_jobs)

    # Convert JobDocument to dict for JSON response
    jobs_dict = [
        {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "file_size_input": job.file_size_input,
            "file_size_output": job.file_size_output,
            "compression_ratio": job.compression_ratio,
            "error": job.error,
            "config": job.config,
        }
        for job in jobs
    ]

    return {
        "jobs": jobs_dict,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get the current status of a conversion job.

    This endpoint is useful for clients that have lost their WebSocket connection
    and want to poll for job status as a fallback mechanism.

    Args:
        job_id: The job ID
        current_user: Authenticated user (if auth enabled)

    Returns:
        Job status information including:
        - job_id: The job identifier
        - status: Current status (queued, running, completed, failed, cancelled)
        - progress: Current progress percentage (0-100)
        - message: Latest progress message
        - created_at: Job creation timestamp
        - download_url: Download URL (only if status is completed)
        - filename: Original filename
        - error: Error message (only if status is failed)

    Raises:
        HTTPException: If job not found (404) or access denied (403)

    Example:
        GET /api/v1/jobs/abc123/status
        Response:
        {
            "job_id": "abc123",
            "status": "running",
            "progress": 45.5,
            "message": "Processing page 5 of 10",
            "created_at": "2024-12-12T10:30:00Z",
            "filename": "document.pdf"
        }

    """
    try:
        job = job_manager.get_job(job_id)
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check job ownership if auth is enabled
    if auth_config_instance.enabled and current_user:
        if job.user_id != current_user.user_id:
            logger.warning(
                f"User {current_user.email} attempted to access job {job_id} "
                f"owned by {job.user_id}"
            )
            raise HTTPException(status_code=403, detail="Access denied to this job")

    # Build response with current job status
    response = {
        "job_id": job_id,
        "status": job.status,
        "progress": getattr(job, "progress_percentage", 0.0),
        "message": getattr(job, "progress_message", ""),
        "created_at": (
            job.created_at.isoformat() if hasattr(job, "created_at") else None
        ),
        "filename": job.filename,
    }

    # Add download URL if job is completed
    if job.status == "completed":
        response["download_url"] = f"/download/{job_id}"
        response["filename_output"] = f"{job.filename.rsplit('.', 1)[0]}_pdfa.pdf"

    # Add error message if job failed
    if job.status == "failed" and hasattr(job, "error_message"):
        response["error"] = job.error_message

    logger.debug(f"Status query for job {job_id}: {job.status}")

    return response


@app.get("/download/{job_id}")
async def download_result(
    job_id: str,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Download the converted PDF for a completed job.

    Args:
        job_id: The job ID
        current_user: Authenticated user (if auth enabled)

    Returns:
        The converted PDF file

    Raises:
        HTTPException: If job not found, not completed, or access denied

    """
    try:
        job = job_manager.get_job(job_id)
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check job ownership if auth is enabled
    if auth_config_instance.enabled and current_user:
        if job.user_id != current_user.user_id:
            logger.warning(
                f"User {current_user.email} attempted to download job {job_id} "
                f"owned by {job.user_id}"
            )
            raise HTTPException(status_code=403, detail="Access denied to this job")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job.status})",
        )

    # Check if output path exists
    if not job.output_path:
        logger.error(f"Job {job_id} has no output_path despite being completed")
        raise HTTPException(
            status_code=500,
            detail="Job completed but output file path is missing",
        )

    # Check file existence - handle race condition where file might be deleted
    # between status check and FileResponse
    if not job.output_path.exists():
        logger.error(
            f"Output file for job {job_id} not found at {job.output_path} "
            "(may have been cleaned up)"
        )
        raise HTTPException(
            status_code=404,
            detail="Output file not found (may have been cleaned up after TTL expired)",
        )

    filename = f"{job.filename.rsplit('.', 1)[0]}_pdfa.pdf"

    logger.info(f"Downloading result for job {job_id}: {filename}")

    # Use FileResponse which handles the file reading
    # Note: There's still a small race condition window between exists() check
    # and FileResponse reading the file, but FileResponse will handle
    # FileNotFoundError gracefully
    return FileResponse(
        path=job.output_path,
        media_type="application/pdf",
        filename=filename,
    )
