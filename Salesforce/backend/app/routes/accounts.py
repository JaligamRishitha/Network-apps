from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import math
import os
import uuid

from ..database import get_db
from ..auth import get_current_user
from .. import schemas, crud
from ..db_models import User, AccountRequestStatus, AccountCreationRequest, MulesoftRequest
from ..logger import log_action
from ..integrations import account_approval_integration

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def account_to_response(account, request: Optional[AccountCreationRequest] = None) -> schemas.AccountResponse:
    return schemas.AccountResponse(
        id=account.id,
        name=account.name,
        email=account.email,
        phone=account.phone,
        website=account.website,
        industry=account.industry,
        description=account.description,
        billing_address=account.billing_address,
        street=account.street,
        zip_code=account.zip_code,
        country=account.country,
        owner_id=account.owner_id,
        created_at=account.created_at,
        updated_at=account.updated_at,
        owner_alias=account.owner.alias if account.owner else None,
        request_id=request.id if request else None,
        request_status=request.status if request else None,
        servicenow_ticket_id=request.servicenow_ticket_id if request else None,
        integration_status=request.integration_status if request else None,
        correlation_id=request.correlation_id if request else None,
    )


def account_request_to_response(request) -> schemas.AccountRequestResponse:
    return schemas.AccountRequestResponse(
        id=request.id,
        name=request.name,
        status=request.status,
        auto_approved=request.auto_approved,
        correlation_id=request.correlation_id,
        requested_by_id=request.requested_by_id,
        approved_by_id=request.approved_by_id,
        servicenow_ticket_id=request.servicenow_ticket_id,
        servicenow_status=request.servicenow_status,
        mulesoft_transaction_id=request.mulesoft_transaction_id,
        integration_status=request.integration_status,
        error_message=request.error_message,
        created_account_id=request.created_account_id,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def is_manager(user: User) -> bool:
    return user.role in {"admin", "manager"}


def verify_mulesoft_secret(secret: Optional[str]) -> None:
    expected = os.getenv("MULESOFT_SHARED_SECRET", "mulesoft-salesforce-shared-secret-2024")
    if secret != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid MuleSoft secret")


def latest_requests_by_account_id(
    db: Session,
    account_ids: list[int],
) -> dict[int, AccountCreationRequest]:
    if not account_ids:
        return {}
    requests = (
        db.query(AccountCreationRequest)
        .filter(AccountCreationRequest.created_account_id.in_(account_ids))
        .order_by(AccountCreationRequest.created_at.desc())
        .all()
    )
    latest: dict[int, AccountCreationRequest] = {}
    for req in requests:
        acct_id = req.created_account_id
        if acct_id and acct_id not in latest:
            latest[acct_id] = req
    return latest


@router.get("", response_model=schemas.PaginatedResponse)
async def list_accounts(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    owner_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List only approved/created accounts.
    Pending requests are shown in the Requests tab.
    """
    skip = (page - 1) * page_size
    accounts, total = crud.get_accounts(
        db,
        skip=skip,
        limit=page_size,
        search=q,
        owner_id=owner_id,
        sort_by=sort_by,
        sort_order=sort_order
    )

    request_map = latest_requests_by_account_id(db, [a.id for a in accounts])

    return schemas.PaginatedResponse(
        items=[account_to_response(a, request_map.get(a.id)) for a in accounts],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Response = None
):
    if not account.owner_id:
        account.owner_id = current_user.id

    # Create account request - DO NOT create account yet
    correlation_id = str(uuid.uuid4())
    request = AccountCreationRequest(
        name=account.name,
        requested_payload=account.model_dump(),
        status=AccountRequestStatus.PENDING.value,
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Send to MuleSoft → ServiceNow for approval
    if is_manager(current_user):
        request = await account_approval_integration.record_manager_audit(db, request, current_user)
    else:
        request = await account_approval_integration.record_user_submission(db, request, current_user)

    log_action(
        action_type="ACCOUNT_REQUEST_CREATED",
        user=current_user.username,
        details=f"Created account request {request.id} - sent to MuleSoft/ServiceNow",
        status="success",
    )

    return {
        "request": {
            "id": request.id,
            "name": request.name,
            "status": request.status,
            "integration_status": request.integration_status,
            "mulesoft_transaction_id": request.mulesoft_transaction_id,
            "created_at": request.created_at
        }
    }


@router.get("/requests", response_model=schemas.PaginatedResponse)
async def list_account_requests(
    status_filter: Optional[AccountRequestStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skip = (page - 1) * page_size
    requested_by_id = None if is_manager(current_user) else current_user.id
    items, total = crud.list_account_requests(
        db,
        status=status_filter.value if status_filter else None,
        requested_by_id=requested_by_id,
        skip=skip,
        limit=page_size,
    )

    return schemas.PaginatedResponse(
        items=[account_request_to_response(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/requests/{request_id}/approve", response_model=schemas.AccountCreateResult)
async def approve_account_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve request and create account (called by ServiceNow webhook or manager)"""
    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    # Create the actual account
    try:
        payload = request.requested_payload or {}
        account_data = schemas.AccountCreate(**payload)
        if not account_data.owner_id:
            account_data.owner_id = request.requested_by_id

        db_account = crud.create_account(db, account_data)
        
        # Update request status
        request.status = AccountRequestStatus.COMPLETED.value
        request.created_account_id = db_account.id
        request.integration_status = "COMPLETED"
        db.commit()
        
        log_action(
            action_type="ACCOUNT_APPROVED",
            user=current_user.username,
            details=f"Approved request {request.id} -> account {db_account.id}",
            status="success",
        )
        
        return schemas.AccountCreateResult(
            flow="approved_and_created",
            account=account_to_response(db_account),
            request=account_request_to_response(request),
        )
    except Exception as exc:
        request.status = AccountRequestStatus.FAILED.value
        request.integration_status = "FAILED"
        request.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))





