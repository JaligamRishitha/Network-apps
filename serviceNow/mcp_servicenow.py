#!/usr/bin/env python3
"""
MCP Server for ServiceNow Integration - REAL MODE
Connects to actual ServiceNow backend at http://localhost:4780
"""

import json
import httpx
from typing import Optional
from mcp.server import Server
from mcp.types import TextContent

# ServiceNow Backend Configuration
SERVICENOW_BASE_URL = "http://149.102.158.71:4780"
MCP_HOST = "0.0.0.0"
MCP_PORT = 8093

server = Server("servicenow-integration")


async def api_call(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
    token: Optional[str] = None,
) -> dict:
    """Make API call to ServiceNow backend"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{SERVICENOW_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
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
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code >= 400:
                return {
                    "error": f"ServiceNow API Error {response.status_code}",
                    "details": response.text,
                }
            return response.json()
        except Exception as e:
            return {"error": f"Connection error", "details": str(e)}


# ============================================================================
# INCIDENT MANAGEMENT
# ============================================================================

@server.call_tool()
async def list_incidents(limit: int = 50, status: str = "", priority: str = ""):
    """List ServiceNow incidents from real backend"""
    params = {"limit": limit}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    result = await api_call("GET", "/incidents/", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_incident(incident_id: str):
    """Get ServiceNow incident by ID from real backend"""
    # Try as incident_id first, then as ticket number
    result = await api_call("GET", f"/tickets/{incident_id}")
    if "error" in result:
        # Try by ticket number
        result = await api_call("GET", f"/tickets/by-number/{incident_id}")
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def create_incident(
    short_description: str,
    description: str = "",
    priority: str = "3",
    category: str = "inquiry",
    assigned_to: str = "",
):
    """Create new ServiceNow incident in real backend"""
    data = {
        "title": short_description,
        "description": description,
        "priority": priority,
        "category": category,
        "status": "open",
    }
    if assigned_to:
        data["assigned_to"] = assigned_to

    result = await api_call("POST", "/tickets/", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_incident(
    incident_id: str,
    status: str = "",
    priority: str = "",
    assigned_to: str = "",
    notes: str = "",
):
    """Update ServiceNow incident in real backend"""
    data = {}
    if status:
        data["status"] = status
    if priority:
        data["priority"] = priority
    if assigned_to:
        data["assigned_to"] = assigned_to
    if notes:
        data["notes"] = notes

    result = await api_call("PUT", f"/tickets/{incident_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def close_incident(incident_id: str, close_notes: str = ""):
    """Close ServiceNow incident in real backend"""
    data = {
        "status": "resolved",
        "resolution_notes": close_notes,
    }
    result = await api_call("PUT", f"/tickets/{incident_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def add_work_note(incident_id: str, work_note: str):
    """Add work note to ServiceNow incident"""
    data = {
        "notes": work_note,
    }
    result = await api_call("PUT", f"/tickets/{incident_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def assign_incident(incident_id: str, assigned_to: str):
    """Assign incident to user and set to In Progress"""
    data = {
        "assigned_to": assigned_to,
        "status": "in_progress",
    }
    result = await api_call("PUT", f"/tickets/{incident_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def link_sap_work_order(incident_id: str, sap_work_order_id: str):
    """Link SAP work order ID to ServiceNow incident"""
    data = {
        "sap_work_order_id": sap_work_order_id,
    }
    result = await api_call("PUT", f"/tickets/{incident_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def get_pending_tickets(limit: int = 20):
    """Get ServiceNow tickets in open or in_progress state"""
    result = await api_call("GET", "/tickets/", params={"limit": limit})
    if "error" not in result and isinstance(result, list):
        # Filter for pending/open tickets
        pending = [t for t in result if t.get("status") in ["open", "pending", "in_progress"]]
        return [TextContent(type="text", text=json.dumps({"result": pending, "total": len(pending)}))]
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# APPROVAL MANAGEMENT
# ============================================================================

@server.call_tool()
async def list_approvals(limit: int = 50, status: str = ""):
    """List ServiceNow approval requests"""
    params = {"limit": limit}
    if status:
        params["status"] = status
    result = await api_call("GET", "/approvals/", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


@server.call_tool()
async def update_approval(approval_id: str, decision: str, comments: str = ""):
    """Approve or reject approval request"""
    data = {
        "status": decision,  # "approved" or "rejected"
    }
    if comments:
        data["comments"] = comments
    result = await api_call("PUT", f"/approvals/{approval_id}", data)
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# USERS & CONFIGURATION ITEMS
# ============================================================================

@server.call_tool()
async def list_users(limit: int = 50):
    """List ServiceNow users"""
    # Note: This endpoint might need adjustment based on actual backend
    result = await api_call("GET", "/users/", params={"limit": limit})
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# HEALTH CHECK
# ============================================================================

@server.call_tool()
async def servicenow_health_check():
    """Check ServiceNow backend connectivity"""
    result = await api_call("GET", "/health")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# SERVER SETUP
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

    print(f"Starting ServiceNow MCP server in HTTP mode (REAL MODE)")
    print(f"  Host: {MCP_HOST}")
    print(f"  Port: {MCP_PORT}")
    print(f"  ServiceNow Backend: {SERVICENOW_BASE_URL}")
    print(f"  SSE Endpoint: http://149.102.158.71:{MCP_PORT}/sse")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


def run_stdio_server():
    """Run MCP server in stdio mode for local use"""
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        print("Starting ServiceNow MCP server in stdio mode (REAL MODE)")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(main())


if __name__ == "__main__":
    import sys

    if "--stdio" in sys.argv:
        run_stdio_server()
    else:
        run_http_server()
