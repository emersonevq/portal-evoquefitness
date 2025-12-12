# Auth0 Single Sign-On (SSO) Setup Guide

## Overview

This guide explains how to set up Single Sign-On (SSO) between multiple portals (Evoque Portal and Financial Portal) using Auth0. With proper configuration, users can log in to one portal and automatically be authenticated in the other portal without re-entering credentials.

## Problem Solved

**Before:** Users had to log in separately to each portal, even though both used Auth0.

**After:** Users log in to one portal (e.g., Evoque), and when they access the other portal (Financial), they're automatically logged in via Auth0's session management.

## How SSO Works

1. **User logs in to Portal Evoque** → Auth0 creates a session cookie at `https://your-auth0-domain.auth0.com`
2. **User accesses Portal Financeiro** → Application checks for existing Auth0 session
3. **Auth0 session found** → User is automatically authenticated without re-entering credentials
4. **No Auth0 session** → User is shown the login page

## Key Components Changed

### Frontend Auth Context (`frontend/src/lib/auth-context.tsx`)

**New Features:**
- **Secure State Parameter Generation**: Uses `crypto.getRandomValues()` for cryptographically secure CSRF protection
- **State Parameter Validation**: Validates the state parameter returned from Auth0 to prevent CSRF attacks
- **Proper OAuth 2.0 Flow**: Implements standard OAuth authorization code flow
- **Error Handling**: Properly handles Auth0 errors, including `login_required` which indicates no existing session

**Key Functions:**
```typescript
// Generates secure random state parameter
generateSecureState(): string

// Validates OAuth callback
handleAuth0Callback(code, state)

// Logs in with Auth0
loginWithAuth0()
```

## Required Auth0 Configuration

### 1. Auth0 Tenant Settings

Make sure you have:
- Auth0 account and domain (e.g., `your-domain.auth0.com`)
- Two applications created: one for Portal Evoque, one for Portal Financeiro
- Database connection enabled (Username-Password-Authentication)

### 2. Portal Evoque Application Settings

In Auth0 Dashboard → Applications → Portal Evoque:

**Application URIs:**
- **Login URL**: `https://portalevoque.com`
- **Callback URLs**:
  ```
  http://localhost:5173/auth/callback
  http://localhost:3005/auth/callback
  https://portalevoque.com/auth/callback
  https://app.portalevoque.com/auth/callback
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
  ```
- **Logout URLs**:
  ```
  http://localhost:5173
  http://localhost:3005
  https://portalevoque.com
  https://app.portalevoque.com
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```
- **Allowed Web Origins** (for CORS/Silent Auth):
  ```
  http://localhost:5173
  http://localhost:3005
  https://portalevoque.com
  https://app.portalevoque.com
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```

**Connections:**
- Enable "Username-Password-Authentication" database connection
- Enable social connections if needed (Google, etc.)

### 3. Portal Financeiro Application Settings

In Auth0 Dashboard → Applications → Portal Financeiro:

**Application URIs:**
- **Login URL**: `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io`
- **Callback URLs**:
  ```
  http://localhost:5173/auth/callback
  http://localhost:3005/auth/callback
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
  ```
- **Logout URLs**:
  ```
  http://localhost:5173
  http://localhost:3005
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```
- **Allowed Web Origins**:
  ```
  http://localhost:5173
  http://localhost:3005
  https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
  ```

**Connections:**
- Enable "Username-Password-Authentication" database connection (SAME as Portal Evoque)
- Enable social connections if needed

### 4. Environment Variables Required

Both applications need these environment variables configured:

```env
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id-here
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_AUTH0_AUDIENCE=your-api-audience
VITE_AUTH0_LOGOUT_URI=http://localhost:5173
```

For production, update the URLs:
```env
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id-here
VITE_AUTH0_REDIRECT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback
VITE_AUTH0_AUDIENCE=your-api-audience
VITE_AUTH0_LOGOUT_URI=https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io
```

## SSO Login Flow

### Step 1: User Clicks Login Button

User on Portal Financeiro clicks "Entrar com Auth0" button.

### Step 2: Frontend Initiates OAuth

```typescript
const state = generateSecureState();
sessionStorage.setItem("auth_state", state);

window.location.href = `https://your-domain.auth0.com/authorize?
  response_type=code
  client_id=${CLIENT_ID}
  redirect_uri=${REDIRECT_URI}
  scope=openid profile email offline_access
  state=${state}`;
```

### Step 3: Auth0 Checks Session

- **If user is logged in at Auth0** (from Portal Evoque): Auth0 immediately returns authorization code
- **If user is NOT logged in**: Auth0 shows login form or error `login_required`

### Step 4: Redirect Back to App

Auth0 redirects to: `https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback?code=xxx&state=yyy`

### Step 5: Frontend Validates State

```typescript
const storedState = sessionStorage.getItem("auth_state");
if (state !== storedState) {
  throw new Error("CSRF attack detected - state mismatch");
}
```

### Step 6: Exchange Code for Token

Frontend sends code to backend: `POST /api/auth/auth0-exchange`

