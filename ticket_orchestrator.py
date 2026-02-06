#!/usr/bin/env python3
"""
Ticket Orchestration System
Receives tickets from ServiceNow, classifies them, routes to Mistral Agent, tracks execution
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import httpx
import json
import logging
from enum import Enum
from orchestrator_database import (
    create_ticket as db_create_ticket,
    get_ticket as db_get_ticket,
    update_ticket as db_update_ticket,
    list_tickets as db_list_tickets,
    get_ticket_stats as db_get_stats,
    ticket_exists as db_ticket_exists,
    ticket_to_dict
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ticket Orchestrator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class TicketPriority(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low

class TicketCategory(str, Enum):
    PASSWORD_RESET = "password_reset"
    USER_CREATION = "user_creation"
    USER_DEACTIVATION = "user_deactivation"
    INTEGRATION_ERROR = "integration_error"
    DATA_SYNC_ISSUE = "data_sync_issue"
    SYSTEM_ERROR = "system_error"
    MANUAL = "manual"  # Requires human intervention

class TicketStatus(str, Enum):
    RECEIVED = "received"
    CLASSIFIED = "classified"
    ASSIGNED_TO_AGENT = "assigned_to_agent"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"
    REQUIRES_HUMAN = "requires_human"

class ServiceNowTicket(BaseModel):
    """Incoming ticket from ServiceNow"""
    sys_id: str
    number: str
    short_description: str
    description: str
    priority: str
    state: str
    assigned_to: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

class OrchestrationTicket(BaseModel):
    """Internal ticket representation"""
    id: str
    servicenow_id: str
    servicenow_number: str
    title: str
    description: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    assigned_agent: Optional[str] = None
    resolution_log: List[Dict] = []
    metadata: Dict = {}

class AgentAction(BaseModel):
    """Action request to Mistral Agent"""
    ticket_id: str
    action_type: str
    parameters: Dict
    context: Dict

class AgentResponse(BaseModel):
    """Response from Mistral Agent"""
    ticket_id: str
    status: str  # success, failed, needs_info
    actions_taken: List[str]
    result: Dict
    error: Optional[str] = None

# ============================================================================
# DATABASE STORAGE (Replaced in-memory with SQLite)
# ============================================================================
# Database operations are now handled by orchestrator_database.py

# ============================================================================
# TICKET CLASSIFICATION ENGINE
# ============================================================================

def classify_ticket(ticket: ServiceNowTicket) -> TicketCategory:
    """
    AI-based ticket classification
    Determines if ticket can be auto-resolved and which category
    """
    description_lower = (ticket.short_description + " " + ticket.description).lower()

    # Password reset patterns
    if any(keyword in description_lower for keyword in ["password reset", "forgot password", "reset password", "cannot login", "locked out"]):
        return TicketCategory.PASSWORD_RESET

    # Account creation patterns (check BEFORE integration_error to avoid mulesoft keyword match)
    if any(keyword in description_lower for keyword in ["account creation", "new account", "create account", "account approval"]):
        return TicketCategory.USER_CREATION

    # User creation patterns
    if any(keyword in description_lower for keyword in ["create user", "new user", "user account", "onboard", "provision user"]):
        return TicketCategory.USER_CREATION

    # User deactivation patterns
    if any(keyword in description_lower for keyword in ["deactivate user", "remove user", "disable user", "offboard", "user left"]):
        return TicketCategory.USER_DEACTIVATION

    # Integration error patterns (moved after account creation check)
    if any(keyword in description_lower for keyword in ["integration error", "api error", "sync failed", "connection error"]):
        return TicketCategory.INTEGRATION_ERROR

    # Data sync issues
    if any(keyword in description_lower for keyword in ["data not syncing", "records missing", "duplicate data", "salesforce to sap"]):
        return TicketCategory.DATA_SYNC_ISSUE

    # System errors
    if any(keyword in description_lower for keyword in ["500 error", "system down", "application crash", "database error"]):
        return TicketCategory.SYSTEM_ERROR

    # Default to manual
    return TicketCategory.MANUAL

def can_auto_resolve(category: TicketCategory, priority: TicketPriority) -> bool:
    """
    Determine if ticket can be auto-resolved by agent
    """
    # Send ALL tickets to the agent for processing
    # The agent will determine if it can handle the ticket or needs human intervention
    return True

# ============================================================================
# MISTRAL AGENT INTEGRATION
# ============================================================================

MISTRAL_AGENT_URL = "http://localhost:7532"  # Your Mistral agent endpoint

async def send_to_mistral_agent(ticket: OrchestrationTicket) -> AgentResponse:
    """
    Send ticket to Mistral Agent for resolution
    """
    # Prepare action based on ticket category
    action = AgentAction(
        ticket_id=ticket.id,
        action_type=ticket.category.value,
        parameters=extract_parameters(ticket),
        context={
            "servicenow_number": ticket.servicenow_number,
            "priority": ticket.priority.value,
            "description": ticket.description
        }
    )

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{MISTRAL_AGENT_URL}/api/agent/execute",
                json=action.model_dump()
            )
            response.raise_for_status()
            return AgentResponse(**response.json())
    except Exception as e:
        logger.error(f"Failed to contact Mistral agent: {e}")
        return AgentResponse(
            ticket_id=ticket.id,
            status="failed",
            actions_taken=[],
            result={},
            error=str(e)
        )

def extract_parameters(ticket: OrchestrationTicket) -> Dict:
    """
    Extract action parameters from ticket description
    """
    params = {}
    description = ticket.description.lower()

    if ticket.category == TicketCategory.PASSWORD_RESET:
        # Extract username/email
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', ticket.description)
        if email_match:
            params["email"] = email_match.group(0)

        # Extract system
        if "salesforce" in description:
            params["system"] = "salesforce"
        elif "sap" in description:
            params["system"] = "sap"
        else:
            params["system"] = "all"  # Reset in all systems

    elif ticket.category == TicketCategory.USER_CREATION:
        # Extract user details
        params["action"] = "create_user"
        # You'd parse the description for name, email, role, etc.

    elif ticket.category == TicketCategory.INTEGRATION_ERROR:
        # Extract systems involved
        if "salesforce" in description and "sap" in description:
            params["systems"] = ["salesforce", "sap"]
            params["integration_layer"] = "mulesoft"

    return params

# ============================================================================
# SERVICENOW WEBHOOK ENDPOINT
# ============================================================================

@app.post("/api/webhook/servicenow")
async def receive_servicenow_ticket(ticket: ServiceNowTicket, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for ServiceNow to send tickets
    Configure in ServiceNow: Business Rules → Outbound REST Message
    """
    logger.info(f"Received ticket from ServiceNow: {ticket.number}")

    # Classify ticket
    category = classify_ticket(ticket)

    # Map priority
    priority_map = {"1": TicketPriority.P1, "2": TicketPriority.P2, "3": TicketPriority.P3, "4": TicketPriority.P4}
    priority = priority_map.get(ticket.priority, TicketPriority.P3)

    # Create orchestration ticket using ServiceNow ticket number as ID
    orch_ticket = OrchestrationTicket(
        id=ticket.number,  # Use ServiceNow ticket number directly
        servicenow_id=ticket.sys_id,
        servicenow_number=ticket.number,
        title=ticket.short_description,
        description=ticket.description,
        priority=priority,
        category=category,
        status=TicketStatus.CLASSIFIED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={
            "servicenow_state": ticket.state,
            "servicenow_category": ticket.category
        }
    )

    # Store ticket in database
    db_create_ticket(orch_ticket.model_dump())

    # Check if can auto-resolve
    if can_auto_resolve(category, priority):
        # Update status to assigned
        db_update_ticket(orch_ticket.id, {"status": TicketStatus.ASSIGNED_TO_AGENT.value})

        # Send to agent in background
        background_tasks.add_task(process_ticket_with_agent, orch_ticket.id)

        return {
            "status": "accepted",
            "orchestration_ticket_id": orch_ticket.id,
            "category": category.value,
            "auto_resolve": True,
            "message": "Ticket assigned to AI agent for resolution"
        }
    else:
        # Update status to requires human
        db_update_ticket(orch_ticket.id, {"status": TicketStatus.REQUIRES_HUMAN.value})

        return {
            "status": "accepted",
            "orchestration_ticket_id": orch_ticket.id,
            "category": category.value,
            "auto_resolve": False,
            "message": "Ticket requires human intervention"
        }

