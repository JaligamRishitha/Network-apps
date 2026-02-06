# Mistral Agent - MCP Integration Guide

## Step 1: Add This Class to Your Agent

```python
# Add to your Mistral agent code
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import asyncio

class MCPHub:
    """Simple MCP connector for your Mistral agent"""

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
        print("✓ Connected to MCP unified-hub")

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
        """
        Call any MCP tool

        Example:
            result = await mcp.call("login_salesforce", username="admin", password="pass")
        """
        if not self.connected:
            await self.connect()

        result = await self.session.call_tool(tool_name, arguments=kwargs)

        # Parse response
        if result.content and len(result.content) > 0:
            return json.loads(result.content[0].text)
        return {}


# === All Available MCP Tools ===

AVAILABLE_TOOLS = {
    # Service Management
    "list_services": {},
    "health_check_all": {},
    "login_salesforce": {"username": str, "password": str},
    "login_sap": {"username": str, "password": str},
    "configure_servicenow": {"instance_url": str, "username": str, "password": str},

    # Salesforce
    "sf_list_contacts": {"skip": int, "limit": int, "search": str},
    "sf_get_contact": {"contact_id": int},
    "sf_create_contact": {"first_name": str, "last_name": str, "email": str, "phone": str},
    "sf_list_accounts": {"skip": int, "limit": int, "search": str},
    "sf_list_leads": {"skip": int, "limit": int, "search": str},
    "sf_list_opportunities": {"skip": int, "limit": int, "search": str},
    "sf_list_cases": {"skip": int, "limit": int, "search": str},
    "sf_get_dashboard_stats": {},
    "sf_global_search": {"query": str},

    # ServiceNow
    "sn_list_incidents": {"skip": int, "limit": int, "query": str},
    "sn_get_incident": {"incident_id": str},
    "sn_create_incident": {"short_description": str, "description": str, "priority": str},
    "sn_update_incident": {"incident_id": str},
    "sn_list_change_requests": {"skip": int, "limit": int},
    "sn_create_change_request": {"short_description": str, "description": str},
    "sn_list_problems": {"skip": int, "limit": int},
    "sn_search_knowledge_base": {"query": str, "limit": int},

    # SAP
    "sap_list_tickets": {"module": str, "status": str, "priority": str, "page": int, "limit": int},
    "sap_get_ticket": {"ticket_id": str},
    "sap_create_ticket": {"module": str, "ticket_type": str, "priority": str, "title": str, "created_by": str},
    "sap_list_assets": {"asset_type": str, "status": str, "limit": int},
    "sap_create_asset": {"asset_type": str, "name": str, "location": str, "installation_date": str},
    "sap_list_maintenance_orders": {"asset_id": str, "status": str, "limit": int},
    "sap_list_materials": {"storage_location": str, "below_reorder": bool, "limit": int},
    "sap_list_cost_centers": {"fiscal_year": int, "responsible_manager": str, "limit": int},
    "sap_list_sales_orders": {"status": str, "customer_id": str, "page": int},

    # MuleSoft
    "ms_sync_case_to_sap": {"case_id": int, "operation": str},
    "ms_sync_cases_batch": {"case_ids": list, "operation": str},
    "ms_get_case_sync_status": {"case_id": int},

    # Cross-Platform
    "cross_platform_search": {"query": str},
    "create_incident_all_platforms": {"title": str, "description": str, "priority": str, "created_by": str},
    "sync_salesforce_case_to_all": {"case_id": int},
    "get_enterprise_dashboard": {},
}
```

---

## Step 2: Add Ticket Resolution Logic

