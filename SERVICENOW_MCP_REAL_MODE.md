# ServiceNow MCP: Mock Mode → Real Mode

## Current Situation

### Mock Mode (Current - OLD):
- **File:** `/home/pradeep1a/Network-apps/serviceNow/mcp_servicenow.py`
- **Status:** Using in-memory fake data
- **Reason:** Quick testing without dependencies
- **Problem:** Not connected to real ServiceNow database

### Real Backend (Available):
- **Container:** `servicenow-backend` on port 4780
- **Database:** PostgreSQL `servicenow-db` on port 4793
- **Status:** ✅ Running and healthy
- **API:** FastAPI with /incidents/, /tickets/, /approvals/

---

## Solution: Real Mode MCP

### New File Created:
**📄 `/home/pradeep1a/Network-apps/serviceNow/mcp_servicenow_real.py`**

**Features:**
- Connects to real ServiceNow backend at `http://localhost:4780`
- Uses actual PostgreSQL database
- All tools work with real incidents/tickets/approvals
- Production-ready

---

## How to Switch to Real Mode

### Option 1: Replace Mock with Real (Recommended)

```bash
cd /home/pradeep1a/Network-apps/serviceNow

# Backup mock version
cp mcp_servicenow.py mcp_servicenow_mock_backup.py

# Replace with real version
cp mcp_servicenow_real.py mcp_servicenow.py

# Stop old MCP
pkill -f "mcp_servicenow"

# Start new MCP in real mode
nohup python3 mcp_servicenow.py > mcp_servicenow.log 2>&1 &

# Check status
tail -f mcp_servicenow.log
```

### Option 2: Run Both (Development)

```bash
# Keep mock on port 8093
# Run real on different port 8094

# Edit mcp_servicenow_real.py
# Change: MCP_PORT = 8094

# Start real mode
nohup python3 mcp_servicenow_real.py > mcp_real.log 2>&1 &
```

---

## Testing Real Mode

### 1. Health Check
```bash
# Test backend is running
curl http://localhost:4780/health

# Expected:
{
  "status": "healthy",
  "service": "servicenow-backend",
  "timestamp": "2026-02-05T..."
}
```

### 2. Test MCP Connection
```python
# Using MCP client
import httpx

# Connect to MCP
response = httpx.post(
    "http://localhost:8093/messages",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "servicenow_health_check"
        }
    }
)
```

### 3. Create Test Ticket
```bash
# Via ServiceNow backend directly
curl -X POST http://localhost:4780/tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test ServiceNow Real Mode",
    "description": "Testing MCP connection",
    "priority": "3",
    "category": "inquiry",
    "status": "open"
  }'
```

### 4. List Tickets via MCP
```python
# Use MCP tool: list_incidents or get_pending_tickets
# Should return real tickets from database
```

---

## Comparison: Mock vs Real

| Feature | Mock Mode | Real Mode |
|---------|-----------|-----------|
| **Data Storage** | In-memory (lost on restart) | PostgreSQL database |
| **Persistence** | ❌ No | ✅ Yes |
| **Shared Data** | ❌ No (per MCP instance) | ✅ Yes (shared database) |
| **Authentication** | None | Backend handles it |
| **Production Ready** | ❌ No | ✅ Yes |
| **Testing** | ✅ Easy | Requires backend |
| **Real Workflows** | ❌ No | ✅ Yes |

---

## Why Mock Mode Was Used Initially

1. **Quick Development**
   - No need to set up database
   - No authentication needed
   - Faster iteration

2. **Testing**
   - Predictable data
   - No external dependencies
   - Easy to debug

3. **Demonstration**
   - Works without real ServiceNow
   - Can show MCP functionality
   - No credentials needed

---

## Why Switch to Real Mode Now

1. **Production Workflow**
   - Agent needs real tickets from Salesforce
   - Orchestrator needs to update real tickets
   - Integration with SAP requires persistence

2. **Data Persistence**
   - Tickets survive MCP restarts
   - Shared across all services
   - Audit trail in database

3. **Real Integration**
   - Salesforce → ServiceNow → Agent → SAP
   - All services use same tickets
   - True end-to-end workflow

---

## Orchestrator Integration

### With Real Mode:

```python
# Orchestrator flow:
# 1. Salesforce creates appointment
# 2. ServiceNow ticket auto-created (in DB)
# 3. Orchestrator polls tickets via MCP
tickets = servicenow_mcp.get_pending_tickets()

# 4. Send to agent for validation
for ticket in tickets:
    decision = agent.validate(ticket)

    # 5. Update ticket in real database
    if decision["approved"]:
        servicenow_mcp.assign_incident(
            ticket_id=ticket["id"],
            assigned_to=decision["engineer"]
        )
        servicenow_mcp.link_sap_work_order(
            ticket_id=ticket["id"],
            sap_work_order_id=sap_order_id
        )
```

---

## Troubleshooting

### MCP Won't Start
```bash
# Check dependencies
pip3 install httpx mcp starlette uvicorn

# Check port availability
sudo netstat -tlnp | grep 8093

# Check backend is running
docker ps | grep servicenow
```

### Can't Connect to Backend
```bash
# Test backend directly
curl http://localhost:4780/health

# Check logs
docker logs servicenow-backend

# Restart backend if needed
docker restart servicenow-backend
```

### Authentication Errors
```bash
# Backend might require auth for some endpoints
# MCP handles this automatically
# Check if token is needed:
curl http://localhost:4780/tickets/

# If auth required, MCP will need to login first
```

---

## Recommendation

**Switch to Real Mode immediately** because:

1. ✅ You already have a real ServiceNow backend running
2. ✅ Your workflow needs real data persistence
3. ✅ Agent & orchestrator need shared state
4. ✅ Integration testing requires real database
5. ✅ Mock mode is only for demos/initial development

---

## Quick Migration Script

```bash
#!/bin/bash
# migrate_servicenow_mcp_to_real.sh

cd /home/pradeep1a/Network-apps/serviceNow

echo "Backing up mock MCP..."
cp mcp_servicenow.py mcp_servicenow_mock.py.backup

echo "Replacing with real MCP..."
cp mcp_servicenow_real.py mcp_servicenow.py

echo "Stopping old MCP..."
pkill -f "mcp_servicenow"

echo "Starting real mode MCP..."
nohup python3 mcp_servicenow.py > mcp_servicenow.log 2>&1 &

sleep 3

echo "Checking status..."
if ps aux | grep -v grep | grep mcp_servicenow > /dev/null; then
    echo "✅ ServiceNow MCP started in REAL MODE"
    echo "📝 Logs: tail -f mcp_servicenow.log"
else
    echo "❌ Failed to start. Check logs:"
    cat mcp_servicenow.log
fi
```

---

**Status:** Real mode MCP created and ready to use
**Action Required:** Switch from mock to real mode
**Files:**
- Mock: `/home/pradeep1a/Network-apps/serviceNow/mcp_servicenow.py` (OLD)
- Real: `/home/pradeep1a/Network-apps/serviceNow/mcp_servicenow_real.py` (NEW)
