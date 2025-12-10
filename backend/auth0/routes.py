from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.db import get_db
from auth0.validator import verify_auth0_token
from auth0.management import get_auth0_client
from auth0.config import AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_TOKEN_URL
from ti.models import User
import json
import traceback
import requests

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
def auth0_exchange(code: str, redirect_uri: str, db: Session = Depends(get_db)):
    """
    Exchange Auth0 authorization code for access token (backend does this for security)

    This endpoint:
    1. Exchanges the auth code from Auth0 for an access token
    2. Validates the token
    3. Checks if user exists in the database
    4. Returns user data and permissions

    Args:
        code: Auth0 authorization code from callback
        redirect_uri: The redirect URI used in the initial auth request
        db: Database session
    """
    try:
        # Exchange code for token with Auth0 (done on backend for security)
        token_response = requests.post(
            AUTH0_TOKEN_URL,
            json={
                "client_id": AUTH0_CLIENT_ID,
                "client_secret": AUTH0_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=10,
        )

        if not token_response.ok:
            error_data = token_response.json()
            print(f"❌ Auth0 token exchange failed: {error_data}")
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange code for token"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="No access token in response"
            )

        # Verify token and extract payload
        payload = verify_auth0_token(access_token)
        email = payload.get("email")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
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
            "access_token": access_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Auth0 exchange error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/auth0-login")
def auth0_login(token: str, db: Session = Depends(get_db)):
    """
    Validate Auth0 JWT token and authenticate user
    
    This endpoint:
    1. Validates the Auth0 JWT token
    2. Checks if user exists in the database
    3. Returns user data and permissions
    
    Args:
        token: Auth0 access token (from Bearer header in client)
        db: Database session
    """
    try:
        # Verify token
        payload = verify_auth0_token(token)
        
        # Get email from token
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
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


@router.get("/auth0-user")
def get_auth0_user(token: str, db: Session = Depends(get_db)):
    """
    Get current authenticated user information
    
    Args:
        token: Auth0 access token
        db: Database session
    """
    try:
        # Verify token
        payload = verify_auth0_token(token)
        email = payload.get("email")
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
            )
        
        # Find user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
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
