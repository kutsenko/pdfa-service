"""Pydantic models for MongoDB documents.

This module defines the data models for all MongoDB collections used in the
pdfa-service. These models provide validation, serialization, and type safety
for database operations.

All models use Pydantic BaseModel for automatic validation and serialization
to/from MongoDB BSON format.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class UserDocument(BaseModel):
    """User profile document stored in MongoDB.

    Stores minimal user information from Google OAuth along with login statistics.
    User profiles are created/updated on each successful login.

    Attributes:
        user_id: Google user ID from OAuth 'sub' field (unique)
        email: User email address
        name: Display name
        picture: Profile picture URL (optional)
        created_at: Account creation timestamp
        last_login_at: Last successful login timestamp
        login_count: Total number of successful logins

    """

    user_id: str
    email: str
    name: str
    picture: str | None = None
    created_at: datetime
    last_login_at: datetime
    login_count: int = 1

    model_config = {"arbitrary_types_allowed": True}


class UserPreferencesDocument(BaseModel):
    """User preferences for default conversion parameters.

    Stores user's preferred default settings for the PDF converter.
    These defaults are auto-applied when the user visits the converter form.

    Attributes:
        user_id: User identifier (unique index)
        default_pdfa_level: Preferred PDF type (standard, 1, 2, or 3)
        default_ocr_language: Preferred OCR language code (e.g., "deu+eng")
        default_compression_profile: Preferred compression setting
        default_ocr_enabled: Whether OCR should be enabled by default
        default_skip_ocr_on_tagged: Whether to skip OCR for tagged PDFs by default
        updated_at: Last update timestamp

    """

    user_id: str
    default_pdfa_level: Literal["standard", "1", "2", "3"] = "2"
    default_ocr_language: str = "deu+eng"
    default_compression_profile: Literal[
        "balanced", "quality", "aggressive", "minimal"
    ] = "balanced"
    default_ocr_enabled: bool = True
    default_skip_ocr_on_tagged: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}


class JobEvent(BaseModel):
    """Single event in a job's execution history.

    Events capture decision points and actions during job processing,
    providing a detailed audit trail for troubleshooting and analytics.

    Event types track key decisions and milestones:
    - format_conversion: Office/Image→PDF conversion
    - ocr_decision: Decision to perform/skip OCR with reasoning
    - compression_selected: Compression profile choice
    - passthrough_mode: Pass-through mode activated
    - fallback_applied: Fallback tier used (tier 2 or 3)
    - job_timeout: Job exceeded timeout limit
    - job_cleanup: Job resources cleaned up

    Attributes:
        timestamp: When the event occurred (UTC, auto-generated)
        event_type: Category of event (from predefined types)
        message: Human-readable description in English
        details: Structured event-specific data (JSON-serializable dict)

    Example:
        >>> event = JobEvent(
        ...     event_type="ocr_decision",
        ...     message="OCR skipped due to tagged PDF",
        ...     details={"reason": "tagged_pdf", "has_struct_tree_root": True}
        ... )

    """

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: Literal[
        "format_conversion",
        "ocr_decision",
        "compression_selected",
        "passthrough_mode",
        "fallback_applied",
        "job_timeout",
        "job_cleanup",
    ]
    message: str
    details: dict[str, Any]

    model_config = {"arbitrary_types_allowed": True}


class JobDocument(BaseModel):
    """Conversion job document stored in MongoDB.

    Stores metadata for all conversion jobs, providing persistent history and
    analytics. Jobs are created when conversion starts and updated as they progress.

    TTL: Jobs are automatically deleted after 90 days (configurable).

    Attributes:
        job_id: Unique job identifier (UUID)
        user_id: User who created the job (None if auth disabled)
        status: Current job status
        filename: Original input filename
        config: Conversion configuration parameters
        created_at: Job creation timestamp
        started_at: Processing start timestamp (None if queued)
        completed_at: Completion timestamp (None if not completed)
        duration_seconds: Processing duration in seconds (None if not completed)
        file_size_input: Input file size in bytes (None if not measured)
        file_size_output: Output file size in bytes (None if not completed)
        compression_ratio: Output/input size ratio (None if not completed)
        error: Error message if failed (None if successful)
        progress: Current progress information (optional)

    """

    job_id: str
    user_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    filename: str
    config: dict[str, Any]
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    file_size_input: int | None = None
    file_size_output: int | None = None
    compression_ratio: float | None = None
    error: str | None = None
    progress: dict[str, Any] | None = None
    events: list[JobEvent] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("compression_ratio", mode="before")
    @classmethod
    def compute_compression_ratio(cls, v: float | None, info) -> float | None:
        """Compute compression ratio if not provided."""
        if v is not None:
            return v
        # If compression_ratio not provided, try to compute from file sizes
        data = info.data
        if (
            data.get("file_size_input")
            and data.get("file_size_output")
            and data["file_size_input"] > 0
        ):
            return data["file_size_output"] / data["file_size_input"]
        return None


class OAuthStateDocument(BaseModel):
    """OAuth state token document for CSRF protection.

    Stores OAuth state tokens during the authorization flow to prevent CSRF attacks.
    State tokens are created when initiating OAuth login and validated during callback.

    TTL: States are automatically deleted after 10 minutes (expired tokens).

    Attributes:
        state: URL-safe random state token (unique)
        created_at: Token creation timestamp
        ip_address: Client IP address that initiated OAuth
        user_agent: Client user agent string (for audit purposes)

    """

    state: str
    created_at: datetime
    ip_address: str
    user_agent: str | None = None

    model_config = {"arbitrary_types_allowed": True}


class AuditLogDocument(BaseModel):
    """Audit log document for tracking user and system events.

    Stores audit trail for security, compliance, and analytics purposes.
    All significant events (logins, job operations, auth failures) are logged.

    TTL: Audit logs are automatically deleted after 1 year (configurable).

    Attributes:
        event_type: Type of event (user_login, job_created, etc.)
        user_id: User associated with event (None for system events)
        timestamp: Event occurrence timestamp
        ip_address: Client IP address
        user_agent: Client user agent string (optional)
        details: Event-specific additional data (optional)

    """

    event_type: Literal[
        "user_login",
        "user_logout",
        "job_created",
        "job_completed",
        "job_failed",
        "job_cancelled",
        "api_call",
        "auth_failure",
        "auth_token_refresh",
    ]
    user_id: str | None = None
    timestamp: datetime
    ip_address: str
    user_agent: str | None = None
    details: dict[str, Any] | None = None

    model_config = {"arbitrary_types_allowed": True}


# Type aliases for convenience
JobStatus = Literal["queued", "processing", "completed", "failed", "cancelled"]
EventType = Literal[
    "user_login",
    "user_logout",
    "job_created",
    "job_completed",
    "job_failed",
    "job_cancelled",
    "api_call",
    "auth_failure",
    "auth_token_refresh",
]
