"""
Integration Endpoints API routes.
SAP ERP API - For Camel flows and external system integration
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import xml.etree.ElementTree as ET
import httpx
import uuid
import os

from backend.db.database import get_db
from backend.db.models import PasswordResetTicket as PasswordResetTicketModel
from backend.services.electricity_service import ElectricityService, ElectricityLoadRequest
import json


router = APIRouter(prefix="/integration", tags=["Integration"])

# MuleSoft callback URL
MULESOFT_URL = os.getenv("MULESOFT_URL", "http://mulesoft-backend:4797")


# Request/Response Models

class ChangeRecord(BaseModel):
    entity_type: str
    entity_id: str
    change_type: str  # created, updated, deleted
    changed_at: str
    changed_by: str
    changes: dict


class ChangesResponse(BaseModel):
    entity: str
    since: str
    records: List[ChangeRecord]
    total: int
    has_more: bool


class BulkExportRequest(BaseModel):
    entity_type: str  # orders, customers, materials, invoices
    filters: Optional[dict] = None
    fields: Optional[List[str]] = None
    format: str = "json"


class BulkExportResponse(BaseModel):
    export_id: str
    entity_type: str
    record_count: int
    status: str
    download_url: Optional[str]
    created_at: str


class WebhookPayload(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    timestamp: str
    data: dict


class WebhookResponse(BaseModel):
    received: bool
    webhook_id: str
    processed_at: str
    status: str


class ElectricityLoadRequestPayload(BaseModel):
    """Electricity load enhancement request from MuleSoft"""
    request_id: str = Field(..., alias="RequestID")
    customer_id: str = Field(..., alias="CustomerID")
    current_load: float = Field(..., alias="CurrentLoad")
    requested_load: float = Field(..., alias="RequestedLoad")
    connection_type: str = Field(..., alias="ConnectionType")
    city: str = Field(..., alias="City")
    pin_code: str = Field(..., alias="PinCode")
    
    class Config:
        populate_by_name = True


class ElectricityLoadResponse(BaseModel):
    status: str
    request_id: str
    customer_id: str
    estimated_cost: float
    priority: str
    tickets_created: dict
    workflow_status: str
    next_steps: List[str]


# Demo change tracking - matches actual data
_change_log = [
    {
        "entity_type": "orders",
        "entity_id": "SO-2024-00001",
        "change_type": "created",
        "changed_at": "2026-01-10T10:30:00Z",
        "changed_by": "admin",
        "changes": {"status": "new", "customer_id": "CUST-001", "total_amount": 12500.00},
    },
    {
        "entity_type": "orders",
        "entity_id": "SO-2024-00001",
        "change_type": "updated",
        "changed_at": "2026-01-11T14:00:00Z",
        "changed_by": "admin",
        "changes": {"status": {"from": "new", "to": "processing"}},
    },
    {
        "entity_type": "orders",
        "entity_id": "SO-2024-00002",
        "change_type": "created",
        "changed_at": "2026-01-12T09:00:00Z",
        "changed_by": "admin",
        "changes": {"status": "new", "customer_id": "CUST-002", "total_amount": 45000.00},
    },
    {
        "entity_type": "customers",
        "entity_id": "CUST-003",
        "change_type": "created",
        "changed_at": "2026-01-14T09:00:00Z",
        "changed_by": "admin",
        "changes": {"name": "StartUp Ventures", "credit_limit": 50000.00},
    },
    {
        "entity_type": "materials",
        "entity_id": "MAT-001",
        "change_type": "updated",
        "changed_at": "2026-01-15T10:30:00Z",
        "changed_by": "manager",
        "changes": {"quantity": {"from": 300, "to": 500}},
    },
]

_export_counter = 1
_webhook_counter = 1


@router.get("/changes", response_model=ChangesResponse)
async def get_changed_records(
    entity: str = Query(..., description="Entity type: orders, customers, materials, invoices"),
    since: str = Query(..., description="ISO timestamp to get changes since"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get changed records since a timestamp.
    Used for incremental sync with external systems.
    """
    # Filter changes by entity and timestamp
    filtered = [
        c for c in _change_log
        if c["entity_type"] == entity and c["changed_at"] >= since
    ]
    
    has_more = len(filtered) > limit
    records = filtered[:limit]
    
    return ChangesResponse(
        entity=entity,
        since=since,
        records=[ChangeRecord(**r) for r in records],
        total=len(records),
        has_more=has_more,
    )


