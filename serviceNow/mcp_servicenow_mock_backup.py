#!/usr/bin/env python3
"""
MCP Server for ServiceNow Integration
Provides tools to interact with ServiceNow ITSM (Mock Mode)
"""

import json
import asyncio
from typing import Optional
from mcp.server import Server
from mcp.types import TextContent, Tool

# ServiceNow Configuration (Mock Mode)
SERVICENOW_INSTANCE = "https://dev12345.service-now.com"
SERVICENOW_USER = "admin"
SERVICENOW_PASSWORD = "password"
MCP_HOST = "0.0.0.0"
MCP_PORT = 8093

server = Server("servicenow-integration")

# Mock data for testing
MOCK_INCIDENTS = [
    {"sys_id": "INC0001", "number": "INC0001", "short_description": "Email not working", "state": "1", "priority": "3", "assigned_to": "John Doe"},
    {"sys_id": "INC0002", "number": "INC0002", "short_description": "VPN connection issues", "state": "2", "priority": "2", "assigned_to": "Jane Smith"},
    {"sys_id": "INC0003", "number": "INC0003", "short_description": "Printer offline", "state": "1", "priority": "4", "assigned_to": "Bob Wilson"},
    {"sys_id": "INC0004", "number": "INC0004", "short_description": "Software installation request", "state": "3", "priority": "3", "assigned_to": "Alice Brown"},
    {"sys_id": "INC0005", "number": "INC0005", "short_description": "Password reset needed", "state": "6", "priority": "4", "assigned_to": "Charlie Davis"},
]

MOCK_CHANGES = [
    {"sys_id": "CHG0001", "number": "CHG0001", "short_description": "Server upgrade", "state": "1", "priority": "2", "type": "normal"},
    {"sys_id": "CHG0002", "number": "CHG0002", "short_description": "Network maintenance", "state": "2", "priority": "3", "type": "standard"},
    {"sys_id": "CHG0003", "number": "CHG0003", "short_description": "Database migration", "state": "1", "priority": "1", "type": "emergency"},
]

MOCK_PROBLEMS = [
    {"sys_id": "PRB0001", "number": "PRB0001", "short_description": "Recurring network outages", "state": "1", "priority": "2"},
    {"sys_id": "PRB0002", "number": "PRB0002", "short_description": "Application performance degradation", "state": "2", "priority": "3"},
]

MOCK_USERS = [
    {"sys_id": "USR001", "user_name": "john.doe", "first_name": "John", "last_name": "Doe", "email": "john.doe@company.com"},
    {"sys_id": "USR002", "user_name": "jane.smith", "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@company.com"},
    {"sys_id": "USR003", "user_name": "admin", "first_name": "Admin", "last_name": "User", "email": "admin@company.com"},
]

MOCK_CMDB = [
    {"sys_id": "CI001", "name": "Web Server 01", "sys_class_name": "cmdb_ci_server", "operational_status": "1"},
    {"sys_id": "CI002", "name": "Database Server 01", "sys_class_name": "cmdb_ci_database", "operational_status": "1"},
    {"sys_id": "CI003", "name": "Network Switch 01", "sys_class_name": "cmdb_ci_netgear", "operational_status": "1"},
    {"sys_id": "CI004", "name": "Firewall 01", "sys_class_name": "cmdb_ci_firewall", "operational_status": "1"},
]


