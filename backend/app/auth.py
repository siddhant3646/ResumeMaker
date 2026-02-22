"""
Auth0 Authentication Middleware
JWT Token Verification with JWKS
"""

import os
import jwt
from jwt.algorithms import RSAAlgorithm
import aiohttp
import logging
from functools import lru_cache
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_ALGORITHMS = ["RS256"]

# JWKS URL (to get public keys for verification)
JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json" if AUTH0_DOMAIN else ""

# Cache for JWKS keys with TTL
_jwks_cache: Dict[str, Any] = {"keys": None, "expires_at": None}
JWKS_CACHE_TTL = 3600  # 1 hour

security = HTTPBearer(auto_error=False)


async def get_jwks() -> Dict[str, Any]:
    """
    Fetch and cache Auth0 JWKS keys with TTL
    """
    global _jwks_cache
    
    # Return cached keys if still valid
    if _jwks_cache["keys"] and _jwks_cache["expires_at"]:
        if datetime.now() < _jwks_cache["expires_at"]:
            return _jwks_cache["keys"]
    
    if not AUTH0_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth0 domain not configured"
        )
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(JWKS_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Auth0 JWKS unavailable: {response.status}"
                    )
                
                jwks = await response.json()
                
                # Validate JWKS structure
                if "keys" not in jwks or not jwks["keys"]:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Invalid JWKS response from Auth0"
                    )
                
                # Cache the keys
                _jwks_cache = {
                    "keys": jwks,
                    "expires_at": datetime.now() + timedelta(seconds=JWKS_CACHE_TTL)
                }
                
                logger.info("JWKS keys fetched and cached successfully")
                return jwks
                
    except aiohttp.ClientError as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth0 authentication service unavailable"
        )


async def verify_token(token: str) -> dict:
    """
    Verify JWT token from Auth0 with proper signature validation
    Returns decoded token payload
    """
    if not AUTH0_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth0 not configured"
        )
    
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    
    try:
        # Get unverified header to extract key ID (kid)
        try:
            header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: malformed JWT"
            )
        
        kid = header.get('kid')
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing key ID"
            )
        
        # Fetch JWKS and find matching key
        jwks = await get_jwks()
        
        rsa_key = None
        for key in jwks["keys"]:
            if key.get("kid") == kid:
                rsa_key = key
                break
        
        if not rsa_key:
            # Key not found - refresh cache and try again
            _jwks_cache["keys"] = None
            jwks = await get_jwks()
            
            for key in jwks["keys"]:
                if key.get("kid") == kid:
                    rsa_key = key
                    break
            
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: signing key not found"
                )
        
        # Construct public key from JWKS
        try:
            public_key = RSAAlgorithm.from_jwk(rsa_key)
        except Exception as e:
            logger.error(f"Failed to construct public key: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: unable to verify signature"
            )
        
        # Verify the token with the public key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
            options={
                "require": ["exp", "iat", "sub"],
                "verify_exp": True,
                "verify_iat": True,
            }
        )
        
        # Validate required claims
        if "sub" not in payload or not payload["sub"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience"
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected token verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user
    Use this in route handlers: current_user: dict = Depends(get_current_user)
    """
    # Allow preflight requests
    if request.method == "OPTIONS":
        return {"sub": "preflight", "email": None, "name": None}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = await verify_token(token)
    
    # Ensure sub claim exists
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
