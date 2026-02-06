#!/usr/bin/env python3
"""
Salesforce → ServiceNow Webhook Integration
Automatically creates ServiceNow tickets for Salesforce appointments and work orders
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Salesforce-ServiceNow Integration", version="1.0.0")

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

class SalesforceAppointment(BaseModel):
    """Salesforce appointment webhook payload"""
    id: int
    customer_name: str
    appointment_date: str
    appointment_time: str
    service_type: str
    location: Optional[str] = ""
    notes: Optional[str] = ""
    status: str = "scheduled"
    created_by: Optional[str] = "system"

class SalesforceWorkOrder(BaseModel):
    """Salesforce work order webhook payload"""
    id: int
    title: str
    description: str
    priority: str  # High, Medium, Low
    assigned_to: Optional[str] = ""
    due_date: Optional[str] = ""
    work_order_type: str  # maintenance, installation, repair
    status: str = "new"
    created_by: Optional[str] = "system"

class ServiceNowTicketResponse(BaseModel):
    """Response after creating ServiceNow ticket"""
    salesforce_id: int
    salesforce_type: str  # appointment or work_order
    servicenow_ticket_id: str
    servicenow_ticket_number: str
    ticket_type: str  # service_request, incident, change_request
    status: str
    requires_approval: bool
    message: str

# ============================================================================
# MCP CONNECTOR
# ============================================================================

class MCPConnector:
    """MCP client for ServiceNow operations"""

    def __init__(self):
        self.session = None
        self._client = None
        self._session_context = None
        self.connected = False

    async def connect(self):
        """Connect to MCP unified-hub"""
        if self.connected:
            return

        server_params = StdioServerParameters(
            command="/home/pradeep1a/Network-apps/mcp_venv/bin/python3",
            args=["/home/pradeep1a/Network-apps/mcp_unified.py"]
        )

        self._client = stdio_client(server_params)
        read, write = await self._client.__aenter__()

        self._session_context = ClientSession(read, write)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

        self.connected = True
        logger.info("✓ Connected to MCP unified-hub")

    async def disconnect(self):
        """Disconnect from MCP"""
        if not self.connected:
            return

        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._client:
            await self._client.__aexit__(None, None, None)

        self.connected = False

    async def call(self, tool_name: str, **kwargs):
        """Call MCP tool"""
        if not self.connected:
            await self.connect()

        result = await self.session.call_tool(tool_name, arguments=kwargs)

        if result.content and len(result.content) > 0:
            return json.loads(result.content[0].text)
        return {}


# Global MCP connector
mcp = MCPConnector()

@app.on_event("startup")
async def startup_event():
    """Initialize MCP connection on startup"""
    await mcp.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect MCP on shutdown"""
    await mcp.disconnect()

# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

@app.post("/api/webhooks/salesforce/appointment", response_model=ServiceNowTicketResponse)
async def salesforce_appointment_webhook(appointment: SalesforceAppointment):
    """
    Webhook endpoint for Salesforce appointments
    Creates ServiceNow Service Request ticket

    Configure in Salesforce:
    URL: http://your-server:8080/api/webhooks/salesforce/appointment
    Method: POST
    Trigger: After Insert on Appointment
    """
    logger.info(f"Received Salesforce appointment webhook: ID={appointment.id}")

    try:
        # Create ServiceNow Service Request
        short_desc = f"Service Appointment: {appointment.service_type} for {appointment.customer_name}"

        description = f"""
Salesforce Appointment Details:
- Customer: {appointment.customer_name}
- Service Type: {appointment.service_type}
- Date: {appointment.appointment_date}
- Time: {appointment.appointment_time}
- Location: {appointment.location}
- Notes: {appointment.notes}
- Salesforce ID: {appointment.id}

This is an automated ticket created from Salesforce.
Approval required before scheduling.
        """.strip()

        # Create ServiceNow ticket via MCP
        sn_ticket = await mcp.call(
            "sn_create_incident",
            short_description=short_desc,
            description=description,
            priority="3",  # Medium priority for appointments
            urgency="3",
            impact="3"
        )

        if "error" in sn_ticket:
            raise HTTPException(status_code=500, detail=f"ServiceNow error: {sn_ticket['error']}")

        # Extract ServiceNow ticket info
        ticket_sys_id = sn_ticket.get("result", {}).get("sys_id", "unknown")
        ticket_number = sn_ticket.get("result", {}).get("number", "unknown")

        # Update ticket to pending approval status
        await mcp.call(
            "sn_update_incident",
            incident_id=ticket_sys_id,
            state="3",  # On Hold
            hold_reason="Awaiting approval",
            work_notes=f"Salesforce Appointment ID: {appointment.id}"
        )

        logger.info(f"✓ Created ServiceNow ticket {ticket_number} for appointment {appointment.id}")

        return ServiceNowTicketResponse(
            salesforce_id=appointment.id,
            salesforce_type="appointment",
            servicenow_ticket_id=ticket_sys_id,
            servicenow_ticket_number=ticket_number,
            ticket_type="service_request",
            status="pending_approval",
            requires_approval=True,
            message=f"ServiceNow ticket {ticket_number} created and awaiting approval"
        )

    except Exception as e:
        logger.error(f"Error processing appointment webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/salesforce/workorder", response_model=ServiceNowTicketResponse)