@router.post("/requests/{request_id}/mulesoft-accept", response_model=schemas.AccountCreateResult)
async def mulesoft_accept_account_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simulates MuleSoft accepting the request and calling back into Salesforce.
    In real integration, MuleSoft would invoke this after downstream approval.
    """
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")

    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    try:
        payload = request.requested_payload or {}
        account_data = schemas.AccountCreate(**payload)
        if not account_data.owner_id:
            account_data.owner_id = request.requested_by_id

        db_account = crud.create_account(db, account_data)
        request = crud.complete_account_request_with_account(db, request, db_account, current_user)
        request = crud.update_account_request_integration(
            db,
            request,
            integration_status="COMPLETED",
        )
    except Exception:
        request = crud.fail_account_request(db, request, "MuleSoft acceptance failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account creation failed")

    log_action(
        action_type="ACCOUNT_REQUEST_ACCEPTED_BY_MULESOFT",
        user=current_user.username,
        details=f"MuleSoft accepted request {request.id} -> account {request.created_account_id}",
        status="success",
    )

    return schemas.AccountCreateResult(
        flow="mulesoft_accepted_and_created",
        account=account_to_response(crud.get_account(db, db_account.id)),
        request=account_request_to_response(request),
    )


@router.post("/requests/{request_id}/mulesoft-callback", response_model=schemas.AccountCreateResult)
async def mulesoft_callback_account_request(
    request_id: int,
    payload: schemas.MuleSoftAccountCallback,
    x_mulesoft_secret: Optional[str] = Header(None, alias="X-MuleSoft-Secret"),
    db: Session = Depends(get_db),
):
    """
    Endpoint intended for MuleSoft to call after orchestration/approval.
    Secured via shared secret header.
    """
    verify_mulesoft_secret(x_mulesoft_secret)

    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    if not payload.accepted:
        request = crud.reject_account_request(db, request, request.requested_by, reason=payload.message or payload.status)
        request = crud.update_account_request_integration(
            db,
            request,
            integration_status="FAILED",
            error_message=payload.message,
        )
        log_action(
            action_type="ACCOUNT_REQUEST_REJECTED_BY_MULESOFT",
            user="mulesoft",
            details=f"Request {request.id} rejected by MuleSoft",
            status="error",
        )
        return schemas.AccountCreateResult(flow="mulesoft_rejected", request=account_request_to_response(request))

    try:
        payload_data = request.requested_payload or {}
        account_data = schemas.AccountCreate(**payload_data)
        if not account_data.owner_id:
            account_data.owner_id = request.requested_by_id

        db_account = crud.create_account(db, account_data)
        request = crud.complete_account_request_with_account(db, request, db_account, request.requested_by)
        request = crud.update_account_request_integration(
            db,
            request,
            integration_status="COMPLETED",
        )
    except Exception:
        request = crud.fail_account_request(db, request, "MuleSoft callback failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Account creation failed")

    log_action(
        action_type="ACCOUNT_REQUEST_ACCEPTED_BY_MULESOFT",
        user="mulesoft",
        details=f"MuleSoft callback accepted request {request.id} -> account {request.created_account_id}",
        status="success",
    )

    return schemas.AccountCreateResult(
        flow="mulesoft_callback_created",
        account=account_to_response(crud.get_account(db, db_account.id)),
        request=account_request_to_response(request),
    )


class MuleSoftStatusUpdate(BaseModel):
    integration_status: Optional[str] = None
    servicenow_status: Optional[str] = None
    servicenow_ticket_id: Optional[str] = None
    mulesoft_transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    status: Optional[str] = None


@router.put("/requests/{request_id}", response_model=schemas.AccountRequestResponse)
async def update_account_request_status(
    request_id: int,
    payload: MuleSoftStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update account request integration status.
    Used by MuleSoft to update validation/approval status.
    """
    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")

    # Update integration fields
    request = crud.update_account_request_integration(
        db,
        request,
        integration_status=payload.integration_status,
        servicenow_status=payload.servicenow_status,
        servicenow_ticket_id=payload.servicenow_ticket_id,
        mulesoft_transaction_id=payload.mulesoft_transaction_id,
        error_message=payload.error_message,
    )

    # Update main status if provided
    if payload.status:
        request.status = payload.status
        db.commit()
        db.refresh(request)

    log_action(
        action_type="ACCOUNT_REQUEST_STATUS_UPDATED",
        user=current_user.username,
        details=f"Updated request {request_id} - integration_status: {payload.integration_status}",
        status="success",
    )

    return account_request_to_response(request)


