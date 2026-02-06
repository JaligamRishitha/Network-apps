from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get counts for current user
    leads, leads_total = crud.get_leads(db, owner_id=current_user.id, limit=1)
    opportunities, opps_total = crud.get_opportunities(db, owner_id=current_user.id, limit=1)
    contacts, contacts_total = crud.get_contacts(db, owner_id=current_user.id, limit=1)

    # Get cases by priority
    cases_by_priority = crud.get_cases_by_priority(db, owner_id=current_user.id)

    # Get recent records
    recent = crud.get_recent_records(db, current_user.id, limit=10)

    return schemas.DashboardStats(
        leads_count=leads_total,
        opportunities_count=opps_total,
        contacts_count=contacts_total,
        cases_by_priority=cases_by_priority,
        recent_records=[
            schemas.RecentRecordResponse(
                id=r.id,
                record_type=r.record_type,
                record_id=r.record_id,
                record_name=r.record_name,
                accessed_at=r.accessed_at
            )
            for r in recent
        ]
    )


@router.get("/recent-records")
async def get_recent_records(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recent = crud.get_recent_records(db, current_user.id, limit=limit)
    return [
        {
            "id": r.id,
            "record_type": r.record_type,
            "record_id": r.record_id,
            "record_name": r.record_name,
            "accessed_at": r.accessed_at
        }
        for r in recent
    ]


@router.get("/search", response_model=schemas.SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = crud.global_search(db, q, limit=limit)
    return schemas.SearchResponse(
        results=results,
        total=len(results)
    )
