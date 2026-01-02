# OAuth Setup for localhost:8000

Quick guide to enable Google OAuth authentication on localhost:8000.

## Prerequisites

- Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- OpenSSL installed (for generating JWT secret)

## Step 1: Google Cloud Console Setup

1. **Go to Google Cloud Console:**
   - Visit https://console.cloud.google.com/
   - Create a new project or select an existing one

2. **Enable Google+ API (if not already enabled):**
   - Navigate to **APIs & Services** → **Library**
   - Search for "Google+ API" and enable it

3. **Create OAuth 2.0 Credentials:**
   - Navigate to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - If prompted, configure the OAuth consent screen first:
     - User Type: External (for testing) or Internal (for organization)
     - Fill in application name (e.g., "PDF/A Converter Local")
     - Add your email as developer contact
     - Save and continue

4. **Configure OAuth Client:**
   - Application type: **Web application**
   - Name: "PDF/A Converter - localhost"
   - **Authorized JavaScript origins:**
     - Add: `http://localhost:8000`
   - **Authorized redirect URIs:**
     - Add: `http://localhost:8000/auth/callback`
   - Click **Create**

5. **Copy Credentials:**
   - Copy the **Client ID** (ends with `.apps.googleusercontent.com`)
   - Copy the **Client Secret**
   - Keep these secure!

## Step 2: Configure Local Environment

1. **Copy environment template:**
   ```bash
   cd /home/dalv/git/pdfa-service
   cp .env.example .env
   ```

2. **Generate JWT secret key:**
   ```bash
   openssl rand -hex 32
   ```
   Copy the output (64 character hex string)

3. **Edit `.env` file:**
   ```bash
   nano .env  # or use your preferred editor
   ```

4. **Update authentication settings:**
   ```bash
   # Enable authentication
   PDFA_ENABLE_AUTH=true

   # Google OAuth credentials (from step 1)
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here

   # JWT secret (from step 2)
   JWT_SECRET_KEY=your-64-character-hex-string-here
   JWT_ALGORITHM=HS256
   JWT_EXPIRY_HOURS=24

   # Redirect URI (already correct for localhost)
   OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
   ```

5. **Save the file** (Ctrl+X, Y, Enter in nano)

## Step 3: Start the Service

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Start with environment file:**
   ```bash
   uvicorn pdfa.api:app --reload --env-file .env
   ```

   Or if using Docker Compose:
   ```bash
   docker-compose up
   ```

## Step 4: Test OAuth Login

1. **Open browser:**
   - Navigate to http://localhost:8000

2. **You should see:**
   - Welcome screen with software description
   - Login screen with "Sign in with Google" button
   - Tabs are hidden (since you're not authenticated)

3. **Click "Sign in with Google":**
   - You'll be redirected to Google's consent screen
   - Select your Google account
   - Grant permissions
   - You'll be redirected back to http://localhost:8000

4. **After successful login:**
   - User profile appears in top bar
   - Welcome screen disappears
   - Tabs become visible
   - You can use all features

## Troubleshooting

### "Authentication is disabled" error
- Check that `PDFA_ENABLE_AUTH=true` in .env
- Restart the service after changing .env

### "redirect_uri_mismatch" error
- Verify redirect URI in Google Console matches exactly: `http://localhost:8000/auth/callback`
- Check `OAUTH_REDIRECT_URI` in .env matches
- Must be HTTP (not HTTPS) for localhost

### "Invalid client" error
- Double-check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
- Make sure there are no extra spaces or quotes
- Verify credentials are from the correct Google Cloud project

### Login button doesn't redirect
- Check browser console for errors (F12)
- Verify service is running on port 8000
- Check that MongoDB is running and accessible

### Token expired
- Tokens expire after 24 hours (configurable via JWT_EXPIRY_HOURS)
- Click "Sign Out" and sign in again

## Security Notes

- ⚠️  **Never commit your `.env` file to Git** (already in `.gitignore`)
- ⚠️  **Use different credentials for production** (with HTTPS)
- ✅  Localhost OAuth is safe for development/testing
- ✅  JWT secret should be different for each environment

## Next Steps

- For production deployment, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)
- For more authentication details, see [AUTHENTICATION.md](AUTHENTICATION.md)
- For API usage with tokens, see the API documentation at http://localhost:8000/docs
