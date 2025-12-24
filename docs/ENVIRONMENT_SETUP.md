# Environment Configuration Setup

**Also available in:** [Deutsch](ENVIRONMENT_SETUP.de.md)

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your configuration**

3. **Start the service:**
   ```bash
   uvicorn pdfa.api:app --env-file .env
   ```

---

## Authentication Setup (Optional)

The service supports optional Google OAuth 2.0 authentication. By default, authentication is **disabled**.

### Step 1: Enable Authentication

In your `.env` file, set:

```bash
PDFA_ENABLE_AUTH=true
```

### Step 2: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure the OAuth consent screen:
   - User Type: Internal (for organization) or External (for public)
   - App name: "PDF/A Service" (or your preferred name)
   - Scopes: Add `openid`, `email`, `profile`
6. Create OAuth 2.0 Client ID:
   - Application type: **Web application**
   - Name: "PDF/A Service"
   - Authorized redirect URIs:
     - For local: `http://localhost:8000/auth/callback`
     - For production: `https://yourdomain.com/auth/callback`
7. Copy the **Client ID** and **Client Secret**

### Step 3: Generate JWT Secret Key

Generate a secure random key (minimum 32 characters):

```bash
openssl rand -hex 32
```

Or use Python:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Configure `.env` File

Edit your `.env` file with the values from steps 2 and 3:

```bash
# Enable authentication
PDFA_ENABLE_AUTH=true

# Google OAuth credentials (from Step 2)
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz

# JWT secret (from Step 3)
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

# OAuth redirect URI (must match Google Console)
REDIRECT_URI=http://localhost:8000/auth/callback

# Optional: JWT configuration
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
```

### Step 5: Verify Configuration

Start the service and check the logs:

```bash
uvicorn pdfa.api:app --env-file .env --reload
```

You should see:
```
INFO:     Authentication ENABLED - Google OAuth + JWT
```

If authentication is disabled, you'll see:
```
INFO:     Authentication DISABLED (PDFA_ENABLE_AUTH=false)
```

---

## Configuration Reference

### Authentication Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `PDFA_ENABLE_AUTH` | No | `false` | Enable/disable authentication (`true`/`false`) |
| `GOOGLE_CLIENT_ID` | Yes* | - | Google OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | Yes* | - | Google OAuth 2.0 Client Secret |
| `JWT_SECRET_KEY` | Yes* | - | Secret key for JWT signing (min 32 chars) |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm (`HS256`, `HS384`, `HS512`) |
| `JWT_EXPIRY_HOURS` | No | `24` | JWT token expiry time in hours |
| `REDIRECT_URI` | No | `http://localhost:8000/auth/callback` | OAuth redirect URI |

\* Required only when `PDFA_ENABLE_AUTH=true`

### Service Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `HOST` | No | `0.0.0.0` | Server host address |
| `PORT` | No | `8000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Security Best Practices

### JWT Secret Key

✅ **DO:**
- Generate a **random** secret key (min 32 characters)
- Use `openssl rand -hex 32` or similar
- Keep the secret key **confidential**
- Use different keys for development/production
- Store in environment variables or secret management

❌ **DON'T:**
- Use predictable values like "secret" or "password"
- Commit the secret key to Git
- Share the secret key publicly
- Reuse the same key across projects

### OAuth Credentials

✅ **DO:**
- Keep Client Secret confidential
- Use different OAuth apps for dev/prod
- Restrict authorized redirect URIs
- Regularly rotate credentials
- Use internal user type for organizations

❌ **DON'T:**
- Commit OAuth secrets to Git
- Share credentials publicly
- Use production credentials in development

### Production Deployment

For production deployments:

1. **Use HTTPS** for all redirect URIs
2. **Enable CORS** restrictions
3. **Use environment-specific** OAuth apps
4. **Rotate secrets** regularly
5. **Monitor** authentication logs
6. **Use Redis/database** for OAuth state storage (not in-memory)

---

## Testing the Setup

### 1. Test Without Authentication (Default)

```bash
# .env file:
PDFA_ENABLE_AUTH=false

# Start server
uvicorn pdfa.api:app --env-file .env

# Test API (no auth required)
curl http://localhost:8000/health
# → {"status":"healthy"}
```

### 2. Test With Authentication

```bash
# .env file:
PDFA_ENABLE_AUTH=true
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
JWT_SECRET_KEY=your-jwt-secret

# Start server
uvicorn pdfa.api:app --env-file .env

# Open browser
open http://localhost:8000

# Click "Sign in with Google"
# After login, you should see the upload interface
```

### 3. Test API Authentication

```bash
# Get token via web UI login, then:
curl http://localhost:8000/convert \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test.pdf"
```

---

## Troubleshooting

### "Invalid state parameter" Error

**Cause:** OAuth state not persisted between requests (fixed in latest version)

**Solution:** Update to latest version with module-level state storage

### "GOOGLE_CLIENT_ID is required" Error

**Cause:** Authentication enabled but credentials not configured

**Solution:**
1. Check `.env` file exists and is loaded
2. Verify `GOOGLE_CLIENT_ID` is set in `.env`
3. Make sure `.env` file is in the working directory

### "JWT_SECRET_KEY must be at least 32 characters" Error

**Cause:** JWT secret too short

**Solution:** Generate a longer secret:
```bash
openssl rand -hex 32
```

### "redirect_uri_mismatch" Error

**Cause:** Redirect URI mismatch between `.env` and Google Console

**Solution:**
1. Check `REDIRECT_URI` in `.env`
2. Verify it matches exactly in Google Cloud Console
3. Ensure protocol (http/https) matches

### Authentication Not Working

**Debug steps:**
1. Check server logs on startup
2. Verify `PDFA_ENABLE_AUTH=true` in `.env`
3. Test `/auth/login` endpoint manually
4. Check browser console for errors
5. Verify OAuth app is enabled in Google Console

---

## Example `.env` Files

### Development (No Auth)

```bash
PDFA_ENABLE_AUTH=false
LOG_LEVEL=DEBUG
```

### Development (With Auth)

```bash
PDFA_ENABLE_AUTH=true
GOOGLE_CLIENT_ID=123456-dev.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dev-secret
JWT_SECRET_KEY=dev-secret-key-abcdef1234567890abcdef1234567890
REDIRECT_URI=http://localhost:8000/auth/callback
LOG_LEVEL=DEBUG
```

### Production

```bash
PDFA_ENABLE_AUTH=true
GOOGLE_CLIENT_ID=123456-prod.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=${GOOGLE_SECRET_FROM_VAULT}
JWT_SECRET_KEY=${JWT_SECRET_FROM_VAULT}
REDIRECT_URI=https://pdfa.yourdomain.com/auth/callback
JWT_EXPIRY_HOURS=12
LOG_LEVEL=INFO
```

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Project SECURITY.md](../SECURITY.md)
