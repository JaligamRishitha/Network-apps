# Complete Deployment Guide
## Autonomous Ticket Resolution System

## Architecture Overview

```
ServiceNow Tickets
       ↓
  [Webhook]
       ↓
Ticket Orchestrator (Port 5001)
  - Receives tickets
  - Classifies by type
  - Routes to agent
       ↓
Mistral Agent API (Port 5000)
  - Your Mistral AI agent
  - Uses MCP client
       ↓
MCP Servers (stdio)
  - mcp_unified.py
  - 45+ tools
       ↓
Target Applications
  - Salesforce (4799)
  - ServiceNow (4780)
  - SAP (4798)
  - MuleSoft (4797)
```

---

## Installation Steps

### 1. Install Dependencies

```bash
cd /home/pradeep1a/Network-apps

# Install MCP library
pip install mcp

# Install API dependencies
pip install fastapi uvicorn httpx pydantic
```

### 2. File Structure

Your project now has:
```
Network-apps/
├── mcp_unified.py                      # MCP server (existing)
├── ticket_orchestrator.py              # Ticket router (new)
├── mistral_agent_mcp_integration.py    # MCP client wrapper (new)
├── mistral_agent_api.py                # Mistral agent API (new)
├── DEPLOYMENT_GUIDE.md                 # This file
└── [Your 4 applications...]
```

---

## Configuration

### 1. Configure ServiceNow Webhook

In ServiceNow:
1. Go to **System Definition → Business Rules**
2. Create new Business Rule on `incident` table
3. **When:** After Insert
4. **Actions → Insert → Script:**

```javascript
(function executeRule(current, previous) {
    try {
        var r = new sn_ws.RESTMessageV2();
        r.setEndpoint('http://207.180.217.117:5001/api/webhook/servicenow');
        r.setHttpMethod('POST');
        r.setRequestHeader('Content-Type', 'application/json');

        var payload = {
            sys_id: current.sys_id.toString(),
            number: current.number.toString(),
            short_description: current.short_description.toString(),
            description: current.description.toString(),
            priority: current.priority.toString(),
            state: current.state.toString(),
            category: current.category.toString(),
            subcategory: current.subcategory.toString()
        };

        r.setRequestBody(JSON.stringify(payload));
        var response = r.execute();

        gs.info('Ticket sent to orchestrator: ' + response.getBody());
    } catch(ex) {
        gs.error('Failed to send ticket: ' + ex.message);
    }
})(current, previous);
```

### 2. Configure Orchestrator URLs

Edit `ticket_orchestrator.py`:
```python
# Line 97: Update Mistral Agent URL
MISTRAL_AGENT_URL = "http://localhost:5000"

# Line 241: Update ServiceNow credentials
SERVICENOW_USER = "your_admin_user"
SERVICENOW_PASSWORD = "your_password"
```

### 3. Configure MCP Server Credentials

Edit `mistral_agent_mcp_integration.py`:
```python
# Update login credentials for your systems
# Lines 150, 180: Update admin credentials
"username": "your_admin",
"password": "your_password"
```

---

## Running the System

### Option 1: Run Each Component Separately (For Testing)

**Terminal 1 - Start Mistral Agent API:**
```bash
cd /home/pradeep1a/Network-apps
python3 mistral_agent_api.py
```
Output: `Uvicorn running on http://0.0.0.0:5000`

**Terminal 2 - Start Ticket Orchestrator:**
```bash
cd /home/pradeep1a/Network-apps
python3 ticket_orchestrator.py
```
Output: `Uvicorn running on http://0.0.0.0:5001`

**Terminal 3 - Test MCP Connection:**
```bash
cd /home/pradeep1a/Network-apps
python3 mistral_agent_mcp_integration.py
```

### Option 2: Run as Services (Production)

Create systemd service files:

**File: `/etc/systemd/system/mistral-agent.service`**
```ini
[Unit]
Description=Mistral Agent API
After=network.target

[Service]
Type=simple
User=pradeep1a
WorkingDirectory=/home/pradeep1a/Network-apps
Environment="PATH=/home/pradeep1a/Network-apps/mcp_venv/bin"
ExecStart=/home/pradeep1a/Network-apps/mcp_venv/bin/python3 mistral_agent_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**File: `/etc/systemd/system/ticket-orchestrator.service`**
```ini
[Unit]
Description=Ticket Orchestrator
After=network.target

[Service]
Type=simple
User=pradeep1a
WorkingDirectory=/home/pradeep1a/Network-apps
Environment="PATH=/home/pradeep1a/Network-apps/mcp_venv/bin"
ExecStart=/home/pradeep1a/Network-apps/mcp_venv/bin/python3 ticket_orchestrator.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mistral-agent
sudo systemctl enable ticket-orchestrator
sudo systemctl start mistral-agent
sudo systemctl start ticket-orchestrator

# Check status
sudo systemctl status mistral-agent
sudo systemctl status ticket-orchestrator
```

---

## Testing

### 1. Test MCP Connection

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "mcp_connection": "connected",
  "mcp_servers_health": {
    "salesforce": {"status": "healthy"},
    "sap": {"status": "healthy"},
    ...
  }
}
```

