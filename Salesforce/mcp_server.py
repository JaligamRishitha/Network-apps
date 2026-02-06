#!/usr/bin/env python3
"""
MCP Server for Salesforce Clone Backend
Provides tools to interact with all CRM objects and operations

Runs in HTTP mode by default for remote connections.
Use --stdio flag for local stdio mode.
"""

import json
import httpx
import asyncio
import os
from typing import Any, Optional
from mcp.server import Server
from mcp.types import TextContent

# Configuration from environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "http://149.102.158.71:4799")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8090"))
DEFAULT_TOKEN = None

server = Server("salesforce-crm")


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
    """Make authenticated API call to backend"""
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
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            return {
                "error": f"API Error {response.status_code}",
                "details": response.text,
            }
        return response.json()


# ============================================================================
# AUTHENTICATION TOOLS
# ============================================================================

@server.call_tool()
async def login(username: str, password: str):
    """Login to get JWT token"""
    result = await api_call(
        "POST",
        "/api/auth/login",
        {"username": username, "password": password},
    )
    if "access_token" in result:
        set_token(result["access_token"])
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_current_user():
    """Get current authenticated user"""
    result = await api_call("GET", "/api/auth/me")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def list_users():
    """List all users"""
    result = await api_call("GET", "/api/auth/users")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# CONTACTS TOOLS
# ============================================================================