@router.post("/bulk-export", response_model=BulkExportResponse)
async def bulk_data_export(request: BulkExportRequest):
    """
    Initiate bulk data export for integration.
    Returns export job ID for async processing.
    """
    global _export_counter
    
    valid_entities = ["orders", "customers", "materials", "invoices", "vendors"]
    if request.entity_type not in valid_entities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Must be one of: {valid_entities}"
        )
    
    export_id = f"EXP-{_export_counter:06d}"
    _export_counter += 1
    
    # In production, this would queue an async job
    return BulkExportResponse(
        export_id=export_id,
        entity_type=request.entity_type,
        record_count=0,  # Would be populated after export completes
        status="processing",
        download_url=None,
        created_at=datetime.now().isoformat(),
    )


@router.post("/webhook", response_model=WebhookResponse)
async def receive_webhook(payload: WebhookPayload):
    """
    Receive webhooks from external systems.
    Used for real-time sync and event processing.
    """
    global _webhook_counter
    
    webhook_id = f"WH-{_webhook_counter:06d}"
    _webhook_counter += 1
    
    # Log the webhook for processing
    # In production, this would queue for async processing
    
    return WebhookResponse(
        received=True,
        webhook_id=webhook_id,
        processed_at=datetime.now().isoformat(),
        status="accepted",
    )


@router.get("/sync-status")
async def get_sync_status(
    system: Optional[str] = None,
):
    """Get synchronization status with external systems."""
    statuses = [
        {
            "system": "crm",
            "last_sync": "2024-01-15T15:30:00Z",
            "status": "healthy",
            "records_synced": 1250,
            "errors": 0,
        },
        {
            "system": "itsm",
            "last_sync": "2024-01-15T15:25:00Z",
            "status": "healthy",
            "records_synced": 450,
            "errors": 2,
        },
    ]
    
    if system:
        statuses = [s for s in statuses if s["system"] == system]
    
    return {"sync_statuses": statuses}


@router.post("/mulesoft/load-request", response_model=ElectricityLoadResponse)
async def receive_electricity_load_request(
    payload: ElectricityLoadRequestPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive electricity load enhancement request from MuleSoft.
    
    This endpoint processes load enhancement requests and:
    - Creates PM ticket for field work order
    - Creates FI ticket for cost approval (if needed)
    - Creates MM ticket for equipment procurement (if needed)
    - Initiates approval workflow
    - Returns estimated cost and timeline
    """
    try:
        electricity_service = ElectricityService(db)
        
        load_request = ElectricityLoadRequest(
            request_id=payload.request_id,
            customer_id=payload.customer_id,
            current_load=payload.current_load,
            requested_load=payload.requested_load,
            connection_type=payload.connection_type,
            city=payload.city,
            pin_code=payload.pin_code,
        )
        
        result = await electricity_service.process_load_request(load_request)
        
        return ElectricityLoadResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process load request: {str(e)}"
        )


@router.post("/mulesoft/load-request/xml", response_model=ElectricityLoadResponse)
async def receive_electricity_load_request_xml(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive electricity load enhancement request from MuleSoft in XML format.
    
    Accepts XML payload like:
    ```xml
    <ElectricityLoadRequest>
        <RequestID>SF-REQ-10021</RequestID>
        <CustomerID>CUST-88991</CustomerID>
        <CurrentLoad>5</CurrentLoad>
        <RequestedLoad>10</RequestedLoad>
        <ConnectionType>RESIDENTIAL</ConnectionType>
        <City>Hyderabad</City>
        <PinCode>500081</PinCode>
    </ElectricityLoadRequest>
    ```
    """
    try:
        # Read XML from request body
        xml_payload = await request.body()
        xml_string = xml_payload.decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(xml_string)
        
        # Extract fields
        request_id = root.find("RequestID").text
        customer_id = root.find("CustomerID").text
        current_load = float(root.find("CurrentLoad").text)
        requested_load = float(root.find("RequestedLoad").text)
        connection_type = root.find("ConnectionType").text
        city = root.find("City").text
        pin_code = root.find("PinCode").text
        
        electricity_service = ElectricityService(db)
        
        load_request = ElectricityLoadRequest(
            request_id=request_id,
            customer_id=customer_id,
            current_load=current_load,
            requested_load=requested_load,
            connection_type=connection_type,
            city=city,
            pin_code=pin_code,
        )
        
        result = await electricity_service.process_load_request(load_request)
        
        return ElectricityLoadResponse(**result)
    
    except ET.ParseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid XML format: {str(e)}"
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required XML field: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process load request: {str(e)}"
        )


# =============================================================================
# PASSWORD RESET TICKET INTEGRATION (ServiceNow → MuleSoft → SAP)
# =============================================================================

