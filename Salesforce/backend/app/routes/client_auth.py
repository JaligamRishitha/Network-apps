"""
Client Auth API - Authentication for the Client Portal
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import os

from ..database import get_db
from ..db_models import ClientUser

router = APIRouter(prefix="/api/client-auth", tags=["Client Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str


@router.post("/login")
def client_login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a client portal user."""
    cu = db.query(ClientUser).filter(ClientUser.email == body.email).first()
    if not cu:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not pwd_context.verify(body.password, cu.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not cu.is_active:
        raise HTTPException(status_code=403, detail="Account not yet activated. Please wait for approval.")

    if cu.password_expired:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": cu.email,
        "client_user_id": cu.id,
        "account_id": cu.account_id,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": cu.id,
            "name": cu.name,
            "email": cu.email,
            "account_id": cu.account_id,
            "account_name": cu.account.name if cu.account else None,
        },
        "password_expired": cu.password_expired,
    }


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, db: Session = Depends(get_db)):
    """Change password for a client portal user."""
    cu = db.query(ClientUser).filter(ClientUser.email == body.email).first()
    if not cu:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(body.old_password, cu.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    cu.password_hash = pwd_context.hash(body.new_password)
    cu.password_expired = False
    db.commit()

    return {"message": "Password changed successfully"}
