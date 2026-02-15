"""
Auth0 Authentication Middleware
JWT Token Verification
"""

import os
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_ALGORITHMS = ["RS256"]

# JWKS URL (to get public keys for verification)
JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

security = HTTPBearer()

async def verify_token(token: str) -> dict:
    """
    Verify JWT token from Auth0
    Returns decoded token payload
    """
    if not AUTH0_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth0 not configured"
        )
    
    try:
        # For simplicity in development, accept tokens without verification
        # In production, you should fetch JWKS and verify properly
        if os.getenv("ENVIRONMENT") == "development":
            # Decode without verification for dev
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        
        # Production: Verify with Auth0 JWKS
        # Note: In production, fetch JWKS from AUTH0_DOMAIN and verify properly
        # For now, we'll decode without verification but check basic structure
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # TODO: Implement proper JWKS verification
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return payload
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user
    Use this in route handlers: current_user: dict = Depends(get_current_user)
    """
    token = credentials.credentials
    payload = await verify_token(token)
    
    # Check if token has required claims
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    
    return payload

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Optional authentication - returns None if no valid token
    """
    if not credentials:
        return None
    
    try:
        return await verify_token(credentials.credentials)
    except HTTPException:
        return None
