import requests
from functools import lru_cache
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import (
    AUTH0_DOMAIN,
    AUTH0_AUDIENCE,
    AUTH0_ISSUER,
    AUTH0_JWKS_URL,
)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import json
import base64

security = HTTPBearer()


@lru_cache(maxsize=1)
def get_jwks():
    """Fetch and cache JSON Web Key Set from Auth0"""
    try:
        response = requests.get(AUTH0_JWKS_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching JWKS from Auth0: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch Auth0 public keys"
        )


def get_signing_key(kid: str) -> dict:
    """Get the signing key from JWKS by key ID"""
    jwks = get_jwks()
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    raise HTTPException(
        status_code=401,
        detail="Unable to find a signing key that matches"
    )


def verify_auth0_token(token: str) -> dict:
    """
    Verify and decode Auth0 JWT token

    Args:
        token: The JWT token from Authorization header

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Get the unverified header to extract the key ID
        unverified_header = jwt.get_unverified_header(token)
        print(f"[AUTH0] Token header: {unverified_header}")

        if "kid" not in unverified_header:
            raise HTTPException(
                status_code=401,
                detail="Invalid token header"
            )

        # Get the signing key
        signing_key = get_signing_key(unverified_header["kid"])

        # Build the key for verification (convert JWK to PEM)
        key = jwt.algorithms.RSAAlgorithm.from_jwk(signing_key)

        # First, decode without verification to see what we're dealing with
        try:
            unverified_payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            print(f"[AUTH0] Unverified payload: {unverified_payload}")
            print(f"[AUTH0] Token aud claim: {unverified_payload.get('aud')}")
            print(f"[AUTH0] Token iss claim: {unverified_payload.get('iss')}")
        except Exception as debug_e:
            print(f"[AUTH0] Could not decode unverified payload: {debug_e}")
        print(f"[AUTH0] Expected audience: {AUTH0_AUDIENCE}")
        print(f"[AUTH0] Expected issuer: {AUTH0_ISSUER}")

        # Decode and verify the token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=AUTH0_ISSUER,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
            }
        )

        print(f"[AUTH0] ✓ Token verified successfully for user: {payload.get('email')}")
        return payload

    except JWTError as e:
        # Catch all JWT errors including claims validation
        error_msg = str(e).lower()
        print(f"[AUTH0] JWT Error: {str(e)}")
        if "claims" in error_msg or "aud" in error_msg or "iss" in error_msg:
            print(f"❌ Token claims validation failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token claims"
            )
        else:
            print(f"❌ JWT validation failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
    except Exception as e:
        print(f"❌ Token verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=401,
            detail="Token verification failed"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to verify Auth0 token in protected routes
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    token = credentials.credentials
    return verify_auth0_token(token)
