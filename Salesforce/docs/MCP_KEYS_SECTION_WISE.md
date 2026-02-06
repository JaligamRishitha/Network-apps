# MCP Keys - Section Wise

## 1. SALESFORCE CRM
**Server Key:** `salesforce-crm`

### Authentication
- `login`
- `get_current_user`
- `list_users`

### Contacts
- `list_contacts`
- `get_contact`
- `create_contact`
- `update_contact`
- `delete_contact`

### Accounts
- `list_accounts`
- `get_account`
- `create_account`
- `update_account`
- `delete_account`

### Leads
- `list_leads`
- `get_lead`
- `create_lead`
- `update_lead`
- `delete_lead`
- `convert_lead`

### Opportunities
- `list_opportunities`
- `get_opportunity`
- `create_opportunity`
- `update_opportunity`
- `delete_opportunity`

### Cases
- `list_cases`
- `get_case`
- `create_case`
- `update_case`
- `delete_case`
- `escalate_case`
- `merge_cases`

### Dashboard
- `get_dashboard_stats`
- `get_recent_records`
- `global_search`

### Activities
- `list_activities`
- `create_activity`

### Logs
- `get_logs`

### Health
- `health_check`

---

## 2. MULESOFT INTEGRATION
**Server Key:** `mulesoft-integration`

### Case Synchronization
- `sync_case_to_sap`
- `sync_cases_batch`

### Status & Monitoring
- `get_case_sync_status`
- `get_sap_case_status`
- `trigger_auto_sync`

### Configuration
- `mulesoft_health_check`
- `get_mulesoft_config`

---

## 3. SERVICENOW INTEGRATION
**Server Key:** `servicenow-integration`

### Incidents
- `list_incidents`
- `get_incident`
- `create_incident`
- `update_incident`
- `close_incident`

### Change Requests
- `list_change_requests`
- `get_change_request`
- `create_change_request`
- `update_change_request`

### Problems
- `list_problems`
- `get_problem`
- `create_problem`

### Configuration Items
- `list_config_items`
- `get_config_item`

### Users
- `list_users`
- `get_user`

### Knowledge Base
- `search_knowledge_base`
- `get_knowledge_article`

### Health
- `servicenow_health_check`
