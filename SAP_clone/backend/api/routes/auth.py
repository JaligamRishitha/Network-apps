"""
Authentication API routes with database storage.
Requirements: 7.1 - JWT authentication endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.auth_service import AuthService, Role, InvalidTokenError
from backend.db.database import get_db
from backend.db.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request payload"""
    username: str
    password: str
    roles: List[str] = ["Maintenance_Engineer"]


class LoginResponse(BaseModel):
    """Login response with JWT token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Token refresh request"""
    token: str


class ValidateUserRequest(BaseModel):
    """Validate user for password reset"""
    username: str


class ValidateUserResponse(BaseModel):
    """User validation response"""
    exists: bool
    username: str
    message: str


def get_auth_service() -> AuthService:
    """Dependency to get auth service"""
    return AuthService()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and issue JWT token from database.
    Requirement 7.1 - Issue JWT with user_id, roles, expiration_time
    """
    # Strip whitespace from credentials
    username = request.username.strip()
    password = request.password.strip()

    # Check user from database
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Convert role strings to Role enum
    user_roles = [Role(r) for r in user.roles]

    # Create token
    token = auth_service.create_token(
        user_id=username,
        roles=user_roles,
    )

    return LoginResponse(
        access_token=token,
        expires_in=auth_service.expiration_minutes * 60,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh an existing JWT token.
    """
    try:
        new_token = auth_service.refresh_token(request.token)
        return LoginResponse(
            access_token=new_token,
            expires_in=auth_service.expiration_minutes * 60,
        )
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/validate-user", response_model=ValidateUserResponse)
async def validate_user_for_password_reset(
    request: ValidateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate if a user exists in the SAP system for password reset.
    This endpoint does not require authentication and is used by agents
    to verify user existence before initiating password reset flow.
    """
    username = request.username.strip()

    # Check if user exists in database
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    user_exists = user is not None

    if user_exists:
        return ValidateUserResponse(
            exists=True,
            username=username,
            message=f"User '{username}' found in SAP system"
        )
    else:
        return ValidateUserResponse(
            exists=False,
            username=username,
            message=f"User '{username}' not found in SAP system"
        )
