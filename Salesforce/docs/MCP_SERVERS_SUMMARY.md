# MCP Servers Configuration - Complete

## Three MCP Servers Configured

### 1. Salesforce CRM (`salesforce-crm`)
**File:** `mcp_server.py`
**Tools:** 40+ tools for CRM operations
- Authentication (3 tools)
- Contacts (5 tools)
- Accounts (5 tools)
- Leads (6 tools)
- Opportunities (5 tools)
- Cases (7 tools)
- Dashboard (3 tools)
- Activities (2 tools)
- Logs (1 tool)
- Health (1 tool)

### 2. MuleSoft Integration (`mulesoft-integration`)
**File:** `mcp_mulesoft.py`
**Tools:** 7 tools for SAP integration
- `sync_case_to_sap` - Sync single case to SAP
- `sync_cases_batch` - Batch sync multiple cases
- `get_case_sync_status` - Get sync status
- `get_sap_case_status` - Query SAP case status
- `trigger_auto_sync` - Auto-sync case
- `mulesoft_health_check` - Health check
- `get_mulesoft_config` - Get configuration

### 3. ServiceNow Integration (`servicenow-integration`)
**File:** `mcp_servicenow.py`
**Tools:** 15+ tools for ITSM operations
- Incidents (5 tools)
- Change Requests (4 tools)
- Problems (3 tools)
- Configuration Items (2 tools)
- Users (2 tools)
- Knowledge Base (2 tools)
- Health Check (1 tool)

## Configuration File
**Location:** `~/.kiro/config.json`

```json
{
  "mcpServers": {
    "salesforce-crm": {...},
    "mulesoft-integration": {...},
    "servicenow-integration": {...}
  }
}
```

## Usage

### Salesforce CRM
```
/login username=admin password=admin123
/list_contacts
/create_lead first_name=John last_name=Doe company=ACME
```

### MuleSoft Integration
```
/sync_case_to_sap case_id=1 operation=CREATE
/get_case_sync_status case_id=1
/mulesoft_health_check
```

### ServiceNow Integration
```
/list_incidents
/create_incident short_description="Network Down" priority=1
/search_knowledge_base query="password reset"
```

## Configuration Required

### ServiceNow
Update credentials in `mcp_servicenow.py`:
```python
SERVICENOW_INSTANCE = "https://your-instance.service-now.com"
SERVICENOW_USER = "your-username"
SERVICENOW_PASSWORD = "your-password"
```

### MuleSoft
Configured via backend environment variables:
- `MULESOFT_BASE_URL`
- `MULESOFT_CLIENT_ID`
- `MULESOFT_CLIENT_SECRET`

## Next Steps

1. Restart Kiro CLI
2. All three MCP servers will be available
3. Use `/help` to see all available tools
4. Update ServiceNow credentials for ITSM integration
5. Configure MuleSoft credentials in backend

## Files Created

- `mcp_server.py` - Salesforce CRM MCP server
- `mcp_mulesoft.py` - MuleSoft integration MCP server
- `mcp_servicenow.py` - ServiceNow integration MCP server
- `~/.kiro/config.json` - Updated with all three servers
