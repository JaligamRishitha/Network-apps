#!/usr/bin/env python3
"""
Unified MCP Server - Enterprise Integration Hub
Connects Salesforce, MuleSoft, ServiceNow, and SAP MCP servers
Provides a single interface for cross-platform operations
"""

import json
import httpx
from typing import Optional
from mcp.server import Server
from mcp.types import TextContent

# ============================================================================
# CONFIGURATION
# ============================================================================


# Service endpoints configuration
SERVICES = {
    "salesforce": {
        "name": "Salesforce CRM",
        "base_url": "http://149.102.158.71:4799",
        "description": "CRM operations - Contacts, Accounts, Leads, Opportunities, Cases",
    },
    "mulesoft": {
        "name": "MuleSoft Integration",
        "base_url": "http://149.102.158.71:4797",
        "description": "SAP integration via MuleSoft - Case sync, batch operations",
    },
    "servicenow": {
        "name": "ServiceNow ITSM",
        "base_url": "http://149.102.158.71:4780",
        "description": "IT Service Management - Incidents, Changes, Problems, CMDB",
    },
    "sap": {
        "name": "SAP ERP",
        "base_url": "http://149.102.158.71:4798",
        "description": "ERP operations - PM, MM, FI, Sales, Tickets",
    },
}

# Authentication tokens for each service
TOKENS = {
    "salesforce": None,
    "mulesoft": None,
    "servicenow": None,
    "sap": None,
}

# ServiceNow credentials
SERVICENOW_USER = "admin"
SERVICENOW_PASSWORD = "password"

server = Server("unified-enterprise-hub")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def set_token(service: str, token: str):
    """Set authentication token for a specific service"""
    global TOKENS
    if service in TOKENS:
        TOKENS[service] = token


