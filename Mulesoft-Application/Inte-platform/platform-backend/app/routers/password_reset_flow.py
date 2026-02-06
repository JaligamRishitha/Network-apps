"""
Password Reset Flow Router - Orchestrates password reset ticket flow.

CORRECT FLOW:
1. ServiceNow creates password reset ticket
2. Ticket is sent to MuleSoft (this service)
3. MuleSoft forwards ticket to SAP
4. SAP displays ticket in Tickets tab
5. SAP admin resets password and updates ticket status
6. SAP sends status back to MuleSoft (via callback)
7. MuleSoft forwards status to ServiceNow
8. ServiceNow updates ticket and audits

MuleSoft is ONLY an integration layer - NO password changes happen here.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import httpx
import uuid
import os

from app.database import get_db
from app.models import IntegrationLog, PasswordResetTicket
import json

router = APIRouter(prefix="/password-reset", tags=["Password Reset Flow"])

# Backend URLs
SAP_URL = os.getenv("SAP_URL", "http://sap-backend:4798")
SERVICENOW_URL = os.getenv("SERVICENOW_URL", "http://servicenow-backend:4780")


class TicketStatus(str, Enum):
    """Ticket status"""
    PENDING = "pending"
    SENT_TO_SAP = "sent_to_sap"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class PasswordResetTicketCreate(BaseModel):
    """Request from ServiceNow to create password reset ticket"""
    servicenow_ticket_id: str = Field(..., description="ServiceNow ticket number")
    username: str = Field(..., description="SAP username to reset password for")
    user_email: Optional[str] = Field(None, description="User's email")
    requester_name: str = Field(..., description="Name of person who raised the ticket")
    requester_email: Optional[str] = Field(None, description="Requester's email")
    reason: Optional[str] = Field(None, description="Reason for password reset")
    priority: str = Field(default="medium", description="Ticket priority")


class PasswordResetTicketResponse(BaseModel):
    """Response after forwarding ticket to SAP"""
    correlation_id: str
    servicenow_ticket_id: str
    sap_ticket_id: Optional[str] = None
    username: str
    status: TicketStatus
    message: str
    timestamp: str


class SAPCallbackPayload(BaseModel):
    """Callback payload from SAP when ticket status changes"""
    sap_ticket_id: str
    servicenow_ticket_id: str
    username: str
    status: str  # Open, In_Progress, Completed, Failed
    comment: Optional[str] = None
    correlation_id: Optional[str] = None
    temp_password: Optional[str] = None
    timestamp: str


class TicketStatusResponse(BaseModel):
    """Status of a password reset ticket"""
    correlation_id: str
    servicenow_ticket_id: str
    sap_ticket_id: Optional[str]
    username: str
    status: str
    sap_status: Optional[str]
    servicenow_updated: bool
    created_at: str
    updated_at: str
    history: List[Dict[str, Any]]


# Database persistence (tickets stored in PostgreSQL)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def forward_ticket_to_sap(ticket_data: Dict[str, Any]) -> Dict[str, Any]:
    """Forward password reset ticket to SAP"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SAP_URL}/api/integration/mulesoft/password-reset-ticket",
                json={
                    "ticket_id": ticket_data["servicenow_ticket_id"],
                    "username": ticket_data["username"],
                    "user_email": ticket_data.get("user_email"),
                    "requester_name": ticket_data["requester_name"],
                    "requester_email": ticket_data.get("requester_email"),
                    "reason": ticket_data.get("reason"),
                    "priority": ticket_data.get("priority", "medium"),
                    "source_system": "servicenow",
                    "callback_url": f"http://mulesoft-backend:4797/api/password-reset/sap-callback",
                    "correlation_id": ticket_data["correlation_id"]
                }
            )

            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"SAP returned {response.status_code}: {response.text}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def update_servicenow_ticket(
    servicenow_ticket_id: str,
    status: str,
    comment: str,
    temp_password: Optional[str] = None
) -> bool:
    """Update ticket status in ServiceNow"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {
                "ticket_number": servicenow_ticket_id,
                "status": "Closed" if status == "Completed" else status,
                "resolution_notes": comment,
                "source": "sap_integration"
            }

            if temp_password:
                payload["work_notes"] = f"Temporary password generated. Please communicate securely to user."

            response = await client.patch(
                f"{SERVICENOW_URL}/api/tickets/{servicenow_ticket_id}/status",
                json=payload
            )

            return response.status_code in [200, 201]

    except Exception as e:
        print(f"Failed to update ServiceNow: {e}")
        return False


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/from-servicenow", response_model=PasswordResetTicketResponse)
async def receive_ticket_from_servicenow(
    request: PasswordResetTicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive password reset ticket from ServiceNow.

    Flow:
    1. ServiceNow sends ticket here
    2. MuleSoft validates and forwards to SAP
    3. Returns correlation ID for tracking
    """
    correlation_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    # Create tracking record in database
    db_ticket = PasswordResetTicket(
        correlation_id=correlation_id,
        servicenow_ticket_id=request.servicenow_ticket_id,
        sap_ticket_id=None,
        username=request.username,
        user_email=request.user_email,
        requester_name=request.requester_name,
        requester_email=request.requester_email,
        reason=request.reason,
        priority=request.priority,
        status=TicketStatus.PENDING.value,
        sap_status=None,
        servicenow_updated=False,
        history=json.dumps([{
            "action": "received_from_servicenow",
            "timestamp": timestamp.isoformat() + "Z",
            "details": f"Ticket {request.servicenow_ticket_id} received from ServiceNow"
        }])
    )
    db.add(db_ticket)
    db.flush()

    # Log the request
    log = IntegrationLog(
        integration_id=1,
        level="INFO",
        message=f"Password reset ticket received from ServiceNow: {request.servicenow_ticket_id} for user {request.username}"
    )
    db.add(log)
    db.commit()

    # Forward to SAP
    ticket_data = {
        "correlation_id": correlation_id,
        "servicenow_ticket_id": request.servicenow_ticket_id,
        "username": request.username,
        "user_email": request.user_email,
        "requester_name": request.requester_name,
        "requester_email": request.requester_email,
        "reason": request.reason,
        "priority": request.priority
    }
    sap_result = await forward_ticket_to_sap(ticket_data)

    if sap_result["success"]:
        sap_data = sap_result["data"]
        db_ticket.sap_ticket_id = sap_data.get("sap_ticket_id")
        db_ticket.status = TicketStatus.SENT_TO_SAP.value

        history = json.loads(db_ticket.history)
        history.append({
            "action": "forwarded_to_sap",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": f"Ticket forwarded to SAP. SAP Ticket ID: {db_ticket.sap_ticket_id}"
        })
        db_ticket.history = json.dumps(history)
        db.commit()

        return PasswordResetTicketResponse(
            correlation_id=correlation_id,
            servicenow_ticket_id=request.servicenow_ticket_id,
            sap_ticket_id=db_ticket.sap_ticket_id,
            username=request.username,
            status=TicketStatus.SENT_TO_SAP,
            message="Ticket forwarded to SAP. Awaiting admin action.",
            timestamp=timestamp.isoformat() + "Z"
        )
    else:
        db_ticket.status = TicketStatus.FAILED.value
        history = json.loads(db_ticket.history)
        history.append({
            "action": "sap_forward_failed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": f"Failed to forward to SAP: {sap_result['error']}"
        })
        db_ticket.history = json.dumps(history)
        db.commit()

        raise HTTPException(
            status_code=502,
            detail={
                "correlation_id": correlation_id,
                "error": "Failed to forward ticket to SAP",
                "details": sap_result["error"]
            }
        )