async def salesforce_workorder_webhook(work_order: SalesforceWorkOrder):
    """
    Webhook endpoint for Salesforce work orders
    Creates ServiceNow Incident or Change Request based on type

    Configure in Salesforce:
    URL: http://your-server:8080/api/webhooks/salesforce/workorder
    Method: POST
    Trigger: After Insert on WorkOrder
    """
    logger.info(f"Received Salesforce work order webhook: ID={work_order.id}")

    try:
        # Determine ticket type and priority
        if work_order.work_order_type == "maintenance":
            ticket_type = "change_request"
            priority_map = {"High": "2", "Medium": "3", "Low": "4"}
        else:
            ticket_type = "incident"
            priority_map = {"High": "1", "Medium": "2", "Low": "3"}

        priority = priority_map.get(work_order.priority, "3")

        # Create ServiceNow ticket
        short_desc = f"Work Order: {work_order.title}"

        description = f"""
Salesforce Work Order Details:
- Title: {work_order.title}
- Type: {work_order.work_order_type}
- Priority: {work_order.priority}
- Assigned To: {work_order.assigned_to}
- Due Date: {work_order.due_date}
- Description: {work_order.description}
- Salesforce ID: {work_order.id}

This is an automated ticket created from Salesforce.
Approval required before execution.
        """.strip()

        if ticket_type == "incident":
            # Create Incident
            sn_ticket = await mcp.call(
                "sn_create_incident",
                short_description=short_desc,
                description=description,
                priority=priority,
                urgency=priority,
                impact=priority
            )
        else:
            # Create Change Request
            sn_ticket = await mcp.call(
                "sn_create_change_request",
                short_description=short_desc,
                description=description,
                type="normal",
                priority=priority
            )

        if "error" in sn_ticket:
            raise HTTPException(status_code=500, detail=f"ServiceNow error: {sn_ticket['error']}")

        # Extract ticket info
        ticket_sys_id = sn_ticket.get("result", {}).get("sys_id", "unknown")
        ticket_number = sn_ticket.get("result", {}).get("number", "unknown")

        # Update to pending approval
        if ticket_type == "incident":
            await mcp.call(
                "sn_update_incident",
                incident_id=ticket_sys_id,
                state="3",  # On Hold
                hold_reason="Awaiting approval for work order execution",
                work_notes=f"Salesforce Work Order ID: {work_order.id}"
            )

        logger.info(f"✓ Created ServiceNow {ticket_type} {ticket_number} for work order {work_order.id}")

        return ServiceNowTicketResponse(
            salesforce_id=work_order.id,
            salesforce_type="work_order",
            servicenow_ticket_id=ticket_sys_id,
            servicenow_ticket_number=ticket_number,
            ticket_type=ticket_type,
            status="pending_approval",
            requires_approval=True,
            message=f"ServiceNow {ticket_type} {ticket_number} created and awaiting approval"
        )

    except Exception as e:
        logger.error(f"Error processing work order webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPROVAL ENDPOINTS
# ============================================================================

@app.post("/api/approvals/appointments/{appointment_id}/approve")
async def approve_appointment(appointment_id: int, approver: str):
    """
    Approve a Salesforce appointment
    Updates ServiceNow ticket status
    """
    logger.info(f"Approving appointment {appointment_id} by {approver}")

    try:
        # Search for ServiceNow ticket with this appointment ID
        incidents = await mcp.call(
            "sn_list_incidents",
            query=f"work_notesLIKESalesforce Appointment ID: {appointment_id}",
            limit=1,
            skip=0
        )

        if not incidents or "result" not in incidents or len(incidents["result"]) == 0:
            raise HTTPException(status_code=404, detail=f"ServiceNow ticket not found for appointment {appointment_id}")

        ticket = incidents["result"][0]
        ticket_id = ticket["sys_id"]
        ticket_number = ticket["number"]

        # Update ticket to approved and in progress
        await mcp.call(
            "sn_update_incident",
            incident_id=ticket_id,
            state="2",  # In Progress
            work_notes=f"Approved by {approver} at {datetime.now().isoformat()}. Appointment can proceed."
        )

        logger.info(f"✓ Approved ServiceNow ticket {ticket_number}")

        return {
            "status": "approved",
            "appointment_id": appointment_id,
            "servicenow_ticket": ticket_number,
            "approved_by": approver,
            "message": "Appointment approved and ticket updated"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approvals/workorders/{workorder_id}/approve")
async def approve_workorder(workorder_id: int, approver: str):
    """
    Approve a Salesforce work order
    Updates ServiceNow ticket status
    """
    logger.info(f"Approving work order {workorder_id} by {approver}")

    try:
        # Search for ServiceNow ticket
        incidents = await mcp.call(
            "sn_list_incidents",
            query=f"work_notesLIKESalesforce Work Order ID: {workorder_id}",
            limit=1,
            skip=0
        )

        if not incidents or "result" not in incidents or len(incidents["result"]) == 0:
            raise HTTPException(status_code=404, detail=f"ServiceNow ticket not found for work order {workorder_id}")

        ticket = incidents["result"][0]
        ticket_id = ticket["sys_id"]
        ticket_number = ticket["number"]

        # Update ticket to approved
        await mcp.call(
            "sn_update_incident",
            incident_id=ticket_id,
            state="2",  # In Progress
            work_notes=f"Approved by {approver} at {datetime.now().isoformat()}. Work order execution authorized."
        )

        logger.info(f"✓ Approved ServiceNow ticket {ticket_number}")

        return {
            "status": "approved",
            "workorder_id": workorder_id,
            "servicenow_ticket": ticket_number,
            "approved_by": approver,
            "message": "Work order approved and ticket updated"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approvals/workorders/{workorder_id}/reject")
async def reject_workorder(workorder_id: int, approver: str, reason: str):
    """Reject a work order"""
    logger.info(f"Rejecting work order {workorder_id} by {approver}")

    try:
        # Search for ServiceNow ticket
        incidents = await mcp.call(
            "sn_list_incidents",
            query=f"work_notesLIKESalesforce Work Order ID: {workorder_id}",
            limit=1,
            skip=0
        )

        if not incidents or "result" not in incidents or len(incidents["result"]) == 0:
            raise HTTPException(status_code=404, detail=f"ServiceNow ticket not found")

        ticket = incidents["result"][0]
        ticket_id = ticket["sys_id"]
        ticket_number = ticket["number"]

        # Update ticket to closed/rejected
        await mcp.call(
            "sn_update_incident",
            incident_id=ticket_id,
            state="7",  # Closed
            close_code="Rejected",
            close_notes=f"Rejected by {approver}. Reason: {reason}"
        )

        logger.info(f"✓ Rejected ServiceNow ticket {ticket_number}")

        return {
            "status": "rejected",
            "workorder_id": workorder_id,
            "servicenow_ticket": ticket_number,
            "rejected_by": approver,
            "reason": reason,
            "message": "Work order rejected and ticket closed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/integration/status")
async def integration_status():
    """Check integration status"""
    try:
        # Check MCP connection
        mcp_status = "connected" if mcp.connected else "disconnected"

        # Check ServiceNow health
        health = await mcp.call("health_check_all")

        return {
            "status": "healthy",
            "mcp_connection": mcp_status,
            "servicenow_status": health.get("servicenow", {}).get("status", "unknown"),
            "salesforce_status": health.get("salesforce", {}).get("status", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/integration/pending-approvals")
async def list_pending_approvals():
    """List all pending approval tickets"""
    try:
        # Query ServiceNow for tickets on hold
        incidents = await mcp.call(
            "sn_list_incidents",
            query="state=3^hold_reason=Awaiting approval",
            limit=50,
            skip=0
        )

        pending_tickets = []
        if "result" in incidents:
            for ticket in incidents["result"]:
                pending_tickets.append({
                    "servicenow_number": ticket.get("number"),
                    "short_description": ticket.get("short_description"),
                    "priority": ticket.get("priority"),
                    "created": ticket.get("sys_created_on"),
                    "sys_id": ticket.get("sys_id")
                })

        return {
            "total": len(pending_tickets),
            "tickets": pending_tickets
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "salesforce-servicenow-integration",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