# ============================================================================
# AGENT PROCESSING
# ============================================================================

async def process_ticket_with_agent(ticket_id: str):
    """
    Process ticket with Mistral Agent
    """
    db_ticket = db_get_ticket(ticket_id)
    if not db_ticket:
        logger.error(f"Ticket {ticket_id} not found")
        return

    logger.info(f"Processing ticket {ticket_id} with Mistral Agent")

    # Update status to in progress
    db_update_ticket(ticket_id, {"status": TicketStatus.IN_PROGRESS.value})

    # Recreate OrchestrationTicket object for agent
    ticket_dict = ticket_to_dict(db_ticket)
    ticket = OrchestrationTicket(**ticket_dict)

    # Send to Mistral Agent
    agent_response = await send_to_mistral_agent(ticket)

    # Update resolution log
    resolution_entry = {
        "timestamp": datetime.now().isoformat(),
        "actions": agent_response.actions_taken,
        "result": agent_response.result
    }

    db_ticket = db_get_ticket(ticket_id)
    resolution_log = db_ticket.resolution_log if db_ticket.resolution_log else []
    resolution_log.append(resolution_entry)

    if agent_response.status == "success":
        db_update_ticket(ticket_id, {
            "status": TicketStatus.RESOLVED.value,
            "resolution_log": resolution_log
        })
        logger.info(f"Ticket {ticket_id} resolved successfully")

        # Update ServiceNow ticket
        ticket_dict = ticket_to_dict(db_get_ticket(ticket_id))
        ticket = OrchestrationTicket(**ticket_dict)
        await update_servicenow_ticket(ticket, "resolved", agent_response)
    else:
        db_update_ticket(ticket_id, {
            "status": TicketStatus.FAILED.value,
            "resolution_log": resolution_log
        })
        logger.error(f"Ticket {ticket_id} failed: {agent_response.error}")

        # Update ServiceNow ticket
        ticket_dict = ticket_to_dict(db_get_ticket(ticket_id))
        ticket = OrchestrationTicket(**ticket_dict)
        await update_servicenow_ticket(ticket, "failed", agent_response)