class PasswordResetTicketRequest(BaseModel):
    """Password reset ticket from MuleSoft/ServiceNow"""
    ticket_id: str = Field(..., description="ServiceNow ticket ID")
    username: str = Field(..., description="SAP username to reset password for")
    user_email: Optional[str] = Field(None, description="User's email")
    requester_name: str = Field(..., description="Name of person who raised the ticket")
    requester_email: Optional[str] = Field(None, description="Requester's email")
    reason: Optional[str] = Field(None, description="Reason for password reset")
    priority: str = Field(default="medium", description="Ticket priority")
    source_system: str = Field(default="servicenow", description="Source system")
    callback_url: Optional[str] = Field(None, description="MuleSoft callback URL for status updates")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class PasswordResetTicketResponse(BaseModel):
    """Response for password reset ticket creation"""
    sap_ticket_id: str
    servicenow_ticket_id: str
    username: str
    status: str
    message: str
    created_at: str


class PasswordResetStatusUpdate(BaseModel):
    """Status update for password reset ticket"""
    sap_ticket_id: str
    new_status: str  # Open, In_Progress, Completed, Failed
    comment: Optional[str] = None
    changed_by: str
    new_password: Optional[str] = None  # Only set when password is reset


class PasswordResetTicketDetail(BaseModel):
    """Detailed password reset ticket info"""
    sap_ticket_id: str
    servicenow_ticket_id: str
    username: str
    user_email: Optional[str]
    requester_name: str
    reason: Optional[str]
    priority: str
    status: str
    created_at: str
    updated_at: str
    assigned_to: Optional[str]
    comments: List[Dict[str, Any]]


