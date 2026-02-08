#!/usr/bin/env python3
"""
MCP Server for SAP ERP Integration
Provides tools to interact with SAP modules: PM, MM, FI, Sales, and Tickets
"""

import json
import httpx
from typing import Optional
from mcp.server import Server
from mcp.types import TextContent, Tool

# SAP Backend Configuration
API_BASE_URL = "http://207.180.217.117:4798"
MCP_HOST = "0.0.0.0"
MCP_PORT = 8092
DEFAULT_TOKEN = None

server = Server("sap-erp-integration")


def set_token(token: str):
    """Set authentication token for API calls"""
    global DEFAULT_TOKEN
    DEFAULT_TOKEN = token


async def api_call(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    token: Optional[str] = None,
    params: Optional[dict] = None,
) -> dict:
    """Make authenticated API call to SAP backend"""
    headers = {"Content-Type": "application/json"}
    if token or DEFAULT_TOKEN:
        headers["Authorization"] = f"Bearer {token or DEFAULT_TOKEN}"

    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method == "PATCH":
            response = await client.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            return {
                "error": f"SAP API Error {response.status_code}",
                "details": response.text,
            }
        return response.json()


# ============================================================================
# AUTHENTICATION TOOLS
# ============================================================================

async def sap_login(username: str, password: str):
    """Login to SAP and get JWT token"""
    result = await api_call(
        "POST",
        "/api/v1/auth/login",
        {"username": username, "password": password},
    )
    if "access_token" in result:
        set_token(result["access_token"])
    return [TextContent(type="text", text=json.dumps(result))]


async def sap_refresh_token(token: str):
    """Refresh SAP JWT token"""
    result = await api_call("POST", "/api/v1/auth/refresh", {"token": token})
    if "access_token" in result:
        set_token(result["access_token"])
    return [TextContent(type="text", text=json.dumps(result))]


async def validate_user_for_password_reset(username: str):
    """
    Validate if a user exists in SAP database for password reset.
    Returns whether the user exists and can proceed with password reset flow.
    This does not require authentication and is safe to call for user validation.
    """
    result = await api_call(
        "POST",
        "/api/v1/auth/validate-user",
        {"username": username},
    )
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# TICKET MANAGEMENT TOOLS
# ============================================================================

