import requests
from functools import lru_cache
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from .config import (
    AUTH0_DOMAIN,
    AUTH0_AUDIENCE,
    AUTH0_ISSUER,
    AUTH0_JWKS_URL,
)

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
        
        if "kid" not in unverified_header:
            raise HTTPException(
                status_code=401,
                detail="Invalid token header"
            )
        
        # Get the signing key
        signing_key = get_signing_key(unverified_header["kid"])
        
        # Build the key for verification (convert JWK to PEM)
        key = jwt.algorithms.RSAAlgorithm.from_jwk(signing_key)
        
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
        
        return payload
        
    except JWTError as e:
        # Catch all JWT errors including claims validation
        error_msg = str(e).lower()
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
        raise HTTPException(
            status_code=401,
            detail="Token verification failed"
        )


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    Dependency to verify Auth0 token in protected routes
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    token = credentials.credentials
    return verify_auth0_token(token)
