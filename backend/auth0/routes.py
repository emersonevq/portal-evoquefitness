from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.db import get_db
from auth0.validator import verify_auth0_token
from auth0.management import get_auth0_client
from ti.models import User
import json
import traceback

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Auth0LoginRequest(BaseModel):
    token: str


@router.post("/auth0-login")
def auth0_login(request: Auth0LoginRequest, db: Session = Depends(get_db)):
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
        payload = verify_auth0_token(request.token)

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
