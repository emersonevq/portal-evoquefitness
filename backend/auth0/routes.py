from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.db import get_db
from auth0.validator import verify_auth0_token
from auth0.management import get_auth0_client
from auth0.config import AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_TOKEN_URL, AUTH0_AUDIENCE
from ti.models import User
import json
import traceback
import requests

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Auth0ExchangeRequest(BaseModel):
    """Request model for Auth0 code exchange"""
    code: str
    redirect_uri: str


class Auth0LoginRequest(BaseModel):
    """Request model for Auth0 login"""
    token: str


class Auth0UserRequest(BaseModel):
    """Request model for getting Auth0 user"""
    token: str


@router.get("/debug/config")
def debug_config():
    """
    Debug endpoint to check Auth0 configuration (remove in production!)
    """
    return {
        "auth0_domain": AUTH0_DOMAIN,
        "auth0_audience": AUTH0_AUDIENCE,
        "auth0_client_id": AUTH0_CLIENT_ID[:10] + "..." if AUTH0_CLIENT_ID else "NOT SET",
        "auth0_client_secret_set": bool(AUTH0_CLIENT_SECRET),
        "auth0_token_url": AUTH0_TOKEN_URL,
    }


@router.post("/auth0-exchange")
def auth0_exchange(request: Auth0ExchangeRequest, db: Session = Depends(get_db)):
    """
    Exchange Auth0 authorization code for access token (backend does this for security)

    This endpoint:
    1. Exchanges the auth code from Auth0 for an access token
    2. Validates the token
    3. Checks if user exists in the database
    4. Returns user data and permissions

    Args:
        request: Auth0ExchangeRequest with code and redirect_uri
        db: Database session
    """
    try:
        print(f"\n{'='*60}")
        print(f"[AUTH0-EXCHANGE] ✓ Endpoint called")
        print(f"[AUTH0-EXCHANGE] Code: {request.code[:20]}...")
        print(f"[AUTH0-EXCHANGE] Redirect URI: {request.redirect_uri}")

        # Exchange code for token with Auth0 (done on backend for security)
        print(f"[AUTH0-EXCHANGE] Exchanging code with Auth0...")
        print(f"[AUTH0-EXCHANGE] Token URL: {AUTH0_TOKEN_URL}")
        print(f"[AUTH0-EXCHANGE] Client ID: {AUTH0_CLIENT_ID[:10]}...")

        token_response = requests.post(
            AUTH0_TOKEN_URL,
            json={
                "client_id": AUTH0_CLIENT_ID,
                "client_secret": AUTH0_CLIENT_SECRET,
                "code": request.code,
                "grant_type": "authorization_code",
                "redirect_uri": request.redirect_uri,
            },
            timeout=10,
        )

        print(f"[AUTH0-EXCHANGE] Token response status: {token_response.status_code}")

        if not token_response.ok:
            error_data = token_response.json()
            print(f"[AUTH0-EXCHANGE] ✗ Token exchange failed: {error_data}")
            raise HTTPException(
                status_code=400,
                detail=f"Auth0 token exchange failed: {error_data.get('error_description', 'Unknown error')}"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            print(f"[AUTH0-EXCHANGE] ✗ No access token in response")
            raise HTTPException(
                status_code=400,
                detail="No access token in response"
            )

        print(f"[AUTH0-EXCHANGE] ✓ Got access token: {access_token[:20]}...")

        # Verify token and extract payload
        print(f"[AUTH0-EXCHANGE] Verifying token...")
        payload = verify_auth0_token(access_token)
        print(f"[AUTH0-EXCHANGE] ✓ Token verified")
        print(f"[AUTH0-EXCHANGE] Token payload keys: {list(payload.keys())}")

        email = payload.get("email")
        email_verified = payload.get("email_verified", False)
        auth0_user_id = payload.get("sub")

        print(f"[AUTH0-EXCHANGE] Email from token: {email}")
        print(f"[AUTH0-EXCHANGE] Email verified: {email_verified}")
        print(f"[AUTH0-EXCHANGE] Auth0 user ID: {auth0_user_id}")

        if not email:
            print(f"[AUTH0-EXCHANGE] ✗ Email not found in token")
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
            )

        if not email_verified:
            print(f"[AUTH0-EXCHANGE] ✗ Email not verified in Auth0")
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please verify your email in Auth0 before accessing the system."
            )

        # Find user in database
        print(f"[AUTH0-EXCHANGE] Looking up user by email: {email}")
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"[AUTH0-EXCHANGE] ✗ User not found in database")
            print(f"[AUTH0-EXCHANGE] Total users in DB: {db.query(User).count()}")
            raise HTTPException(
                status_code=403,
                detail=f"User with email '{email}' not found in system. Contact administrator."
            )

        print(f"[AUTH0-EXCHANGE] ✓ User found: {user.nome} {user.sobrenome}")

        if getattr(user, "bloqueado", False):
            print(f"[AUTH0-EXCHANGE] ✗ User is blocked")
            raise HTTPException(
                status_code=403,
                detail="User is blocked. Contact administrator."
            )

        # Sync Auth0 user ID and email verification status
        try:
            user.auth0_id = auth0_user_id
            user.email_verified = email_verified
            db.commit()
            db.refresh(user)
            print(f"[AUTH0-EXCHANGE] ✓ User auth0_id and email_verified synced")
        except Exception as e:
            print(f"[AUTH0-EXCHANGE] ⚠️ Failed to sync user: {str(e)}")
            db.rollback()

        # Parse user sectors
        setores_list = []
        if getattr(user, "_setores", None):
            try:
                setores_list = json.loads(getattr(user, "_setores", "[]"))
            except Exception:
                setores_list = []

        # Parse BI subcategories
        bi_subcategories_list = None
        if getattr(user, "_bi_subcategories", None):
            try:
                bi_subcategories_list = json.loads(
                    getattr(user, "_bi_subcategories", "null")
                )
            except Exception:
                bi_subcategories_list = None

        print(f"[AUTH0-EXCHANGE] ✓ Authentication successful")
        print(f"[AUTH0-EXCHANGE] User sectors: {setores_list}")
        print(f"[AUTH0-EXCHANGE] User access level: {user.nivel_acesso}")
        print(f"{'='*60}\n")

        return {
            "id": user.id,
            "nome": user.nome,
            "sobrenome": user.sobrenome,
            "email": user.email,
            "nivel_acesso": user.nivel_acesso,
            "setores": setores_list,
            "bi_subcategories": bi_subcategories_list,
            "access_token": access_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH0-EXCHANGE] ✗ Error: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/auth0-login")
