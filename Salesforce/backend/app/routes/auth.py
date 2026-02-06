from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .. import schemas, crud
from ..db_models import User
from ..logger import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
async def login(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_login.username, user_login.password)
    if not user:
        log_action(
            action_type="LOGIN_FAILED",
            user=user_login.username,
            details="Invalid credentials",
            status="error"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_action(
        action_type="LOGIN_SUCCESS",
        user=user_login.username,
        details=f"User {user_login.username} logged in",
        status="success"
    )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        log_action(
            action_type="REGISTER_FAILED",
            user=user.username,
            details="Username already exists",
            status="error"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        log_action(
            action_type="REGISTER_FAILED",
            user=user.username,
            details="Email already exists",
            status="error"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = crud.create_user(db, user)
    log_action(
        action_type="REGISTER_SUCCESS",
        user=user.username,
        details=f"New user registered: {user.username}",
        status="success"
    )
    
    return schemas.UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
        avatar_url=new_user.avatar_url,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        alias=new_user.alias
    )


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return schemas.UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        alias=current_user.alias
    )


@router.get("/users", response_model=list[schemas.UserResponse])
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = crud.get_users(db)
    return [
        schemas.UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role,
            avatar_url=u.avatar_url,
            is_active=u.is_active,
            created_at=u.created_at,
            alias=u.alias
        )
        for u in users
    ]
