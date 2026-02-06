from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import math
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, MulesoftRequest
from .. import schemas

router = APIRouter(prefix="/api/mulesoft", tags=["mulesoft"])


class MulesoftRequestResponse(BaseModel):
    id: int
    account_id: Optional[int]
    name: Optional[str]
    request_type: str
    status: str
    mulesoft_response: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedMulesoftResponse(BaseModel):
    items: list[MulesoftRequestResponse]
    total: int
    page: int
    page_size: int
    pages: int


@router.get("/requests", response_model=PaginatedMulesoftResponse)
async def list_mulesoft_requests(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MulesoftRequest)
    
    if status:
        query = query.filter(MulesoftRequest.status == status)
    
    total = query.count()
    skip = (page - 1) * page_size
    
    items = query.order_by(MulesoftRequest.created_at.desc()).offset(skip).limit(page_size).all()
    
    return PaginatedMulesoftResponse(
        items=[MulesoftRequestResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/requests/{request_id}", response_model=MulesoftRequestResponse)
async def get_mulesoft_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = db.query(MulesoftRequest).filter(MulesoftRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MuleSoft request not found")
    
    return MulesoftRequestResponse.from_orm(request)