async def update_servicenow_ticket(ticket: OrchestrationTicket, status: str, agent_response: AgentResponse):
    """
    Update ServiceNow ticket with resolution
    """
    servicenow_url = "http://149.102.158.71:4780"

    # Build work notes based on ticket type
    if ticket.category.value == "password_reset" and status == "resolved":
        # For password reset, include the generated password
        password = agent_response.result.get("password", "N/A")
        email = agent_response.result.get("email", "N/A")
        work_notes = f"""
AI Agent - Password Reset Completed:
Status: {status}
New Password: {password}
Email Notification Sent To: {email}
Actions: {', '.join(agent_response.actions_taken)}
Orchestration Ticket: {ticket.id}
        """
    elif ticket.category.value == "user_creation" and status == "resolved":
        # For account creation, include approval status
        approved = agent_response.result.get("approved", False)
        account_name = agent_response.result.get("account_name", "N/A")
        work_notes = f"""
AI Agent - Account Creation Approved:
Status: {status}
Account: {account_name}
Auto-Approved: {'Yes' if approved else 'No'}
Actions: {', '.join(agent_response.actions_taken)}
Orchestration Ticket: {ticket.id}
        """
    else:
        # Default work notes for other ticket types
        work_notes = f"""
AI Agent Resolution:
Status: {status}
Actions Taken: {', '.join(agent_response.actions_taken)}
Result: {json.dumps(agent_response.result, indent=2)}
Orchestration Ticket: {ticket.id}
        """

    # For account creation approvals, update the tickets table instead of incidents
    if ticket.category.value == "user_creation":
        update_data = {
            "status": "approved" if status == "resolved" else "rejected",
            "resolution_notes": work_notes
        }
        endpoint = f"{servicenow_url}/tickets/{ticket.servicenow_id}"
    else:
        update_data = {
            "work_notes": work_notes,
            "state": "6" if status == "resolved" else "3",  # 6=Resolved, 3=Work in Progress
            "close_notes": work_notes if status == "resolved" else ""
        }
        endpoint = f"{servicenow_url}/api/now/table/incident/{ticket.servicenow_id}"

    try:
        # Update ServiceNow via direct database connection (more reliable than API)
        import subprocess

        if ticket.category.value == "user_creation":
            # Update tickets table for account creation
            cmd = f'''docker exec postgres-servicenow psql -U postgres -d servicenow_db -c "UPDATE tickets SET status = '{update_data['status']}', resolution_notes = E'{update_data['resolution_notes']}', updated_at = NOW() WHERE id = {ticket.servicenow_id};"'''
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Updated ServiceNow ticket {ticket.servicenow_number} via DB (category: {ticket.category.value}, status: {status})")

                # Trigger ServiceNow webhook to MuleSoft
                async with httpx.AsyncClient(timeout=5) as client:
                    webhook_payload = {
                        "ticket_number": ticket.servicenow_number,
                        "status": update_data['status'],
                        "approval_id": 0,
                        "comments": update_data['resolution_notes'],
                        "timestamp": datetime.now().isoformat() + "Z",
                        "source": "orchestrator"
                    }
                    try:
                        webhook_response = await client.post(
                            "http://149.102.158.71:4797/api/webhooks/servicenow/approval-update",
                            json=webhook_payload,
                            headers={"Content-Type": "application/json"}
                        )
                        logger.info(f"📤 Webhook sent to MuleSoft: {webhook_response.status_code}")
                    except Exception as webhook_error:
                        logger.warning(f"⚠️ Webhook to MuleSoft failed: {webhook_error}")
            else:
                logger.error(f"❌ DB update failed: {result.stderr}")
        else:
            # For incidents, use the API approach
            logger.warning(f"⚠️ Incident updates not yet implemented via DB")

    except Exception as e:
        logger.error(f"❌ Failed to update ServiceNow ticket {ticket.servicenow_number}: {e}")

