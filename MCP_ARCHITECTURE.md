# MCP Architecture & Communication Flow

## 1. What is MCP (Model Context Protocol)?

MCP is a protocol that allows AI models (like Claude) to interact with external tools, APIs, and databases through a standardized interface.

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   AI MODEL   │  JSON   │  MCP SERVER  │  HTTP   │   EXTERNAL   │
│   (Claude)   │ ◄─────► │   (Python)   │ ◄─────► │     APIs     │
│              │   RPC   │              │  REST   │              │
└──────────────┘         └──────────────┘         └──────────────┘

  MCP Client               MCP Server                Backend Services
```

---

## 2. High-Level Architecture

```
                                 ┌─────────────────────┐
                                 │      Claude AI      │
                                 │    (MCP Client)     │
                                 └──────────┬──────────┘
                                            │
                                   JSON-RPC over stdio
                                            │
                                            ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                          MASTER MCP (Unified Hub)                             │
│                           mcp_unified.py (716 lines)                          │
│                              45+ MCP Tools                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│  list_services() │ health_check_all() │ cross_platform_search()              │
│  login_salesforce() │ login_sap() │ create_incident_all_platforms()          │
└───────────────────────────────────────────────────────────────────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              │                             │                             │
              ▼                             ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│    SALESFORCE MCP       │   │    SERVICENOW MCP       │   │       SAP MCP           │
│   mcp_server.py         │   │   mcp_servicenow.py     │   │     mcp_sap.py          │
│     47+ Tools           │   │      20+ Tools          │   │      25+ Tools          │
└───────────┬─────────────┘   └───────────┬─────────────┘   └───────────┬─────────────┘
            │                             │                             │
       HTTP REST                     HTTP REST                     HTTP REST
            │                             │                             │
            ▼                             ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   SALESFORCE BACKEND    │   │   SERVICENOW BACKEND    │   │      SAP BACKEND        │
│   FastAPI (Port 8000)   │   │   FastAPI (Port 4780)   │   │   FastAPI (Port 4798)   │
└───────────┬─────────────┘   └───────────┬─────────────┘   └───────────┬─────────────┘
            │                             │                             │
            ▼                             ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   PostgreSQL (4791)     │   │   PostgreSQL (4793)     │   │   PostgreSQL (4794)     │
│   salesforce_crm        │   │   servicenow_db         │   │   sap_erp               │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
```

---

## 3. Detailed Communication Flow

### Creating a Contact via MCP (Step-by-Step)

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │    │ Claude  │    │   MCP   │    │ FastAPI │    │PostgreSQL│
│         │    │   AI    │    │ Server  │    │ Backend │    │   DB    │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │              │
     │ "Create a    │              │              │              │
     │  contact     │              │              │              │
     │  John Doe"   │              │              │              │
     │─────────────►│              │              │              │
     │              │              │              │              │
     │              │ call_tool    │              │              │
     │              │ create_      │              │              │
     │              │ contact()    │              │              │
     │              │─────────────►│              │              │
     │              │              │              │              │
     │              │              │ POST /api/   │              │
     │              │              │ contacts     │              │
     │              │              │ {first_name: │              │
     │              │              │  "John",...} │              │
     │              │              │─────────────►│              │
     │              │              │              │              │
     │              │              │              │ INSERT INTO  │
     │              │              │              │ contacts     │
     │              │              │              │─────────────►│
     │              │              │              │              │
     │              │              │              │   {id: 9}    │
     │              │              │              │◄─────────────│
     │              │              │              │              │
     │              │              │ {id: 9,      │              │
     │              │              │  first_name: │              │
     │              │              │  "John",...} │              │
     │              │◄─────────────│              │              │
     │              │              │              │              │
     │ "Contact     │              │              │              │
     │  created     │              │              │              │
     │  with ID 9"  │              │              │              │
     │◄─────────────│              │              │              │
```

---

## 4. MCP Server Components

```python
# SERVER INITIALIZATION
from mcp.server import Server
server = Server("salesforce-crm")

# TOOL REGISTRATION
@server.call_tool()
async def create_contact(first_name, last_name, email):
    result = await api_call("POST", "/api/contacts", data)
    return [TextContent(type="text", text=json.dumps(result))]

# API CALL HELPER
async def api_call(method, endpoint, data, token):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers, json=data)
    return response.json()
```

---

## 5. External Application Integration

```
                    ┌─────────────────────────────────────┐
                    │           MASTER MCP HUB            │
                    └─────────────────┬───────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  SALESFORCE   │           │  SERVICENOW   │           │      SAP      │
│    (Local)    │           │  (External)   │           │  (External)   │
├───────────────┤           ├───────────────┤           ├───────────────┤
│ Protocol:     │           │ Protocol:     │           │ Protocol:     │
│ HTTP REST     │           │ HTTP REST     │           │ HTTP REST     │
│               │           │               │           │               │
│ Auth:         │           │ Auth:         │           │ Auth:         │
│ JWT Bearer    │           │ Basic Auth    │           │ OAuth2        │
│               │           │               │           │               │
│ Base URL:     │           │ Base URL:     │           │ Base URL:     │
│ localhost:8000│           │ *.service-now │           │ sap-instance  │
│               │           │ .com          │           │ .com          │
└───────────────┘           └───────────────┘           └───────────────┘
```

---

## 6. MuleSoft Integration Flow (Salesforce → SAP)

