from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import logging
from jwt import PyJWTError

from Platform.src.config.config import config


bearer_scheme = HTTPBearer(auto_error=False)


logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    id: str

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TokenData:
    """
    Validates a Bearer JWT, extracts the 'sub' (user id) claim,
    and returns a TokenData(id=<user_id>).
    Raises 401 if missing/invalid.
    """

    logger.debug("get_current_user called with credentials: %s", credentials)

    if credentials is None or credentials.scheme.lower() != "bearer":
        logger.warning(
            "Authentication failed: missing or invalid scheme (%s)",
            credentials.scheme if credentials else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    logger.debug("Bearer token received, beginning decode")

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        logger.info("JWT decoded successfully")
    except PyJWTError as e:
        logger.error("JWT decode error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("user_id")
    if not user_id:
        logger.warning("JWT payload missing 'user_id' claim: %s", payload)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Authenticated user_id=%s", user_id)
    return TokenData(id=user_id)