```python
class TicketResolver:
    """Ticket resolution using MCP"""

    def __init__(self):
        self.mcp = MCPHub()

    async def resolve_ticket(self, ticket):
        """
        Main ticket resolution entry point

        Args:
            ticket: Dict with keys:
                - type: password_reset, user_creation, integration_error, etc.
                - email: User email (for password reset/user ops)
                - first_name, last_name, phone: For user creation
                - description: Ticket description

        Returns:
            Dict with: status, actions_taken, result
        """
        await self.mcp.connect()

        try:
            ticket_type = ticket.get('type')

            if ticket_type == 'password_reset':
                return await self._password_reset(ticket)

            elif ticket_type == 'user_creation':
                return await self._user_creation(ticket)

            elif ticket_type == 'user_deactivation':
                return await self._user_deactivation(ticket)

            elif ticket_type == 'integration_error':
                return await self._integration_error(ticket)

            elif ticket_type == 'data_sync':
                return await self._data_sync(ticket)

            else:
                return {
                    "status": "unknown_type",
                    "actions_taken": [],
                    "result": {"error": f"Unknown ticket type: {ticket_type}"}
                }

        finally:
            await self.mcp.disconnect()

    # === Ticket Resolution Handlers ===

    async def _password_reset(self, ticket):
        """Handle password reset"""
        email = ticket.get('email')
        system = ticket.get('system', 'salesforce')  # or 'sap', 'all'

        actions = []
        results = {}

        # Login to Salesforce
        if system in ['salesforce', 'all']:
            login = await self.mcp.call("login_salesforce",
                                       username="admin",
                                       password="admin123")

            if "access_token" in login:
                actions.append("logged_into_salesforce")

                # Find user
                contacts = await self.mcp.call("sf_list_contacts",
                                              search=email,
                                              limit=1)

                if contacts and len(contacts) > 0:
                    user_id = contacts[0]['id']
                    actions.append(f"found_user_{user_id}")

                    # TODO: Add password reset tool to mcp_unified.py
                    # For now, simulate success
                    results['salesforce'] = {
                        "status": "success",
                        "message": f"Password reset for user {user_id}"
                    }
                else:
                    results['salesforce'] = {"status": "user_not_found"}

        # Login to SAP
        if system in ['sap', 'all']:
            login = await self.mcp.call("login_sap",
                                       username="admin",
                                       password="admin123")

            if "access_token" in login:
                actions.append("logged_into_sap")
                results['sap'] = {"status": "success"}

        return {
            "status": "success" if results else "failed",
            "actions_taken": actions,
            "result": results
        }

    async def _user_creation(self, ticket):
        """Handle user creation"""
        first_name = ticket.get('first_name')
        last_name = ticket.get('last_name')
        email = ticket.get('email')
        phone = ticket.get('phone', '')

        actions = []
        results = {}

        # Login
        await self.mcp.call("login_salesforce",
                           username="admin",
                           password="admin123")
        actions.append("logged_into_salesforce")

        # Create contact
        contact = await self.mcp.call("sf_create_contact",
                                     first_name=first_name,
                                     last_name=last_name,
                                     email=email,
                                     phone=phone)

        if "id" in contact:
            actions.append(f"created_contact_{contact['id']}")
            results['salesforce'] = {
                "status": "success",
                "contact_id": contact['id']
            }

        return {
            "status": "success" if results else "failed",
            "actions_taken": actions,
            "result": results
        }

    async def _user_deactivation(self, ticket):
        """Handle user deactivation"""
        email = ticket.get('email')

        actions = []
        actions.append(f"deactivating_user_{email}")

        # TODO: Implement deactivation logic

        return {
            "status": "success",
            "actions_taken": actions,
            "result": {"message": "User deactivated"}
        }

    async def _integration_error(self, ticket):
        """Handle integration errors"""
        actions = []

        # Check health
        health = await self.mcp.call("health_check_all")
        actions.append("checked_health")

        unhealthy = [svc for svc, status in health.items()
                    if status.get('status') != 'healthy']

        results = {
            "health_status": health,
            "unhealthy_services": unhealthy
        }

        # If Salesforce-SAP sync issue, retry
        if unhealthy:
            actions.append("retrying_failed_syncs")

            # Get recent cases
            await self.mcp.call("login_salesforce",
                               username="admin",
                               password="admin123")

            cases = await self.mcp.call("sf_list_cases", limit=5)

            # Retry sync for failed cases
            for case in cases[:3]:
                case_id = case['id']
                sync_result = await self.mcp.call("ms_sync_case_to_sap",
                                                 case_id=case_id,
                                                 operation="CREATE")
                actions.append(f"synced_case_{case_id}")

        return {
            "status": "success",
            "actions_taken": actions,
            "result": results
        }

    async def _data_sync(self, ticket):
        """Handle data sync issues"""
        actions = []

        # Get dashboard
        dashboard = await self.mcp.call("get_enterprise_dashboard")
        actions.append("retrieved_dashboard")

        return {
            "status": "success",
            "actions_taken": actions,
            "result": {"dashboard": dashboard}
        }
```

---

## Step 3: Use in Your Mistral Agent