```
     SALESFORCE                   MULESOFT                      SAP
    ┌──────────┐               ┌──────────┐               ┌──────────┐
    │  Case    │               │Integration│              │  SAP     │
    │ Created  │               │  Layer    │               │  Case    │
    └────┬─────┘               └────┬─────┘               └────┬─────┘
         │                          │                          │
         │  1. Create Case          │                          │
         │  POST /api/cases         │                          │
         │─────────────────────────►│                          │
         │                          │                          │
         │  2. Trigger Sync         │                          │
         │  POST /api/sap-          │                          │
         │  integration/cases/sync  │                          │
         │─────────────────────────►│                          │
         │                          │                          │
         │                          │  3. Transform Data       │
         │                          │  CRM Case → SAP Format   │
         │                          │                          │
         │                          │  4. POST to SAP          │
         │                          │  /api/sap/cases          │
         │                          │─────────────────────────►│
         │                          │                          │
         │                          │  5. SAP Case ID          │
         │                          │  {sap_case_id: "SAP123"} │
         │                          │◄─────────────────────────│
         │                          │                          │
         │  6. Update Mapping       │                          │
         │  sap_case_mapping table  │                          │
         │◄─────────────────────────│                          │
```

---

## 7. JWT Authentication Flow

```
  ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
  │  Claude  │         │   MCP    │         │ FastAPI  │         │   DB     │
  │    AI    │         │  Server  │         │ Backend  │         │          │
  └────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
       │                    │                    │                    │
       │  1. login()        │                    │                    │
       │───────────────────►│                    │                    │
       │                    │                    │                    │
       │                    │ 2. POST /api/auth/ │                    │
       │                    │    login           │                    │
       │                    │ {username,password}│                    │
       │                    │───────────────────►│                    │
       │                    │                    │                    │
       │                    │                    │ 3. Verify user     │
       │                    │                    │───────────────────►│
       │                    │                    │                    │
       │                    │                    │ 4. User data       │
       │                    │                    │◄───────────────────│
       │                    │                    │                    │
       │                    │                    │ 5. Generate JWT    │
       │                    │                    │                    │
       │                    │ 6. {access_token}  │                    │
       │                    │◄───────────────────│                    │
       │                    │                    │                    │
       │                    │ 7. Store token     │                    │
       │                    │                    │                    │
       │ 8. Login success   │                    │                    │
       │◄───────────────────│                    │                    │
       │                    │                    │                    │
       │  9. Subsequent API calls use Bearer token                   │
       │───────────────────►│ Authorization:     │                    │
       │                    │ Bearer eyJhbG...   │                    │
       │                    │───────────────────►│                    │
```

---

## 8. Cross-Platform Incident Creation

```
                              Master MCP
                         create_incident_all_platforms()
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │ SALESFORCE  │         │ SERVICENOW  │         │    SAP      │
    │             │         │             │         │             │
    │ POST /api/  │         │ POST /api/  │         │ POST /api/  │
    │ cases       │         │ now/table/  │         │ tickets     │
    │             │         │ incident    │         │             │
    └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
           │                       │                       │
           ▼                       ▼                       ▼
    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │ Case ID: 8  │         │ INC0012345  │         │ TKT-PM-001  │
    └─────────────┘         └─────────────┘         └─────────────┘
```

---

## 9. Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Presentation** | Claude AI (MCP Client), React Frontend |
| **MCP Layer** | Python 3.x, mcp library, httpx, asyncio |
| **API Layer** | FastAPI, Pydantic, python-jose, passlib |
| **Database Layer** | PostgreSQL 16, SQLAlchemy ORM, Docker |

---

## 10. Port Mapping

| Service | Port | Description |
|---------|------|-------------|
| Salesforce DB | 4791 | PostgreSQL - salesforce_crm |
| MuleSoft DB | 4792 | PostgreSQL - mulesoft_integration |
| ServiceNow DB | 4793 | PostgreSQL - servicenow_db |
| SAP DB | 4794 | PostgreSQL - sap_erp |
| MuleSoft Backend | 4797 | FastAPI - Integration Platform |
| SAP Backend | 4798 | FastAPI - SAP Clone API |
| Salesforce Backend | 4799/8000 | FastAPI - CRM API |
| ServiceNow Backend | 4780 | FastAPI - ITSM API |

---

## 11. MCP Configuration

```json
{
  "mcpServers": {
    "salesforce-crm": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    },
    "unified-hub": {
      "command": "python",
      "args": ["mcp_unified.py"],
      "env": {
        "SALESFORCE_URL": "http://localhost:8000",
        "SERVICENOW_URL": "https://instance.service-now.com",
        "SAP_URL": "http://localhost:4798"
      }
    }
  }
}
```

---

## 12. Key Communication Protocols

| From | To | Protocol | Format |
|------|-----|----------|--------|
| Claude AI | MCP Server | JSON-RPC over stdio | JSON |
| MCP Server | Backend API | HTTP REST | JSON |
| Backend API | Database | SQLAlchemy ORM | SQL |
| Salesforce | MuleSoft | HTTP REST | JSON |
| MuleSoft | SAP | HTTP REST | JSON |
| Master MCP | ServiceNow | HTTP REST + Basic Auth | JSON |

---

## 13. Summary

The MCP architecture enables AI models to interact with enterprise applications through a standardized protocol:

1. **Claude AI** sends natural language requests
2. **MCP Server** translates requests into API calls
3. **Backend APIs** process requests and interact with databases
4. **PostgreSQL** stores and retrieves data
5. **Integration Layer** (MuleSoft) syncs data across platforms

This architecture provides:
- **Unified Interface**: Single point of access for all enterprise systems
- **Scalability**: Each service can scale independently
- **Security**: JWT authentication and role-based access
- **Auditability**: All operations logged for compliance