async def api_call(
    service: str,
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """Make API call to specified service"""
    if service not in SERVICES:
        return {"error": f"Unknown service: {service}"}

    base_url = SERVICES[service]["base_url"]
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # Add authentication
    auth = None
    if service == "servicenow":
        auth = (SERVICENOW_USER, SERVICENOW_PASSWORD)
    elif TOKENS.get(service):
        headers["Authorization"] = f"Bearer {TOKENS[service]}"

    url = f"{base_url}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0, auth=auth) as client:
        try:
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
                return {"error": f"Unsupported method: {method}"}

            if response.status_code >= 400:
                return {
                    "error": f"{service.upper()} API Error {response.status_code}",
                    "details": response.text,
                }
            return response.json()
        except Exception as e:
            return {"error": f"Connection error to {service}", "details": str(e)}


# ============================================================================
# SERVICE DISCOVERY & HEALTH
# ============================================================================

@server.call_tool()
async def list_services():
    """List all available enterprise services and their capabilities"""
    return [TextContent(type="text", text=json.dumps(SERVICES, indent=2))]


@server.call_tool()
async def health_check_all():
    """Check health status of all connected services"""
    results = {}

    # Salesforce health
    try:
        sf_result = await api_call("salesforce", "GET", "/api/health")
        results["salesforce"] = {"status": "healthy" if "error" not in sf_result else "unhealthy", "details": sf_result}
    except Exception as e:
        results["salesforce"] = {"status": "unhealthy", "error": str(e)}

    # MuleSoft health
    try:
        ms_result = await api_call("mulesoft", "GET", "/api/sap-integration/health")
        results["mulesoft"] = {"status": "healthy" if "error" not in ms_result else "unhealthy", "details": ms_result}
    except Exception as e:
        results["mulesoft"] = {"status": "unhealthy", "error": str(e)}

    # ServiceNow health
    try:
        sn_result = await api_call("servicenow", "GET", "/api/now/table/sys_user?sysparm_limit=1")
        results["servicenow"] = {"status": "healthy" if "error" not in sn_result else "unhealthy", "details": "Connected"}
    except Exception as e:
        results["servicenow"] = {"status": "unhealthy", "error": str(e)}

    # SAP health
    try:
        sap_result = await api_call("sap", "GET", "/api/health")
        results["sap"] = {"status": "healthy" if "error" not in sap_result else "unhealthy", "details": sap_result}
    except Exception as e:
        results["sap"] = {"status": "unhealthy", "error": str(e)}

    return [TextContent(type="text", text=json.dumps(results, indent=2))]


# ============================================================================
# UNIFIED AUTHENTICATION
# ============================================================================

@server.call_tool()
async def login_salesforce(username: str, password: str):
    """Login to Salesforce CRM"""
    result = await api_call("salesforce", "POST", "/api/auth/login", {"username": username, "password": password})
    if "access_token" in result:
        set_token("salesforce", result["access_token"])
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def login_sap(username: str, password: str):
    """Login to SAP ERP"""
    result = await api_call("sap", "POST", "/api/auth/login", {"username": username, "password": password})
    if "access_token" in result:
        set_token("sap", result["access_token"])
        set_token("mulesoft", result["access_token"])  # MuleSoft uses same backend
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def configure_servicenow(instance_url: str, username: str, password: str):
    """Configure ServiceNow credentials"""
    global SERVICENOW_USER, SERVICENOW_PASSWORD
    SERVICES["servicenow"]["base_url"] = instance_url
    SERVICENOW_USER = username
    SERVICENOW_PASSWORD = password
    return [TextContent(type="text", text=json.dumps({"status": "configured", "instance": instance_url}))]


# ============================================================================
# SALESFORCE OPERATIONS
# ============================================================================

@server.call_tool()
async def sf_list_contacts(skip: int = 0, limit: int = 50, search: str = ""):
    """List Salesforce contacts"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("salesforce", "GET", "/api/contacts", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_get_contact(contact_id: int):
    """Get Salesforce contact by ID"""
    result = await api_call("salesforce", "GET", f"/api/contacts/{contact_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_create_contact(first_name: str, last_name: str, email: str = "", phone: str = "", account_id: int = 0):
    """Create Salesforce contact"""
    data = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone}
    if account_id:
        data["account_id"] = account_id
    result = await api_call("salesforce", "POST", "/api/contacts", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_list_accounts(skip: int = 0, limit: int = 50, search: str = ""):
    """List Salesforce accounts"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("salesforce", "GET", "/api/accounts", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_list_leads(skip: int = 0, limit: int = 50, search: str = ""):
    """List Salesforce leads"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("salesforce", "GET", "/api/leads", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_list_opportunities(skip: int = 0, limit: int = 50, search: str = ""):
    """List Salesforce opportunities"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("salesforce", "GET", "/api/opportunities", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_list_cases(skip: int = 0, limit: int = 50, search: str = ""):
    """List Salesforce cases"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("salesforce", "GET", "/api/cases", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_get_dashboard_stats():
    """Get Salesforce dashboard statistics"""
    result = await api_call("salesforce", "GET", "/api/dashboard/stats")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sf_global_search(query: str):
    """Global search across all Salesforce objects"""
    result = await api_call("salesforce", "GET", "/api/dashboard/search", params={"q": query})
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# MULESOFT INTEGRATION OPERATIONS
# ============================================================================

@server.call_tool()
async def ms_sync_case_to_sap(case_id: int, operation: str = "CREATE"):
    """Sync Salesforce case to SAP via MuleSoft"""
    result = await api_call("mulesoft", "POST", "/api/sap-integration/cases/sync", {"case_id": case_id, "operation": operation})
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def ms_sync_cases_batch(case_ids: list, operation: str = "CREATE"):
    """Batch sync multiple cases to SAP via MuleSoft"""
    result = await api_call("mulesoft", "POST", "/api/sap-integration/cases/sync-batch", {"case_ids": case_ids, "operation": operation})
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def ms_get_case_sync_status(case_id: int):
    """Get case synchronization status from MuleSoft"""
    result = await api_call("mulesoft", "GET", f"/api/sap-integration/cases/{case_id}/sync-status")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def ms_get_sap_case_status(sap_case_id: str):
    """Query case status from SAP via MuleSoft"""
    result = await api_call("mulesoft", "POST", "/api/sap-integration/sap-cases/status", {"sap_case_id": sap_case_id})
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVICENOW OPERATIONS
# ============================================================================

@server.call_tool()
async def sn_list_incidents(skip: int = 0, limit: int = 50, query: str = ""):
    """List ServiceNow incidents"""
    params = {"sysparm_offset": skip, "sysparm_limit": limit}
    if query:
        params["sysparm_query"] = query
    result = await api_call("servicenow", "GET", "/api/now/table/incident", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_get_incident(incident_id: str):
    """Get ServiceNow incident by ID"""
    result = await api_call("servicenow", "GET", f"/api/now/table/incident/{incident_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_create_incident(short_description: str, description: str = "", priority: str = "3", urgency: str = "3", impact: str = "3"):
    """Create ServiceNow incident"""
    data = {
        "short_description": short_description,
        "description": description,
        "priority": priority,
        "urgency": urgency,
        "impact": impact,
    }
    result = await api_call("servicenow", "POST", "/api/now/table/incident", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_update_incident(incident_id: str, **kwargs):
    """Update ServiceNow incident"""
    result = await api_call("servicenow", "PUT", f"/api/now/table/incident/{incident_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_list_change_requests(skip: int = 0, limit: int = 50):
    """List ServiceNow change requests"""
    params = {"sysparm_offset": skip, "sysparm_limit": limit}
    result = await api_call("servicenow", "GET", "/api/now/table/change_request", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_create_change_request(short_description: str, description: str = "", type: str = "normal", priority: str = "3"):
    """Create ServiceNow change request"""
    data = {"short_description": short_description, "description": description, "type": type, "priority": priority}
    result = await api_call("servicenow", "POST", "/api/now/table/change_request", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_list_problems(skip: int = 0, limit: int = 50):
    """List ServiceNow problems"""
    params = {"sysparm_offset": skip, "sysparm_limit": limit}
    result = await api_call("servicenow", "GET", "/api/now/table/problem", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sn_search_knowledge_base(query: str, limit: int = 10):
    """Search ServiceNow knowledge base"""
    params = {"sysparm_query": f"short_descriptionLIKE{query}", "sysparm_limit": limit}
    result = await api_call("servicenow", "GET", "/api/now/table/kb_knowledge", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SAP OPERATIONS
# ============================================================================

# Tickets
@server.call_tool()
async def sap_list_tickets(module: str = "", status: str = "", priority: str = "", page: int = 1, limit: int = 20):
    """List SAP tickets"""
    params = {"page": page, "limit": limit}
    if module:
        params["module"] = module
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    result = await api_call("sap", "GET", "/api/tickets", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_get_ticket(ticket_id: str):
    """Get SAP ticket by ID"""
    result = await api_call("sap", "GET", f"/api/tickets/{ticket_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_create_ticket(module: str, ticket_type: str, priority: str, title: str, created_by: str, description: str = ""):
    """Create SAP ticket"""
    data = {"module": module, "ticket_type": ticket_type, "priority": priority, "title": title, "created_by": created_by, "description": description}
    result = await api_call("sap", "POST", "/api/tickets", data)
    return [TextContent(type="text", text=json.dumps(result))]


# Plant Maintenance
@server.call_tool()
async def sap_list_assets(asset_type: str = "", status: str = "", limit: int = 20, offset: int = 0):
    """List SAP PM assets"""
    params = {"limit": limit, "offset": offset}
    if asset_type:
        params["asset_type"] = asset_type
    if status:
        params["status"] = status
    result = await api_call("sap", "GET", "/api/pm/assets", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_create_asset(asset_type: str, name: str, location: str, installation_date: str, status: str = "operational", description: str = ""):
    """Create SAP PM asset"""
    data = {"asset_type": asset_type, "name": name, "location": location, "installation_date": installation_date, "status": status, "description": description}
    result = await api_call("sap", "POST", "/api/pm/assets", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_list_maintenance_orders(asset_id: str = "", status: str = "", limit: int = 20, offset: int = 0):
    """List SAP PM maintenance orders"""
    params = {"limit": limit, "offset": offset}
    if asset_id:
        params["asset_id"] = asset_id
    if status:
        params["status"] = status
    result = await api_call("sap", "GET", "/api/pm/maintenance-orders", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_create_maintenance_order(asset_id: str, order_type: str, description: str, scheduled_date: str, created_by: str, priority: str = "P3"):
    """Create SAP PM maintenance order"""
    data = {"asset_id": asset_id, "order_type": order_type, "description": description, "scheduled_date": scheduled_date, "created_by": created_by, "priority": priority}
    result = await api_call("sap", "POST", "/api/pm/maintenance-orders", data)
    return [TextContent(type="text", text=json.dumps(result))]


# Materials Management
@server.call_tool()
async def sap_list_materials(storage_location: str = "", below_reorder: bool = False, limit: int = 20, offset: int = 0):
    """List SAP MM materials"""
    params = {"limit": limit, "offset": offset, "below_reorder": below_reorder}
    if storage_location:
        params["storage_location"] = storage_location
    result = await api_call("sap", "GET", "/api/mm/materials", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_create_material(description: str, quantity: int, unit_of_measure: str, reorder_level: int, storage_location: str):
    """Create SAP MM material"""
    data = {"description": description, "quantity": quantity, "unit_of_measure": unit_of_measure, "reorder_level": reorder_level, "storage_location": storage_location}
    result = await api_call("sap", "POST", "/api/mm/materials", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_create_stock_transaction(material_id: str, quantity_change: int, transaction_type: str, performed_by: str, reference_doc: str = "", notes: str = ""):
    """Create SAP MM stock transaction"""
    data = {"material_id": material_id, "quantity_change": quantity_change, "transaction_type": transaction_type, "performed_by": performed_by, "reference_doc": reference_doc, "notes": notes}
    result = await api_call("sap", "POST", "/api/mm/stock-transactions", data)
    return [TextContent(type="text", text=json.dumps(result))]


# Finance
@server.call_tool()
async def sap_list_cost_centers(fiscal_year: int = 0, responsible_manager: str = "", limit: int = 20, offset: int = 0):
    """List SAP FI cost centers"""
    params = {"limit": limit, "offset": offset}
    if fiscal_year:
        params["fiscal_year"] = fiscal_year
    if responsible_manager:
        params["responsible_manager"] = responsible_manager
    result = await api_call("sap", "GET", "/api/fi/cost-centers", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_create_cost_entry(cost_center_id: str, amount: float, cost_type: str, created_by: str, description: str = ""):
    """Create SAP FI cost entry"""
    data = {"cost_center_id": cost_center_id, "amount": amount, "cost_type": cost_type, "created_by": created_by, "description": description}
    result = await api_call("sap", "POST", "/api/fi/cost-entries", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_list_approval_requests(cost_center_id: str = "", decision: str = "", limit: int = 20, offset: int = 0):
    """List SAP FI approval requests"""
    params = {"limit": limit, "offset": offset}
    if cost_center_id:
        params["cost_center_id"] = cost_center_id
    if decision:
        params["decision"] = decision
    result = await api_call("sap", "GET", "/api/fi/approval-requests", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_approve_request(approval_id: str, decided_by: str, comment: str = ""):
    """Approve SAP FI request"""
    data = {"decided_by": decided_by, "comment": comment}
    result = await api_call("sap", "POST", f"/api/fi/approval-requests/{approval_id}/approve", data)
    return [TextContent(type="text", text=json.dumps(result))]


# Sales
@server.call_tool()
async def sap_list_sales_orders(status: str = "", customer_id: str = "", page: int = 1, page_size: int = 20):
    """List SAP sales orders"""
    params = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if customer_id:
        params["customer_id"] = customer_id
    result = await api_call("sap", "GET", "/api/sales/orders", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def sap_get_sales_order(order_id: str):
    """Get SAP sales order by ID"""
    result = await api_call("sap", "GET", f"/api/sales/orders/{order_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# CROSS-PLATFORM OPERATIONS
# ============================================================================

@server.call_tool()
async def cross_platform_search(query: str):
    """Search across all platforms for matching records"""
    results = {
        "query": query,
        "salesforce": None,
        "servicenow": None,
        "sap": None,
    }

    # Search Salesforce
    try:
        sf_result = await api_call("salesforce", "GET", "/api/dashboard/search", params={"q": query})
        results["salesforce"] = sf_result
    except Exception as e:
        results["salesforce"] = {"error": str(e)}

    # Search ServiceNow knowledge base
    try:
        sn_result = await api_call("servicenow", "GET", "/api/now/table/kb_knowledge", params={"sysparm_query": f"short_descriptionLIKE{query}", "sysparm_limit": 10})
        results["servicenow"] = sn_result
    except Exception as e:
        results["servicenow"] = {"error": str(e)}

    # Search SAP tickets
    try:
        sap_result = await api_call("sap", "GET", "/api/tickets", params={"page": 1, "limit": 10})
        results["sap"] = sap_result
    except Exception as e:
        results["sap"] = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(results, indent=2))]


@server.call_tool()
async def create_incident_all_platforms(
    title: str,
    description: str,
    priority: str = "3",
    created_by: str = "system",
):
    """Create incident/case/ticket across all platforms simultaneously"""
    results = {
        "title": title,
        "salesforce_case": None,
        "servicenow_incident": None,
        "sap_ticket": None,
    }

    # Create Salesforce case
    try:
        sf_result = await api_call("salesforce", "POST", "/api/cases", {
            "subject": title,
            "description": description,
            "priority": "High" if priority in ["1", "2"] else "Medium",
            "status": "New",
            "contact_id": 1,
        })
        results["salesforce_case"] = sf_result
    except Exception as e:
        results["salesforce_case"] = {"error": str(e)}

    # Create ServiceNow incident
    try:
        sn_result = await api_call("servicenow", "POST", "/api/now/table/incident", {
            "short_description": title,
            "description": description,
            "priority": priority,
            "urgency": priority,
            "impact": priority,
        })
        results["servicenow_incident"] = sn_result
    except Exception as e:
        results["servicenow_incident"] = {"error": str(e)}

    # Create SAP ticket
    try:
        sap_result = await api_call("sap", "POST", "/api/tickets", {
            "module": "PM",
            "ticket_type": "incident",
            "priority": f"P{priority}",
            "title": title,
            "description": description,
            "created_by": created_by,
        })
        results["sap_ticket"] = sap_result
    except Exception as e:
        results["sap_ticket"] = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(results, indent=2))]


@server.call_tool()
async def sync_salesforce_case_to_all(case_id: int):
    """Sync a Salesforce case to SAP (via MuleSoft) and create corresponding ServiceNow incident"""
    results = {
        "case_id": case_id,
        "mulesoft_sync": None,
        "servicenow_incident": None,
    }

    # Get case details first
    case_details = await api_call("salesforce", "GET", f"/api/cases/{case_id}")

    if "error" in case_details:
        return [TextContent(type="text", text=json.dumps({"error": "Failed to fetch case", "details": case_details}))]

    # Sync to SAP via MuleSoft
    try:
        ms_result = await api_call("mulesoft", "POST", "/api/sap-integration/cases/sync", {"case_id": case_id, "operation": "CREATE"})
        results["mulesoft_sync"] = ms_result
    except Exception as e:
        results["mulesoft_sync"] = {"error": str(e)}

    # Create ServiceNow incident
    try:
        sn_result = await api_call("servicenow", "POST", "/api/now/table/incident", {
            "short_description": case_details.get("subject", f"Case #{case_id}"),
            "description": case_details.get("description", ""),
            "priority": "2" if case_details.get("priority") == "High" else "3",
        })
        results["servicenow_incident"] = sn_result
    except Exception as e:
        results["servicenow_incident"] = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(results, indent=2))]


@server.call_tool()
async def get_enterprise_dashboard():
    """Get unified dashboard with stats from all platforms"""
    dashboard = {
        "salesforce": None,
        "servicenow": None,
        "sap": None,
    }

    # Salesforce stats
    try:
        sf_stats = await api_call("salesforce", "GET", "/api/dashboard/stats")
        dashboard["salesforce"] = sf_stats
    except Exception as e:
        dashboard["salesforce"] = {"error": str(e)}

    # ServiceNow incident count
    try:
        sn_incidents = await api_call("servicenow", "GET", "/api/now/table/incident", params={"sysparm_limit": 1})
        dashboard["servicenow"] = {"incidents": "connected" if "error" not in sn_incidents else "error"}
    except Exception as e:
        dashboard["servicenow"] = {"error": str(e)}

    # SAP tickets
    try:
        sap_tickets = await api_call("sap", "GET", "/api/tickets", params={"page": 1, "limit": 1})
        dashboard["sap"] = {"tickets_total": sap_tickets.get("total", 0) if "error" not in sap_tickets else "error"}
    except Exception as e:
        dashboard["sap"] = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(dashboard, indent=2))]


# ============================================================================
# NOTIFICATION & HELPER TOOLS
# ============================================================================

@server.call_tool()
async def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = ""):
    """
    Send email notification to engineer, manager, or customer.
    Used by orchestrator to notify stakeholders about work orders.
    """
    # Mock email sending (in production, would use SMTP/SendGrid/AWS SES)
    result = {
        "status": "sent",
        "to": to,
        "subject": subject,
        "body_preview": body[:100] + "..." if len(body) > 100 else body,
        "timestamp": "2026-02-05T21:00:00Z",
        "mode": "mock"
    }
    if cc:
        result["cc"] = cc
    if bcc:
        result["bcc"] = bcc

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@server.call_tool()
async def send_sms(phone: str, message: str):
    """
    Send SMS alert to engineer or manager.
    Used for urgent notifications and emergency callouts.
    """
    # Mock SMS sending (in production, would use Twilio/AWS SNS)
    result = {
        "status": "sent",
        "phone": phone,
        "message": message,
        "timestamp": "2026-02-05T21:00:00Z",
        "mode": "mock"
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@server.call_tool()
async def log_event(event_type: str, event_data: dict, source: str = "orchestrator"):
    """
    Log workflow event for audit trail and monitoring.
    Tracks all actions taken by orchestrator and agent.
    """
    result = {
        "logged": True,
        "event_type": event_type,
        "source": source,
        "timestamp": "2026-02-05T21:00:00Z",
        "event_id": f"EVT-{hash(str(event_data)) % 100000:05d}",
        "data": event_data
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@server.call_tool()
async def escalate_to_human(
    reason: str,
    priority: str,
    context: dict,
    notify_managers: bool = True
):
    """
    Escalate issue to human operator when agent cannot handle automatically.
    Used when validation fails, budget exceeded, or manual review required.
    """
    result = {
        "escalated": True,
        "reason": reason,
        "priority": priority,
        "timestamp": "2026-02-05T21:00:00Z",
        "escalation_id": f"ESC-{hash(reason) % 100000:05d}",
        "context": context,
        "notifications_sent": notify_managers,
        "assigned_to_queue": "operations_team"
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@server.call_tool()
async def get_workflow_status(workflow_id: str):
    """
    Get current status of a workflow execution.
    Tracks progress through Salesforce → ServiceNow → SAP → Agent → Orchestrator.
    """
    # Mock workflow status
    result = {
        "workflow_id": workflow_id,
        "status": "in_progress",
        "current_stage": "agent_validation",
        "stages": [
            {"name": "salesforce_request", "status": "completed", "timestamp": "2026-02-05T20:00:00Z"},
            {"name": "servicenow_ticket", "status": "completed", "timestamp": "2026-02-05T20:01:00Z"},
            {"name": "agent_validation", "status": "in_progress", "timestamp": "2026-02-05T20:02:00Z"},
            {"name": "sap_order_creation", "status": "pending", "timestamp": None},
        ],
        "mode": "mock"
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(main())
