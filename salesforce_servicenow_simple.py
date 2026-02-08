#!/usr/bin/env python3
"""
Salesforce → ServiceNow Webhook Integration (Simple Version - No MCP)
Direct HTTP calls to ServiceNow API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Salesforce-ServiceNow Integration", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICENOW_CONFIG = {
    "base_url": "http://207.180.217.117:4780",
    "username": "admin",
    "password": "password"
}

# ============================================================================
# DATA MODELS
# ============================================================================

class SalesforceAppointment(BaseModel):
    id: int
    customer_name: str
    appointment_date: str
    appointment_time: str
    service_type: str
    location: Optional[str] = ""
    notes: Optional[str] = ""
    status: str = "scheduled"

class SalesforceWorkOrder(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    assigned_to: Optional[str] = ""
    due_date: Optional[str] = ""
    work_order_type: str
    status: str = "new"

# ============================================================================
# SERVICENOW API CLIENT
# ============================================================================

async def create_servicenow_incident(short_description: str, description: str, priority: str = "3"):
    """Direct API call to ServiceNow - No MCP needed"""

    url = f"{SERVICENOW_CONFIG['base_url']}/api/now/table/incident"

    data = {
        "short_description": short_description,
        "description": description,
        "priority": priority,
        "state": "3",  # On Hold (Awaiting approval)
        "hold_reason": "Awaiting approval"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=data,
            auth=(SERVICENOW_CONFIG['username'], SERVICENOW_CONFIG['password']),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code >= 400:
            raise Exception(f"ServiceNow API error: {response.status_code} - {response.text}")

        return response.json()

async def update_servicenow_incident(sys_id: str, **fields):
    """Update ServiceNow incident"""

    url = f"{SERVICENOW_CONFIG['base_url']}/api/now/table/incident/{sys_id}"

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            url,
            json=fields,
            auth=(SERVICENOW_CONFIG['username'], SERVICENOW_CONFIG['password']),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code >= 400:
            raise Exception(f"ServiceNow API error: {response.status_code}")

        return response.json()

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.post("/api/webhooks/salesforce/appointment")
async def salesforce_appointment_webhook(appointment: SalesforceAppointment):
    """
    Salesforce appointment webhook - Creates ServiceNow ticket directly
    No MCP overhead!
    """
    logger.info(f"Received appointment webhook: ID={appointment.id}")

    try:
        # Create ServiceNow ticket - Direct API call
        short_desc = f"Service Appointment: {appointment.service_type} for {appointment.customer_name}"

        description = f"""
Salesforce Appointment Details:
- Customer: {appointment.customer_name}
- Service Type: {appointment.service_type}
- Date: {appointment.appointment_date}
- Time: {appointment.appointment_time}
- Location: {appointment.location}
- Salesforce ID: {appointment.id}

Automated ticket - Approval required.
        """.strip()

        # Direct ServiceNow API call (Fast!)
        result = await create_servicenow_incident(
            short_description=short_desc,
            description=description,
            priority="3"
        )

        ticket_sys_id = result["result"]["sys_id"]
        ticket_number = result["result"]["number"]

        logger.info(f"✓ Created ServiceNow ticket {ticket_number}")

        return {
            "salesforce_id": appointment.id,
            "servicenow_ticket_id": ticket_sys_id,
            "servicenow_ticket_number": ticket_number,
            "status": "pending_approval",
            "message": f"ServiceNow ticket {ticket_number} created"
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/salesforce/workorder")
async def salesforce_workorder_webhook(work_order: SalesforceWorkOrder):
    """Salesforce work order webhook"""
    logger.info(f"Received work order webhook: ID={work_order.id}")

    try:
        priority_map = {"High": "1", "Medium": "2", "Low": "3"}
        priority = priority_map.get(work_order.priority, "3")

        short_desc = f"Work Order: {work_order.title}"

        description = f"""
Salesforce Work Order Details:
- Title: {work_order.title}
- Type: {work_order.work_order_type}
- Priority: {work_order.priority}
- Due Date: {work_order.due_date}
- Description: {work_order.description}
- Salesforce ID: {work_order.id}

Automated ticket - Approval required.
        """.strip()

        # Direct API call
        result = await create_servicenow_incident(
            short_description=short_desc,
            description=description,
            priority=priority
        )

        ticket_sys_id = result["result"]["sys_id"]
        ticket_number = result["result"]["number"]

        logger.info(f"✓ Created ServiceNow ticket {ticket_number}")

        return {
            "salesforce_id": work_order.id,
            "servicenow_ticket_id": ticket_sys_id,
            "servicenow_ticket_number": ticket_number,
            "status": "pending_approval",
            "message": f"ServiceNow ticket {ticket_number} created"
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approvals/{ticket_sys_id}/approve")
async def approve_ticket(ticket_sys_id: str, approver: str):
    """Approve a ticket"""
    logger.info(f"Approving ticket {ticket_sys_id}")

    try:
        # Update directly
        result = await update_servicenow_incident(
            sys_id=ticket_sys_id,
            state="2",  # In Progress
            work_notes=f"Approved by {approver} at {datetime.now().isoformat()}"
        )

        ticket_number = result["result"]["number"]

        return {
            "status": "approved",
            "ticket_number": ticket_number,
            "approved_by": approver
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "version": "2.0.0 (No MCP)"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