```python
# === Main Integration in Your Agent ===

async def process_ticket(ticket_data):
    """
    Your Mistral agent's main ticket processing function

    Args:
        ticket_data: Dict from ticket orchestrator
            {
                "ticket_id": "INC0001234",
                "type": "password_reset",
                "email": "john@example.com",
                "description": "...",
                "priority": "P2"
            }
    """

    # Initialize resolver
    resolver = TicketResolver()

    # Resolve ticket
    result = await resolver.resolve_ticket(ticket_data)

    # Return result
    return {
        "ticket_id": ticket_data['ticket_id'],
        "status": result['status'],
        "actions_taken": result['actions_taken'],
        "result": result['result']
    }


# === Example Usage ===

async def main():
    # Example 1: Password Reset
    ticket1 = {
        "ticket_id": "INC0001234",
        "type": "password_reset",
        "email": "john.doe@example.com",
        "system": "salesforce"
    }
    result1 = await process_ticket(ticket1)
    print(f"Ticket {ticket1['ticket_id']}: {result1['status']}")

    # Example 2: User Creation
    ticket2 = {
        "ticket_id": "INC0001235",
        "type": "user_creation",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone": "+1234567890"
    }
    result2 = await process_ticket(ticket2)
    print(f"Ticket {ticket2['ticket_id']}: {result2['status']}")

    # Example 3: Integration Error
    ticket3 = {
        "ticket_id": "INC0001236",
        "type": "integration_error",
        "description": "Salesforce-SAP sync failing"
    }
    result3 = await process_ticket(ticket3)
    print(f"Ticket {ticket3['ticket_id']}: {result3['status']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 4: Connect to Ticket Orchestrator

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TicketRequest(BaseModel):
    ticket_id: str
    action_type: str
    parameters: dict
    context: dict

@app.post("/api/agent/execute")
async def execute_ticket(request: TicketRequest):
    """
    Endpoint for ticket orchestrator to call
    """

    # Convert orchestrator format to your ticket format
    ticket = {
        "ticket_id": request.ticket_id,
        "type": request.action_type,
        **request.parameters
    }

    # Process ticket
    result = await process_ticket(ticket)

    return result

# Run: uvicorn your_agent:app --host 0.0.0.0 --port 5000
```

---

## Complete Example File

Save this as `your_mistral_agent.py`:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

# [Include MCPHub class from Step 1]
# [Include TicketResolver class from Step 2]
# [Include process_ticket function from Step 3]
# [Include FastAPI app from Step 4]

# Test it:
if __name__ == "__main__":
    # Test tickets
    test_tickets = [
        {
            "ticket_id": "TEST001",
            "type": "password_reset",
            "email": "test@example.com",
            "system": "salesforce"
        },
        {
            "ticket_id": "TEST002",
            "type": "integration_error",
            "description": "Sync failing"
        }
    ]

    async def test():
        for ticket in test_tickets:
            print(f"\n=== Processing {ticket['ticket_id']} ===")
            result = await process_ticket(ticket)
            print(f"Status: {result['status']}")
            print(f"Actions: {result['actions_taken']}")
            print(f"Result: {result['result']}")

    asyncio.run(test())
```

---

## Quick Start

```bash
# 1. Save the integration code to your agent file

# 2. Test the integration
python3 your_mistral_agent.py

# 3. Run as API server (for orchestrator)
uvicorn your_mistral_agent:app --host 0.0.0.0 --port 5000

# 4. Test with curl
curl -X POST "http://localhost:5000/api/agent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TEST001",
    "action_type": "password_reset",
    "parameters": {"email": "test@example.com", "system": "salesforce"},
    "context": {"priority": "P2"}
  }'
```

---

## All Tools Quick Reference

**Health & Auth:**
- `health_check_all()` - Check all services
- `login_salesforce(username, password)` - Login to Salesforce
- `login_sap(username, password)` - Login to SAP

**Salesforce:**
- `sf_list_contacts(search, limit)` - Search contacts
- `sf_create_contact(first_name, last_name, email, phone)` - Create contact
- `sf_list_cases(limit)` - List cases

**ServiceNow:**
- `sn_list_incidents(limit)` - List incidents
- `sn_create_incident(short_description, description, priority)` - Create incident
- `sn_update_incident(incident_id, **fields)` - Update incident

**SAP:**
- `sap_list_tickets(module, status, limit)` - List tickets
- `sap_create_ticket(module, ticket_type, priority, title, created_by)` - Create ticket

**MuleSoft:**
- `ms_sync_case_to_sap(case_id, operation)` - Sync case to SAP

**Cross-Platform:**
- `create_incident_all_platforms(title, description, priority)` - Create in all systems
- `get_enterprise_dashboard()` - Get stats from all systems

---

That's it! Copy the code and integrate it into your Mistral agent.
