from pydantic import BaseModel

class QuotationCreate(BaseModel):
    account_id: int
    title: str
    amount: float
    tax_amount: float = 0

class InvoiceCreate(BaseModel):
    account_id: int
    description: str
    amount: float
    invoice_type: str = "Standard"
    tax_amount: float = 0

class ServiceAccountCreate(BaseModel):
    account_id: int
    warranty_status: str = "Active"
    service_level: str = "Silver"

class WarrantyExtensionCreate(BaseModel):
    service_account_id: int
    extension_start_date: str
    extension_end_date: str
    extension_cost: float = 0

class SLACreate(BaseModel):
    service_account_id: int
    name: str
    response_time_hours: int
    resolution_time_hours: int
    uptime_percentage: float = 99.9
    support_hours: str = "24/7"


class ServiceAppointmentCreate(BaseModel):
    account_id: Optional[int] = None
    case_id: Optional[int] = None
    subject: str
    description: Optional[str] = None
    appointment_type: str = "Field Service"
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    priority: str = "Normal"
    location: Optional[str] = None
    required_skills: Optional[str] = None
    required_parts: Optional[str] = None


class SchedulingCallbackRequest(BaseModel):
    status: str  # SUCCESS, PARTS_UNAVAILABLE, TECHNICIAN_UNAVAILABLE, FAILED
    assigned_technician_id: Optional[int] = None
    technician_name: Optional[str] = None
    parts_available: Optional[bool] = True
    parts_status: Optional[str] = None
    mulesoft_transaction_id: Optional[str] = None
    correlation_id: Optional[str] = None
    sap_hr_response: Optional[str] = None
    sap_inventory_response: Optional[str] = None
    error_message: Optional[str] = None


class WorkOrderCreate(BaseModel):
    account_id: Optional[int] = None
    case_id: Optional[int] = None
    subject: str
    description: Optional[str] = None
    priority: str = "Medium"
    service_type: str = "Warranty"
    product: Optional[str] = None


class WorkOrderCallbackRequest(BaseModel):
    status: str  # SUCCESS, ENTITLEMENT_FAILED, FAILED
    entitlement_verified: Optional[bool] = False
    entitlement_type: Optional[str] = None
    entitlement_end_date: Optional[str] = None
    sap_order_id: Optional[str] = None
    sap_notification_id: Optional[str] = None
    mulesoft_transaction_id: Optional[str] = None
    correlation_id: Optional[str] = None
    error_message: Optional[str] = None

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
import math

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, ServiceAccount, ServiceLevelAgreement, Quotation, Invoice, WarrantyExtension, ServiceAppointment, SchedulingRequest, WorkOrder, Account
from ..logger import log_action

router = APIRouter(prefix="/api/service", tags=["service"])

