#!/usr/bin/env python3
"""
MuleSoft Integration MCP Server
Bridges Salesforce CRM with SAP ERP Backend

This MCP server provides tools to:
1. Sync Salesforce Cases to SAP Work Orders
2. Check SAP Work Order status
3. Trigger material checks and FI approvals

Integration Flow:
Salesforce CRM → MuleSoft MCP → SAP Backend API → PM → MM → FI
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Optional
import httpx

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)


# Configuration
SAP_BACKEND_URL = os.getenv("SAP_BACKEND_URL", "http://localhost:2004")
MULESOFT_CLIENT_ID = os.getenv("MULESOFT_CLIENT_ID", "mulesoft-client")
MULESOFT_CLIENT_SECRET = os.getenv("MULESOFT_CLIENT_SECRET", "mulesoft-secret")

# Create MCP server
server = Server("mulesoft-integration")


# =====================
# Helper Functions
# =====================

async def call_sap_api(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Call SAP Backend API"""
    url = f"{SAP_BACKEND_URL}/api/v1{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-MuleSoft-Client-ID": MULESOFT_CLIENT_ID,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()


def format_response(data: Any) -> str:
    """Format response data as JSON string"""
    if isinstance(data, dict) or isinstance(data, list):
        return json.dumps(data, indent=2, default=str)
    return str(data)


# =====================
# MCP Tool Definitions
# =====================