@router.post("/sap-callback")
async def receive_sap_callback(
    payload: SAPCallbackPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receive status update callback from SAP.

    When SAP admin processes the ticket (resets password), SAP calls this endpoint.
    MuleSoft then updates ServiceNow with the new status.
    """
    timestamp = datetime.utcnow()

    # Find the ticket by correlation_id or servicenow_ticket_id
    db_ticket = db.query(PasswordResetTicket).filter(
        (PasswordResetTicket.correlation_id == payload.correlation_id) |
        (PasswordResetTicket.servicenow_ticket_id == payload.servicenow_ticket_id)
    ).first()

    if not db_ticket:
        # Create a new tracking record if not found (SAP-initiated)
        db_ticket = PasswordResetTicket(
            correlation_id=payload.correlation_id or str(uuid.uuid4()),
            servicenow_ticket_id=payload.servicenow_ticket_id,
            sap_ticket_id=payload.sap_ticket_id,
            username=payload.username,
            status=TicketStatus.PENDING.value,
            sap_status=None,
            servicenow_updated=False,
            history=json.dumps([])
        )
        db.add(db_ticket)
        db.flush()

    # Update ticket data
    db_ticket.sap_status = payload.status

    # Map SAP status to our status
    if payload.status == "Completed":
        db_ticket.status = TicketStatus.COMPLETED.value
    elif payload.status == "Failed":
        db_ticket.status = TicketStatus.FAILED.value
    elif payload.status == "In_Progress":
        db_ticket.status = TicketStatus.IN_PROGRESS.value

    history = json.loads(db_ticket.history)
    history.append({
        "action": "sap_callback_received",
        "timestamp": timestamp.isoformat() + "Z",
        "details": f"SAP status update: {payload.status}. Comment: {payload.comment or 'None'}"
    })
    db_ticket.history = json.dumps(history)

    # Log
    log = IntegrationLog(
        integration_id=1,
        level="INFO",
        message=f"SAP callback received for ticket {payload.sap_ticket_id}: status={payload.status}"
    )
    db.add(log)
    db.commit()

    # Update ServiceNow
    comment = payload.comment or f"Password reset {payload.status.lower()} in SAP"
    servicenow_updated = await update_servicenow_ticket(
        payload.servicenow_ticket_id,
        payload.status,
        comment,
        payload.temp_password
    )

    db_ticket.servicenow_updated = servicenow_updated
    history = json.loads(db_ticket.history)
    history.append({
        "action": "servicenow_update",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "details": f"ServiceNow update {'successful' if servicenow_updated else 'failed'}"
    })
    db_ticket.history = json.dumps(history)
    db.commit()

    return {
        "status": "received",
        "correlation_id": db_ticket.correlation_id,
        "servicenow_ticket_id": payload.servicenow_ticket_id,
        "sap_ticket_id": payload.sap_ticket_id,
        "sap_status": payload.status,
        "servicenow_updated": servicenow_updated,
        "timestamp": timestamp.isoformat() + "Z"
    }


@router.get("/status/{correlation_id}", response_model=TicketStatusResponse)
async def get_ticket_status(correlation_id: str, db: Session = Depends(get_db)):
    """Get the status of a password reset ticket by correlation ID."""
    ticket = db.query(PasswordResetTicket).filter(
        PasswordResetTicket.correlation_id == correlation_id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {correlation_id}")

    return TicketStatusResponse(
        correlation_id=ticket.correlation_id,
        servicenow_ticket_id=ticket.servicenow_ticket_id,
        sap_ticket_id=ticket.sap_ticket_id,
        username=ticket.username,
        status=ticket.status,
        sap_status=ticket.sap_status,
        servicenow_updated=ticket.servicenow_updated,
        created_at=ticket.created_at.isoformat() + "Z",
        updated_at=ticket.updated_at.isoformat() + "Z",
        history=json.loads(ticket.history) if ticket.history else []
    )


@router.get("/tickets")
async def list_password_reset_tickets(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all password reset tickets tracked by MuleSoft."""
    query = db.query(PasswordResetTicket)

    if status:
        query = query.filter(PasswordResetTicket.status == status)

    # Sort by created_at descending
    tickets = query.order_by(PasswordResetTicket.created_at.desc()).limit(limit).all()

    return {
        "tickets": [
            {
                "correlation_id": t.correlation_id,
                "servicenow_ticket_id": t.servicenow_ticket_id,
                "sap_ticket_id": t.sap_ticket_id,
                "username": t.username,
                "status": t.status,
                "sap_status": t.sap_status,
                "servicenow_updated": t.servicenow_updated,
                "created_at": t.created_at.isoformat() + "Z",
                "updated_at": t.updated_at.isoformat() + "Z"
            }
            for t in tickets
        ],
        "total": query.count()
    }


@router.get("/health")
async def password_reset_flow_health():
    """Health check for password reset flow service."""
    sap_healthy = False
    servicenow_healthy = False

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{SAP_URL}/health")
            sap_healthy = response.status_code == 200
    except:
        pass

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{SERVICENOW_URL}/health")
            servicenow_healthy = response.status_code == 200
    except:
        pass

    return {
        "status": "healthy" if (sap_healthy and servicenow_healthy) else "degraded",
        "service": "password-reset-flow",
        "flow": "ServiceNow → MuleSoft → SAP → MuleSoft → ServiceNow",
        "dependencies": {
            "sap": "healthy" if sap_healthy else "unhealthy",
            "servicenow": "healthy" if servicenow_healthy else "unhealthy"
        },
        "active_tickets": len(ticket_store),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