async def list_tickets(
    module: str = "",
    status: str = "",
    priority: str = "",
    page: int = 1,
    limit: int = 20,
):
    """List SAP tickets with optional filtering by module, status, priority"""
    params = {"page": page, "limit": limit}
    if module:
        params["module"] = module
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    result = await api_call("GET", "/api/v1/tickets", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_ticket(ticket_id: str):
    """Get SAP ticket by ID"""
    result = await api_call("GET", f"/api/v1/tickets/{ticket_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_ticket(
    module: str,
    ticket_type: str,
    priority: str,
    title: str,
    created_by: str,
    description: str = "",
):
    """Create new SAP ticket"""
    data = {
        "module": module,
        "ticket_type": ticket_type,
        "priority": priority,
        "title": title,
        "created_by": created_by,
        "description": description,
    }
    result = await api_call("POST", "/api/v1/tickets", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_ticket_status(
    ticket_id: str,
    new_status: str,
    changed_by: str,
    comment: str = "",
):
    """Update SAP ticket status"""
    data = {
        "new_status": new_status,
        "changed_by": changed_by,
        "comment": comment,
    }
    result = await api_call("PATCH", f"/api/v1/tickets/{ticket_id}/status", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_ticket_audit_trail(ticket_id: str):
    """Get audit trail for a SAP ticket"""
    result = await api_call("GET", f"/api/v1/tickets/{ticket_id}/audit")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# PLANT MAINTENANCE (PM) TOOLS
# ============================================================================

async def list_assets(
    asset_type: str = "",
    status: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP PM assets with optional filtering"""
    params = {"limit": limit, "offset": offset}
    if asset_type:
        params["asset_type"] = asset_type
    if status:
        params["status"] = status
    result = await api_call("GET", "/api/v1/pm/assets", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_asset(asset_id: str):
    """Get SAP PM asset by ID"""
    result = await api_call("GET", f"/api/v1/pm/assets/{asset_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_asset(
    asset_type: str,
    name: str,
    location: str,
    installation_date: str,
    status: str = "operational",
    description: str = "",
):
    """Create new SAP PM asset"""
    data = {
        "asset_type": asset_type,
        "name": name,
        "location": location,
        "installation_date": installation_date,
        "status": status,
        "description": description,
    }
    result = await api_call("POST", "/api/v1/pm/assets", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def list_maintenance_orders(
    asset_id: str = "",
    status: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP PM maintenance orders"""
    params = {"limit": limit, "offset": offset}
    if asset_id:
        params["asset_id"] = asset_id
    if status:
        params["status"] = status
    result = await api_call("GET", "/api/v1/pm/maintenance-orders", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def create_maintenance_order(
    asset_id: str,
    order_type: str,
    description: str,
    scheduled_date: str,
    created_by: str,
    priority: str = "P3",
):
    """Create SAP PM maintenance order"""
    data = {
        "asset_id": asset_id,
        "order_type": order_type,
        "description": description,
        "scheduled_date": scheduled_date,
        "created_by": created_by,
        "priority": priority,
    }
    result = await api_call("POST", "/api/v1/pm/maintenance-orders", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def create_incident(
    asset_id: str,
    fault_type: str,
    description: str,
    reported_by: str,
    severity: str = "P2",
):
    """Create SAP PM incident"""
    data = {
        "asset_id": asset_id,
        "fault_type": fault_type,
        "description": description,
        "reported_by": reported_by,
        "severity": severity,
    }
    result = await api_call("POST", "/api/v1/pm/incidents", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# MATERIALS MANAGEMENT (MM) TOOLS
# ============================================================================

async def list_materials(
    storage_location: str = "",
    below_reorder: bool = False,
    limit: int = 20,
    offset: int = 0,
):
    """List SAP MM materials"""
    params = {"limit": limit, "offset": offset, "below_reorder": below_reorder}
    if storage_location:
        params["storage_location"] = storage_location
    result = await api_call("GET", "/api/v1/mm/materials", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_material(material_id: str):
    """Get SAP MM material by ID"""
    result = await api_call("GET", f"/api/v1/mm/materials/{material_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_material(
    description: str,
    quantity: int,
    unit_of_measure: str,
    reorder_level: int,
    storage_location: str,
    material_id: str = "",
):
    """Create new SAP MM material"""
    data = {
        "description": description,
        "quantity": quantity,
        "unit_of_measure": unit_of_measure,
        "reorder_level": reorder_level,
        "storage_location": storage_location,
    }
    if material_id:
        data["material_id"] = material_id
    result = await api_call("POST", "/api/v1/mm/materials", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def create_stock_transaction(
    material_id: str,
    quantity_change: int,
    transaction_type: str,
    performed_by: str,
    reference_doc: str = "",
    notes: str = "",
):
    """Process SAP MM stock transaction (receipt, issue, transfer, adjustment)"""
    data = {
        "material_id": material_id,
        "quantity_change": quantity_change,
        "transaction_type": transaction_type,
        "performed_by": performed_by,
        "reference_doc": reference_doc,
        "notes": notes,
    }
    result = await api_call("POST", "/api/v1/mm/stock-transactions", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_material_transaction_history(
    material_id: str,
    limit: int = 20,
    offset: int = 0,
):
    """Get transaction history for a SAP MM material"""
    params = {"limit": limit, "offset": offset}
    result = await api_call("GET", f"/api/v1/mm/materials/{material_id}/transactions", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def list_purchase_requisitions(
    material_id: str = "",
    status: str = "",
    cost_center_id: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP MM purchase requisitions"""
    params = {"limit": limit, "offset": offset}
    if material_id:
        params["material_id"] = material_id
    if status:
        params["status"] = status
    if cost_center_id:
        params["cost_center_id"] = cost_center_id
    result = await api_call("GET", "/api/v1/mm/purchase-requisitions", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def create_purchase_requisition(
    material_id: str,
    quantity: int,
    cost_center_id: str,
    justification: str,
    requested_by: str,
):
    """Create SAP MM purchase requisition"""
    data = {
        "material_id": material_id,
        "quantity": quantity,
        "cost_center_id": cost_center_id,
        "justification": justification,
        "requested_by": requested_by,
    }
    result = await api_call("POST", "/api/v1/mm/purchase-requisitions", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# FINANCE (FI) TOOLS
# ============================================================================

async def list_cost_centers(
    fiscal_year: int = 0,
    responsible_manager: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP FI cost centers"""
    params = {"limit": limit, "offset": offset}
    if fiscal_year:
        params["fiscal_year"] = fiscal_year
    if responsible_manager:
        params["responsible_manager"] = responsible_manager
    result = await api_call("GET", "/api/v1/fi/cost-centers", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_cost_center(cost_center_id: str):
    """Get SAP FI cost center by ID"""
    result = await api_call("GET", f"/api/v1/fi/cost-centers/{cost_center_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_cost_center(
    name: str,
    budget_amount: float,
    fiscal_year: int,
    responsible_manager: str,
    cost_center_id: str = "",
    description: str = "",
):
    """Create SAP FI cost center"""
    data = {
        "name": name,
        "budget_amount": budget_amount,
        "fiscal_year": fiscal_year,
        "responsible_manager": responsible_manager,
        "description": description,
    }
    if cost_center_id:
        data["cost_center_id"] = cost_center_id
    result = await api_call("POST", "/api/v1/fi/cost-centers", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def list_cost_entries(
    cost_center_id: str = "",
    ticket_id: str = "",
    cost_type: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP FI cost entries"""
    params = {"limit": limit, "offset": offset}
    if cost_center_id:
        params["cost_center_id"] = cost_center_id
    if ticket_id:
        params["ticket_id"] = ticket_id
    if cost_type:
        params["cost_type"] = cost_type
    result = await api_call("GET", "/api/v1/fi/cost-entries", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def create_cost_entry(
    cost_center_id: str,
    amount: float,
    cost_type: str,
    created_by: str,
    ticket_id: str = "",
    description: str = "",
):
    """Create SAP FI cost entry"""
    data = {
        "cost_center_id": cost_center_id,
        "amount": amount,
        "cost_type": cost_type,
        "created_by": created_by,
        "description": description,
    }
    if ticket_id:
        data["ticket_id"] = ticket_id
    result = await api_call("POST", "/api/v1/fi/cost-entries", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def list_approval_requests(
    cost_center_id: str = "",
    decision: str = "",
    requested_by: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP FI approval requests"""
    params = {"limit": limit, "offset": offset}
    if cost_center_id:
        params["cost_center_id"] = cost_center_id
    if decision:
        params["decision"] = decision
    if requested_by:
        params["requested_by"] = requested_by
    result = await api_call("GET", "/api/v1/fi/approval-requests", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def create_approval_request(
    cost_center_id: str,
    amount: float,
    justification: str,
    requested_by: str,
):
    """Create SAP FI approval request"""
    data = {
        "cost_center_id": cost_center_id,
        "amount": amount,
        "justification": justification,
        "requested_by": requested_by,
    }
    result = await api_call("POST", "/api/v1/fi/approval-requests", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def approve_request(approval_id: str, decided_by: str, comment: str = ""):
    """Approve SAP FI approval request"""
    data = {"decided_by": decided_by, "comment": comment}
    result = await api_call("POST", f"/api/v1/fi/approval-requests/{approval_id}/approve", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def reject_request(approval_id: str, decided_by: str, comment: str = ""):
    """Reject SAP FI approval request"""
    data = {"decided_by": decided_by, "comment": comment}
    result = await api_call("POST", f"/api/v1/fi/approval-requests/{approval_id}/reject", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SALES TOOLS
# ============================================================================

async def list_sales_orders(
    status: str = "",
    customer_id: str = "",
    page: int = 1,
    page_size: int = 20,
):
    """List SAP sales orders"""
    params = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if customer_id:
        params["customer_id"] = customer_id
    result = await api_call("GET", "/api/sales/orders", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_sales_order(order_id: str):
    """Get SAP sales order by ID"""
    result = await api_call("GET", f"/api/sales/orders/{order_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_sales_order(
    customer_id: str,
    customer_name: str,
    delivery_date: str,
    items: list,
    currency: str = "USD",
):
    """Create SAP sales order. Items should be a list of dicts with line_item, material_id, description, quantity, unit_price, total"""
    data = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "delivery_date": delivery_date,
        "items": items,
        "currency": currency,
    }
    result = await api_call("POST", "/api/sales/orders", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_sales_order(order_id: str, **kwargs):
    """Update SAP sales order"""
    result = await api_call("PUT", f"/api/sales/orders/{order_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_sales_order_status(order_id: str, status: str):
    """Update SAP sales order status (new, processing, shipped, delivered, cancelled)"""
    data = {"status": status}
    result = await api_call("PATCH", f"/api/sales/orders/{order_id}/status", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# WORK ORDER FLOW TOOLS (PM -> MM -> FI Integration)
# ============================================================================

async def list_work_orders(
    flow_status: str = "",
    customer_name: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List SAP work orders with optional filtering by status or customer"""
    params = {"limit": limit, "offset": offset}
    if flow_status:
        params["flow_status"] = flow_status
    if customer_name:
        params["customer_name"] = customer_name
    result = await api_call("GET", "/api/v1/work-order-flow/work-orders", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_work_order(work_order_id: str):
    """Get SAP work order by ID"""
    result = await api_call("GET", f"/api/v1/work-order-flow/work-orders/{work_order_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_work_order(
    title: str,
    description: str,
    customer_name: str,
    site_location: str,
    requested_date: str,
    cost_center_id: str,
    created_by: str,
    materials: list,
    crm_reference_id: str = "",
    customer_contact: str = "",
    priority: str = "medium",
    assigned_to: str = "",
):
    """Create SAP work order with materials for PM -> MM -> FI workflow"""
    data = {
        "title": title,
        "description": description,
        "customer_name": customer_name,
        "site_location": site_location,
        "requested_date": requested_date,
        "cost_center_id": cost_center_id,
        "created_by": created_by,
        "materials": materials,
        "priority": priority,
    }
    if crm_reference_id:
        data["crm_reference_id"] = crm_reference_id
    if customer_contact:
        data["customer_contact"] = customer_contact
    if assigned_to:
        data["assigned_to"] = assigned_to
    result = await api_call("POST", "/api/v1/work-order-flow/work-orders", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def check_work_order_materials(work_order_id: str, performed_by: str):
    """Send work order to MM for material availability check"""
    data = {"performed_by": performed_by}
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/check-materials", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def request_work_order_purchase(
    work_order_id: str,
    performed_by: str,
    justification: str = "",
):
    """MM raises FI ticket for purchasing materials that are not available"""
    data = {"performed_by": performed_by}
    if justification:
        data["justification"] = justification
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/request-purchase", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def approve_work_order_purchase(
    work_order_id: str,
    approved: bool,
    decided_by: str,
    comment: str = "",
):
    """FI approves or rejects work order purchase request"""
    data = {
        "approved": approved,
        "decided_by": decided_by,
    }
    if comment:
        data["comment"] = comment
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/approve-purchase", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def proceed_work_order(work_order_id: str, performed_by: str):
    """Proceed with work order after materials confirmed available"""
    data = {"performed_by": performed_by}
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/proceed", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def start_work_order(
    work_order_id: str,
    performed_by: str,
    scheduled_date: str = "",
):
    """Start working on work order"""
    data = {"performed_by": performed_by}
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/start", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def complete_work_order(work_order_id: str, performed_by: str):
    """Complete work order"""
    data = {"performed_by": performed_by}
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/complete", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_work_order_history(work_order_id: str):
    """Get flow history for a work order (PM -> MM -> FI transitions)"""
    result = await api_call("GET", f"/api/v1/work-order-flow/work-orders/{work_order_id}/history")
    return [TextContent(type="text", text=json.dumps(result))]


async def get_pending_purchase_work_orders():
    """Get work orders pending purchase request (materials shortage)"""
    result = await api_call("GET", "/api/v1/work-order-flow/work-orders/pending-purchase")
    return [TextContent(type="text", text=json.dumps(result))]


async def get_pending_approval_work_orders():
    """Get work orders pending FI approval"""
    result = await api_call("GET", "/api/v1/work-order-flow/work-orders/pending-approval")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# CRM INTEGRATION TOOLS
# ============================================================================

async def sync_crm_case(
    case_id: str,
    case_number: str,
    subject: str,
    description: str,
    account_name: str,
    site_address: str,
    priority: str = "Medium",
    materials: list = None,
    contact_name: str = "",
    owner_name: str = "",
    cost_center_id: str = "CC-DEFAULT",
    operation: str = "CREATE",
):
    """Sync a CRM case (e.g., from Salesforce) to SAP as a work order"""
    data = {
        "operation": operation,
        "case": {
            "case_id": case_id,
            "case_number": case_number,
            "subject": subject,
            "description": description,
            "account_name": account_name,
            "site_address": site_address,
            "priority": priority,
            "materials": materials or [],
            "contact_name": contact_name,
            "owner_name": owner_name,
            "cost_center_id": cost_center_id,
        }
    }
    result = await api_call("POST", "/api/v1/crm-integration/sync-case", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_crm_case_status(case_id: str):
    """Get SAP work order status for a CRM case"""
    result = await api_call("GET", f"/api/v1/crm-integration/case-status/{case_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def crm_integration_health():
    """Check CRM integration health"""
    result = await api_call("GET", "/api/v1/crm-integration/health")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# APPOINTMENT VALIDATION TOOLS (For Agent)
# ============================================================================

async def validate_appointment(
    required_parts: str,
    location: str,
):
    """
    Validate appointment request against SAP master data.
    Checks parts availability and location.
    Used by agent for appointment approval decisions.
    """
    data = {
        "required_parts": required_parts,
        "location": location,
    }
    result = await api_call("POST", "/api/api/appointments/validate", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def search_materials_by_query(query: str):
    """Search for materials in SAP inventory by keyword"""
    result = await api_call("GET", "/api/api/appointments/parts/search", params={"query": query})
    return [TextContent(type="text", text=json.dumps(result))]


async def find_available_technicians(required_skills: str = ""):
    """Find available engineers/technicians with optional skill filtering"""
    params = {}
    if required_skills:
        params["skill"] = required_skills
    result = await api_call("GET", "/api/api/appointments/technicians/available", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def search_location_assets(location: str):
    """Search for assets/locations in SAP by name or ID"""
    result = await api_call(
        "GET",
        "/api/api/appointments/locations/search",
        params={"location": location}
    )
    return [TextContent(type="text", text=json.dumps(result))]


async def get_material_recommendations():
    """Get recommended materials for common appointment types"""
    result = await api_call("GET", "/api/api/appointments/materials/recommendations")
    return [TextContent(type="text", text=json.dumps(result))]


async def reserve_materials_for_work_order(
    work_order_id: str,
    material_id: str,
    quantity: int,
    required_date: str = "",
):
    """Reserve materials from inventory for a work order"""
    data = {
        "work_order_id": work_order_id,
        "material_id": material_id,
        "quantity": quantity,
    }
    if required_date:
        data["required_date"] = required_date
    result = await api_call("POST", "/api/v1/mm/material-reservations", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_work_order_status(work_order_id: str, status: str, updated_by: str, notes: str = ""):
    """Update work order status and add notes"""
    data = {
        "status": status,
        "updated_by": updated_by,
    }
    if notes:
        data["notes"] = notes
    result = await api_call("PATCH", f"/api/v1/work-order-flow/work-orders/{work_order_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# HEALTH CHECK
# ============================================================================

async def sap_health_check():
    """Check SAP backend health"""
    try:
        result = await api_call("GET", "/health")
        return [TextContent(type="text", text=json.dumps({"status": "healthy", "details": result}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "unhealthy", "error": str(e)}))]


# ============================================================================
# MCP TOOL REGISTRATION - list_tools and call_tool handlers
# ============================================================================

# Dispatch map: tool name -> function
TOOL_DISPATCH = {
    "sap_login": sap_login,
    "sap_refresh_token": sap_refresh_token,
    "validate_user_for_password_reset": validate_user_for_password_reset,
    "list_tickets": list_tickets,
    "get_ticket": get_ticket,
    "create_ticket": create_ticket,
    "update_ticket_status": update_ticket_status,
    "get_ticket_audit_trail": get_ticket_audit_trail,
    "list_assets": list_assets,
    "get_asset": get_asset,
    "create_asset": create_asset,
    "list_maintenance_orders": list_maintenance_orders,
    "create_maintenance_order": create_maintenance_order,
    "create_incident": create_incident,
    "list_materials": list_materials,
    "get_material": get_material,
    "create_material": create_material,
    "create_stock_transaction": create_stock_transaction,
    "get_material_transaction_history": get_material_transaction_history,
    "list_purchase_requisitions": list_purchase_requisitions,
    "create_purchase_requisition": create_purchase_requisition,
    "list_cost_centers": list_cost_centers,
    "get_cost_center": get_cost_center,
    "create_cost_center": create_cost_center,
    "list_cost_entries": list_cost_entries,
    "create_cost_entry": create_cost_entry,
    "list_approval_requests": list_approval_requests,
    "create_approval_request": create_approval_request,
    "approve_request": approve_request,
    "reject_request": reject_request,
    "list_sales_orders": list_sales_orders,
    "get_sales_order": get_sales_order,
    "create_sales_order": create_sales_order,
    "update_sales_order": update_sales_order,
    "update_sales_order_status": update_sales_order_status,
    "list_work_orders": list_work_orders,
    "get_work_order": get_work_order,
    "create_work_order": create_work_order,
    "check_work_order_materials": check_work_order_materials,
    "request_work_order_purchase": request_work_order_purchase,
    "approve_work_order_purchase": approve_work_order_purchase,
    "proceed_work_order": proceed_work_order,
    "start_work_order": start_work_order,
    "complete_work_order": complete_work_order,
    "get_work_order_history": get_work_order_history,
    "get_pending_purchase_work_orders": get_pending_purchase_work_orders,
    "get_pending_approval_work_orders": get_pending_approval_work_orders,
    "sync_crm_case": sync_crm_case,
    "get_crm_case_status": get_crm_case_status,
    "crm_integration_health": crm_integration_health,
    "validate_appointment": validate_appointment,
    "search_materials_by_query": search_materials_by_query,
    "find_available_technicians": find_available_technicians,
    "search_location_assets": search_location_assets,
    "get_material_recommendations": get_material_recommendations,
    "reserve_materials_for_work_order": reserve_materials_for_work_order,
    "update_work_order_status": update_work_order_status,
    "sap_health_check": sap_health_check,
}


@server.list_tools()
async def handle_list_tools():
    """Return the list of available SAP tools"""
    return [
        # --- Authentication Tools ---
        Tool(
            name="sap_login",
            description="Login to SAP and get JWT token",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "SAP username"},
                    "password": {"type": "string", "description": "SAP password"},
                },
                "required": ["username", "password"],
            },
        ),
        Tool(
            name="sap_refresh_token",
            description="Refresh SAP JWT token",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Current JWT token to refresh"},
                },
                "required": ["token"],
            },
        ),
        Tool(
            name="validate_user_for_password_reset",
            description="Validate if a user exists in SAP database for password reset. Returns whether the user exists and can proceed with password reset flow. This does not require authentication and is safe to call for user validation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username to validate"},
                },
                "required": ["username"],
            },
        ),
        # --- Ticket Management Tools ---
        Tool(
            name="list_tickets",
            description="List SAP tickets with optional filtering by module, status, priority",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {"type": "string", "description": "Filter by module"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "priority": {"type": "string", "description": "Filter by priority"},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                    "limit": {"type": "integer", "description": "Items per page", "default": 20},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_ticket",
            description="Get SAP ticket by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID"},
                },
                "required": ["ticket_id"],
            },
        ),
        Tool(
            name="create_ticket",
            description="Create new SAP ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {"type": "string", "description": "SAP module (PM, MM, FI, etc.)"},
                    "ticket_type": {"type": "string", "description": "Type of ticket"},
                    "priority": {"type": "string", "description": "Ticket priority"},
                    "title": {"type": "string", "description": "Ticket title"},
                    "created_by": {"type": "string", "description": "Creator username"},
                    "description": {"type": "string", "description": "Ticket description", "default": ""},
                },
                "required": ["module", "ticket_type", "priority", "title", "created_by"],
            },
        ),
        Tool(
            name="update_ticket_status",
            description="Update SAP ticket status",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID"},
                    "new_status": {"type": "string", "description": "New status"},
                    "changed_by": {"type": "string", "description": "User making the change"},
                    "comment": {"type": "string", "description": "Status change comment", "default": ""},
                },
                "required": ["ticket_id", "new_status", "changed_by"],
            },
        ),
        Tool(
            name="get_ticket_audit_trail",
            description="Get audit trail for a SAP ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID"},
                },
                "required": ["ticket_id"],
            },
        ),
        # --- Plant Maintenance (PM) Tools ---
        Tool(
            name="list_assets",
            description="List SAP PM assets with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_type": {"type": "string", "description": "Filter by asset type"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_asset",
            description="Get SAP PM asset by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Asset ID"},
                },
                "required": ["asset_id"],
            },
        ),
        Tool(
            name="create_asset",
            description="Create new SAP PM asset",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_type": {"type": "string", "description": "Type of asset"},
                    "name": {"type": "string", "description": "Asset name"},
                    "location": {"type": "string", "description": "Asset location"},
                    "installation_date": {"type": "string", "description": "Installation date"},
                    "status": {"type": "string", "description": "Asset status", "default": "operational"},
                    "description": {"type": "string", "description": "Asset description", "default": ""},
                },
                "required": ["asset_type", "name", "location", "installation_date"],
            },
        ),
        Tool(
            name="list_maintenance_orders",
            description="List SAP PM maintenance orders",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Filter by asset ID"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="create_maintenance_order",
            description="Create SAP PM maintenance order",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Asset ID"},
                    "order_type": {"type": "string", "description": "Order type"},
                    "description": {"type": "string", "description": "Order description"},
                    "scheduled_date": {"type": "string", "description": "Scheduled date"},
                    "created_by": {"type": "string", "description": "Creator username"},
                    "priority": {"type": "string", "description": "Priority level", "default": "P3"},
                },
                "required": ["asset_id", "order_type", "description", "scheduled_date", "created_by"],
            },
        ),
        Tool(
            name="create_incident",
            description="Create SAP PM incident",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Asset ID"},
                    "fault_type": {"type": "string", "description": "Type of fault"},
                    "description": {"type": "string", "description": "Incident description"},
                    "reported_by": {"type": "string", "description": "Reporter username"},
                    "severity": {"type": "string", "description": "Severity level", "default": "P2"},
                },
                "required": ["asset_id", "fault_type", "description", "reported_by"],
            },
        ),
        # --- Materials Management (MM) Tools ---
        Tool(
            name="list_materials",
            description="List SAP MM materials",
            inputSchema={
                "type": "object",
                "properties": {
                    "storage_location": {"type": "string", "description": "Filter by storage location"},
                    "below_reorder": {"type": "boolean", "description": "Only show materials below reorder level", "default": False},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_material",
            description="Get SAP MM material by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {"type": "string", "description": "Material ID"},
                },
                "required": ["material_id"],
            },
        ),
        Tool(
            name="create_material",
            description="Create new SAP MM material",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Material description"},
                    "quantity": {"type": "integer", "description": "Initial quantity"},
                    "unit_of_measure": {"type": "string", "description": "Unit of measure"},
                    "reorder_level": {"type": "integer", "description": "Reorder level threshold"},
                    "storage_location": {"type": "string", "description": "Storage location"},
                    "material_id": {"type": "string", "description": "Optional material ID", "default": ""},
                },
                "required": ["description", "quantity", "unit_of_measure", "reorder_level", "storage_location"],
            },
        ),
        Tool(
            name="create_stock_transaction",
            description="Process SAP MM stock transaction (receipt, issue, transfer, adjustment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {"type": "string", "description": "Material ID"},
                    "quantity_change": {"type": "integer", "description": "Quantity change (positive or negative)"},
                    "transaction_type": {"type": "string", "description": "Transaction type (receipt, issue, transfer, adjustment)"},
                    "performed_by": {"type": "string", "description": "User performing the transaction"},
                    "reference_doc": {"type": "string", "description": "Reference document", "default": ""},
                    "notes": {"type": "string", "description": "Transaction notes", "default": ""},
                },
                "required": ["material_id", "quantity_change", "transaction_type", "performed_by"],
            },
        ),
        Tool(
            name="get_material_transaction_history",
            description="Get transaction history for a SAP MM material",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {"type": "string", "description": "Material ID"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": ["material_id"],
            },
        ),
        Tool(
            name="list_purchase_requisitions",
            description="List SAP MM purchase requisitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {"type": "string", "description": "Filter by material ID"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "cost_center_id": {"type": "string", "description": "Filter by cost center ID"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="create_purchase_requisition",
            description="Create SAP MM purchase requisition",
            inputSchema={
                "type": "object",
                "properties": {
                    "material_id": {"type": "string", "description": "Material ID"},
                    "quantity": {"type": "integer", "description": "Quantity to purchase"},
                    "cost_center_id": {"type": "string", "description": "Cost center ID"},
                    "justification": {"type": "string", "description": "Purchase justification"},
                    "requested_by": {"type": "string", "description": "Requester username"},
                },
                "required": ["material_id", "quantity", "cost_center_id", "justification", "requested_by"],
            },
        ),
        # --- Finance (FI) Tools ---
        Tool(
            name="list_cost_centers",
            description="List SAP FI cost centers",
            inputSchema={
                "type": "object",
                "properties": {
                    "fiscal_year": {"type": "integer", "description": "Filter by fiscal year", "default": 0},
                    "responsible_manager": {"type": "string", "description": "Filter by responsible manager"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_cost_center",
            description="Get SAP FI cost center by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost_center_id": {"type": "string", "description": "Cost center ID"},
                },
                "required": ["cost_center_id"],
            },
        ),
        Tool(
            name="create_cost_center",
            description="Create SAP FI cost center",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Cost center name"},
                    "budget_amount": {"type": "number", "description": "Budget amount"},
                    "fiscal_year": {"type": "integer", "description": "Fiscal year"},
                    "responsible_manager": {"type": "string", "description": "Responsible manager"},
                    "cost_center_id": {"type": "string", "description": "Optional cost center ID", "default": ""},
                    "description": {"type": "string", "description": "Cost center description", "default": ""},
                },
                "required": ["name", "budget_amount", "fiscal_year", "responsible_manager"],
            },
        ),
        Tool(
            name="list_cost_entries",
            description="List SAP FI cost entries",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost_center_id": {"type": "string", "description": "Filter by cost center ID"},
                    "ticket_id": {"type": "string", "description": "Filter by ticket ID"},
                    "cost_type": {"type": "string", "description": "Filter by cost type"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="create_cost_entry",
            description="Create SAP FI cost entry",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost_center_id": {"type": "string", "description": "Cost center ID"},
                    "amount": {"type": "number", "description": "Cost amount"},
                    "cost_type": {"type": "string", "description": "Type of cost"},
                    "created_by": {"type": "string", "description": "Creator username"},
                    "ticket_id": {"type": "string", "description": "Associated ticket ID", "default": ""},
                    "description": {"type": "string", "description": "Cost entry description", "default": ""},
                },
                "required": ["cost_center_id", "amount", "cost_type", "created_by"],
            },
        ),
        Tool(
            name="list_approval_requests",
            description="List SAP FI approval requests",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost_center_id": {"type": "string", "description": "Filter by cost center ID"},
                    "decision": {"type": "string", "description": "Filter by decision status"},
                    "requested_by": {"type": "string", "description": "Filter by requester"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="create_approval_request",
            description="Create SAP FI approval request",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost_center_id": {"type": "string", "description": "Cost center ID"},
                    "amount": {"type": "number", "description": "Requested amount"},
                    "justification": {"type": "string", "description": "Request justification"},
                    "requested_by": {"type": "string", "description": "Requester username"},
                },
                "required": ["cost_center_id", "amount", "justification", "requested_by"],
            },
        ),
        Tool(
            name="approve_request",
            description="Approve SAP FI approval request",
            inputSchema={
                "type": "object",
                "properties": {
                    "approval_id": {"type": "string", "description": "Approval request ID"},
                    "decided_by": {"type": "string", "description": "Approver username"},
                    "comment": {"type": "string", "description": "Approval comment", "default": ""},
                },
                "required": ["approval_id", "decided_by"],
            },
        ),
        Tool(
            name="reject_request",
            description="Reject SAP FI approval request",
            inputSchema={
                "type": "object",
                "properties": {
                    "approval_id": {"type": "string", "description": "Approval request ID"},
                    "decided_by": {"type": "string", "description": "Rejector username"},
                    "comment": {"type": "string", "description": "Rejection comment", "default": ""},
                },
                "required": ["approval_id", "decided_by"],
            },
        ),
        # --- Sales Tools ---
        Tool(
            name="list_sales_orders",
            description="List SAP sales orders",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status"},
                    "customer_id": {"type": "string", "description": "Filter by customer ID"},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                    "page_size": {"type": "integer", "description": "Items per page", "default": 20},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_sales_order",
            description="Get SAP sales order by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Sales order ID"},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="create_sales_order",
            description="Create SAP sales order. Items should be a list of dicts with line_item, material_id, description, quantity, unit_price, total",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "customer_name": {"type": "string", "description": "Customer name"},
                    "delivery_date": {"type": "string", "description": "Delivery date"},
                    "items": {"type": "array", "description": "List of order line items", "items": {"type": "object"}},
                    "currency": {"type": "string", "description": "Currency code", "default": "USD"},
                },
                "required": ["customer_id", "customer_name", "delivery_date", "items"],
            },
        ),
        Tool(
            name="update_sales_order",
            description="Update SAP sales order",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Sales order ID"},
                },
                "required": ["order_id"],
                "additionalProperties": True,
            },
        ),
        Tool(
            name="update_sales_order_status",
            description="Update SAP sales order status (new, processing, shipped, delivered, cancelled)",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Sales order ID"},
                    "status": {"type": "string", "description": "New status"},
                },
                "required": ["order_id", "status"],
            },
        ),
        # --- Work Order Flow Tools ---
        Tool(
            name="list_work_orders",
            description="List SAP work orders with optional filtering by status or customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "flow_status": {"type": "string", "description": "Filter by flow status"},
                    "customer_name": {"type": "string", "description": "Filter by customer name"},
                    "limit": {"type": "integer", "description": "Max results", "default": 20},
                    "offset": {"type": "integer", "description": "Result offset", "default": 0},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_work_order",
            description="Get SAP work order by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                },
                "required": ["work_order_id"],
            },
        ),
        Tool(
            name="create_work_order",
            description="Create SAP work order with materials for PM -> MM -> FI workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Work order title"},
                    "description": {"type": "string", "description": "Work order description"},
                    "customer_name": {"type": "string", "description": "Customer name"},
                    "site_location": {"type": "string", "description": "Site location"},
                    "requested_date": {"type": "string", "description": "Requested completion date"},
                    "cost_center_id": {"type": "string", "description": "Cost center ID"},
                    "created_by": {"type": "string", "description": "Creator username"},
                    "materials": {"type": "array", "description": "List of required materials", "items": {"type": "object"}},
                    "crm_reference_id": {"type": "string", "description": "CRM case reference ID", "default": ""},
                    "customer_contact": {"type": "string", "description": "Customer contact info", "default": ""},
                    "priority": {"type": "string", "description": "Priority level", "default": "medium"},
                    "assigned_to": {"type": "string", "description": "Assigned technician", "default": ""},
                },
                "required": ["title", "description", "customer_name", "site_location", "requested_date", "cost_center_id", "created_by", "materials"],
            },
        ),
        Tool(
            name="check_work_order_materials",
            description="Send work order to MM for material availability check",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "performed_by": {"type": "string", "description": "User performing the check"},
                },
                "required": ["work_order_id", "performed_by"],
            },
        ),
        Tool(
            name="request_work_order_purchase",
            description="MM raises FI ticket for purchasing materials that are not available",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "performed_by": {"type": "string", "description": "User performing the request"},
                    "justification": {"type": "string", "description": "Purchase justification", "default": ""},
                },
                "required": ["work_order_id", "performed_by"],
            },
        ),
        Tool(
            name="approve_work_order_purchase",
            description="FI approves or rejects work order purchase request",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "approved": {"type": "boolean", "description": "Whether to approve (true) or reject (false)"},
                    "decided_by": {"type": "string", "description": "Approver/rejector username"},
                    "comment": {"type": "string", "description": "Decision comment", "default": ""},
                },
                "required": ["work_order_id", "approved", "decided_by"],
            },
        ),
        Tool(
            name="proceed_work_order",
            description="Proceed with work order after materials confirmed available",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "performed_by": {"type": "string", "description": "User proceeding with the order"},
                },
                "required": ["work_order_id", "performed_by"],
            },
        ),
        Tool(
            name="start_work_order",
            description="Start working on work order",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "performed_by": {"type": "string", "description": "User starting the work"},
                    "scheduled_date": {"type": "string", "description": "Scheduled start date", "default": ""},
                },
                "required": ["work_order_id", "performed_by"],
            },
        ),
        Tool(
            name="complete_work_order",
            description="Complete work order",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "performed_by": {"type": "string", "description": "User completing the work"},
                },
                "required": ["work_order_id", "performed_by"],
            },
        ),
        Tool(
            name="get_work_order_history",
            description="Get flow history for a work order (PM -> MM -> FI transitions)",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                },
                "required": ["work_order_id"],
            },
        ),
        Tool(
            name="get_pending_purchase_work_orders",
            description="Get work orders pending purchase request (materials shortage)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_pending_approval_work_orders",
            description="Get work orders pending FI approval",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        # --- CRM Integration Tools ---
        Tool(
            name="sync_crm_case",
            description="Sync a CRM case (e.g., from Salesforce) to SAP as a work order",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "CRM case ID"},
                    "case_number": {"type": "string", "description": "CRM case number"},
                    "subject": {"type": "string", "description": "Case subject"},
                    "description": {"type": "string", "description": "Case description"},
                    "account_name": {"type": "string", "description": "Account/customer name"},
                    "site_address": {"type": "string", "description": "Site address"},
                    "priority": {"type": "string", "description": "Case priority", "default": "Medium"},
                    "materials": {"type": "array", "description": "Required materials list", "items": {"type": "object"}, "default": []},
                    "contact_name": {"type": "string", "description": "Contact person name", "default": ""},
                    "owner_name": {"type": "string", "description": "Case owner name", "default": ""},
                    "cost_center_id": {"type": "string", "description": "Cost center ID", "default": "CC-DEFAULT"},
                    "operation": {"type": "string", "description": "Sync operation (CREATE, UPDATE)", "default": "CREATE"},
                },
                "required": ["case_id", "case_number", "subject", "description", "account_name", "site_address"],
            },
        ),
        Tool(
            name="get_crm_case_status",
            description="Get SAP work order status for a CRM case",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "CRM case ID"},
                },
                "required": ["case_id"],
            },
        ),
        Tool(
            name="crm_integration_health",
            description="Check CRM integration health",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        # --- Appointment Validation Tools ---
        Tool(
            name="validate_appointment",
            description="Validate appointment request against SAP master data. Checks parts availability and location. Used by agent for appointment approval decisions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "required_parts": {"type": "string", "description": "Required parts for the appointment"},
                    "location": {"type": "string", "description": "Appointment location"},
                },
                "required": ["required_parts", "location"],
            },
        ),
        Tool(
            name="search_materials_by_query",
            description="Search for materials in SAP inventory by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="find_available_technicians",
            description="Find available engineers/technicians with optional skill filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "required_skills": {"type": "string", "description": "Filter by required skills", "default": ""},
                },
                "required": [],
            },
        ),
        Tool(
            name="search_location_assets",
            description="Search for assets/locations in SAP by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location name or ID to search"},
                },
                "required": ["location"],
            },
        ),
        Tool(
            name="get_material_recommendations",
            description="Get recommended materials for common appointment types",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="reserve_materials_for_work_order",
            description="Reserve materials from inventory for a work order",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "material_id": {"type": "string", "description": "Material ID to reserve"},
                    "quantity": {"type": "integer", "description": "Quantity to reserve"},
                    "required_date": {"type": "string", "description": "Date materials are required", "default": ""},
                },
                "required": ["work_order_id", "material_id", "quantity"],
            },
        ),
        Tool(
            name="update_work_order_status",
            description="Update work order status and add notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "Work order ID"},
                    "status": {"type": "string", "description": "New status"},
                    "updated_by": {"type": "string", "description": "User making the update"},
                    "notes": {"type": "string", "description": "Status update notes", "default": ""},
                },
                "required": ["work_order_id", "status", "updated_by"],
            },
        ),
        # --- Health Check ---
        Tool(
            name="sap_health_check",
            description="Check SAP backend health",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Dispatch tool calls to the correct function by name"""
    if name not in TOOL_DISPATCH:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    func = TOOL_DISPATCH[name]

    # Special handling for update_sales_order which uses **kwargs
    if name == "update_sales_order":
        order_id = arguments.pop("order_id", "")
        return await func(order_id, **arguments)

    return await func(**arguments)


# ============================================================================
# SERVER STARTUP
# ============================================================================

def run_http_server():
    """Run MCP server in HTTP/SSE mode for remote connections"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
        middleware=middleware,
    )

    print(f"Starting SAP MCP server in HTTP mode")
    print(f"  Host: {MCP_HOST}")
    print(f"  Port: {MCP_PORT}")
    print(f"  API Backend: {API_BASE_URL}")
    print(f"  SSE Endpoint: http://207.180.217.117:{MCP_PORT}/sse")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


def run_stdio_server():
    """Run MCP server in stdio mode for local use"""
    print("Starting SAP MCP server in stdio mode")
    server.run()


if __name__ == "__main__":
    import sys

    if "--stdio" in sys.argv:
        run_stdio_server()
    else:
        run_http_server()
