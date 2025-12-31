# Authentication Guide

The service supports optional Google OAuth 2.0 authentication to restrict access to authorized users. When enabled, users must sign in with their Google account to use the web interface and API.

📚 **Detailed Setup Guide:** See [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) ([Deutsch](ENVIRONMENT_SETUP.de.md)) for complete setup instructions, troubleshooting, and best practices.

## Quick Setup

1. **Copy example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and configure authentication** (see detailed guide above)

3. **Start service:**
   ```bash
   uvicorn pdfa.api:app --env-file .env
   ```

## Enabling Authentication

Authentication is **disabled by default**. To enable it, configure the following environment variables:

```bash
# Enable authentication
export PDFA_ENABLE_AUTH=true

# Google OAuth credentials (from Google Cloud Console)
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# JWT secret key (generate with: openssl rand -hex 32)
export JWT_SECRET_KEY="your-secret-key-min-32-chars"

# Optional: Customize JWT expiry (default: 24 hours)
export JWT_EXPIRY_HOURS=24

# Optional: OAuth callback URL (default: http://localhost:8000/auth/callback)
export OAUTH_REDIRECT_URI="http://localhost:8000/auth/callback"
```

## Default User (When Authentication Disabled)

When authentication is disabled (`PDFA_ENABLE_AUTH=false`), the service automatically creates a local default user to enable features like job history and persistent storage without requiring OAuth setup.

The default user can be customized via environment variables:

```bash
# Default user configuration (only used when PDFA_ENABLE_AUTH=false)
export DEFAULT_USER_ID="local-default"        # Default user ID
export DEFAULT_USER_EMAIL="local@localhost"    # Default user email
export DEFAULT_USER_NAME="Local User"          # Default user display name
```

**How it works:**
- On service startup, if authentication is disabled, a default user is created in MongoDB
- All API operations use this default user automatically
- Job history (`GET /api/v1/jobs/history`) returns jobs for the default user
- WebSocket connections are attributed to the default user
- This is **idempotent** - restarting the service won't create duplicate users

**Use cases:**
- ✅ Local development without OAuth setup
- ✅ Single-user deployments
- ✅ Testing and prototyping
- ⚠️  Not recommended for multi-user production deployments (use OAuth instead)

## Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Select **Web application** as application type
6. Add authorized redirect URIs:
   - For local development: `http://localhost:8000/auth/callback`
   - For production: `https://your-domain.com/auth/callback`
7. Copy the **Client ID** and **Client Secret**
8. Set them as environment variables

## Using the API with Authentication

When authentication is enabled, API requests require a JWT bearer token:

```bash
# Step 1: Obtain a token (use the web interface to login, then extract from browser)
# Or implement the OAuth flow in your client application

# Step 2: Make authenticated API requests
curl -X POST "http://localhost:8000/convert" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf;type=application/pdf" \
  --output output.pdf
```

## Web Interface with Authentication

When authentication is enabled:
1. Users are presented with a "Sign in with Google" button
2. After successful login, the user's profile is displayed in the top bar
3. All API calls from the web interface include the JWT token automatically
4. Users can sign out using the "Sign Out" button

## Authentication Features

- **User-scoped jobs**: Each user can only access their own conversion jobs
- **Secure token storage**: JWT tokens stored in browser localStorage
- **Automatic auth detection**: Web interface auto-detects if auth is enabled
- **24-hour token expiry**: Users must re-login daily (configurable)
- **WebSocket authentication**: Real-time progress updates are also authenticated

## Public Endpoints (Always Accessible)

Even with authentication enabled, these endpoints remain public:
- `GET /health` - Health check for monitoring
- `GET /auth/login` - Initiates OAuth login flow
- `GET /auth/callback` - Handles OAuth callback
- `GET /docs` - API documentation (Swagger UI)

## Disabling Authentication

To disable authentication, simply remove or set to `false`:

```bash
export PDFA_ENABLE_AUTH=false
# or remove the variable entirely
```

When disabled, all endpoints are publicly accessible without authentication (default behavior).