def auth0_login(request: Auth0LoginRequest, db: Session = Depends(get_db)):
    """
    Validate Auth0 JWT token and authenticate user

    This endpoint:
    1. Validates the Auth0 JWT token
    2. Verifies email is confirmed in Auth0
    3. Checks if user exists in the database
    4. Returns user data and permissions

    Args:
        request: Auth0LoginRequest with token
        db: Database session
    """
    try:
        # Verify token
        payload = verify_auth0_token(request.token)

        # Get email from token
        email = payload.get("email")
        email_verified = payload.get("email_verified", False)
        auth0_user_id = payload.get("sub")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
            )

        if not email_verified:
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please verify your email in Auth0 before accessing the system."
            )

        # Find user in database
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=403,
                detail=f"User with email '{email}' not found in system. Contact administrator."
            )

        if getattr(user, "bloqueado", False):
            raise HTTPException(
                status_code=403,
                detail="User is blocked. Contact administrator."
            )

        # Sync Auth0 user ID and email verification status
        try:
            user.auth0_id = auth0_user_id
            user.email_verified = email_verified
            db.commit()
            db.refresh(user)
        except Exception as e:
            print(f"⚠️ Failed to sync user: {str(e)}")
            db.rollback()
        
        # Parse user sectors
        setores_list = []
        if getattr(user, "_setores", None):
            try:
                setores_list = json.loads(getattr(user, "_setores", "[]"))
            except Exception:
                setores_list = []
        
        # Parse BI subcategories
        bi_subcategories_list = None
        if getattr(user, "_bi_subcategories", None):
            try:
                bi_subcategories_list = json.loads(
                    getattr(user, "_bi_subcategories", "null")
                )
            except Exception:
                bi_subcategories_list = None
        
        return {
            "id": user.id,
            "nome": user.nome,
            "sobrenome": user.sobrenome,
            "email": user.email,
            "nivel_acesso": user.nivel_acesso,
            "setores": setores_list,
            "bi_subcategories": bi_subcategories_list,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Auth0 login error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/auth0-user")
def get_auth0_user(request: Auth0UserRequest, db: Session = Depends(get_db)):
    """
    Get current authenticated user information

    Args:
        request: Auth0UserRequest with token
        db: Database session
    """
    try:
        # Verify token
        payload = verify_auth0_token(request.token)
        email = payload.get("email")
        email_verified = payload.get("email_verified", False)
        auth0_user_id = payload.get("sub")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
            )

        if not email_verified:
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please verify your email in Auth0 before accessing the system."
            )

        # Find user
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Sync Auth0 user ID and email verification status
        try:
            user.auth0_id = auth0_user_id
            user.email_verified = email_verified
            db.commit()
            db.refresh(user)
        except Exception as e:
            print(f"⚠️ Failed to sync user: {str(e)}")
            db.rollback()
        
        # Parse sectors
        setores_list = []
        if getattr(user, "_setores", None):
            try:
                setores_list = json.loads(getattr(user, "_setores", "[]"))
            except Exception:
                setores_list = []
        
        return {
            "id": user.id,
            "nome": user.nome,
            "sobrenome": user.sobrenome,
            "email": user.email,
            "nivel_acesso": user.nivel_acesso,
            "setores": setores_list,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving user"
        )