async def notify_mulesoft_status_change(
    ticket_data: Dict[str, Any],
    new_status: str,
    comment: Optional[str] = None,
    new_password: Optional[str] = None
):
    """Send status update callback to MuleSoft"""
    callback_url = ticket_data.get("callback_url")
    if not callback_url:
        callback_url = f"{MULESOFT_URL}/api/password-reset/sap-callback"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {
                "sap_ticket_id": ticket_data["sap_ticket_id"],
                "servicenow_ticket_id": ticket_data["servicenow_ticket_id"],
                "username": ticket_data["username"],
                "status": new_status,
                "comment": comment,
                "correlation_id": ticket_data.get("correlation_id"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            if new_password and new_status == "Completed":
                payload["temp_password"] = new_password

            await client.post(callback_url, json=payload)
    except Exception as e:
        print(f"Failed to notify MuleSoft: {e}")


@router.post("/mulesoft/password-reset-ticket", response_model=PasswordResetTicketResponse)
async def receive_password_reset_ticket(
    request: PasswordResetTicketRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive password reset ticket from MuleSoft (originated from ServiceNow).

    This endpoint:
    1. Creates a password reset ticket in SAP
    2. Ticket appears in SAP Tickets tab for admin to process
    3. When admin resets password and closes ticket, status is sent back to MuleSoft
    """
    # Generate SAP ticket ID
    sap_ticket_id = f"SAP-PWD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    correlation_id = request.correlation_id or str(uuid.uuid4())

    # Store ticket in database
    db_ticket = PasswordResetTicketModel(
        sap_ticket_id=sap_ticket_id,
        servicenow_ticket_id=request.ticket_id,
        username=request.username,
        user_email=request.user_email,
        requester_name=request.requester_name,
        requester_email=request.requester_email,
        reason=request.reason or "Password reset requested",
        priority=request.priority,
        correlation_id=correlation_id,
        callback_url=request.callback_url,
        status="Open",
        assigned_to=None,
        comments=json.dumps([])
    )
    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)

    return PasswordResetTicketResponse(
        sap_ticket_id=sap_ticket_id,
        servicenow_ticket_id=request.ticket_id,
        username=request.username,
        status="Open",
        message="Password reset ticket created in SAP. Awaiting admin action.",
        created_at=db_ticket.created_at.isoformat() + "Z"
    )


@router.get("/password-reset-tickets", response_model=List[PasswordResetTicketDetail])
async def list_password_reset_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all password reset tickets in SAP.
    This endpoint is used by SAP UI to display tickets in the Tickets tab.
    """
    from sqlalchemy import select

    query = select(PasswordResetTicketModel)

    if status:
        query = query.where(PasswordResetTicketModel.status == status)

    # Sort by created_at descending
    query = query.order_by(PasswordResetTicketModel.created_at.desc())

    result = await db.execute(query)
    tickets = result.scalars().all()

    return [
        PasswordResetTicketDetail(
            sap_ticket_id=t.sap_ticket_id,
            servicenow_ticket_id=t.servicenow_ticket_id,
            username=t.username,
            user_email=t.user_email,
            requester_name=t.requester_name,
            reason=t.reason,
            priority=t.priority,
            status=t.status,
            created_at=t.created_at.isoformat() + "Z",
            updated_at=t.updated_at.isoformat() + "Z",
            assigned_to=t.assigned_to,
            comments=json.loads(t.comments) if t.comments else []
        )
        for t in tickets
    ]


@router.get("/password-reset-tickets/{ticket_id}", response_model=PasswordResetTicketDetail)
async def get_password_reset_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific password reset ticket by ID."""
    from sqlalchemy import select

    result = await db.execute(
        select(PasswordResetTicketModel).where(PasswordResetTicketModel.sap_ticket_id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    return PasswordResetTicketDetail(
        sap_ticket_id=ticket.sap_ticket_id,
        servicenow_ticket_id=ticket.servicenow_ticket_id,
        username=ticket.username,
        user_email=ticket.user_email,
        requester_name=ticket.requester_name,
        reason=ticket.reason,
        priority=ticket.priority,
        status=ticket.status,
        created_at=ticket.created_at.isoformat() + "Z",
        updated_at=ticket.updated_at.isoformat() + "Z",
        assigned_to=ticket.assigned_to,
        comments=json.loads(ticket.comments) if ticket.comments else []
    )


@router.patch("/password-reset-tickets/{ticket_id}/status")
async def update_password_reset_ticket_status(
    ticket_id: str,
    update: PasswordResetStatusUpdate,
    background_tasks: BackgroundTasks,
):
    """
    Update password reset ticket status.
    Called by SAP admin after resetting the password.

    When status is changed to 'Completed', notification is sent to MuleSoft
    which then updates ServiceNow.
    """
    if ticket_id not in password_reset_tickets:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    ticket = password_reset_tickets[ticket_id]
    old_status = ticket["status"]

    # Validate status transition
    valid_statuses = ["Open", "In_Progress", "Completed", "Failed"]
    if update.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    # Update ticket
    ticket["status"] = update.new_status
    ticket["updated_at"] = datetime.utcnow().isoformat() + "Z"

    if update.comment:
        ticket["comments"].append({
            "comment": update.comment,
            "by": update.changed_by,
            "at": datetime.utcnow().isoformat() + "Z",
            "status_change": f"{old_status} → {update.new_status}"
        })

    # Notify MuleSoft of status change (background task)
    background_tasks.add_task(
        notify_mulesoft_status_change,
        ticket,
        update.new_status,
        update.comment,
        update.new_password
    )

    return {
        "ticket_id": ticket_id,
        "old_status": old_status,
        "new_status": update.new_status,
        "message": f"Status updated. {'MuleSoft/ServiceNow will be notified.' if update.new_status in ['Completed', 'Failed'] else ''}"
    }


@router.post("/password-reset-tickets/{ticket_id}/reset-password")
async def execute_password_reset(
    ticket_id: str,
    changed_by: str = Query(..., description="Admin username"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute password reset for a ticket.
    This endpoint:
    1. Generates a new temporary password
    2. Updates the user's password in SAP
    3. Marks ticket as Completed
    4. Sends notification to MuleSoft → ServiceNow
    """
    from sqlalchemy import select

    result = await db.execute(
        select(PasswordResetTicketModel).where(PasswordResetTicketModel.sap_ticket_id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    if ticket.status == "Completed":
        raise HTTPException(status_code=400, detail="Password already reset for this ticket")

    # Generate temporary password
    import secrets
    import string
    chars = string.ascii_letters + string.digits + "!@#$%"
    temp_password = ''.join(secrets.choice(chars) for _ in range(12))

    # Update ticket status
    old_status = ticket.status
    ticket.status = "Completed"
    ticket.temp_password = temp_password

    comments = json.loads(ticket.comments) if ticket.comments else []
    comments.append({
        "comment": f"Password reset executed by {changed_by}. Temporary password generated.",
        "by": changed_by,
        "at": datetime.utcnow().isoformat() + "Z",
        "status_change": f"{old_status} → Completed"
    })
    ticket.comments = json.dumps(comments)

    await db.commit()
    await db.refresh(ticket)

    # Notify MuleSoft
    if background_tasks:
        ticket_dict = {
            "sap_ticket_id": ticket.sap_ticket_id,
            "servicenow_ticket_id": ticket.servicenow_ticket_id,
            "username": ticket.username,
            "status": ticket.status,
            "callback_url": ticket.callback_url,
            "correlation_id": ticket.correlation_id
        }
        background_tasks.add_task(
            notify_mulesoft_status_change,
            ticket_dict,
            "Completed",
            f"Password reset completed by {changed_by}",
            temp_password
        )

    return {
        "ticket_id": ticket_id,
        "username": ticket.username,
        "status": "Completed",
        "temp_password": temp_password,
        "message": "Password reset successful. User must change password on first login.",
        "servicenow_notified": True
    }
