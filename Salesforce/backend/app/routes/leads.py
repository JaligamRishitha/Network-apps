from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..services import AssignmentService, LeadConversionService, DuplicateDetectionService
from ..db_models import User
from ..logger import log_action

router = APIRouter(prefix="/api/leads", tags=["leads"])


def lead_to_response(lead) -> schemas.LeadResponse:
    return schemas.LeadResponse(
        id=lead.id,
        first_name=lead.first_name,
        last_name=lead.last_name,
        company=lead.company,
        title=lead.title,
        phone=lead.phone,
        email=lead.email,
        status=lead.status,
        score=lead.score,
        region=lead.region,
        source=lead.source,
        description=lead.description,
        owner_id=lead.owner_id,
        is_converted=lead.is_converted,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        full_name=lead.full_name,
        owner_alias=lead.owner.alias if lead.owner else None
    )


@router.get("", response_model=schemas.PaginatedResponse)
async def list_leads(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * page_size
    leads, total = crud.get_leads(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return schemas.PaginatedResponse(
        items=[lead_to_response(l) for l in leads],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{lead_id}", response_model=schemas.LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = crud.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "lead", lead.id, lead.full_name)

    return lead_to_response(lead)


@router.post("", response_model=schemas.LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead: schemas.LeadCreate,
    check_duplicates: bool = Query(False),
    auto_assign: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check for duplicates if requested
    if check_duplicates and (lead.email or lead.phone):
        dup_service = DuplicateDetectionService(db)
        warning = dup_service.check_lead_duplicates(lead.email, lead.phone)
        if warning.matching_records:
            log_action(
                action_type="CREATE_LEAD_DUPLICATE_FOUND",
                user=current_user.username,
                details=f"Duplicate check for lead {lead.first_name} {lead.last_name}",
                status="error"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Potential duplicates found",
                    "duplicates": warning.matching_records
                }
            )

    # Create the lead first
    db_lead = crud.create_lead(db, lead)
    
    log_action(
        action_type="CREATE_LEAD",
        user=current_user.username,
        details=f"Lead created: {lead.first_name} {lead.last_name} ({lead.email})",
        status="success"
    )

    # Apply assignment rules if auto_assign is True
    if auto_assign and not lead.owner_id:
        assignment_service = AssignmentService(db)
        owner_id = assignment_service.apply_lead_assignment(db_lead)
        if owner_id:
            crud.update_lead(db, db_lead.id, schemas.LeadUpdate(owner_id=owner_id))
            log_action(
                action_type="LEAD_ASSIGNED",
                user=current_user.username,
                details=f"Lead {db_lead.id} auto-assigned to user {owner_id}",
                status="success"
            )

    return lead_to_response(crud.get_lead(db, db_lead.id))


@router.put("/{lead_id}", response_model=schemas.LeadResponse)
async def update_lead(
    lead_id: int,
    lead: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_lead = crud.update_lead(db, lead_id, lead)
    if not db_lead:
        log_action(
            action_type="UPDATE_LEAD_FAILED",
            user=current_user.username,
            details=f"Lead {lead_id} not found",
            status="error"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    log_action(
        action_type="UPDATE_LEAD",
        user=current_user.username,
        details=f"Lead {lead_id} updated",
        status="success"
    )
    
    return lead_to_response(crud.get_lead(db, lead_id))


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_lead(db, lead_id)
    if not success:
        log_action(
            action_type="DELETE_LEAD_FAILED",
            user=current_user.username,
            details=f"Lead {lead_id} not found",
            status="error"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    log_action(
        action_type="DELETE_LEAD",
        user=current_user.username,
        details=f"Lead {lead_id} deleted",
        status="success"
    )


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: int,
    conversion_data: schemas.LeadConvert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversion_service = LeadConversionService(db)

    try:
        account, contact, opportunity = conversion_service.convert_lead(
            lead_id,
            conversion_data,
            current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {
        "success": True,
        "account_id": account.id if account else None,
        "contact_id": contact.id if contact else None,
        "opportunity_id": opportunity.id if opportunity else None
    }


@router.put("/{lead_id}/change-owner", response_model=schemas.LeadResponse)
async def change_lead_owner(
    lead_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lead = crud.update_lead(db, lead_id, schemas.LeadUpdate(owner_id=owner_id))
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    return lead_to_response(crud.get_lead(db, lead_id))


@router.post("/check-duplicates", response_model=schemas.DuplicateWarning)
async def check_duplicates(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone required"
        )

    dup_service = DuplicateDetectionService(db)
    return dup_service.check_lead_duplicates(email, phone)
