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
    WORK_ORDER = "work_order"
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

    # Work order / appointment patterns
    if any(keyword in description_lower for keyword in ["work order", "service appointment", "appointment request", "field service", "maintenance order"]):
        return TicketCategory.WORK_ORDER

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
        import re
        params["action"] = "create_user"
        email_match = re.search(r'Email:\s*([\w\.\-\+]+@[\w\.\-]+\.\w+)', ticket.description)
        if email_match:
            params["email"] = email_match.group(0).split(":")[-1].strip()
        client_id_match = re.search(r'Client User ID:\s*(\d+)', ticket.description)
        if client_id_match:
            params["client_user_id"] = client_id_match.group(1)
        acct_match = re.search(r'Account:\s*(.+?)(?:\s*\(ID:|\n|$)', ticket.description)
        if acct_match:
            params["account_name"] = acct_match.group(1).strip()

    elif ticket.category == TicketCategory.INTEGRATION_ERROR:
        # Extract systems involved
        if "salesforce" in description and "sap" in description:
            params["systems"] = ["salesforce", "sap"]
            params["integration_layer"] = "mulesoft"

    elif ticket.category == TicketCategory.WORK_ORDER:
        # Parse fields matching the Salesforce appointment ticket format:
        #   Type: ..., Location: ..., Required Skills: ..., Required Parts: ...
        #   Scheduled Start: ..., Scheduled End: ..., Request ID: ...
        import re
        raw = ticket.description

        def _extract(field_name: str) -> str:
            match = re.search(rf'{field_name}\s*:\s*(.+)', raw, re.IGNORECASE)
            return match.group(1).strip() if match else ""

        params["subject"] = ticket.title
        params["appointment_type"] = _extract("Type") or "Field Service"
        params["location"] = _extract("Location") or "Not specified"
        params["required_parts"] = _extract("Required Parts") or "Not specified"
        params["scheduled_start"] = _extract("Scheduled Start") or "Not specified"
        params["scheduled_end"] = _extract("Scheduled End") or "Not specified"
        params["request_id"] = _extract("Request ID") or ""
        params["description"] = ticket.description

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

    # Store ticket in database (skip if already exists)
    if db_ticket_exists(orch_ticket.id):
        logger.info(f"Ticket {ticket.number} already exists, skipping")
        return {
            "status": "duplicate",
            "orchestration_ticket_id": orch_ticket.id,
            "message": "Ticket already received"
        }
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

        # For user_creation: activate client user in Salesforce if applicable
        if ticket.category.value == "user_creation":
            # Try agent response first, then fall back to extracting from ticket description
            client_user_id = agent_response.result.get("client_user_id")
            if not client_user_id and "Client User ID:" in ticket.description:
                import re
                id_match = re.search(r'Client User ID:\s*(\d+)', ticket.description)
                if id_match:
                    client_user_id = id_match.group(1)

            if client_user_id:
                try:
                    import requests as sync_requests
                    activate_resp = sync_requests.patch(
                        f"http://207.180.217.117:4799/api/client-users/{client_user_id}/activate",
                        timeout=10
                    )
                    if activate_resp.status_code == 200:
                        logger.info(f"Salesforce client user {client_user_id} activated successfully")
                    else:
                        logger.error(f"Failed to activate client user {client_user_id}: {activate_resp.status_code} - {activate_resp.text}")
                except Exception as e:
                    logger.error(f"Error activating client user {client_user_id}: {e}")
            else:
                logger.warning(f"No client_user_id found for user_creation ticket {ticket_id}")

        # For password reset, update the password in SAP database
        if ticket.category.value == "password_reset":
            new_password = agent_response.result.get("password")
            sap_username = ticket.metadata.get("sap_username") or ticket.description.split("SAP Username:")[1].split("\n")[0].strip() if "SAP Username:" in ticket.description else None
            if new_password and sap_username:
                try:
                    import requests as sync_requests
                    # Login to SAP as admin
                    sap_auth = sync_requests.post(
                        "http://207.180.217.117:4798/api/v1/auth/login",
                        json={"username": "admin", "password": "admin123"},
                        timeout=10
                    )
                    if sap_auth.status_code == 200:
                        sap_token = sap_auth.json().get("access_token")
                        # Update password in SAP
                        sap_resp = sync_requests.patch(
                            f"http://207.180.217.117:4798/api/v1/users/{sap_username}/password",
                            json={"username": sap_username, "new_password": new_password},
                            headers={"Authorization": f"Bearer {sap_token}"},
                            timeout=10
                        )
                        if sap_resp.status_code == 200:
                            logger.info(f"SAP password updated for user {sap_username}")
                        else:
                            logger.error(f"Failed to update SAP password: {sap_resp.status_code} - {sap_resp.text}")
                    else:
                        logger.error(f"Failed to authenticate with SAP for password update")
                except Exception as e:
                    logger.error(f"Error updating SAP password: {e}")

            # Also update Salesforce client_users password if applicable
            import re as _re_pw
            pw_email_match = _re_pw.search(r'[\w\.\-\+]+@[\w\.\-]+\.\w+', ticket.description)
            pw_email = pw_email_match.group(0) if pw_email_match else None
            if new_password and pw_email:
                try:
                    import requests as sync_requests
                    # Validate client user exists
                    validate_resp = sync_requests.post(
                        "http://207.180.217.117:4799/api/client-users/validate",
                        json={"email": pw_email},
                        timeout=10
                    )
                    if validate_resp.status_code == 200 and validate_resp.json().get("exists"):
                        # Update client user password
                        pw_resp = sync_requests.patch(
                            f"http://207.180.217.117:4799/api/client-users/{pw_email}/password",
                            json={"new_password": new_password},
                            timeout=10
                        )
                        if pw_resp.status_code == 200:
                            logger.info(f"Salesforce client user password updated for {pw_email}")
                        else:
                            logger.error(f"Failed to update Salesforce client user password: {pw_resp.status_code}")
                    else:
                        logger.info(f"No Salesforce client user found for {pw_email}, skipping client password update")
                except Exception as e:
                    logger.error(f"Error updating Salesforce client user password: {e}")

        # For work_order: agent validated — now orchestrator creates work order in SAP
        if ticket.category.value == "work_order":
            try:
                import requests as sync_requests
                import re

                # Extract request ID from ticket description
                request_id_match = re.search(r'Request ID:\s*(\d+)', ticket.description)
                sf_request_id = request_id_match.group(1) if request_id_match else None

                # Login to SAP
                sap_auth = sync_requests.post(
                    "http://207.180.217.117:4798/api/v1/auth/login",
                    json={"username": "admin", "password": "admin123"},
                    timeout=10
                )
                if sap_auth.status_code == 200:
                    sap_token = sap_auth.json().get("access_token")
                    # Create work order using the correct work-order-flow endpoint
                    wo_payload = {
                        "title": ticket.title,
                        "description": ticket.description,
                        "customer_name": "Salesforce Customer",
                        "site_location": agent_response.result.get("location", "Not specified"),
                        "requested_date": agent_response.result.get("scheduled_start", datetime.now().strftime("%Y-%m-%d")),
                        "cost_center_id": "CC-DEFAULT",
                        "created_by": "orchestrator",
                        "materials": [],
                        "priority": "medium",
                        "crm_reference_id": sf_request_id or ""
                    }
                    wo_resp = sync_requests.post(
                        "http://207.180.217.117:4798/api/v1/work-order-flow/work-orders",
                        json=wo_payload,
                        headers={"Authorization": f"Bearer {sap_token}"},
                        timeout=10
                    )
                    if wo_resp.status_code in [200, 201]:
                        wo_data = wo_resp.json()
                        work_order_id = wo_data.get("work_order_id") or wo_data.get("id", "WO-UNKNOWN")
                        agent_response.result["work_order_id"] = work_order_id
                        logger.info(f"SAP work order created: {work_order_id} for ticket {ticket_id}")

                        # Update materials check status based on agent validation
                        validation = agent_response.result.get("validation_details", {})
                        parts_validation = validation.get("parts_validation", {})
                        parts_valid = validation.get("valid", True)
                        all_available = parts_valid and parts_validation.get("status") != "unavailable"

                        mat_status = {
                            "all_available": all_available,
                            "shortage_count": 0 if all_available else 1,
                            "checked_by": "ai_agent",
                            "details": parts_validation.get("status", "validated_by_agent")
                        }
                        mat_resp = sync_requests.patch(
                            f"http://207.180.217.117:4798/api/v1/work-order-flow/work-orders/{work_order_id}/materials-status",
                            json=mat_status,
                            headers={"Authorization": f"Bearer {sap_token}"},
                            timeout=10
                        )
                        if mat_resp.status_code in [200, 201]:
                            logger.info(f"SAP work order {work_order_id} materials status updated: {'Available' if all_available else 'Shortage'}")
                        else:
                            logger.error(f"SAP materials status update failed: {mat_resp.status_code}")

                        # If materials are short, create a ticket in SAP Tickets tab
                        if not all_available:
                            short_parts = parts_validation.get("unavailable_parts", [])
                            short_details = parts_validation.get("details", "Materials shortage detected by AI agent")
                            required_parts_str = wo_payload.get("description", "")
                            # Extract required parts from ticket description
                            import re as _re
                            parts_match = _re.search(r'Required Parts:\s*(.+)', ticket.description, _re.IGNORECASE)
                            parts_list = parts_match.group(1).strip() if parts_match else "See work order description"

                            sap_ticket_payload = {
                                "module": "MM",
                                "ticket_type": "Procurement",
                                "priority": ticket.priority.value,
                                "title": f"Materials Shortage - Work Order {work_order_id}",
                                "description": (
                                    f"Materials shortage detected for Work Order: {work_order_id}\n"
                                    f"ServiceNow Ticket: {ticket.servicenow_number}\n"
                                    f"Customer: {wo_payload.get('customer_name', 'N/A')}\n"
                                    f"Site Location: {wo_payload.get('site_location', 'N/A')}\n"
                                    f"Required Parts: {parts_list}\n"
                                    f"Shortage Details: {short_details}\n"
                                    f"Unavailable Parts: {', '.join(short_parts) if short_parts else 'Check with warehouse'}\n\n"
                                    f"Action Required: Procure missing materials for the work order."
                                ),
                                "created_by": "orchestrator"
                            }
                            tkt_resp = sync_requests.post(
                                "http://207.180.217.117:4798/api/v1/tickets",
                                json=sap_ticket_payload,
                                headers={"Authorization": f"Bearer {sap_token}"},
                                timeout=10
                            )
                            if tkt_resp.status_code in [200, 201]:
                                sap_ticket_id = tkt_resp.json().get("ticket_id", "UNKNOWN")
                                logger.info(f"SAP shortage ticket created: {sap_ticket_id} for work order {work_order_id}")
                            else:
                                logger.error(f"SAP shortage ticket creation failed: {tkt_resp.status_code} - {tkt_resp.text}")
                    else:
                        logger.error(f"SAP work order creation failed: {wo_resp.status_code} - {wo_resp.text}")
                        agent_response.result["work_order_id"] = "CREATION_FAILED"
                else:
                    logger.error("Failed to authenticate with SAP for work order creation")
                    agent_response.result["work_order_id"] = "AUTH_FAILED"

                # Update Salesforce appointment request status
                if sf_request_id:
                    try:
                        sf_auth = sync_requests.post(
                            "http://207.180.217.117:4799/api/auth/login",
                            json={"username": "admin", "password": "admin123"},
                            timeout=10
                        )
                        if sf_auth.status_code == 200:
                            sf_token = sf_auth.json().get("access_token")
                            sf_update = {
                                "status": "APPROVED",
                                "sap_work_order_id": agent_response.result.get("work_order_id", ""),
                                "orchestrator_ticket_id": ticket_id,
                                "resolution_notes": f"Auto-approved by AI agent. SAP Work Order: {agent_response.result.get('work_order_id', 'N/A')}"
                            }
                            sf_resp = sync_requests.patch(
                                f"http://207.180.217.117:4799/api/service/appointment-requests/{sf_request_id}/status",
                                json=sf_update,
                                headers={"Authorization": f"Bearer {sf_token}"},
                                timeout=10
                            )
                            if sf_resp.status_code in [200, 201]:
                                logger.info(f"Salesforce appointment request {sf_request_id} updated to APPROVED")
                            else:
                                logger.error(f"Salesforce update failed: {sf_resp.status_code} - {sf_resp.text}")
                        else:
                            logger.error("Failed to authenticate with Salesforce")
                    except Exception as sf_err:
                        logger.error(f"Error updating Salesforce: {sf_err}")

            except Exception as e:
                logger.error(f"Error creating SAP work order: {e}")
                agent_response.result["work_order_id"] = "ERROR"

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
    servicenow_url = "http://207.180.217.117:4780"

    # Build work notes based on ticket type
    if ticket.category.value == "password_reset" and status == "resolved":
        email = agent_response.result.get("email", "N/A")
        work_notes = f"""Password reset done successfully.
Temporary password has been sent to {email}.
User will be required to change password on first login.
Orchestration Ticket: {ticket.id}"""
    elif ticket.category.value == "work_order" and status == "resolved":
        work_order_id = agent_response.result.get("work_order_id", "N/A")
        work_notes = f"""AI Agent - Work Order Created:
SAP Work Order ID: {work_order_id}
Validation: Passed
Actions: {', '.join(agent_response.actions_taken)}
Orchestration Ticket: {ticket.id}"""
    elif ticket.category.value == "work_order" and status == "failed":
        issues = agent_response.result.get("issues", [])
        work_notes = f"""AI Agent - Work Order Validation Failed:
Issues: {', '.join(issues) if issues else agent_response.error or 'Unknown'}
Actions: {', '.join(agent_response.actions_taken)}
Orchestration Ticket: {ticket.id}"""
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

    # For account creation and work order approvals, update the tickets table
    if ticket.category.value in ("user_creation", "work_order"):
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
        # Get ServiceNow auth token
        import requests as sync_requests
        token_resp = sync_requests.post(
            f"{servicenow_url}/token",
            data={"username": "admin@company.com", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        sn_token = token_resp.json().get("access_token") if token_resp.status_code == 200 else None

        if not sn_token:
            logger.error(f"Failed to get ServiceNow token for updating ticket {ticket.servicenow_number}")
            return

        headers = {"Authorization": f"Bearer {sn_token}", "Content-Type": "application/json"}

        if ticket.category.value in ("user_creation", "work_order"):
            # Update ticket via ServiceNow API
            resp = sync_requests.put(
                f"{servicenow_url}/tickets/{ticket.servicenow_id}",
                json=update_data,
                headers=headers,
                timeout=10
            )

            if resp.status_code in [200, 201]:
                logger.info(f"Updated ServiceNow ticket {ticket.servicenow_number} (status: {update_data['status']})")
            else:
                logger.error(f"ServiceNow update failed: HTTP {resp.status_code} - {resp.text}")
        else:
            # For other tickets (password_reset, incidents), update via ticket status API
            ticket_status_update = {
                "status": "resolved" if status == "resolved" else "rejected",
                "resolution_notes": work_notes
            }
            resp = sync_requests.patch(
                f"{servicenow_url}/api/tickets/{ticket.servicenow_number}/status",
                json=ticket_status_update,
                headers=headers,
                timeout=10
            )

            if resp.status_code in [200, 201]:
                logger.info(f"Updated ServiceNow ticket {ticket.servicenow_number} (status: {status})")
            else:
                logger.error(f"ServiceNow ticket update failed: HTTP {resp.status_code} - {resp.text}")

    except Exception as e:
        logger.error(f"Failed to update ServiceNow ticket {ticket.servicenow_number}: {e}")

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
