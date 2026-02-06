from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User
from ..logger import log_action

router = APIRouter(prefix="/api/logs", tags=["logs"])


class FrontendLog(BaseModel):
    action_type: str
    details: str
    element: str = None


@router.post("/frontend-click")
async def log_frontend_click(
    log_data: FrontendLog,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log frontend clicks and user interactions"""
    details = f"CLICK: {log_data.element} | {log_data.details}" if log_data.element else log_data.details
    
    log_action(
        action_type=f"FRONTEND_CLICK",
        user=current_user.username,
        details=details,
        status="success"
    )
    
    return {"status": "logged"}


@router.post("/action")
async def log_action_endpoint(
    log_data: FrontendLog,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generic endpoint to log any action from frontend"""
    log_action(
        action_type=log_data.action_type,
        user=current_user.username,
        details=log_data.details,
        status="success"
    )
    
    return {"status": "logged"}


@router.get("")
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs"""
    from ..db_models import AuditLog
    
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": log.id,
            "action_type": log.action_type,
            "user": log.user,
            "details": log.details,
            "status": log.status,
            "created_at": log.created_at
        }
        for log in logs
    ]
