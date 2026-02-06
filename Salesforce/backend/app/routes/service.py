from pydantic import BaseModel
from typing import Optional

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

class WorkOrderCreate(BaseModel):
    account_id: Optional[int] = None
    case_id: Optional[int] = None
    subject: str
    description: Optional[str] = None
    priority: str = "Medium"
    service_type: str = "Warranty"
    product: Optional[str] = None

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, ServiceAccount, ServiceLevelAgreement, Quotation, Invoice, WarrantyExtension, ServiceAppointment, SchedulingRequest, WorkOrder, AppointmentRequest, AppointmentRequestStatus, WorkOrderRequest, WorkOrderRequestStatus
from ..logger import log_action
from ..servicenow import get_servicenow_client
from ..sap import get_sap_client

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
# SCENARIO 2: Service Appointments & Scheduling
# ============================================

@router.get("/appointments")
async def list_service_appointments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all service appointments"""
    appointments = db.query(ServiceAppointment).offset(skip).limit(limit).all()
    return appointments


@router.get("/appointments/{appointment_id}/available-technicians")
async def get_available_technicians_for_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available technicians from SAP HR for an appointment"""

    # Get appointment details
    appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Service appointment not found")

    # Query SAP HR for available technicians
    sap_client = get_sap_client()

    # Parse required skills if provided
    skills = []
    if appointment.required_skills:
        skills = [skill.strip() for skill in appointment.required_skills.split(",")]

    # Get scheduled date
    scheduled_date = appointment.scheduled_start.isoformat() if appointment.scheduled_start else None

    # Query SAP HR
    result = await sap_client.get_available_technicians(
        scheduled_date=scheduled_date,
        skills_required=skills if skills else None,
        location=appointment.location
    )

    if not result.get("success"):
        log_action(
            action_type="SAP_HR_QUERY_FAILED",
            user=current_user.username,
            details=f"Failed to get technicians for appointment {appointment.appointment_number}: {result.get('error')}",
            status="error"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query SAP HR: {result.get('error')}"
        )

    log_action(
        action_type="SAP_HR_QUERY_SUCCESS",
        user=current_user.username,
        details=f"Retrieved {result.get('total_count', 0)} available technicians from SAP HR for appointment {appointment.appointment_number}",
        status="success"
    )

    return {
        "appointment_id": appointment_id,
        "appointment_number": appointment.appointment_number,
        "technicians": result.get("technicians", []),
        "total_count": result.get("total_count", 0),
        "filters_applied": {
            "scheduled_date": scheduled_date,
            "skills_required": skills,
            "location": appointment.location
        }
    }