# Service Accounts
@router.get("/accounts")
async def list_service_accounts(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.query(ServiceAccount).offset(skip).limit(limit).all()
    total = db.query(ServiceAccount).count()
    return {"items": accounts, "total": total}

@router.post("/accounts")
async def create_service_account(
    data: ServiceAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service_account = ServiceAccount(
        account_id=data.account_id,
        warranty_status=data.warranty_status,
        service_level=data.service_level,
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(service_account)
    db.commit()
    db.refresh(service_account)
    
    log_action(
        action_type="CREATE_SERVICE_ACCOUNT",
        user=current_user.username,
        details=f"Service account created for account {data.account_id}",
        status="success"
    )
    
    return service_account

@router.get("/accounts/{account_id}")
async def get_service_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    return account

@router.put("/accounts/{account_id}")
async def update_service_account(
    account_id: int,
    warranty_status: Optional[str] = None,
    service_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(ServiceAccount).filter(ServiceAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Service account not found")
    
    if warranty_status:
        account.warranty_status = warranty_status
    if service_level:
        account.service_level = service_level
    
    db.commit()
    db.refresh(account)
    
    log_action(
        action_type="UPDATE_SERVICE_ACCOUNT",
        user=current_user.username,
        details=f"Service account {account_id} updated",
        status="success"
    )
    
    return account

# Quotations
@router.get("/quotations")
async def list_quotations(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotations = db.query(Quotation).offset(skip).limit(limit).all()
    total = db.query(Quotation).count()
    return {"items": quotations, "total": total}

@router.post("/quotations")
async def create_quotation(
    data: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        quotation = Quotation(
            quotation_number=f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=data.account_id,
            title=data.title,
            amount=data.amount,
            tax_amount=data.tax_amount,
            total_amount=data.amount + data.tax_amount,
            status="Draft",
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        db.add(quotation)
        db.commit()
        db.refresh(quotation)
        
        log_action(
            action_type="CREATE_QUOTATION",
            user=current_user.username,
            details=f"Quotation {quotation.quotation_number} created for £{data.amount}",
            status="success"
        )
        
        return quotation
    except Exception as e:
        db.rollback()
        print(f"Error creating quotation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotations/{quotation_id}")
async def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation

@router.put("/quotations/{quotation_id}")
async def update_quotation(
    quotation_id: int,
    status: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if status:
        quotation.status = status
    if amount:
        quotation.amount = amount
        quotation.total_amount = amount + quotation.tax_amount
    
    db.commit()
    db.refresh(quotation)
    
    log_action(
        action_type="UPDATE_QUOTATION",
        user=current_user.username,
        details=f"Quotation {quotation.quotation_number} updated",
        status="success"
    )
    
    return quotation

# Invoices
@router.get("/invoices")
async def list_invoices(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoices = db.query(Invoice).offset(skip).limit(limit).all()
    total = db.query(Invoice).count()
    return {"items": invoices, "total": total}

@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        invoice = Invoice(
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=data.account_id,
            description=data.description,
            amount=data.amount,
            tax_amount=data.tax_amount,
            total_amount=data.amount + data.tax_amount,
            invoice_type=data.invoice_type,
            status="Draft",
            invoice_date=datetime.now(),
            owner_id=current_user.id,
            created_at=datetime.now()
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        log_action(
            action_type="CREATE_INVOICE",
            user=current_user.username,
            details=f"Invoice {invoice.invoice_number} created ({data.invoice_type}) for £{data.amount}",
            status="success"
        )
        
        return invoice
    except Exception as e:
        db.rollback()
        print(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    status: Optional[str] = None,
    amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if status:
        invoice.status = status
        if status == "Paid":
            invoice.paid_date = datetime.now()
    if amount:
        invoice.amount = amount
        invoice.total_amount = amount + invoice.tax_amount
    
    db.commit()
    db.refresh(invoice)
    
    log_action(
        action_type="UPDATE_INVOICE",
        user=current_user.username,
        details=f"Invoice {invoice.invoice_number} updated to {status}",
        status="success"
    )
    
    return invoice

# Warranty Extensions
@router.get("/warranty-extensions")
async def list_warranty_extensions(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extensions = db.query(WarrantyExtension).offset(skip).limit(limit).all()
    total = db.query(WarrantyExtension).count()
    return {"items": extensions, "total": total}

@router.post("/warranty-extensions")
async def create_warranty_extension(
    data: WarrantyExtensionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extension = WarrantyExtension(
        service_account_id=data.service_account_id,
        extension_start_date=datetime.fromisoformat(data.extension_start_date),
        extension_end_date=datetime.fromisoformat(data.extension_end_date),
        extension_cost=data.extension_cost,
        status="Active",
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(extension)
    db.commit()
    db.refresh(extension)
    
    log_action(
        action_type="CREATE_WARRANTY_EXTENSION",
        user=current_user.username,
        details=f"Warranty extension created for service account {data.service_account_id}",
        status="success"
    )
    
    return extension

@router.get("/slas")
async def list_slas(
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        slas = db.query(ServiceLevelAgreement).offset(skip).limit(limit).all()
        total = db.query(ServiceLevelAgreement).count()
        return {"items": slas, "total": total}
    except Exception as e:
        print(f"Error listing SLAs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/slas")
async def create_sla(
    data: SLACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sla = ServiceLevelAgreement(
        service_account_id=data.service_account_id,
        name=data.name,
        response_time_hours=data.response_time_hours,
        resolution_time_hours=data.resolution_time_hours,
        uptime_percentage=data.uptime_percentage,
        support_hours=data.support_hours,
        created_at=datetime.now()
    )
    db.add(sla)
    db.commit()
    db.refresh(sla)
    
    log_action(
        action_type="CREATE_SLA",
        user=current_user.username,
        details=f"SLA '{data.name}' created for service account {data.service_account_id}",
        status="success"
    )

    return sla


# ============================================
# Service Appointments (Scenario 2)
# ============================================

@router.get("/appointments")
async def list_service_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all service appointments"""
    query = db.query(ServiceAppointment)

    if status_filter:
        query = query.filter(ServiceAppointment.status == status_filter)

    total = query.count()
    skip = (page - 1) * page_size

    appointments = query.order_by(ServiceAppointment.created_at.desc()).offset(skip).limit(page_size).all()

    return {
        "items": [
            {
                "id": apt.id,
                "appointment_number": apt.appointment_number,
                "subject": apt.subject,
                "description": apt.description,
                "appointment_type": apt.appointment_type,
                "scheduled_start": apt.scheduled_start,
                "scheduled_end": apt.scheduled_end,
                "status": apt.status,
                "priority": apt.priority,
                "assigned_technician_id": apt.assigned_technician_id,
                "technician_name": apt.technician_name,
                "location": apt.location,
                "account_id": apt.account_id,
                "case_id": apt.case_id,
                "created_at": apt.created_at,
                "updated_at": apt.updated_at
            }
            for apt in appointments
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 0
    }


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
async def create_service_appointment(
    data: ServiceAppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a service appointment and trigger scheduling request to MuleSoft"""
    # Generate appointment number
    appointment_number = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    correlation_id = str(uuid.uuid4())

    # Create the appointment
    appointment = ServiceAppointment(
        appointment_number=appointment_number,
        account_id=data.account_id,
        case_id=data.case_id,
        subject=data.subject,
        description=data.description,
        appointment_type=data.appointment_type,
        scheduled_start=datetime.fromisoformat(data.scheduled_start) if data.scheduled_start else None,
        scheduled_end=datetime.fromisoformat(data.scheduled_end) if data.scheduled_end else None,
        status="Scheduled",
        priority=data.priority,
        location=data.location,
        required_skills=data.required_skills,
        required_parts=data.required_parts,
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(appointment)
    db.flush()

    # Create scheduling request for MuleSoft
    scheduling_req = SchedulingRequest(
        appointment_id=appointment.id,
        appointment_number=appointment_number,
        request_type="schedule",
        status="PENDING",
        integration_status="PENDING_MULESOFT",
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(scheduling_req)
    db.commit()
    db.refresh(appointment)
    db.refresh(scheduling_req)

    log_action(
        action_type="CREATE_SERVICE_APPOINTMENT",
        user=current_user.username,
        details=f"Service appointment {appointment_number} created",
        status="success"
    )

    return {
        "appointment": {
            "id": appointment.id,
            "appointment_number": appointment_number,
            "subject": appointment.subject,
            "status": appointment.status,
            "scheduled_start": appointment.scheduled_start,
            "scheduled_end": appointment.scheduled_end,
            "created_at": appointment.created_at
        },
        "scheduling_request": {
            "id": scheduling_req.id,
            "correlation_id": correlation_id,
            "status": scheduling_req.status,
            "integration_status": scheduling_req.integration_status
        },
        "message": "Appointment created. Scheduling request sent to MuleSoft."
    }


@router.get("/appointments/{appointment_id}")
async def get_service_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific service appointment"""
    appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


# ============================================
# Scheduling Requests (MuleSoft Integration)
# ============================================

@router.get("/scheduling-requests")
async def list_scheduling_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scheduling requests for Scenario 2"""
    query = db.query(SchedulingRequest)

    if status_filter:
        query = query.filter(SchedulingRequest.status == status_filter)

    total = query.count()
    skip = (page - 1) * page_size

    requests = query.order_by(SchedulingRequest.created_at.desc()).offset(skip).limit(page_size).all()

    return {
        "items": [
            {
                "id": req.id,
                "appointment_id": req.appointment_id,
                "appointment_number": req.appointment_number,
                "request_type": req.request_type,
                "status": req.status,
                "integration_status": req.integration_status,
                "assigned_technician_id": req.assigned_technician_id,
                "technician_name": req.technician_name,
                "parts_available": req.parts_available,
                "parts_status": req.parts_status,
                "mulesoft_transaction_id": req.mulesoft_transaction_id,
                "correlation_id": req.correlation_id,
                "error_message": req.error_message,
                "requested_by_id": req.requested_by_id,
                "created_at": req.created_at,
                "updated_at": req.updated_at
            }
            for req in requests
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 0
    }


@router.post("/scheduling-requests/{request_id}/mulesoft-callback")
async def scheduling_mulesoft_callback(
    request_id: int,
    callback: SchedulingCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint for MuleSoft to update scheduling request status.
    Called after MuleSoft checks SAP HR (technician) and SAP Inventory (parts).

    Endpoint: POST /api/service/scheduling-requests/{request_id}/mulesoft-callback
    """
    scheduling_req = db.query(SchedulingRequest).filter(SchedulingRequest.id == request_id).first()
    if not scheduling_req:
        raise HTTPException(status_code=404, detail=f"Scheduling request {request_id} not found")

    # Update request with callback data
    scheduling_req.status = callback.status
    scheduling_req.updated_at = datetime.now()

    if callback.assigned_technician_id:
        scheduling_req.assigned_technician_id = callback.assigned_technician_id
    if callback.technician_name:
        scheduling_req.technician_name = callback.technician_name
    if callback.parts_available is not None:
        scheduling_req.parts_available = callback.parts_available
    if callback.parts_status:
        scheduling_req.parts_status = callback.parts_status
    if callback.mulesoft_transaction_id:
        scheduling_req.mulesoft_transaction_id = callback.mulesoft_transaction_id
    if callback.correlation_id:
        scheduling_req.correlation_id = callback.correlation_id
    if callback.sap_hr_response:
        scheduling_req.sap_hr_response = callback.sap_hr_response
    if callback.sap_inventory_response:
        scheduling_req.sap_inventory_response = callback.sap_inventory_response
    if callback.error_message:
        scheduling_req.error_message = callback.error_message

    # Update integration status
    if callback.status == "SUCCESS":
        scheduling_req.integration_status = "COMPLETED"
        # Update the appointment with assigned technician
        if scheduling_req.appointment_id:
            appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == scheduling_req.appointment_id).first()
            if appointment:
                appointment.assigned_technician_id = callback.assigned_technician_id
                appointment.technician_name = callback.technician_name
                appointment.status = "Dispatched"
    elif callback.status == "PARTS_UNAVAILABLE":
        scheduling_req.integration_status = "PARTS_CHECK_FAILED"
    elif callback.status == "TECHNICIAN_UNAVAILABLE":
        scheduling_req.integration_status = "HR_CHECK_FAILED"
    elif callback.status == "FAILED":
        scheduling_req.integration_status = "FAILED"

    db.commit()
    db.refresh(scheduling_req)

    return {
        "success": True,
        "request_id": request_id,
        "status": scheduling_req.status,
        "integration_status": scheduling_req.integration_status,
        "assigned_technician_id": scheduling_req.assigned_technician_id,
        "message": f"Scheduling request {request_id} updated to {callback.status}"
    }


@router.post("/scheduling-requests/{request_id}/approve")
async def approve_scheduling_request(
    request_id: int,
    technician_id: int = Query(..., description="Technician ID to assign"),
    technician_name: str = Query("Field Technician", description="Technician name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manual approval for scheduling (simulates MuleSoft success)"""
    scheduling_req = db.query(SchedulingRequest).filter(SchedulingRequest.id == request_id).first()
    if not scheduling_req:
        raise HTTPException(status_code=404, detail="Scheduling request not found")

    if scheduling_req.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Request is already {scheduling_req.status}")

    # Update scheduling request
    scheduling_req.status = "SUCCESS"
    scheduling_req.integration_status = "COMPLETED"
    scheduling_req.assigned_technician_id = technician_id
    scheduling_req.technician_name = technician_name
    scheduling_req.parts_available = True
    scheduling_req.updated_at = datetime.now()

    # Update the appointment
    if scheduling_req.appointment_id:
        appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == scheduling_req.appointment_id).first()
        if appointment:
            appointment.assigned_technician_id = technician_id
            appointment.technician_name = technician_name
            appointment.status = "Dispatched"

    db.commit()

    return {
        "success": True,
        "request_id": request_id,
        "status": "SUCCESS",
        "assigned_technician_id": technician_id,
        "technician_name": technician_name,
        "message": "Scheduling approved and technician assigned"
    }


# ============================================
# Work Orders (Scenario 3)
# ============================================

@router.get("/work-orders")
async def list_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all work orders for Scenario 3"""
    query = db.query(WorkOrder)

    if status_filter:
        query = query.filter(WorkOrder.status == status_filter)

    total = query.count()
    skip = (page - 1) * page_size

    work_orders = query.order_by(WorkOrder.created_at.desc()).offset(skip).limit(page_size).all()

    # Get account names
    account_ids = [wo.account_id for wo in work_orders if wo.account_id]
    accounts_map = {}
    if account_ids:
        accounts = db.query(Account).filter(Account.id.in_(account_ids)).all()
        accounts_map = {a.id: a.name for a in accounts}

    return {
        "items": [
            {
                "id": wo.id,
                "work_order_number": wo.work_order_number,
                "account_id": wo.account_id,
                "account_name": accounts_map.get(wo.account_id) if wo.account_id else None,
                "case_id": wo.case_id,
                "subject": wo.subject,
                "description": wo.description,
                "priority": wo.priority,
                "service_type": wo.service_type,
                "product": wo.product,
                "status": wo.status,
                "integration_status": wo.integration_status,
                "entitlement_verified": wo.entitlement_verified,
                "entitlement_type": wo.entitlement_type,
                "sap_order_id": wo.sap_order_id,
                "sap_notification_id": wo.sap_notification_id,
                "mulesoft_transaction_id": wo.mulesoft_transaction_id,
                "correlation_id": wo.correlation_id,
                "error_message": wo.error_message,
                "created_at": wo.created_at,
                "updated_at": wo.updated_at
            }
            for wo in work_orders
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 0
    }


@router.post("/work-orders", status_code=status.HTTP_201_CREATED)
async def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a work order and trigger MuleSoft integration for Scenario 3"""
    # Generate work order number
    work_order_number = f"WO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    correlation_id = str(uuid.uuid4())

    # Create the work order
    work_order = WorkOrder(
        work_order_number=work_order_number,
        account_id=data.account_id,
        case_id=data.case_id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        service_type=data.service_type,
        product=data.product,
        status="PENDING",
        integration_status="PENDING_MULESOFT",
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
        owner_id=current_user.id,
        created_at=datetime.now()
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    log_action(
        action_type="CREATE_WORK_ORDER",
        user=current_user.username,
        details=f"Work order {work_order_number} created",
        status="success"
    )

    return {
        "work_order": {
            "id": work_order.id,
            "work_order_number": work_order_number,
            "subject": work_order.subject,
            "status": work_order.status,
            "created_at": work_order.created_at
        },
        "integration": {
            "correlation_id": correlation_id,
            "status": work_order.status,
            "integration_status": work_order.integration_status
        },
        "message": "Work order created. Sent to MuleSoft for entitlement check."
    }


@router.get("/work-orders/{work_order_id}")
async def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific work order"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    return work_order


@router.post("/work-orders/{work_order_id}/mulesoft-callback")
async def work_order_mulesoft_callback(
    work_order_id: int,
    callback: WorkOrderCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint for MuleSoft to update work order status.
    Called after MuleSoft checks SAP entitlement and creates SAP service order.

    Endpoint: POST /api/service/work-orders/{work_order_id}/mulesoft-callback
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail=f"Work order {work_order_id} not found")

    # Update work order with callback data
    work_order.status = callback.status
    work_order.updated_at = datetime.now()

    if callback.entitlement_verified is not None:
        work_order.entitlement_verified = callback.entitlement_verified
    if callback.entitlement_type:
        work_order.entitlement_type = callback.entitlement_type
    if callback.entitlement_end_date:
        work_order.entitlement_end_date = datetime.fromisoformat(callback.entitlement_end_date)
    if callback.sap_order_id:
        work_order.sap_order_id = callback.sap_order_id
    if callback.sap_notification_id:
        work_order.sap_notification_id = callback.sap_notification_id
    if callback.mulesoft_transaction_id:
        work_order.mulesoft_transaction_id = callback.mulesoft_transaction_id
    if callback.correlation_id:
        work_order.correlation_id = callback.correlation_id
    if callback.error_message:
        work_order.error_message = callback.error_message

    # Update integration status
    if callback.status == "SUCCESS":
        work_order.integration_status = "COMPLETED"
    elif callback.status == "ENTITLEMENT_FAILED":
        work_order.integration_status = "ENTITLEMENT_CHECK_FAILED"
    elif callback.status == "FAILED":
        work_order.integration_status = "FAILED"

    db.commit()
    db.refresh(work_order)

    return {
        "success": True,
        "work_order_id": work_order_id,
        "status": work_order.status,
        "integration_status": work_order.integration_status,
        "entitlement_verified": work_order.entitlement_verified,
        "sap_order_id": work_order.sap_order_id,
        "message": f"Work order {work_order_id} updated to {callback.status}"
    }


@router.post("/work-orders/{work_order_id}/approve")
async def approve_work_order(
    work_order_id: int,
    sap_order_id: str = Query(None, description="SAP Order ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manual approval for work order (simulates MuleSoft success with entitlement)"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    if work_order.status not in ["PENDING", "ENTITLEMENT_FAILED"]:
        raise HTTPException(status_code=400, detail=f"Work order is already {work_order.status}")

    # Update work order
    work_order.status = "SUCCESS"
    work_order.integration_status = "COMPLETED"
    work_order.entitlement_verified = True
    work_order.entitlement_type = work_order.service_type
    work_order.sap_order_id = sap_order_id or f"SAP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    work_order.sap_notification_id = f"NOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    work_order.updated_at = datetime.now()

    db.commit()

    return {
        "success": True,
        "work_order_id": work_order_id,
        "status": "SUCCESS",
        "entitlement_verified": True,
        "sap_order_id": work_order.sap_order_id,
        "message": "Work order approved and SAP order created"
    }


@router.get("/work-orders/{work_order_id}/check-entitlement")
async def check_work_order_entitlement(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check entitlement status for a work order"""
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")

    return {
        "work_order_id": work_order_id,
        "entitlement_verified": work_order.entitlement_verified,
        "entitlement_type": work_order.entitlement_type,
        "entitlement_end_date": work_order.entitlement_end_date,
        "service_type": work_order.service_type,
        "status": work_order.status
    }
