from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/{record_type}/{record_id}")
async def get_activities(
    record_type: str,
    record_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    valid_types = ["contact", "account", "lead", "opportunity", "case"]
    if record_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid record type. Must be one of: {valid_types}"
        )

    activities = crud.get_activities(db, record_type, record_id, skip, limit)

    return [
        {
            "id": a.id,
            "record_type": a.record_type,
            "record_id": a.record_id,
            "activity_type": a.activity_type,
            "subject": a.subject,
            "details": a.details,
            "created_by": a.created_by,
            "created_at": a.created_at,
            "created_by_name": a.created_by_user.full_name if a.created_by_user else None
        }
        for a in activities
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    valid_types = ["contact", "account", "lead", "opportunity", "case"]
    if activity.record_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid record type. Must be one of: {valid_types}"
        )

    valid_activity_types = ["call", "email", "meeting", "note", "task"]
    if activity.activity_type not in valid_activity_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid activity type. Must be one of: {valid_activity_types}"
        )

    db_activity = crud.create_activity(db, activity, current_user.id)

    return {
        "id": db_activity.id,
        "record_type": db_activity.record_type,
        "record_id": db_activity.record_id,
        "activity_type": db_activity.activity_type,
        "subject": db_activity.subject,
        "details": db_activity.details,
        "created_by": db_activity.created_by,
        "created_at": db_activity.created_at
    }