@router.get("/appointments/{appointment_id}/check-parts")
async def check_parts_for_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check parts availability in SAP Inventory for an appointment"""

    # Get appointment details
    appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Service appointment not found")

    # Parse required parts if provided
    if not appointment.required_parts:
        return {
            "appointment_id": appointment_id,
            "appointment_number": appointment.appointment_number,
            "all_available": True,
            "parts_status": [],
            "message": "No parts required for this appointment"
        }

    # Parse parts (assuming format: "PART-001:2, PART-002:1")
    parts = []
    for part_str in appointment.required_parts.split(","):
        part_str = part_str.strip()
        if ":" in part_str:
            part_number, quantity = part_str.split(":")
            parts.append({
                "part_number": part_number.strip(),
                "quantity": int(quantity.strip())
            })
        else:
            parts.append({
                "part_number": part_str,
                "quantity": 1
            })

    # Query SAP Inventory
    sap_client = get_sap_client()
    result = await sap_client.check_parts_availability(parts)

    if not result.get("success"):
        log_action(
            action_type="SAP_INVENTORY_CHECK_FAILED",
            user=current_user.username,
            details=f"Failed to check parts for appointment {appointment.appointment_number}: {result.get('error')}",
            status="error"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query SAP Inventory: {result.get('error')}"
        )

    log_action(
        action_type="SAP_INVENTORY_CHECK_SUCCESS",
        user=current_user.username,
        details=f"Parts availability checked for appointment {appointment.appointment_number}: {'All available' if result.get('all_available') else 'Some unavailable'}",
        status="success" if result.get("all_available") else "warning"
    )

    return {
        "appointment_id": appointment_id,
        "appointment_number": appointment.appointment_number,
        "all_available": result.get("all_available", False),
        "parts_status": result.get("parts_status", []),
        "checked_at": result.get("checked_at")
    }


@router.get("/appointment-requests/{request_id}/available-technicians")
async def get_available_technicians_for_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available technicians from SAP HR for an appointment request (before appointment is created)"""

    # Get appointment request details
    request = db.query(AppointmentRequest).filter(AppointmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Appointment request not found")

    # Extract data from requested payload
    payload = request.requested_payload

    # Query SAP HR for available technicians
    sap_client = get_sap_client()

    # Parse required skills if provided
    skills = []
    if payload.get("required_skills"):
        skills = [skill.strip() for skill in payload["required_skills"].split(",")]

    # Get scheduled date
    scheduled_date = payload.get("scheduled_start")

    # Query SAP HR
    result = await sap_client.get_available_technicians(
        scheduled_date=scheduled_date,
        skills_required=skills if skills else None,
        location=payload.get("location")
    )

    if not result.get("success"):
        log_action(
            action_type="SAP_HR_QUERY_FAILED",
            user=current_user.username,
            details=f"Failed to get technicians for appointment request {request_id}: {result.get('error')}",
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"SAP HR query failed: {result.get('error')}")

    log_action(
        action_type="SAP_HR_TECHNICIANS_FETCHED",
        user=current_user.username,
        details=f"Fetched {len(result.get('technicians', []))} technicians for appointment request {request_id}",
        status="success"
    )

    return {
        "success": True,
        "technicians": result.get("technicians", []),
        "queried_at": result.get("queried_at")
    }


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
async def create_service_appointment(
    data: ServiceAppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new service appointment request and send to ServiceNow for approval"""
    import uuid

    # Generate correlation ID
    correlation_id = str(uuid.uuid4())

    # Store the requested appointment data as JSON
    requested_payload = {
        "account_id": data.account_id,
        "case_id": data.case_id,
        "subject": data.subject,
        "description": data.description,
        "appointment_type": data.appointment_type,
        "scheduled_start": data.scheduled_start,
        "scheduled_end": data.scheduled_end,
        "priority": data.priority,
        "location": data.location,
        "required_skills": data.required_skills,
        "required_parts": data.required_parts
    }

    # Create appointment request (not the actual appointment yet)
    appointment_request = AppointmentRequest(
        subject=data.subject,
        requested_payload=requested_payload,
        status=AppointmentRequestStatus.PENDING.value,
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
        created_at=datetime.now()
    )

    db.add(appointment_request)
    db.commit()
    db.refresh(appointment_request)

    # Create ServiceNow ticket for approval
    servicenow_client = get_servicenow_client()

    # Priority mapping: Normal=3, High=2, Urgent=1
    priority_map = {"Normal": "3", "High": "2", "Urgent": "1"}
    snow_priority = priority_map.get(data.priority, "3")

    ticket_description = f"""
Service Appointment Request from Salesforce

Request ID: {appointment_request.id}
Type: {data.appointment_type}
Location: {data.location or 'Not specified'}
Required Skills: {data.required_skills or 'Not specified'}
Required Parts: {data.required_parts or 'Not specified'}

Scheduled Start: {data.scheduled_start or 'Not specified'}
Scheduled End: {data.scheduled_end or 'Not specified'}

Description:
{data.description or 'No description provided'}

Please approve this request to create the service appointment.
    """

    ticket_result = await servicenow_client.create_ticket(
        short_description=f"Service Appointment Request: {data.subject}",
        description=ticket_description.strip(),
        category="request",
        priority=snow_priority,
        custom_fields={
            "u_request_type": "Service Appointment",  # Keep for backwards compatibility
            "correlation_id": correlation_id,
            "source_system": "Salesforce",
            "source_request_id": str(appointment_request.id),
            "source_request_type": "Service Appointment"
        }
    )

    # Update request with ServiceNow ticket info
    if ticket_result.get("success"):
        appointment_request.servicenow_ticket_id = ticket_result.get("ticket_number")
        appointment_request.servicenow_status = "submitted"
        appointment_request.integration_status = "SENT_TO_SERVICENOW"
    else:
        appointment_request.servicenow_status = "failed"
        appointment_request.integration_status = "FAILED"
        appointment_request.error_message = ticket_result.get("error", "Unknown error")

    db.commit()
    db.refresh(appointment_request)

    log_action(
        action_type="CREATE_APPOINTMENT_REQUEST",
        user=current_user.username,
        details=f"Appointment request #{appointment_request.id} created, ServiceNow ticket: {ticket_result.get('ticket_number', 'N/A')}",
        status="success"
    )

    return {
        "request": appointment_request,
        "servicenow_ticket": ticket_result.get("ticket_number") if ticket_result.get("success") else None,
        "message": "Service appointment request created and sent to ServiceNow for approval"
    }


@router.get("/scheduling-requests")
async def list_scheduling_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all appointment requests (for Scenario 2 tab)"""
    query = db.query(AppointmentRequest)

    if status_filter:
        query = query.filter(AppointmentRequest.status == status_filter)

    requests = query.order_by(AppointmentRequest.created_at.desc()).offset(skip).limit(limit).all()
    return requests


@router.post("/scheduling-requests/{request_id}/approve")
async def approve_scheduling_request(
    request_id: int,
    technician_id: int = Query(...),
    technician_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Agent approves appointment request, creates appointment, and sends to SAP"""
    import uuid

    # Get appointment request
    appointment_request = db.query(AppointmentRequest).filter(AppointmentRequest.id == request_id).first()
    if not appointment_request:
        raise HTTPException(status_code=404, detail="Appointment request not found")

    if appointment_request.status != AppointmentRequestStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Request is not pending (current status: {appointment_request.status})")

    # Extract requested data from payload
    payload = appointment_request.requested_payload
    required_parts = payload.get("required_parts")

    # Check parts availability in SAP Inventory before creating maintenance order
    parts_available = True
    parts_check_result = None
    if required_parts:
        # Parse required parts
        parts = []
        for part_str in required_parts.split(","):
            part_str = part_str.strip()
            if ":" in part_str:
                part_number, quantity = part_str.split(":")
                parts.append({
                    "part_number": part_number.strip(),
                    "quantity": int(quantity.strip())
                })
            else:
                parts.append({
                    "part_number": part_str,
                    "quantity": 1
                })

        # Check parts availability in SAP Inventory
        sap_client = get_sap_client()
        parts_check_result = await sap_client.check_parts_availability(parts)

        if parts_check_result.get("success"):
            parts_available = parts_check_result.get("all_available", False)
            log_action(
                action_type="SAP_INVENTORY_CHECK",
                user=current_user.username,
                details=f"Parts check for appointment request {request_id}: {'Available' if parts_available else 'Some parts unavailable'}",
                status="success" if parts_available else "warning"
            )
        else:
            log_action(
                action_type="SAP_INVENTORY_CHECK_FAILED",
                user=current_user.username,
                details=f"Failed to check parts for appointment request {request_id}: {parts_check_result.get('error')}",
                status="error"
            )

    # NOW create the actual ServiceAppointment (only after approval!)
    appointment_number = f"APT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    appointment = ServiceAppointment(
        appointment_number=appointment_number,
        account_id=payload.get("account_id"),
        case_id=payload.get("case_id"),
        subject=payload.get("subject"),
        description=payload.get("description"),
        appointment_type=payload.get("appointment_type"),
        scheduled_start=datetime.fromisoformat(payload["scheduled_start"]) if payload.get("scheduled_start") else None,
        scheduled_end=datetime.fromisoformat(payload["scheduled_end"]) if payload.get("scheduled_end") else None,
        priority=payload.get("priority"),
        location=payload.get("location"),
        required_skills=payload.get("required_skills"),
        required_parts=payload.get("required_parts"),
        assigned_technician_id=technician_id,
        technician_name=technician_name,
        status="Scheduled",
        owner_id=appointment_request.requested_by_id,
        created_at=datetime.now()
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Send to SAP - Create Maintenance Order
    sap_client = get_sap_client()
    sap_order_data = {
        "order_type": "PM01",  # Maintenance order
        "description": payload.get("subject", "Service Appointment"),
        "priority": "3" if payload.get("priority") == "Normal" else "2",
        "scheduled_start": payload.get("scheduled_start"),
        "scheduled_end": payload.get("scheduled_end"),
        "technician": str(technician_id),
        "work_center": "WC01",
        "plant": "1000",
        "notes": f"Service appointment from Salesforce. Request ID: {request_id}. ServiceNow: {appointment_request.servicenow_ticket_id}. Parts available: {parts_available}"
    }

    sap_result = await sap_client.create_maintenance_order(sap_order_data)

    # Update appointment request with results
    appointment_request.status = AppointmentRequestStatus.COMPLETED.value if sap_result.get("success") else AppointmentRequestStatus.APPROVED.value
    appointment_request.approved_by_id = current_user.id
    appointment_request.created_appointment_id = appointment.id
    appointment_request.integration_status = "SENT_TO_SAP" if sap_result.get("success") else "SAP_ERROR"
    appointment_request.sap_hr_response = {"technician_id": technician_id, "technician_name": technician_name}
    appointment_request.sap_inventory_response = parts_check_result
    if not sap_result.get("success"):
        appointment_request.error_message = f"SAP integration failed: {sap_result.get('error')}"
    appointment_request.updated_at = datetime.now()

    # Update appointment status based on SAP result
    appointment.status = "Scheduled - SAP Order Created" if sap_result.get("success") else "Scheduled - SAP Error"
    appointment.updated_at = datetime.now()

    db.commit()
    db.refresh(appointment_request)
    db.refresh(appointment)

    log_action(
        action_type="APPROVE_APPOINTMENT_REQUEST",
        user=current_user.username,
        details=f"Appointment request #{request_id} approved, appointment {appointment_number} created, technician {technician_name} assigned, SAP Order: {sap_result.get('order_number', 'N/A')}",
        status="success" if sap_result.get("success") else "warning"
    )

    return {
        "message": "Appointment request approved and sent to SAP successfully" if sap_result.get("success") else "Approved but SAP integration failed",
        "request": appointment_request,
        "appointment": appointment,
        "sap_order_number": sap_result.get("order_number"),
        "sap_order_id": sap_result.get("order_id"),
        "parts_available": parts_available,
        "parts_check": parts_check_result
    }


# ============================================
# SCENARIO 3: Work Orders
# ============================================

@router.get("/workorders")
@router.get("/work-orders")  # Alias with hyphen for frontend
async def list_work_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all work orders"""
    work_orders = db.query(WorkOrder).offset(skip).limit(limit).all()
    return work_orders


@router.post("/workorders", status_code=status.HTTP_201_CREATED)
@router.post("/work-orders", status_code=status.HTTP_201_CREATED)  # Alias with hyphen for frontend
async def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new work order request and send to ServiceNow for approval"""
    import uuid

    # Generate correlation ID
    correlation_id = str(uuid.uuid4())

    # Store the requested work order data as JSON
    requested_payload = {
        "account_id": data.account_id,
        "case_id": data.case_id,
        "subject": data.subject,
        "description": data.description,
        "priority": data.priority,
        "service_type": data.service_type,
        "product": data.product
    }

    # Create work order request (not the actual work order yet)
    work_order_request = WorkOrderRequest(
        subject=data.subject,
        requested_payload=requested_payload,
        status=WorkOrderRequestStatus.PENDING.value,
        correlation_id=correlation_id,
        requested_by_id=current_user.id,
        created_at=datetime.now()
    )

    db.add(work_order_request)
    db.commit()
    db.refresh(work_order_request)

    # Create ServiceNow ticket for approval
    servicenow_client = get_servicenow_client()

    # Priority mapping
    priority_map = {"Low": "4", "Medium": "3", "High": "2", "Critical": "1"}
    snow_priority = priority_map.get(data.priority, "3")

    ticket_description = f"""
Work Order Request from Salesforce

Request ID: {work_order_request.id}
Service Type: {data.service_type}
Product: {data.product or 'Not specified'}
Priority: {data.priority}

Description:
{data.description or 'No description provided'}

Note: This work order requires entitlement verification before sending to SAP.
Please approve this request to create the work order.
    """

    ticket_result = await servicenow_client.create_ticket(
        short_description=f"Work Order Request: {data.subject}",
        description=ticket_description.strip(),
        category="request",
        priority=snow_priority,
        custom_fields={
            "u_request_type": "Work Order",  # Keep for backwards compatibility
            "u_service_type": data.service_type,  # Keep for backwards compatibility
            "correlation_id": correlation_id,
            "source_system": "Salesforce",
            "source_request_id": str(work_order_request.id),
            "source_request_type": "Work Order"
        }
    )

    # Update request with ServiceNow ticket info
    if ticket_result.get("success"):
        work_order_request.servicenow_ticket_id = ticket_result.get("ticket_number")
        work_order_request.servicenow_status = "submitted"
        work_order_request.integration_status = "SENT_TO_SERVICENOW"
    else:
        work_order_request.servicenow_status = "failed"
        work_order_request.integration_status = "FAILED"
        work_order_request.error_message = ticket_result.get("error", "Unknown error")

    db.commit()
    db.refresh(work_order_request)

    log_action(
        action_type="CREATE_WORK_ORDER_REQUEST",
        user=current_user.username,
        details=f"Work order request #{work_order_request.id} created, ServiceNow ticket: {ticket_result.get('ticket_number', 'N/A')}",
        status="success"
    )

    return {
        "request": work_order_request,
        "servicenow_ticket": ticket_result.get("ticket_number") if ticket_result.get("success") else None,
        "message": "Work order request created and sent to ServiceNow for approval"
    }


@router.get("/workorder-requests")
async def list_work_order_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all work order requests (for Scenario 3 tab)"""
    query = db.query(WorkOrderRequest)

    if status_filter:
        query = query.filter(WorkOrderRequest.status == status_filter)

    requests = query.order_by(WorkOrderRequest.created_at.desc()).offset(skip).limit(limit).all()
    return requests


@router.post("/workorder-requests/{request_id}/approve")
@router.post("/work-order-requests/{request_id}/approve")  # Alias
async def approve_work_order_request(
    request_id: int,
    entitlement_verified: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Agent approves work order request, creates work order, and sends to SAP"""
    import uuid

    # Get work order request
    work_order_request = db.query(WorkOrderRequest).filter(WorkOrderRequest.id == request_id).first()
    if not work_order_request:
        raise HTTPException(status_code=404, detail="Work order request not found")

    if work_order_request.status != WorkOrderRequestStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Request is not pending (current status: {work_order_request.status})")

    # Extract requested data from payload
    payload = work_order_request.requested_payload

    if not entitlement_verified:
        # Reject the request
        work_order_request.status = WorkOrderRequestStatus.REJECTED.value
        work_order_request.approved_by_id = current_user.id
        work_order_request.integration_status = "REJECTED_BY_AGENT"
        work_order_request.error_message = "Agent rejected: Entitlement verification failed - service type not covered or expired"
        work_order_request.updated_at = datetime.now()

        db.commit()
        db.refresh(work_order_request)

        log_action(
            action_type="REJECT_WORK_ORDER_REQUEST",
            user=current_user.username,
            details=f"Work order request #{request_id} rejected - Entitlement Failed",
            status="warning"
        )

        return {
            "message": "Work order request rejected by agent",
            "request": work_order_request
        }

    # Agent approved - NOW create the actual WorkOrder
    work_order_number = f"WO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    work_order = WorkOrder(
        work_order_number=work_order_number,
        account_id=payload.get("account_id"),
        case_id=payload.get("case_id"),
        subject=payload.get("subject"),
        description=payload.get("description"),
        priority=payload.get("priority"),
        service_type=payload.get("service_type"),
        product=payload.get("product"),
        status="PENDING",
        entitlement_verified=True,
        entitlement_type=payload.get("service_type"),
        correlation_id=work_order_request.correlation_id,
        requested_by_id=work_order_request.requested_by_id,
        owner_id=work_order_request.requested_by_id,
        created_at=datetime.now()
    )

    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    # Send to SAP - Create Maintenance Order or Sales Order based on service type
    sap_client = get_sap_client()
    sap_result = None

    if payload.get("service_type") in ["Warranty", "Maintenance", "Repair"]:
        # Create PM Maintenance Order
        sap_order_data = {
            "order_type": "PM01",
            "description": payload.get("subject"),
            "priority": "2" if payload.get("priority") == "High" else "3",
            "notes": f"Work Order from Salesforce. Request ID: {request_id}. ServiceNow: {work_order_request.servicenow_ticket_id}. Service Type: {payload.get('service_type')}"
        }
        sap_result = await sap_client.create_maintenance_order(sap_order_data)
    else:
        # Create Sales Order for installation/other services
        sap_order_data = {
            "customer_id": f"CUST-{payload.get('account_id')}" if payload.get("account_id") else "CUST-DEFAULT",
            "order_type": "ZOR",
            "sales_org": "1000",
            "distribution_channel": "10",
            "division": "00",
            "items": [{
                "material": f"SERVICE-{payload.get('service_type', 'GENERIC').upper()}",
                "quantity": 1,
                "unit": "EA",
                "price": 0.00
            }],
            "reference": f"Salesforce Work Order Request {request_id}"
        }
        sap_result = await sap_client.create_sales_order(sap_order_data)

    # Update work order request with results
    work_order_request.status = WorkOrderRequestStatus.COMPLETED.value if sap_result.get("success") else WorkOrderRequestStatus.APPROVED.value
    work_order_request.approved_by_id = current_user.id
    work_order_request.created_work_order_id = work_order.id
    work_order_request.integration_status = "SENT_TO_SAP" if sap_result.get("success") else "SAP_ERROR"
    work_order_request.sap_entitlement_response = {"entitlement_verified": True, "service_type": payload.get("service_type")}
    if not sap_result.get("success"):
        work_order_request.error_message = f"SAP integration failed: {sap_result.get('error')}"
    work_order_request.updated_at = datetime.now()

    # Update work order based on SAP result
    if sap_result.get("success"):
        work_order.status = "APPROVED"
        work_order.sap_order_id = sap_result.get("order_id")
        work_order.sap_notification_id = sap_result.get("order_number")
        work_order.integration_status = "SENT_TO_SAP"
    else:
        work_order.status = "SAP_ERROR"
        work_order.integration_status = "SAP_ERROR"
        work_order.error_message = f"SAP integration failed: {sap_result.get('error')}"

    work_order.mulesoft_transaction_id = work_order_request.servicenow_ticket_id
    work_order.updated_at = datetime.now()

    db.commit()
    db.refresh(work_order_request)
    db.refresh(work_order)

    log_action(
        action_type="APPROVE_WORK_ORDER_REQUEST",
        user=current_user.username,
        details=f"Work order request #{request_id} approved, work order {work_order_number} created, SAP Order: {sap_result.get('order_number', 'N/A') if sap_result else 'N/A'}",
        status="success" if sap_result and sap_result.get("success") else "warning"
    )

    return {
        "message": "Work order request approved and sent to SAP successfully" if sap_result and sap_result.get("success") else "Approved but SAP integration failed",
        "request": work_order_request,
        "work_order": work_order,
        "sap_order_number": sap_result.get("order_number") if sap_result else None,
        "sap_order_id": sap_result.get("order_id") if sap_result else None
    }


@router.post("/workorder-requests/{request_id}/reject")
@router.post("/work-order-requests/{request_id}/reject")  # Alias
async def reject_work_order_request(
    request_id: int,
    reason: str = Query(..., description="Reason for rejection"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Agent rejects work order request"""

    work_order_request = db.query(WorkOrderRequest).filter(WorkOrderRequest.id == request_id).first()
    if not work_order_request:
        raise HTTPException(status_code=404, detail="Work order request not found")

    if work_order_request.status != WorkOrderRequestStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Request is not pending (current status: {work_order_request.status})")

    work_order_request.status = WorkOrderRequestStatus.REJECTED.value
    work_order_request.approved_by_id = current_user.id
    work_order_request.integration_status = "REJECTED_BY_AGENT"
    work_order_request.error_message = f"Agent rejected: {reason}"
    work_order_request.updated_at = datetime.now()

    db.commit()
    db.refresh(work_order_request)

    log_action(
        action_type="REJECT_WORK_ORDER_REQUEST",
        user=current_user.username,
        details=f"Agent rejected work order request #{request_id} - Reason: {reason}",
        status="warning"
    )

    return {
        "message": "Work order request rejected by agent",
        "request": work_order_request
    }


@router.post("/scheduling-requests/{request_id}/reject")
async def reject_scheduling_request(
    request_id: int,
    reason: str = Query(..., description="Reason for rejection"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Agent rejects scheduling request"""

    scheduling_request = db.query(SchedulingRequest).filter(SchedulingRequest.id == request_id).first()
    if not scheduling_request:
        raise HTTPException(status_code=404, detail="Scheduling request not found")

    scheduling_request.status = "AGENT_REJECTED"
    scheduling_request.integration_status = "REJECTED_BY_AGENT"
    scheduling_request.error_message = f"Agent rejected: {reason}"
    scheduling_request.updated_at = datetime.now()

    # Update appointment status
    if scheduling_request.appointment_id:
        appointment = db.query(ServiceAppointment).filter(ServiceAppointment.id == scheduling_request.appointment_id).first()
        if appointment:
            appointment.status = "Rejected"
            appointment.updated_at = datetime.now()

    db.commit()
    db.refresh(scheduling_request)

    log_action(
        action_type="REJECT_SCHEDULING",
        user=current_user.username,
        details=f"Agent rejected scheduling request {request_id} - Reason: {reason}",
        status="warning"
    )

    return {
        "message": "Scheduling request rejected by agent",
        "scheduling_request": scheduling_request
    }
