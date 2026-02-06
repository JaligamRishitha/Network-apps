from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


def opportunity_to_response(opportunity) -> schemas.OpportunityResponse:
    return schemas.OpportunityResponse(
        id=opportunity.id,
        name=opportunity.name,
        account_id=opportunity.account_id,
        amount=opportunity.amount,
        stage=opportunity.stage,
        probability=opportunity.probability,
        close_date=opportunity.close_date,
        description=opportunity.description,
        owner_id=opportunity.owner_id,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at,
        account_name=opportunity.account.name if opportunity.account else None,
        owner_alias=opportunity.owner.alias if opportunity.owner else None
    )


@router.get("", response_model=schemas.PaginatedResponse)
async def list_opportunities(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    stage: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * page_size
    opportunities, total = crud.get_opportunities(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        account_id=account_id,
        stage=stage,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return schemas.PaginatedResponse(
        items=[opportunity_to_response(o) for o in opportunities],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{opportunity_id}", response_model=schemas.OpportunityResponse)
async def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opportunity = crud.get_opportunity(db, opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "opportunity", opportunity.id, opportunity.name)

    return opportunity_to_response(opportunity)


@router.post("", response_model=schemas.OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opportunity: schemas.OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Set owner to current user if not specified
    if not opportunity.owner_id:
        opportunity.owner_id = current_user.id

    db_opportunity = crud.create_opportunity(db, opportunity)
    return opportunity_to_response(crud.get_opportunity(db, db_opportunity.id))


@router.put("/{opportunity_id}", response_model=schemas.OpportunityResponse)
async def update_opportunity(
    opportunity_id: int,
    opportunity: schemas.OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_opportunity = crud.update_opportunity(db, opportunity_id, opportunity)
    if not db_opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    return opportunity_to_response(crud.get_opportunity(db, opportunity_id))


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_opportunity(db, opportunity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )


@router.put("/{opportunity_id}/change-owner", response_model=schemas.OpportunityResponse)
async def change_opportunity_owner(
    opportunity_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opportunity = crud.update_opportunity(
        db, opportunity_id, schemas.OpportunityUpdate(owner_id=owner_id)
    )
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    return opportunity_to_response(crud.get_opportunity(db, opportunity_id))


@router.put("/{opportunity_id}/stage", response_model=schemas.OpportunityResponse)
async def update_opportunity_stage(
    opportunity_id: int,
    stage: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Update probability based on stage
    stage_probabilities = {
        "Prospecting": 10,
        "Qualification": 20,
        "Needs Analysis": 40,
        "Proposal": 60,
        "Negotiation": 80,
        "Closed Won": 100,
        "Closed Lost": 0
    }

    opportunity = crud.update_opportunity(
        db,
        opportunity_id,
        schemas.OpportunityUpdate(
            stage=stage,
            probability=stage_probabilities.get(stage, 0)
        )
    )

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    return opportunity_to_response(crud.get_opportunity(db, opportunity_id))
