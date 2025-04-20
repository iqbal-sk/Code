import datetime
import logging
import jwt

from odmantic import AIOEngine
from odmantic.query import or_
from Platform.src.user_management.models import User
from Platform.src.user_management.exceptions import (
    UserExistsException,
    UserNotFoundException,
    AuthenticationFailedException,
)
from Platform.src.user_management.utils import generate_salt, hash_password, verify_password
from Platform.src.user_management.constants import DEFAULT_ROLES
from Platform.src.config.config import config

logger = logging.getLogger(__name__)

async def create_user(user_data, engine: AIOEngine):
    # Check if a user with the same username or email already exists.
    existing = await engine.find_one(
        User, or_(User.username == user_data.username, User.email == user_data.email)
    )
    if existing:
        logger.warning("Attempt to create user with duplicate username/email: %s / %s",
                       user_data.username, user_data.email)
        raise UserExistsException()

    salt = generate_salt()
    password_hash = hash_password(user_data.password, salt)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        salt=salt,
        firstName=user_data.firstName,
        lastName=user_data.lastName,
        role=user_data.role if user_data.role is not None else DEFAULT_ROLES,
        profilePicture=user_data.profilePicture,
        bio=user_data.bio,
        socialLinks=user_data.socialLinks.dict() if user_data.socialLinks else {},
        preferences=user_data.preferences.dict() if user_data.preferences else {},
    )
    await engine.save(new_user)
    logger.info("Created new user: %s", new_user.username)
    return new_user

async def authenticate_user(user_data, engine: AIOEngine) -> dict:
    logger.info("Authentication attempt for user: %s", user_data.username)
    user = await engine.find_one(User, User.username == user_data.username)
    if not user:
        logger.warning("User not found during authentication: %s", user_data.username)
        raise UserNotFoundException()

    if not verify_password(user_data.password, user.password_hash):
        logger.warning("Authentication failed for user: %s", user_data.username)
        raise AuthenticationFailedException()

    # Update last login timestamp.
    user.lastLogin = datetime.datetime.now(datetime.UTC)
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    await engine.save(user)

    # Create JWT token.
    token_payload = {
        "user_id": str(user.id),
        "username": user.username,
        "roles": user.role,
        "exp": expire,
    }
    token = jwt.encode(token_payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    logger.info("User %s authenticated successfully", user.username)
    return {"access_token": token, "token_type": "bearer"}