@router.post("/requests/{request_id}/reject", response_model=schemas.AccountRequestResponse)
async def reject_account_request(
    request_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = crud.get_account_request(db, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account request not found")
    if request.status != AccountRequestStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending")

    request = crud.update_account_request_integration(db, request, integration_status="FAILED", error_message=reason)
    request = crud.reject_account_request(db, request, current_user, reason=reason)

    log_action(
        action_type="ACCOUNT_REQUEST_REJECTED",
        user=current_user.username,
        details=f"Rejected account request {request.id}",
        status="error",
    )

    return account_request_to_response(request)


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an account creation request."""
    success = crud.delete_account_request(db, request_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    log_action(
        action_type="ACCOUNT_REQUEST_DELETED",
        user=current_user.username,
        details=f"Deleted account request {request_id}",
        status="success",
    )


@router.get("/{account_id}", response_model=schemas.AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = crud.get_account(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Track recent record
    crud.add_recent_record(db, current_user.id, "account", account.id, account.name)

    request_map = latest_requests_by_account_id(db, [account.id])
    return account_to_response(account, request_map.get(account.id))


@router.put("/{account_id}", response_model=schemas.AccountResponse)
async def update_account(
    account_id: int,
    account: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_account = crud.update_account(db, account_id, account)
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account_to_response(crud.get_account(db, account_id))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = crud.delete_account(db, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )


@router.put("/{account_id}/change-owner", response_model=schemas.AccountResponse)
async def change_account_owner(
    account_id: int,
    owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = crud.update_account(db, account_id, schemas.AccountUpdate(owner_id=owner_id))
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account_to_response(crud.get_account(db, account_id))