Backend:
1. Exchanges code for access token with Auth0
2. Validates token signature
3. Extracts user email
4. Looks up user in database
5. Returns user data and permissions

### Step 7: User Logged In

Frontend stores session token and user data in `sessionStorage` and logs user in.

## Troubleshooting

### "The state parameter is missing"

**Cause:** State parameter wasn't properly stored or validated.

**Solution:**
1. Check that `sessionStorage` is enabled in browser
2. Verify state is being stored before redirect: `sessionStorage.setItem("auth_state", state)`
3. Check that redirect URL matches exactly what's in Auth0 configuration

### User Logs in to Evoque, but Not Automatically Logged In to Financeiro

**Cause:** SSO is not working because of missing Auth0 configuration.

**Possible Solutions:**
1. Verify both applications are in the SAME Auth0 tenant
2. Verify both applications have the SAME database connection enabled
3. Verify "Allowed Web Origins" includes the Financial Portal domain
4. Clear browser cookies and try again
5. Check browser console for Auth0 error messages

### User Sees Login Screen on Financial Portal

**Expected Behavior:** If user is NOT logged in at Auth0 (first time accessing the system), they should see the login screen. This is correct!

**When it's a problem:**
- If user WAS just logged in on Portal Evoque, they should NOT see a login screen
- Check Auth0 session cookie is being set (check browser Network tab)

### CORS Errors in Console

**Cause:** Allowed Web Origins not configured correctly in Auth0.

**Solution:**
1. Go to Auth0 Dashboard → Applications → Settings
2. Add your portal domain to "Allowed Web Origins"
3. Save and wait ~1 minute for changes to propagate
4. Clear browser cache and cookies

## Security Features Implemented

### 1. CSRF Protection via State Parameter
- State is generated using cryptographically secure random values
- State is validated on callback
- If state doesn't match, authentication is rejected

### 2. Secure Token Storage
- Access tokens stored in `sessionStorage` only (not localStorage)
- Session expires after 24 hours
- Session can be revoked anytime

### 3. Email Verification
- Users must have verified email in Auth0 (if required)
- Backend validates token before issuing session

### 4. HTTPS Required (Production)
- All OAuth redirects use HTTPS
- Cookies marked as secure (HTTPS only)

## Testing SSO Locally

### Setup Local Environment

1. Set up both portals to run locally:
   ```bash
   # Terminal 1: Portal Evoque
   cd frontend
   npm run dev  # Runs on http://localhost:5173

   # Terminal 2: Portal Financeiro (different project)
   cd frontend
   npm run dev  # Also runs on http://localhost:5173
   ```

   ⚠️ They'll conflict on same port. Use different ports:
   ```bash
   # Terminal 1: Portal Evoque
   npm run dev

   # Terminal 2: Portal Financeiro
   VITE_AUTH0_REDIRECT_URI=http://localhost:5174/auth/callback npm run dev -- --port 5174
   ```

2. Configure Auth0 with both localhost URLs:
   - Portal Evoque: `http://localhost:5173/auth/callback`
   - Portal Financeiro: `http://localhost:5174/auth/callback`

3. Test SSO Flow:
   - Log in to Portal Evoque at `http://localhost:5173`
   - Open Portal Financeiro at `http://localhost:5174`
   - You should be automatically logged in!

## Testing Production

### Before Deploying

1. **Test OAuth Code Exchange**
   ```bash
   curl -X POST https://your-domain.auth0.com/oauth/token \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "code": "AUTH_CODE_FROM_BROWSER",
       "grant_type": "authorization_code",
       "redirect_uri": "https://qas-frontend-app.calmmoss-ededd9fd.eastus.azurecontainerapps.io/auth/callback"
     }'
   ```

2. **Test Token Validation**
   - Check backend `/api/auth/debug/config` endpoint
   - Verify Auth0 configuration is loaded correctly

3. **Test Database Lookup**
   - Ensure user exists in database with same email as Auth0
   - User must have permissions assigned

### Deployment Checklist

- [ ] Auth0 callback URLs updated to production domain
- [ ] Auth0 web origins updated to production domain
- [ ] Logout URLs updated to production domain
- [ ] Environment variables set correctly on server
- [ ] Database contains all users with matching emails
- [ ] HTTPS enabled for all URLs
- [ ] Auth0 require email verification enabled (optional but recommended)

## Advanced: Cross-Domain SSO

For SSO between completely different domains (e.g., `portalevoque.com.br` and `financeiro.outraempresa.com`):

1. Both domains must be in the SAME Auth0 tenant
2. Both applications must have identical database connections
3. Add both domains to "Allowed Web Origins" for each application
4. Auth0 will share the session cookie across domains automatically

⚠️ Note: Cookies do NOT travel across completely different domain registries (.com.br vs .com). Only use the same tenant approach!

## References

- [Auth0 Authorization Code Flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow)
- [Auth0 PKCE (currently not implemented but recommended for SPAs)](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-proof-key-for-code-exchange)
- [Auth0 State Parameter for CSRF Protection](https://auth0.com/docs/secure/attack-protection/state-parameter)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
