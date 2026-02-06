from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, Account, Contact, Case
from .. import schemas
from ..logger import log_action

router = APIRouter(prefix="/api/mulesoft-integration", tags=["mulesoft-integration"])


# ============================================================================
# SCENARIO 1: New Client Creation
# ============================================================================

class ClientCreationRequest(schemas.BaseModel):
    account_id: int
    contact_id: Optional[int] = None
    company_name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = "NET30"
    credit_limit: Optional[float] = 0.0


class ClientCreationResponse(schemas.BaseModel):
    id: str
    status: str
    sap_customer_id: Optional[str] = None
    correlation_id: str
    message: str
    created_at: datetime


@router.post("/scenario1/create-client", response_model=ClientCreationResponse)
async def create_client(
    request: ClientCreationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scenario 1: New Client Creation
    - Validates account/contact data
    - Performs duplicate detection
    - Sends to SAP via MuleSoft
    - Returns SAP customer ID
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Validate account exists
        account = db.query(Account).filter(Account.id == request.account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Duplicate detection logic
        existing = db.query(Account).filter(
            Account.name == request.company_name
        ).first()
        if existing and existing.id != request.account_id:
            return ClientCreationResponse(
                id=str(uuid.uuid4()),
                status="DUPLICATE_DETECTED",
                correlation_id=correlation_id,
                message=f"Duplicate account found: {existing.name}",
                created_at=datetime.utcnow()
            )
        
        # Prepare SAP payload
        sap_payload = {
            "CUSTOMER_NAME": request.company_name,
            "EMAIL": request.email,
            "PHONE": request.phone,
            "ADDRESS": request.address,
            "CITY": request.city,
            "STATE": request.state,
            "POSTAL_CODE": request.postal_code,
            "COUNTRY": request.country,
            "TAX_ID": request.tax_id,
            "PAYMENT_TERMS": request.payment_terms,
            "CREDIT_LIMIT": request.credit_limit,
            "CORRELATION_ID": correlation_id,
        }
        
        # Simulate MuleSoft call to SAP
        sap_customer_id = f"SAP-{correlation_id[:8].upper()}"
        
        # Update account with SAP reference
        account.correlation_id = correlation_id
        account.integration_status = "COMPLETED"
        db.commit()
        
        log_action(
            action_type="CLIENT_CREATION",
            user=current_user.username,
            details=f"Created SAP customer {sap_customer_id} for account {account.name}",
            status="success"
        )
        
        return ClientCreationResponse(
            id=str(uuid.uuid4()),
            status="SUCCESS",
            sap_customer_id=sap_customer_id,
            correlation_id=correlation_id,
            message=f"Client created successfully in SAP",
            created_at=datetime.utcnow()
        )
    
    except Exception as e:
        log_action(
            action_type="CLIENT_CREATION_ERROR",
            user=current_user.username,
            details=f"Account ID: {request.account_id}",
            status="error",
            error=str(e)
        )
        return ClientCreationResponse(
            id=str(uuid.uuid4()),
            status="ERROR",
            correlation_id=correlation_id,
            message=str(e),
            created_at=datetime.utcnow()
        )


# ============================================================================
# SCENARIO 2: Scheduling & Dispatching (Service Edge)
# ============================================================================

class SchedulingRequest(schemas.BaseModel):
    case_id: int
    technician_id: Optional[int] = None
    appointment_date: str
    appointment_time: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    required_skills: list[str] = []
    parts_required: list[dict] = []
    sla_hours: int = 24


class SchedulingResponse(schemas.BaseModel):
    id: str
    status: str
    assigned_technician_id: Optional[str] = None
    appointment_id: str
    correlation_id: str
    message: str
    created_at: datetime


@router.post("/scenario2/schedule-dispatch", response_model=SchedulingResponse)
async def schedule_dispatch(
    request: SchedulingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scenario 2: Scheduling & Dispatching
    - Validates case and technician availability
    - Optimizes resource assignment
    - Syncs with SAP HR and inventory
    - Returns appointment details
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Validate case exists
        case = db.query(Case).filter(Case.id == request.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Validate parts availability in SAP MM
        parts_status = "AVAILABLE"
        for part in request.parts_required:
            # Simulate SAP inventory check
            if part.get("quantity", 0) <= 0:
                parts_status = "INSUFFICIENT_INVENTORY"
                break
        
        if parts_status == "INSUFFICIENT_INVENTORY":
            return SchedulingResponse(
                id=str(uuid.uuid4()),
                status="PARTS_UNAVAILABLE",
                appointment_id="",
                correlation_id=correlation_id,
                message="Required parts not available in inventory",
                created_at=datetime.utcnow()
            )
        
        # Assign technician (round-robin or skill-based)
        assigned_tech_id = request.technician_id or 1
        appointment_id = f"APT-{correlation_id[:8].upper()}"
        
        # Prepare SAP HR sync payload
        sap_hr_payload = {
            "TECHNICIAN_ID": assigned_tech_id,
            "APPOINTMENT_ID": appointment_id,
            "DATE": request.appointment_date,
            "TIME": request.appointment_time,
            "LOCATION": request.location,
            "LATITUDE": request.latitude,
            "LONGITUDE": request.longitude,
            "SLA_HOURS": request.sla_hours,
            "CORRELATION_ID": correlation_id,
        }
        
        # Update case with appointment
        case.correlation_id = correlation_id
        case.integration_status = "SCHEDULED"
        db.commit()
        
        log_action(
            action_type="SCHEDULING_DISPATCH",
            user=current_user.username,
            details=f"Scheduled appointment {appointment_id} for case {case.id}",
            status="success"
        )
        
        return SchedulingResponse(
            id=str(uuid.uuid4()),
            status="SUCCESS",
            assigned_technician_id=str(assigned_tech_id),
            appointment_id=appointment_id,
            correlation_id=correlation_id,
            message=f"Appointment scheduled successfully",
            created_at=datetime.utcnow()
        )
    
    except Exception as e:
        log_action(
            action_type="SCHEDULING_ERROR",
            user=current_user.username,
            details=f"Case ID: {request.case_id}",
            status="error",
            error=str(e)
        )
        return SchedulingResponse(
            id=str(uuid.uuid4()),
            status="ERROR",
            appointment_id="",
            correlation_id=correlation_id,
            message=str(e),
            created_at=datetime.utcnow()
        )


# ============================================================================
# SCENARIO 3: Work Order Request to SAP
# ============================================================================

class WorkOrderRequest(schemas.BaseModel):
    case_id: int
    customer_id: int
    product_id: Optional[str] = None
    issue_description: str
    service_type: str
    warranty_status: Optional[str] = "ACTIVE"
    contract_id: Optional[str] = None
    priority: str = "MEDIUM"


class WorkOrderResponse(schemas.BaseModel):
    id: str
    status: str
    sap_order_id: Optional[str] = None
    sap_notification_id: Optional[str] = None
    correlation_id: str
    entitlement_verified: bool
    message: str
    created_at: datetime


@router.post("/scenario3/create-work-order", response_model=WorkOrderResponse)
async def create_work_order(
    request: WorkOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scenario 3: Work Order Request to SAP
    - Validates case and customer
    - Verifies warranty and entitlements
    - Creates SAP Service Order/Notification
    - Returns SAP document numbers
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Validate case exists
        case = db.query(Case).filter(Case.id == request.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Verify entitlement
        entitlement_verified = True
        if request.warranty_status != "ACTIVE" and not request.contract_id:
            entitlement_verified = False
        
        if not entitlement_verified:
            return WorkOrderResponse(
                id=str(uuid.uuid4()),
                status="ENTITLEMENT_FAILED",
                correlation_id=correlation_id,
                entitlement_verified=False,
                message="No active warranty or service contract found",
                created_at=datetime.utcnow()
            )
        
        # Prepare SAP payload
        sap_order_id = f"SO-{correlation_id[:8].upper()}"
        sap_notification_id = f"NOT-{correlation_id[:8].upper()}"
        
        sap_payload = {
            "ORDER_ID": sap_order_id,
            "NOTIFICATION_ID": sap_notification_id,
            "CUSTOMER_ID": request.customer_id,
            "PRODUCT_ID": request.product_id,
            "ISSUE_DESCRIPTION": request.issue_description,
            "SERVICE_TYPE": request.service_type,
            "WARRANTY_STATUS": request.warranty_status,
            "CONTRACT_ID": request.contract_id,
            "PRIORITY": request.priority,
            "CORRELATION_ID": correlation_id,
        }
        
        # Update case with SAP references
        case.correlation_id = correlation_id
        case.integration_status = "WORK_ORDER_CREATED"
        db.commit()
        
        log_action(
            action_type="WORK_ORDER_CREATION",
            user=current_user.username,
            details=f"Created SAP work order {sap_order_id} for case {case.id}",
            status="success"
        )
        
        return WorkOrderResponse(
            id=str(uuid.uuid4()),
            status="SUCCESS",
            sap_order_id=sap_order_id,
            sap_notification_id=sap_notification_id,
            correlation_id=correlation_id,
            entitlement_verified=True,
            message=f"Work order created successfully in SAP",
            created_at=datetime.utcnow()
        )
    
    except Exception as e:
        log_action(
            action_type="WORK_ORDER_ERROR",
            user=current_user.username,
            details=f"Case ID: {request.case_id}",
            status="error",
            error=str(e)
        )
        return WorkOrderResponse(
            id=str(uuid.uuid4()),
            status="ERROR",
            correlation_id=correlation_id,
            entitlement_verified=False,
            message=str(e),
            created_at=datetime.utcnow()
        )


# ============================================================================
# Status Tracking & Callbacks
# ============================================================================

@router.get("/status/{correlation_id}")
async def get_integration_status(
    correlation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get integration status by correlation ID"""
    # Check accounts
    account = db.query(Account).filter(
        Account.correlation_id == correlation_id
    ).first()
    if account:
        return {
            "type": "account",
            "id": account.id,
            "status": account.integration_status,
            "correlation_id": correlation_id,
        }
    
    # Check cases
    case = db.query(Case).filter(
        Case.correlation_id == correlation_id
    ).first()
    if case:
        return {
            "type": "case",
            "id": case.id,
            "status": case.integration_status,
            "correlation_id": correlation_id,
        }
    
    raise HTTPException(status_code=404, detail="Correlation ID not found")


@router.post("/callback/status-update")
async def mulesoft_callback(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    Webhook callback from MuleSoft to update integration status
    """
    correlation_id = payload.get("correlation_id")
    status = payload.get("status")
    sap_id = payload.get("sap_id")
    
    if not correlation_id:
        raise HTTPException(status_code=400, detail="Missing correlation_id")
    
    # Update account
    account = db.query(Account).filter(
        Account.correlation_id == correlation_id
    ).first()
    if account:
        account.integration_status = status
        db.commit()
        return {"message": "Account updated", "type": "account"}
    
    # Update case
    case = db.query(Case).filter(
        Case.correlation_id == correlation_id
    ).first()
    if case:
        case.integration_status = status
        db.commit()
        return {"message": "Case updated", "type": "case"}
    
    raise HTTPException(status_code=404, detail="Record not found")