### 2. Test Password Reset

```bash
curl -X POST "http://localhost:5000/api/test/password-reset?email=john.doe@example.com&system=salesforce"
```

### 3. Test User Creation

```bash
curl -X POST "http://localhost:5000/api/test/user-creation" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  }'
```

### 4. Simulate ServiceNow Ticket

```bash
curl -X POST "http://localhost:5001/api/webhook/servicenow" \
  -H "Content-Type: application/json" \
  -d '{
    "sys_id": "test123",
    "number": "INC0001234",
    "short_description": "User cannot login - password reset needed",
    "description": "User john.doe@example.com cannot login to Salesforce",
    "priority": "3",
    "state": "1",
    "category": "password",
    "subcategory": "reset"
  }'
```

Expected response:
```json
{
  "status": "accepted",
  "orchestration_ticket_id": "ORCH-000001",
  "category": "password_reset",
  "auto_resolve": true,
  "message": "Ticket assigned to AI agent for resolution"
}
```

### 5. Check Ticket Status

```bash
curl http://localhost:5001/api/tickets/ORCH-000001
```

---

## Monitoring

### View Orchestrator Stats

```bash
curl http://localhost:5001/api/stats
```

Response:
```json
{
  "total_tickets": 10,
  "by_status": {
    "resolved": 7,
    "in_progress": 2,
    "failed": 1
  },
  "by_category": {
    "password_reset": 5,
    "user_creation": 3,
    "integration_error": 2
  },
  "auto_resolved": 7,
  "requires_human": 1
}
```

### View All Tickets

```bash
curl http://localhost:5001/api/tickets
```

### Filter by Status

```bash
curl "http://localhost:5001/api/tickets?status=in_progress"
```

---

## Logs

### View Mistral Agent Logs
```bash
# If running manually
tail -f logs/mistral_agent.log

# If running as service
sudo journalctl -u mistral-agent -f
```

### View Orchestrator Logs
```bash
# If running manually
tail -f logs/orchestrator.log

# If running as service
sudo journalctl -u ticket-orchestrator -f
```

---

## Troubleshooting

### Issue: MCP Connection Fails

**Check:**
```bash
# Test MCP server directly
python3 mcp_unified.py
```

**Fix:** Ensure Python path is correct and all dependencies installed

### Issue: Ticket Not Auto-Resolved

**Check:**
1. Orchestrator logs
2. Mistral agent logs
3. MCP server connectivity

```bash
curl http://localhost:5001/api/tickets/ORCH-XXXXXX
```

### Issue: ServiceNow Webhook Not Working

**Check:**
1. Network connectivity from ServiceNow to orchestrator
2. Firewall rules (port 5001)
3. ServiceNow Business Rule is active

---

## Adding Your Mistral AI Agent Logic

### Where to Add Your Agent

Edit `mistral_agent_mcp_integration.py`:

```python
class TicketResolver:
    async def resolve_ticket(self, ticket_data: Dict) -> Dict:
        """
        ADD YOUR MISTRAL AI AGENT LOGIC HERE

        Current flow:
        1. Receive ticket data
        2. Route to handler based on action_type
        3. Use MCP tools to execute actions

        You can integrate:
        - Your Mistral AI model for decision making
        - Custom prompt engineering
        - Agent reasoning logic
        """

        # Example: Add Mistral AI decision logic
        # mistral_decision = await self.call_mistral_ai(ticket_data)
        # based on decision, call appropriate MCP tools

        action_type = ticket_data.get("action_type")
        # ... rest of the code
```

### Integrating Mistral AI Model

```python
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

class TicketResolver:
    def __init__(self, mcp_connector: MCPConnector):
        self.mcp = mcp_connector
        self.mistral_client = MistralClient(api_key="your_api_key")

    async def analyze_ticket_with_mistral(self, ticket_data: Dict) -> Dict:
        """Use Mistral AI to analyze ticket and decide actions"""

        messages = [
            ChatMessage(role="user", content=f"""
            Analyze this support ticket and determine the best resolution approach:

            Ticket: {ticket_data['context']['description']}
            Category: {ticket_data['action_type']}
            Priority: {ticket_data['context']['priority']}

            Available MCP tools: {await self.mcp.list_tools()}

            Provide:
            1. Root cause analysis
            2. Recommended actions
            3. Which MCP tools to use
            """)
        ]

        response = self.mistral_client.chat(
            model="mistral-large-latest",
            messages=messages
        )

        return response.choices[0].message.content
```

---

## Next Steps

1. ✅ **Test the system end-to-end**
2. ✅ **Add your Mistral AI agent logic**
3. ✅ **Configure ServiceNow webhook**
4. ✅ **Monitor and tune classification rules**
5. ✅ **Add more ticket types as needed**
6. ✅ **Set up production monitoring**

---

## Support

For issues, check:
- MCP server logs
- Agent API logs
- Orchestrator logs
- ServiceNow outbound message logs

All components have health check endpoints:
- Mistral Agent: `http://localhost:5000/api/health`
- Orchestrator: `http://localhost:5001/api/health`