@server.list_tools()
async def list_tools():
    """Return list of available ServiceNow tools"""
    return [
        Tool(name="list_incidents", description="List ServiceNow incidents", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="get_incident", description="Get ServiceNow incident by ID", inputSchema={"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]}),
        Tool(name="create_incident", description="Create new ServiceNow incident", inputSchema={"type": "object", "properties": {"short_description": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string", "default": "3"}}, "required": ["short_description"]}),
        Tool(name="update_incident", description="Update ServiceNow incident", inputSchema={"type": "object", "properties": {"incident_id": {"type": "string"}, "state": {"type": "string"}, "priority": {"type": "string"}}, "required": ["incident_id"]}),
        Tool(name="close_incident", description="Close ServiceNow incident", inputSchema={"type": "object", "properties": {"incident_id": {"type": "string"}, "close_notes": {"type": "string"}}, "required": ["incident_id"]}),
        Tool(name="list_change_requests", description="List ServiceNow change requests", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="get_change_request", description="Get ServiceNow change request by ID", inputSchema={"type": "object", "properties": {"change_id": {"type": "string"}}, "required": ["change_id"]}),
        Tool(name="create_change_request", description="Create new ServiceNow change request", inputSchema={"type": "object", "properties": {"short_description": {"type": "string"}, "type": {"type": "string", "default": "normal"}}, "required": ["short_description"]}),
        Tool(name="list_problems", description="List ServiceNow problems", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="get_problem", description="Get ServiceNow problem by ID", inputSchema={"type": "object", "properties": {"problem_id": {"type": "string"}}, "required": ["problem_id"]}),
        Tool(name="create_problem", description="Create new ServiceNow problem", inputSchema={"type": "object", "properties": {"short_description": {"type": "string"}, "priority": {"type": "string", "default": "3"}}, "required": ["short_description"]}),
        Tool(name="list_users", description="List ServiceNow users", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="get_user", description="Get ServiceNow user by ID", inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]}),
        Tool(name="list_config_items", description="List ServiceNow CMDB configuration items", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="get_config_item", description="Get ServiceNow configuration item by ID", inputSchema={"type": "object", "properties": {"ci_id": {"type": "string"}}, "required": ["ci_id"]}),
        Tool(name="add_work_note", description="Add work note to ServiceNow incident", inputSchema={"type": "object", "properties": {"incident_id": {"type": "string"}, "work_note": {"type": "string"}}, "required": ["incident_id", "work_note"]}),
        Tool(name="assign_incident", description="Assign ServiceNow incident to user", inputSchema={"type": "object", "properties": {"incident_id": {"type": "string"}, "assigned_to": {"type": "string"}}, "required": ["incident_id", "assigned_to"]}),
        Tool(name="link_sap_work_order", description="Link SAP work order ID to ServiceNow incident", inputSchema={"type": "object", "properties": {"incident_id": {"type": "string"}, "sap_work_order_id": {"type": "string"}}, "required": ["incident_id", "sap_work_order_id"]}),
        Tool(name="get_pending_tickets", description="Get ServiceNow incidents with state pending", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}}),
        Tool(name="servicenow_health_check", description="Check ServiceNow connectivity", inputSchema={"type": "object", "properties": {}}),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool execution"""

    if name == "list_incidents":
        limit = arguments.get("limit", 50)
        return [TextContent(type="text", text=json.dumps({"result": MOCK_INCIDENTS[:limit], "mode": "mock"}))]

    elif name == "get_incident":
        incident_id = arguments.get("incident_id")
        for inc in MOCK_INCIDENTS:
            if inc["sys_id"] == incident_id or inc["number"] == incident_id:
                return [TextContent(type="text", text=json.dumps({"result": inc, "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Incident {incident_id} not found", "mode": "mock"}))]

    elif name == "create_incident":
        new_incident = {
            "sys_id": f"INC{len(MOCK_INCIDENTS)+1:04d}",
            "number": f"INC{len(MOCK_INCIDENTS)+1:04d}",
            "short_description": arguments.get("short_description"),
            "description": arguments.get("description", ""),
            "state": "1",
            "priority": arguments.get("priority", "3"),
            "assigned_to": "Unassigned"
        }
        MOCK_INCIDENTS.append(new_incident)
        return [TextContent(type="text", text=json.dumps({"result": new_incident, "message": "Incident created (mock)", "mode": "mock"}))]

    elif name == "update_incident":
        incident_id = arguments.get("incident_id")
        for inc in MOCK_INCIDENTS:
            if inc["sys_id"] == incident_id or inc["number"] == incident_id:
                if "state" in arguments:
                    inc["state"] = arguments["state"]
                if "priority" in arguments:
                    inc["priority"] = arguments["priority"]
                return [TextContent(type="text", text=json.dumps({"result": inc, "message": "Incident updated (mock)", "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Incident {incident_id} not found", "mode": "mock"}))]

    elif name == "close_incident":
        incident_id = arguments.get("incident_id")
        for inc in MOCK_INCIDENTS:
            if inc["sys_id"] == incident_id or inc["number"] == incident_id:
                inc["state"] = "7"
                inc["close_notes"] = arguments.get("close_notes", "")
                return [TextContent(type="text", text=json.dumps({"result": inc, "message": "Incident closed (mock)", "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Incident {incident_id} not found", "mode": "mock"}))]

    elif name == "list_change_requests":
        limit = arguments.get("limit", 50)
        return [TextContent(type="text", text=json.dumps({"result": MOCK_CHANGES[:limit], "mode": "mock"}))]

    elif name == "get_change_request":
        change_id = arguments.get("change_id")
        for chg in MOCK_CHANGES:
            if chg["sys_id"] == change_id or chg["number"] == change_id:
                return [TextContent(type="text", text=json.dumps({"result": chg, "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Change request {change_id} not found", "mode": "mock"}))]

    elif name == "create_change_request":
        new_change = {
            "sys_id": f"CHG{len(MOCK_CHANGES)+1:04d}",
            "number": f"CHG{len(MOCK_CHANGES)+1:04d}",
            "short_description": arguments.get("short_description"),
            "state": "1",
            "priority": "3",
            "type": arguments.get("type", "normal")
        }
        MOCK_CHANGES.append(new_change)
        return [TextContent(type="text", text=json.dumps({"result": new_change, "message": "Change request created (mock)", "mode": "mock"}))]

    elif name == "list_problems":
        limit = arguments.get("limit", 50)
        return [TextContent(type="text", text=json.dumps({"result": MOCK_PROBLEMS[:limit], "mode": "mock"}))]

    elif name == "get_problem":
        problem_id = arguments.get("problem_id")
        for prb in MOCK_PROBLEMS:
            if prb["sys_id"] == problem_id or prb["number"] == problem_id:
                return [TextContent(type="text", text=json.dumps({"result": prb, "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Problem {problem_id} not found", "mode": "mock"}))]

    elif name == "create_problem":
        new_problem = {
            "sys_id": f"PRB{len(MOCK_PROBLEMS)+1:04d}",
            "number": f"PRB{len(MOCK_PROBLEMS)+1:04d}",
            "short_description": arguments.get("short_description"),
            "state": "1",
            "priority": arguments.get("priority", "3")
        }
        MOCK_PROBLEMS.append(new_problem)
        return [TextContent(type="text", text=json.dumps({"result": new_problem, "message": "Problem created (mock)", "mode": "mock"}))]

    elif name == "list_users":
        limit = arguments.get("limit", 50)
        return [TextContent(type="text", text=json.dumps({"result": MOCK_USERS[:limit], "mode": "mock"}))]

    elif name == "get_user":
        user_id = arguments.get("user_id")
        for usr in MOCK_USERS:
            if usr["sys_id"] == user_id or usr["user_name"] == user_id:
                return [TextContent(type="text", text=json.dumps({"result": usr, "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"User {user_id} not found", "mode": "mock"}))]

    elif name == "list_config_items":
        limit = arguments.get("limit", 50)
        return [TextContent(type="text", text=json.dumps({"result": MOCK_CMDB[:limit], "mode": "mock"}))]

    elif name == "get_config_item":
        ci_id = arguments.get("ci_id")
        for ci in MOCK_CMDB:
            if ci["sys_id"] == ci_id or ci["name"] == ci_id:
                return [TextContent(type="text", text=json.dumps({"result": ci, "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Config item {ci_id} not found", "mode": "mock"}))]

    elif name == "add_work_note":
        incident_id = arguments.get("incident_id")
        work_note = arguments.get("work_note")
        for inc in MOCK_INCIDENTS:
            if inc["sys_id"] == incident_id or inc["number"] == incident_id:
                if "work_notes" not in inc:
                    inc["work_notes"] = []
                inc["work_notes"].append(work_note)
                return [TextContent(type="text", text=json.dumps({"result": inc, "message": "Work note added (mock)", "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Incident {incident_id} not found", "mode": "mock"}))]

    elif name == "assign_incident":
        incident_id = arguments.get("incident_id")
        assigned_to = arguments.get("assigned_to")
        for inc in MOCK_INCIDENTS:
            if inc["sys_id"] == incident_id or inc["number"] == incident_id:
                inc["assigned_to"] = assigned_to
                inc["state"] = "2"  # Set to In Progress
                return [TextContent(type="text", text=json.dumps({"result": inc, "message": "Incident assigned (mock)", "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Incident {incident_id} not found", "mode": "mock"}))]

    elif name == "link_sap_work_order":
        incident_id = arguments.get("incident_id")
        sap_work_order_id = arguments.get("sap_work_order_id")
        for inc in MOCK_INCIDENTS:
            if inc["sys_id"] == incident_id or inc["number"] == incident_id:
                inc["u_sap_work_order"] = sap_work_order_id
                return [TextContent(type="text", text=json.dumps({"result": inc, "message": "SAP work order linked (mock)", "mode": "mock"}))]
        return [TextContent(type="text", text=json.dumps({"error": f"Incident {incident_id} not found", "mode": "mock"}))]

    elif name == "get_pending_tickets":
        limit = arguments.get("limit", 20)
        pending = [inc for inc in MOCK_INCIDENTS if inc["state"] in ["1", "2"]]  # New or In Progress
        return [TextContent(type="text", text=json.dumps({"result": pending[:limit], "mode": "mock"}))]

    elif name == "servicenow_health_check":
        return [TextContent(type="text", text=json.dumps({
            "status": "healthy",
            "message": "ServiceNow MCP running in mock mode",
            "mode": "mock",
            "mock_data": {
                "incidents": len(MOCK_INCIDENTS),
                "changes": len(MOCK_CHANGES),
                "problems": len(MOCK_PROBLEMS),
                "users": len(MOCK_USERS),
                "cmdb_items": len(MOCK_CMDB)
            }
        }))]

    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


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

    print(f"Starting ServiceNow MCP server in HTTP mode")
    print(f"  Host: {MCP_HOST}")
    print(f"  Port: {MCP_PORT}")
    print(f"  SSE Endpoint: http://207.180.217.117:{MCP_PORT}/sse")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


def run_stdio_server():
    """Run MCP server in stdio mode for local use"""
    print("Starting ServiceNow MCP server in stdio mode")
    asyncio.run(main())


if __name__ == "__main__":
    import sys

    if "--stdio" in sys.argv:
        run_stdio_server()
    else:
        run_http_server()
