from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..services import DuplicateDetectionService
from ..db_models import User

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


def contact_to_response(contact) -> schemas.ContactResponse:
    return schemas.ContactResponse(
        id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        account_id=contact.account_id,
        title=contact.title,
        phone=contact.phone,
        email=contact.email,
        mailing_address=contact.mailing_address,
        owner_id=contact.owner_id,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
        full_name=contact.full_name,
        account_name=contact.account.name if contact.account else None,
        owner_alias=contact.owner.alias if contact.owner else None
    )


@router.get("", response_model=schemas.PaginatedResponse)
async def list_contacts(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * page_size
    contacts, total = crud.get_contacts(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        account_id=account_id,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return schemas.PaginatedResponse(
        items=[contact_to_response(c) for c in contacts],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{contact_id}", response_model=schemas.ContactResponse)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "contact", contact.id, contact.full_name)

    return contact_to_response(contact)


@router.post("", response_model=schemas.ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: schemas.ContactCreate,
    check_duplicates: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check for duplicates if requested
    if check_duplicates and (contact.email or contact.phone):
        dup_service = DuplicateDetectionService(db)
        warning = dup_service.check_contact_duplicates(contact.email, contact.phone)
        if warning.matching_records:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Potential duplicates found",
                    "duplicates": warning.matching_records
                }
            )

    # Set owner to current user if not specified
    if not contact.owner_id:
        contact.owner_id = current_user.id

    db_contact = crud.create_contact(db, contact)
    return contact_to_response(crud.get_contact(db, db_contact.id))


@router.put("/{contact_id}", response_model=schemas.ContactResponse)
async def update_contact(
    contact_id: int,
    contact: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_contact = crud.update_contact(db, contact_id, contact)
    if not db_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact_to_response(crud.get_contact(db, contact_id))


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_contact(db, contact_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )


@router.put("/{contact_id}/change-owner", response_model=schemas.ContactResponse)
async def change_contact_owner(
    contact_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = crud.update_contact(db, contact_id, schemas.ContactUpdate(owner_id=owner_id))
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return contact_to_response(crud.get_contact(db, contact_id))


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
    return dup_service.check_contact_duplicates(email, phone)