# ============================================================================
# DASHBOARD & MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/tickets")
async def list_tickets(status: Optional[str] = None, category: Optional[str] = None):
    """List all orchestration tickets"""
    db_tickets = db_list_tickets(status=status, category=category)

    return {
        "total": len(db_tickets),
        "tickets": [ticket_to_dict(t) for t in db_tickets]
    }

@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get specific ticket details"""
    db_ticket = db_get_ticket(ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_to_dict(db_ticket)

@app.get("/api/stats")
async def get_statistics():
    """Get orchestration statistics"""
    return db_get_stats()

@app.post("/api/tickets/{ticket_id}/retry")
async def retry_ticket(ticket_id: str, background_tasks: BackgroundTasks):
    """Manually retry a failed ticket"""
    db_ticket = db_get_ticket(ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if db_ticket.status != TicketStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="Only failed tickets can be retried")

    background_tasks.add_task(process_ticket_with_agent, ticket_id)

    return {"status": "retry_scheduled", "ticket_id": ticket_id}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    stats = db_get_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tickets_processed": stats["total_tickets"]
    }

# ============================================================================
# MANUAL INTERVENTION ENDPOINTS
# ============================================================================

@app.post("/api/tickets/{ticket_id}/assign-to-human")
async def assign_to_human(ticket_id: str, assignee: str):
    """Assign ticket to human for manual resolution"""
    db_ticket = db_get_ticket(ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db_update_ticket(ticket_id, {
        "status": TicketStatus.REQUIRES_HUMAN.value,
        "assigned_agent": assignee
    })

    return {"status": "assigned_to_human", "assignee": assignee}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2486)
