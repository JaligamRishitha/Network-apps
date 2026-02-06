"""
User Management API routes with database storage.
Admin-only endpoints for managing users
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.auth_service import AuthService, Role, InvalidTokenError, InsufficientPermissionsError
from backend.services.event_service import EventService, EventType
from backend.db.database import get_db
from backend.db.models import User


router = APIRouter(prefix="/users", tags=["User Management"])


class UserResponse(BaseModel):
    """User response model"""
    username: str
    email: Optional[str] = None
    roles: List[str]
    is_active: bool = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    """Create user request"""
    username: str
    password: str
    email: str
    roles: List[str]


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    username: str
    new_password: str


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int


def get_auth_service() -> AuthService:
    """Dependency to get auth service"""
    return AuthService()


def require_admin(authorization: str = Header(None), auth_service: AuthService = Depends(get_auth_service)):
    """Dependency to require admin role"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = auth_service.validate_token(token)
        if Role.ADMIN not in payload.roles:
            raise HTTPException(status_code=403, detail="Admin role required")
        return payload
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("", response_model=UserListResponse)
async def list_users(
    _admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users (admin only) from database.
    """
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()

    user_responses = [
        UserResponse(
            username=user.username,
            email=user.email,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() + "Z" if user.created_at else None,
            last_login=user.last_login.isoformat() + "Z" if user.last_login else None,
        )
        for user in users
    ]

    return UserListResponse(
        users=user_responses,
        total=len(user_responses),
    )


@router.post("", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    _admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user (admin only) in database.
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.username == request.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail=f"User '{request.username}' already exists")

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_email = result.scalar_one_or_none()

    if existing_email:
        raise HTTPException(status_code=400, detail=f"Email '{request.email}' already in use")

    # Validate roles
    try:
        roles = [Role(r) for r in request.roles]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid role: {str(e)}")

    # Create user in database
    new_user = User(
        username=request.username,
        email=request.email,
        password=request.password,  # TODO: Hash password in production
        roles=request.roles,
        is_active=True,
        created_at=datetime.utcnow(),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Emit USER_CREATED event
    try:
        event_service = EventService()
        await event_service.emit_user_event(
            username=request.username,
            roles=request.roles,
            created_at=new_user.created_at.isoformat() + "Z",
            event_type=EventType.USER_CREATED,
            additional_data={
                "total_roles": len(request.roles),
                "email": request.email,
                "source": "SAP_USER_MANAGEMENT_DB"
            }
        )
    except Exception as e:
        # Log but don't fail user creation
        print(f"Warning: Failed to emit user creation event: {e}")

    return UserResponse(
        username=new_user.username,
        email=new_user.email,
        roles=new_user.roles,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() + "Z",
        last_login=None,
    )


@router.patch("/{username}/password")
async def change_password(
    username: str,
    request: ChangePasswordRequest,
    _admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user password (admin only) in database.
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    # Update password (TODO: Hash password in production)
    user.password = request.new_password
    user.updated_at = datetime.utcnow()

    await db.commit()

    return {"message": f"Password changed successfully for user '{username}'"}


@router.delete("/{username}")
async def delete_user(
    username: str,
    _admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user (admin only) from database.
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete the admin user")

    await db.delete(user)
    await db.commit()

    return {"message": f"User '{username}' deleted successfully"}


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    _admin = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user details (admin only) from database.
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    return UserResponse(
        username=user.username,
        email=user.email,
        roles=user.roles,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() + "Z" if user.created_at else None,
        last_login=user.last_login.isoformat() + "Z" if user.last_login else None,
    )