@server.list_tools()
async def list_tools():
    """List available MuleSoft integration tools"""
    return [
        Tool(
            name="sync_case_to_sap",
            description="Sync a Salesforce Case to SAP as a Work Order. Triggers PM → MM → FI workflow automatically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "Salesforce Case ID"},
                    "case_number": {"type": "string", "description": "Salesforce Case Number"},
                    "subject": {"type": "string", "description": "Case subject/title"},
                    "description": {"type": "string", "description": "Case description"},
                    "account_name": {"type": "string", "description": "Customer/Account name"},
                    "site_address": {"type": "string", "description": "Site location address"},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Urgent"], "default": "Medium"},
                    "cost_center_id": {"type": "string", "description": "SAP Cost Center ID for procurement"},
                    "materials": {
                        "type": "array",
                        "description": "List of required materials",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "product_name": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "unit": {"type": "string", "default": "EA"},
                                "unit_price": {"type": "number"}
                            },
                            "required": ["product_id", "product_name", "quantity"]
                        }
                    },
                    "contact_name": {"type": "string", "description": "Contact person name"},
                    "owner_name": {"type": "string", "description": "Case owner/assignee"},
                    "operation": {"type": "string", "enum": ["CREATE", "UPDATE"], "default": "CREATE"}
                },
                "required": ["case_id", "case_number", "subject", "description", "account_name", "site_address"]
            }
        ),
        Tool(
            name="sync_cases_batch",
            description="Batch sync multiple Salesforce Cases to SAP",
            inputSchema={
                "type": "object",
                "properties": {
                    "cases": {
                        "type": "array",
                        "description": "List of cases to sync",
                        "items": {
                            "type": "object",
                            "properties": {
                                "case_id": {"type": "string"},
                                "case_number": {"type": "string"},
                                "subject": {"type": "string"},
                                "description": {"type": "string"},
                                "account_name": {"type": "string"},
                                "site_address": {"type": "string"},
                                "priority": {"type": "string"},
                                "materials": {"type": "array"}
                            },
                            "required": ["case_id", "case_number", "subject", "account_name", "site_address"]
                        }
                    }
                },
                "required": ["cases"]
            }
        ),
        Tool(
            name="get_case_sync_status",
            description="Get the SAP Work Order status for a synced Salesforce Case",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "Salesforce Case ID"}
                },
                "required": ["case_id"]
            }
        ),
        Tool(
            name="get_sap_case_status",
            description="Query SAP for the current status of a work order by Case ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "Salesforce Case ID"}
                },
                "required": ["case_id"]
            }
        ),
        Tool(
            name="trigger_material_check",
            description="Trigger material availability check in SAP MM for a work order",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "SAP Work Order ID"},
                    "performed_by": {"type": "string", "description": "User performing the action"}
                },
                "required": ["work_order_id"]
            }
        ),
        Tool(
            name="approve_purchase_request",
            description="Approve or reject a purchase request in SAP FI",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "SAP Work Order ID"},
                    "approved": {"type": "boolean", "description": "True to approve, False to reject"},
                    "decided_by": {"type": "string", "description": "User making the decision"},
                    "comment": {"type": "string", "description": "Decision comment"}
                },
                "required": ["work_order_id", "approved", "decided_by"]
            }
        ),
        Tool(
            name="mulesoft_health_check",
            description="Check health of MuleSoft integration and SAP backend connectivity",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_mulesoft_config",
            description="Get current MuleSoft configuration settings",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_sap_work_orders",
            description="List all SAP Work Orders with optional status filter",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["received", "pending_material_check", "materials_available", "materials_shortage",
                                 "purchase_requested", "purchase_approved", "purchase_rejected",
                                 "ready_to_proceed", "in_progress", "completed", "cancelled"],
                        "description": "Filter by work order status"
                    },
                    "limit": {"type": "integer", "default": 20, "description": "Maximum number of results"}
                },
                "required": []
            }
        ),
        Tool(
            name="get_work_order_flow_history",
            description="Get the complete flow history of a work order (PM → MM → FI transitions)",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_order_id": {"type": "string", "description": "SAP Work Order ID"}
                },
                "required": ["work_order_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute MuleSoft integration tool"""

    try:
        if name == "sync_case_to_sap":
            # Build sync request
            sync_data = {
                "operation": arguments.get("operation", "CREATE"),
                "case": {
                    "case_id": arguments["case_id"],
                    "case_number": arguments["case_number"],
                    "subject": arguments["subject"],
                    "description": arguments.get("description", ""),
                    "account_name": arguments["account_name"],
                    "site_address": arguments["site_address"],
                    "priority": arguments.get("priority", "Medium"),
                    "materials": arguments.get("materials", []),
                    "contact_name": arguments.get("contact_name"),
                    "owner_name": arguments.get("owner_name"),
                    "cost_center_id": arguments.get("cost_center_id", "CC-DEFAULT"),
                }
            }

            result = await call_sap_api("POST", "/crm-integration/sync-case", sync_data)
            return [TextContent(type="text", text=format_response(result))]

        elif name == "sync_cases_batch":
            results = []
            for case in arguments["cases"]:
                sync_data = {
                    "operation": "CREATE",
                    "case": {
                        "case_id": case["case_id"],
                        "case_number": case["case_number"],
                        "subject": case["subject"],
                        "description": case.get("description", ""),
                        "account_name": case["account_name"],
                        "site_address": case["site_address"],
                        "priority": case.get("priority", "Medium"),
                        "materials": case.get("materials", []),
                        "cost_center_id": case.get("cost_center_id", "CC-DEFAULT"),
                    }
                }
                try:
                    result = await call_sap_api("POST", "/crm-integration/sync-case", sync_data)
                    results.append({"case_id": case["case_id"], "success": True, "result": result})
                except Exception as e:
                    results.append({"case_id": case["case_id"], "success": False, "error": str(e)})

            return [TextContent(type="text", text=format_response({"batch_results": results}))]

        elif name == "get_case_sync_status" or name == "get_sap_case_status":
            result = await call_sap_api("GET", f"/crm-integration/case-status/{arguments['case_id']}")
            return [TextContent(type="text", text=format_response(result))]

        elif name == "trigger_material_check":
            data = {
                "performed_by": arguments.get("performed_by", "MuleSoft:AUTO")
            }
            result = await call_sap_api("POST", f"/work-order-flow/work-orders/{arguments['work_order_id']}/check-materials", data)
            return [TextContent(type="text", text=format_response(result))]

        elif name == "approve_purchase_request":
            data = {
                "approved": arguments["approved"],
                "decided_by": arguments["decided_by"],
                "comment": arguments.get("comment")
            }
            result = await call_sap_api("POST", f"/work-order-flow/work-orders/{arguments['work_order_id']}/approve-purchase", data)
            return [TextContent(type="text", text=format_response(result))]

        elif name == "mulesoft_health_check":
            # Check SAP backend health
            try:
                sap_health = await call_sap_api("GET", "/../health")
                sap_status = "healthy"
            except Exception as e:
                sap_health = {"error": str(e)}
                sap_status = "unhealthy"

            # Check CRM integration health
            try:
                crm_health = await call_sap_api("GET", "/crm-integration/health")
                crm_status = "healthy"
            except Exception as e:
                crm_health = {"error": str(e)}
                crm_status = "unhealthy"

            return [TextContent(type="text", text=format_response({
                "mulesoft_status": "healthy",
                "sap_backend_status": sap_status,
                "sap_backend_url": SAP_BACKEND_URL,
                "crm_integration_status": crm_status,
                "timestamp": datetime.utcnow().isoformat()
            }))]

        elif name == "get_mulesoft_config":
            return [TextContent(type="text", text=format_response({
                "sap_backend_url": SAP_BACKEND_URL,
                "mulesoft_client_id": MULESOFT_CLIENT_ID,
                "supported_operations": ["CREATE", "UPDATE"],
                "endpoints": {
                    "sync_case": "/api/v1/crm-integration/sync-case",
                    "case_status": "/api/v1/crm-integration/case-status/{case_id}",
                    "work_orders": "/api/v1/work-order-flow/work-orders",
                    "material_check": "/api/v1/work-order-flow/work-orders/{id}/check-materials",
                    "purchase_approval": "/api/v1/work-order-flow/work-orders/{id}/approve-purchase"
                }
            }))]

        elif name == "list_sap_work_orders":
            params = []
            if arguments.get("status"):
                params.append(f"flow_status={arguments['status']}")
            if arguments.get("limit"):
                params.append(f"limit={arguments['limit']}")

            endpoint = "/work-order-flow/work-orders"
            if params:
                endpoint += "?" + "&".join(params)

            result = await call_sap_api("GET", endpoint)
            return [TextContent(type="text", text=format_response(result))]

        elif name == "get_work_order_flow_history":
            result = await call_sap_api("GET", f"/work-order-flow/work-orders/{arguments['work_order_id']}/history")
            return [TextContent(type="text", text=format_response(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.HTTPError as e:
        return [TextContent(type="text", text=format_response({
            "error": "HTTP Error",
            "message": str(e),
            "details": getattr(e.response, 'text', None) if hasattr(e, 'response') else None
        }))]
    except Exception as e:
        return [TextContent(type="text", text=format_response({
            "error": "Error",
            "message": str(e)
        }))]


# =====================
# Main Entry Point
# =====================

async def main():
    """Run the MuleSoft MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