@server.call_tool()
async def list_contacts(skip: int = 0, limit: int = 50, search: str = ""):
    """List contacts with optional search"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/contacts", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_contact(contact_id: int):
    """Get contact by ID"""
    result = await api_call("GET", f"/api/contacts/{contact_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_contact(
    first_name: str,
    last_name: str,
    email: str = "",
    phone: str = "",
    account_id: Optional[int] = None,
):
    """Create new contact"""
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
    }
    if account_id:
        data["account_id"] = account_id
    result = await api_call("POST", "/api/contacts", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_contact(contact_id: int, **kwargs):
    """Update contact"""
    result = await api_call("PUT", f"/api/contacts/{contact_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def delete_contact(contact_id: int):
    """Delete contact"""
    result = await api_call("DELETE", f"/api/contacts/{contact_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# ACCOUNTS TOOLS
# ============================================================================

@server.call_tool()
async def list_accounts(skip: int = 0, limit: int = 50, search: str = ""):
    """List accounts with optional search"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/accounts", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_account(account_id: int):
    """Get account by ID"""
    result = await api_call("GET", f"/api/accounts/{account_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_account(
    name: str,
    industry: str = "",
    revenue: Optional[float] = None,
    employees: Optional[int] = None,
):
    """Create new account"""
    data = {"name": name, "industry": industry}
    if revenue:
        data["revenue"] = revenue
    if employees:
        data["employees"] = employees
    result = await api_call("POST", "/api/accounts", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_account(account_id: int, **kwargs):
    """Update account"""
    result = await api_call("PUT", f"/api/accounts/{account_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def delete_account(account_id: int):
    """Delete account"""
    result = await api_call("DELETE", f"/api/accounts/{account_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# LEADS TOOLS
# ============================================================================

@server.call_tool()
async def list_leads(skip: int = 0, limit: int = 50, search: str = ""):
    """List leads with optional search"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/leads", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_lead(lead_id: int):
    """Get lead by ID"""
    result = await api_call("GET", f"/api/leads/{lead_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_lead(
    first_name: str,
    last_name: str,
    company: str,
    email: str = "",
    phone: str = "",
    lead_score: int = 0,
):
    """Create new lead (auto-assigned)"""
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "company": company,
        "email": email,
        "phone": phone,
        "lead_score": lead_score,
    }
    result = await api_call("POST", "/api/leads", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_lead(lead_id: int, **kwargs):
    """Update lead"""
    result = await api_call("PUT", f"/api/leads/{lead_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def delete_lead(lead_id: int):
    """Delete lead"""
    result = await api_call("DELETE", f"/api/leads/{lead_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def convert_lead(lead_id: int):
    """Convert lead to account, contact, and opportunity"""
    result = await api_call("POST", f"/api/leads/{lead_id}/convert", {})
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# OPPORTUNITIES TOOLS
# ============================================================================

@server.call_tool()
async def list_opportunities(skip: int = 0, limit: int = 50, search: str = ""):
    """List opportunities with optional search"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/opportunities", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_opportunity(opportunity_id: int):
    """Get opportunity by ID"""
    result = await api_call("GET", f"/api/opportunities/{opportunity_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_opportunity(
    name: str,
    account_id: int,
    amount: float,
    stage: str = "Prospecting",
    close_date: str = "",
):
    """Create new opportunity"""
    data = {
        "name": name,
        "account_id": account_id,
        "amount": amount,
        "stage": stage,
    }
    if close_date:
        data["close_date"] = close_date
    result = await api_call("POST", "/api/opportunities", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_opportunity(opportunity_id: int, **kwargs):
    """Update opportunity"""
    result = await api_call("PUT", f"/api/opportunities/{opportunity_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def delete_opportunity(opportunity_id: int):
    """Delete opportunity"""
    result = await api_call("DELETE", f"/api/opportunities/{opportunity_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# CASES TOOLS
# ============================================================================

@server.call_tool()
async def list_cases(skip: int = 0, limit: int = 50, search: str = ""):
    """List cases with optional search"""
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/cases", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_case(case_id: int):
    """Get case by ID"""
    result = await api_call("GET", f"/api/cases/{case_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_case(
    subject: str,
    contact_id: int,
    priority: str = "Medium",
    status: str = "New",
    description: str = "",
):
    """Create new case (auto-assigned)"""
    data = {
        "subject": subject,
        "contact_id": contact_id,
        "priority": priority,
        "status": status,
        "description": description,
    }
    result = await api_call("POST", "/api/cases", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_case(case_id: int, **kwargs):
    """Update case"""
    result = await api_call("PUT", f"/api/cases/{case_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def delete_case(case_id: int):
    """Delete case"""
    result = await api_call("DELETE", f"/api/cases/{case_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def escalate_case(case_id: int):
    """Escalate case"""
    result = await api_call("POST", f"/api/cases/{case_id}/escalate", {})
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def merge_cases(case_id_1: int, case_id_2: int):
    """Merge duplicate cases"""
    result = await api_call(
        "POST",
        "/api/cases/merge",
        {"case_id_1": case_id_1, "case_id_2": case_id_2},
    )
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# DASHBOARD TOOLS
# ============================================================================

@server.call_tool()
async def get_dashboard_stats():
    """Get dashboard statistics"""
    result = await api_call("GET", "/api/dashboard/stats")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_recent_records():
    """Get recent records"""
    result = await api_call("GET", "/api/dashboard/recent-records")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def global_search(query: str):
    """Global search across all objects"""
    result = await api_call("GET", "/api/dashboard/search", params={"q": query})
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# ACTIVITIES TOOLS
# ============================================================================

@server.call_tool()
async def list_activities(skip: int = 0, limit: int = 50):
    """List activities"""
    result = await api_call(
        "GET", "/api/activities", params={"skip": skip, "limit": limit}
    )
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_activity(
    activity_type: str,
    subject: str,
    related_object_type: str,
    related_object_id: int,
    description: str = "",
):
    """Create activity"""
    data = {
        "activity_type": activity_type,
        "subject": subject,
        "related_object_type": related_object_type,
        "related_object_id": related_object_id,
        "description": description,
    }
    result = await api_call("POST", "/api/activities", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# LOGS TOOLS
# ============================================================================

@server.call_tool()
async def get_logs(skip: int = 0, limit: int = 50):
    """Get system logs"""
    result = await api_call(
        "GET", "/api/logs", params={"skip": skip, "limit": limit}
    )
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# HEALTH CHECK
# ============================================================================

@server.call_tool()
async def health_check():
    """Check API health"""
    result = await api_call("GET", "/api/health")
    return [TextContent(type="text", text=json.dumps(result))]


def run_http_server():
    """Run MCP server in HTTP/SSE mode for remote connections"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    # SSE transport for HTTP-based MCP connections
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

    # CORS middleware for cross-origin requests
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

    print(f"Starting MCP server in HTTP mode")
    print(f"  Host: {MCP_HOST}")
    print(f"  Port: {MCP_PORT}")
    print(f"  API Backend: {API_BASE_URL}")
    print(f"  SSE Endpoint: http://{MCP_HOST}:{MCP_PORT}/sse")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


def run_stdio_server():
    """Run MCP server in stdio mode for local use"""
    print("Starting MCP server in stdio mode")
    server.run()


if __name__ == "__main__":
    import sys

    # Default to HTTP mode, use --stdio for local mode
    if "--stdio" in sys.argv:
        run_stdio_server()
    else:
        run_http_server()
