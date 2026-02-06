#!/usr/bin/env python3
"""
MCP Server for SAP ERP Integration
Provides tools to interact with SAP modules: PM, MM, FI, Sales, and Tickets
"""

import json
import httpx
from typing import Optional
from mcp.server import Server
from mcp.types import TextContent

# SAP Backend Configuration
API_BASE_URL = "http://149.102.158.71:4798"
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

@server.call_tool()
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


@server.call_tool()
async def sap_refresh_token(token: str):
    """Refresh SAP JWT token"""
    result = await api_call("POST", "/api/v1/auth/refresh", {"token": token})
    if "access_token" in result:
        set_token(result["access_token"])
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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

@server.call_tool()
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


@server.call_tool()
async def get_ticket(ticket_id: str):
    """Get SAP ticket by ID"""
    result = await api_call("GET", f"/api/v1/tickets/{ticket_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
async def get_ticket_audit_trail(ticket_id: str):
    """Get audit trail for a SAP ticket"""
    result = await api_call("GET", f"/api/v1/tickets/{ticket_id}/audit")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# PLANT MAINTENANCE (PM) TOOLS
# ============================================================================

@server.call_tool()
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


@server.call_tool()
async def get_asset(asset_id: str):
    """Get SAP PM asset by ID"""
    result = await api_call("GET", f"/api/v1/pm/assets/{asset_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
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

@server.call_tool()
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


@server.call_tool()
async def get_material(material_id: str):
    """Get SAP MM material by ID"""
    result = await api_call("GET", f"/api/v1/mm/materials/{material_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
async def get_material_transaction_history(
    material_id: str,
    limit: int = 20,
    offset: int = 0,
):
    """Get transaction history for a SAP MM material"""
    params = {"limit": limit, "offset": offset}
    result = await api_call("GET", f"/api/v1/mm/materials/{material_id}/transactions", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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

@server.call_tool()
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


@server.call_tool()
async def get_cost_center(cost_center_id: str):
    """Get SAP FI cost center by ID"""
    result = await api_call("GET", f"/api/v1/fi/cost-centers/{cost_center_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
async def approve_request(approval_id: str, decided_by: str, comment: str = ""):
    """Approve SAP FI approval request"""
    data = {"decided_by": decided_by, "comment": comment}
    result = await api_call("POST", f"/api/v1/fi/approval-requests/{approval_id}/approve", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def reject_request(approval_id: str, decided_by: str, comment: str = ""):
    """Reject SAP FI approval request"""
    data = {"decided_by": decided_by, "comment": comment}
    result = await api_call("POST", f"/api/v1/fi/approval-requests/{approval_id}/reject", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SALES TOOLS
# ============================================================================

@server.call_tool()
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


@server.call_tool()
async def get_sales_order(order_id: str):
    """Get SAP sales order by ID"""
    result = await api_call("GET", f"/api/sales/orders/{order_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
async def update_sales_order(order_id: str, **kwargs):
    """Update SAP sales order"""
    result = await api_call("PUT", f"/api/sales/orders/{order_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_sales_order_status(order_id: str, status: str):
    """Update SAP sales order status (new, processing, shipped, delivered, cancelled)"""
    data = {"status": status}
    result = await api_call("PATCH", f"/api/sales/orders/{order_id}/status", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# WORK ORDER FLOW TOOLS (PM → MM → FI Integration)
# ============================================================================

@server.call_tool()
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


@server.call_tool()
async def get_work_order(work_order_id: str):
    """Get SAP work order by ID"""
    result = await api_call("GET", f"/api/v1/work-order-flow/work-orders/{work_order_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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
    """Create SAP work order with materials for PM → MM → FI workflow"""
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


@server.call_tool()
async def check_work_order_materials(work_order_id: str, performed_by: str):
    """Send work order to MM for material availability check"""
    data = {"performed_by": performed_by}
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/check-materials", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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


@server.call_tool()
async def proceed_work_order(work_order_id: str, performed_by: str):
    """Proceed with work order after materials confirmed available"""
    data = {"performed_by": performed_by}
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/proceed", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
async def complete_work_order(work_order_id: str, performed_by: str):
    """Complete work order"""
    data = {"performed_by": performed_by}
    result = await api_call("POST", f"/api/v1/work-order-flow/work-orders/{work_order_id}/complete", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_work_order_history(work_order_id: str):
    """Get flow history for a work order (PM → MM → FI transitions)"""
    result = await api_call("GET", f"/api/v1/work-order-flow/work-orders/{work_order_id}/history")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_pending_purchase_work_orders():
    """Get work orders pending purchase request (materials shortage)"""
    result = await api_call("GET", "/api/v1/work-order-flow/work-orders/pending-purchase")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_pending_approval_work_orders():
    """Get work orders pending FI approval"""
    result = await api_call("GET", "/api/v1/work-order-flow/work-orders/pending-approval")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# CRM INTEGRATION TOOLS
# ============================================================================

@server.call_tool()
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


@server.call_tool()
async def get_crm_case_status(case_id: str):
    """Get SAP work order status for a CRM case"""
    result = await api_call("GET", f"/api/v1/crm-integration/case-status/{case_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def crm_integration_health():
    """Check CRM integration health"""
    result = await api_call("GET", "/api/v1/crm-integration/health")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# APPOINTMENT VALIDATION TOOLS (For Agent)
# ============================================================================

@server.call_tool()
async def validate_appointment(
    required_parts: str,
    required_skills: str,
    location: str,
    cost_center_id: str,
    estimated_cost: float,
):
    """
    Validate appointment request against SAP master data.
    Checks parts availability, technician skills, location, and budget.
    Used by agent for appointment approval decisions.
    """
    data = {
        "required_parts": required_parts,
        "required_skills": required_skills,
        "location": location,
        "cost_center_id": cost_center_id,
        "estimated_cost": estimated_cost,
    }
    result = await api_call("POST", "/api/appointments/validate", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def search_materials_by_query(query: str):
    """Search for materials in SAP inventory by keyword"""
    result = await api_call("GET", "/api/appointments/parts/search", params={"query": query})
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def find_available_technicians(required_skills: str = ""):
    """Find available engineers/technicians with optional skill filtering"""
    params = {}
    if required_skills:
        params["skill"] = required_skills
    result = await api_call("GET", "/api/appointments/technicians/available", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def validate_technician_skills(required_skills: str):
    """Check if technicians with required skills are available"""
    result = await api_call(
        "GET",
        "/api/appointments/technicians/validate",
        params={"required_skills": required_skills}
    )
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def search_location_assets(location: str):
    """Search for assets/locations in SAP by name or ID"""
    result = await api_call(
        "GET",
        "/api/appointments/locations/search",
        params={"location": location}
    )
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def check_cost_center_budget(cost_center_id: str, estimated_cost: float):
    """Verify if cost center has sufficient budget for estimated cost"""
    result = await api_call(
        "GET",
        "/api/appointments/budget/check",
        params={"cost_center_id": cost_center_id, "estimated_cost": estimated_cost}
    )
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_material_recommendations():
    """Get recommended materials for common appointment types"""
    result = await api_call("GET", "/api/appointments/materials/recommendations")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
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


@server.call_tool()
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

@server.call_tool()
async def sap_health_check():
    """Check SAP backend health"""
    try:
        result = await api_call("GET", "/health")
        return [TextContent(type="text", text=json.dumps({"status": "healthy", "details": result}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"status": "unhealthy", "error": str(e)}))]


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
    print(f"  SSE Endpoint: http://149.102.158.71:{MCP_PORT}/sse")
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
