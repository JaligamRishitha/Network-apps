# Salesforce CRM MCP Server Setup Guide

## Overview
This MCP (Model Context Protocol) server provides tools to interact with your Salesforce Clone backend API. It exposes all CRUD operations and business logic through standardized MCP tools.

## Installation

### 1. Install MCP Dependencies
```bash
pip install -r mcp_requirements.txt
```

### 2. Configure Kiro CLI
Add the MCP server to your Kiro CLI configuration. The configuration file is typically located at:
- Linux/Mac: `~/.kiro/config.json`
- Windows: `%APPDATA%\kiro\config.json`

Add this to your config:
```json
{
  "mcpServers": {
    "salesforce-crm": {
      "command": "python",
      "args": ["/home/pradeep1a/Network-apps/Salesforce/mcp_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. Ensure Backend is Running
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Available Tools

### Authentication
- `login(username, password)` - Login and get JWT token
- `get_current_user()` - Get current authenticated user
- `list_users()` - List all users

### Contacts
- `list_contacts(skip, limit, search)` - List contacts
- `get_contact(contact_id)` - Get contact details
- `create_contact(first_name, last_name, email, phone, account_id)` - Create contact
- `update_contact(contact_id, **kwargs)` - Update contact
- `delete_contact(contact_id)` - Delete contact

### Accounts
- `list_accounts(skip, limit, search)` - List accounts
- `get_account(account_id)` - Get account details
- `create_account(name, industry, revenue, employees)` - Create account
- `update_account(account_id, **kwargs)` - Update account
- `delete_account(account_id)` - Delete account

### Leads
- `list_leads(skip, limit, search)` - List leads
- `get_lead(lead_id)` - Get lead details
- `create_lead(first_name, last_name, company, email, phone, lead_score)` - Create lead
- `update_lead(lead_id, **kwargs)` - Update lead
- `delete_lead(lead_id)` - Delete lead
- `convert_lead(lead_id)` - Convert lead to account/contact/opportunity

### Opportunities
- `list_opportunities(skip, limit, search)` - List opportunities
- `get_opportunity(opportunity_id)` - Get opportunity details
- `create_opportunity(name, account_id, amount, stage, close_date)` - Create opportunity
- `update_opportunity(opportunity_id, **kwargs)` - Update opportunity
- `delete_opportunity(opportunity_id)` - Delete opportunity

### Cases
- `list_cases(skip, limit, search)` - List cases
- `get_case(case_id)` - Get case details
- `create_case(subject, contact_id, priority, status, description)` - Create case
- `update_case(case_id, **kwargs)` - Update case
- `delete_case(case_id)` - Delete case
- `escalate_case(case_id)` - Escalate case
- `merge_cases(case_id_1, case_id_2)` - Merge duplicate cases

### Dashboard
- `get_dashboard_stats()` - Get dashboard statistics
- `get_recent_records()` - Get recent records
- `global_search(query)` - Search across all objects

### Activities
- `list_activities(skip, limit)` - List activities
- `create_activity(activity_type, subject, related_object_type, related_object_id, description)` - Create activity

### Logs
- `get_logs(skip, limit)` - Get system logs

### Health
- `health_check()` - Check API health

## Usage Examples

### Login
```
/login username=admin password=admin123
```

### Create a Contact
```
/create_contact first_name=John last_name=Doe email=john@example.com phone=555-1234
```

### Search Leads
```
/list_leads search=acme
```

### Convert a Lead
```
/convert_lead lead_id=5
```

### Global Search
```
/global_search query=customer
```

## Environment Variables

The MCP server uses these environment variables (optional):
- `API_BASE_URL` - Backend API URL (default: `http://localhost:8000`)
- `DEFAULT_TOKEN` - Pre-set JWT token (optional)

## Troubleshooting

### Connection Refused
- Ensure backend is running on `http://localhost:8000`
- Check firewall settings

### Authentication Failed
- Use `/login` tool first to get a token
- Token is automatically stored for subsequent calls

### Tool Not Found
- Restart Kiro CLI after updating config
- Verify MCP server is properly configured

## Architecture

The MCP server:
1. Receives tool calls from Kiro CLI
2. Authenticates with JWT tokens
3. Makes HTTP requests to FastAPI backend
4. Returns JSON responses

All API calls are async and support pagination, search, and filtering.
