"""
Client Users API - Manage client portal users linked to Salesforce accounts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from passlib.context import CryptContext
import logging

from ..database import get_db
from ..db_models import ClientUser, Account
from ..servicenow import get_servicenow_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/client-users", tags=["Client Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Schemas ──────────────────────────────────────────────────────────────────

class ClientUserCreate(BaseModel):
    account_id: int
    name: str
    email: str
    password: str

class ClientUserResponse(BaseModel):
    id: int
    account_id: int
    name: str
    email: str
    password_expired: bool
    is_active: bool
    servicenow_ticket_id: Optional[str] = None
    account_name: Optional[str] = None
    created_at: Optional[str] = None

class ValidateRequest(BaseModel):
    email: str

class PasswordUpdateRequest(BaseModel):
    new_password: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _to_response(cu: ClientUser) -> dict:
    return {
        "id": cu.id,
        "account_id": cu.account_id,
        "name": cu.name,
        "email": cu.email,
        "password_expired": cu.password_expired,
        "is_active": cu.is_active,
        "servicenow_ticket_id": cu.servicenow_ticket_id,
        "account_name": cu.account.name if cu.account else None,
        "created_at": cu.created_at.isoformat() if cu.created_at else None,
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("")
async def create_client_user(body: ClientUserCreate, db: Session = Depends(get_db)):
    """Create a new client user and raise a ServiceNow ticket for activation."""
    # Check account exists
    account = db.query(Account).filter(Account.id == body.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check duplicate email
    existing = db.query(ClientUser).filter(ClientUser.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A client user with this email already exists")

    # Create user (inactive until orchestrator activates)
    cu = ClientUser(
        account_id=body.account_id,
        name=body.name,
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        password_expired=True,
        is_active=False,
    )
    db.add(cu)
    db.flush()  # get cu.id before committing

    # Create ServiceNow ticket
    sn_client = get_servicenow_client()
    description = (
        f"Client User Creation Request\n"
        f"Client User ID: {cu.id}\n"
        f"Email: {body.email}\n"
        f"Account: {account.name} (ID: {account.id})\n"
        f"Name: {body.name}\n"
        f"Requires activation by orchestrator."
    )
    try:
        sn_result = await sn_client.create_ticket(
            short_description=f"Create User - {body.name} ({body.email})",
            description=description,
            category="user_creation",
            priority="3",
            custom_fields={
                "source_system": "salesforce",
                "source_request_type": "client_user_creation",
                "source_request_id": str(cu.id),
            },
        )
        if sn_result.get("success"):
            cu.servicenow_ticket_id = sn_result.get("ticket_number") or sn_result.get("ticket_id")
            logger.info(f"ServiceNow ticket created for client user {cu.id}: {cu.servicenow_ticket_id}")
        else:
            logger.error(f"ServiceNow ticket creation failed: {sn_result}")
    except Exception as e:
        logger.error(f"ServiceNow integration error: {e}")

    db.commit()
    db.refresh(cu)
    return _to_response(cu)


@router.get("")
def list_client_users(account_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List client users, optionally filtered by account."""
    q = db.query(ClientUser)
    if account_id is not None:
        q = q.filter(ClientUser.account_id == account_id)
    return [_to_response(cu) for cu in q.order_by(ClientUser.id.desc()).all()]


@router.get("/{user_id}")
def get_client_user(user_id: int, db: Session = Depends(get_db)):
    cu = db.query(ClientUser).filter(ClientUser.id == user_id).first()
    if not cu:
        raise HTTPException(status_code=404, detail="Client user not found")
    return _to_response(cu)


@router.post("/validate")
def validate_client_user(body: ValidateRequest, db: Session = Depends(get_db)):
    """Validate whether a client user exists by email. Used by agent/orchestrator."""
    cu = db.query(ClientUser).filter(ClientUser.email == body.email).first()
    if not cu:
        return {"exists": False}
    # User exists but pending activation — treat as NOT a duplicate
    if not cu.is_active:
        return {
            "exists": False,
            "pending_activation": True,
            "client_user_id": cu.id,
            "account_id": cu.account_id,
            "account_name": cu.account.name if cu.account else None,
            "name": cu.name,
            "message": f"User '{cu.name}' is pending activation. Approve to activate.",
        }
    # Already active — this is a real duplicate
    return {
        "exists": True,
        "client_user_id": cu.id,
        "account_id": cu.account_id,
        "account_name": cu.account.name if cu.account else None,
        "is_active": cu.is_active,
        "name": cu.name,
    }


@router.patch("/{user_id}/activate")
def activate_client_user(user_id: int, db: Session = Depends(get_db)):
    """Activate a client user (called by orchestrator after agent approval)."""
    cu = db.query(ClientUser).filter(ClientUser.id == user_id).first()
    if not cu:
        raise HTTPException(status_code=404, detail="Client user not found")
    cu.is_active = True
    db.commit()
    db.refresh(cu)
    logger.info(f"Client user {user_id} activated")
    return _to_response(cu)


@router.patch("/{email}/password")
def update_client_password(email: str, body: PasswordUpdateRequest, db: Session = Depends(get_db)):
    """Update client user password (called by orchestrator after agent approval)."""
    cu = db.query(ClientUser).filter(ClientUser.email == email).first()
    if not cu:
        raise HTTPException(status_code=404, detail="Client user not found")
    cu.password_hash = pwd_context.hash(body.new_password)
    cu.password_expired = False
    db.commit()
    db.refresh(cu)
    logger.info(f"Client user password updated for {email}")
    return _to_response(cu)
