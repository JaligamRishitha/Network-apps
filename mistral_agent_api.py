#!/usr/bin/env python3
"""
Mistral Agent API Server
Exposes REST API for ticket orchestrator to call
Integrates your Mistral AI agent with MCP
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import logging
import os
from mistral_agent_mcp_integration import MCPConnector, TicketResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mistral Agent API", version="1.0.0")

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

class AgentExecuteRequest(BaseModel):
    """Request to execute agent action"""
    ticket_id: str
    action_type: str
    parameters: Dict
    context: Dict

class AgentExecuteResponse(BaseModel):
    """Response from agent execution"""
    ticket_id: str
    status: str  # success, failed, needs_info
    actions_taken: List[str]
    result: Dict
    error: Optional[str] = None

# ============================================================================
# GLOBAL MCP CONNECTION
# ============================================================================

mcp_connector: Optional[MCPConnector] = None
ticket_resolver: Optional[TicketResolver] = None

@app.on_event("startup")
async def startup_event():
    """Initialize MCP connection on startup"""
    global mcp_connector, ticket_resolver

    logger.info("Initializing MCP connection...")
    mcp_connector = MCPConnector(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_unified.py"))
    await mcp_connector.connect()

    ticket_resolver = TicketResolver(mcp_connector)
    logger.info("MCP connection established and ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect MCP on shutdown"""
    global mcp_connector

    if mcp_connector:
        await mcp_connector.disconnect()
        logger.info("MCP connection closed")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/agent/execute", response_model=AgentExecuteResponse)
async def execute_agent_action(request: AgentExecuteRequest):
    """
    Main endpoint for ticket orchestrator to call
    Executes the agent action and returns result
    """
    if not ticket_resolver:
        raise HTTPException(status_code=503, detail="Agent not ready")

    logger.info(f"Executing action for ticket: {request.ticket_id}")

    try:
        # Prepare ticket data
        ticket_data = {
            "ticket_id": request.ticket_id,
            "action_type": request.action_type,
            "parameters": request.parameters,
            "context": request.context
        }

        # Resolve ticket using MCP
        result = await ticket_resolver.resolve_ticket(ticket_data)

        # Format response
        return AgentExecuteResponse(
            ticket_id=request.ticket_id,
            status=result.get("status", "failed"),
            actions_taken=result.get("actions_taken", []),
            result=result.get("result", {}),
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Error executing agent action: {e}")
        return AgentExecuteResponse(
            ticket_id=request.ticket_id,
            status="failed",
            actions_taken=[],
            result={},
            error=str(e)
        )

@app.get("/api/agent/tools")
async def list_available_tools():
    """List all available MCP tools"""
    if not mcp_connector:
        raise HTTPException(status_code=503, detail="Agent not ready")

    try:
        tools = await mcp_connector.list_tools()
        return {
            "total_tools": len(tools),
            "tools": tools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/mcp-call")
async def direct_mcp_call(tool_name: str, arguments: Dict):
    """
    Direct MCP tool call endpoint
    For testing/debugging purposes
    """
    if not mcp_connector:
        raise HTTPException(status_code=503, detail="Agent not ready")

    try:
        result = await mcp_connector.call_tool(tool_name, arguments)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    mcp_status = "connected" if mcp_connector else "disconnected"

    # Check MCP server health
    mcp_health = {}
    if mcp_connector:
        try:
            mcp_health = await mcp_connector.call_tool("health_check_all", {})
        except:
            mcp_health = {"error": "Failed to check MCP health"}

    return {
        "status": "healthy",
        "mcp_connection": mcp_status,
        "mcp_servers_health": mcp_health
    }

# ============================================================================
# TESTING ENDPOINTS
# ============================================================================

@app.post("/api/test/password-reset")
async def test_password_reset(email: str, system: str = "salesforce"):
    """Test password reset functionality"""
    if not ticket_resolver:
        raise HTTPException(status_code=503, detail="Agent not ready")

    ticket_data = {
        "ticket_id": "TEST-001",
        "action_type": "password_reset",
        "parameters": {"email": email, "system": system},
        "context": {"priority": "P3", "description": "Test password reset"}
    }

    result = await ticket_resolver.resolve_ticket(ticket_data)
    return result

@app.post("/api/test/user-creation")
async def test_user_creation(
    first_name: str,
    last_name: str,
    email: str,
    phone: str = ""
):
    """Test user creation functionality"""
    if not ticket_resolver:
        raise HTTPException(status_code=503, detail="Agent not ready")

    ticket_data = {
        "ticket_id": "TEST-002",
        "action_type": "user_creation",
        "parameters": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone
        },
        "context": {"priority": "P3", "description": "Test user creation"}
    }

    result = await ticket_resolver.resolve_ticket(ticket_data)
    return result

@app.post("/api/test/integration-check")
async def test_integration_check():
    """Test integration error handling"""
    if not ticket_resolver:
        raise HTTPException(status_code=503, detail="Agent not ready")

    ticket_data = {
        "ticket_id": "TEST-003",
        "action_type": "integration_error",
        "parameters": {
            "systems": ["salesforce", "sap"],
            "integration_layer": "mulesoft"
        },
        "context": {"priority": "P2", "description": "Test integration check"}
    }

    result = await ticket_resolver.resolve_ticket(ticket_data)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
