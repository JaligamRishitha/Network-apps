# MCP Tools Added for Agent & Orchestrator

## Summary

Added appointment validation and orchestration tools to existing MCP servers instead of creating new specialized servers.

---

## 1. SAP MCP Server (`/home/pradeep1a/Network-apps/SAP_clone/mcp_sap.py`)

**Port:** 8092
**Base URL Fixed:** Changed from `http://207.180.217.117:2004` to `http://207.180.217.117:4798`

### New Tools Added (10 tools)

#### For Agent Validation:

1. **`validate_appointment`**
   - **Purpose:** Main validation tool for agent
   - **Endpoint:** `POST /api/appointments/validate`
   - **Input:** `required_parts`, `required_skills`, `location`, `cost_center_id`, `estimated_cost`
   - **Output:** Complete validation response with parts, technicians, location, budget
   - **Usage:** Agent calls this to validate ServiceNow tickets

2. **`search_materials_by_query`**
   - **Purpose:** Search materials in inventory by keyword
   - **Endpoint:** `GET /api/appointments/parts/search?query={query}`
   - **Usage:** Agent searches for alternative parts

3. **`find_available_technicians`**
   - **Purpose:** Find available engineers with optional skill filter
   - **Endpoint:** `GET /api/appointments/technicians/available?skill={skills}`
   - **Usage:** Agent finds engineers for assignment

4. **`validate_technician_skills`**
   - **Purpose:** Check if technicians with required skills exist
   - **Endpoint:** `GET /api/appointments/technicians/validate?required_skills={skills}`
   - **Usage:** Agent validates skill availability

5. **`search_location_assets`**
   - **Purpose:** Search for assets/locations in SAP
   - **Endpoint:** `GET /api/appointments/locations/search?location={location}`
   - **Usage:** Agent verifies work location exists

6. **`check_cost_center_budget`**
   - **Purpose:** Verify cost center has sufficient budget
   - **Endpoint:** `GET /api/appointments/budget/check?cost_center_id={id}&estimated_cost={amount}`
   - **Usage:** Agent checks budget availability

7. **`get_material_recommendations`**
   - **Purpose:** Get recommended materials for common appointment types
   - **Endpoint:** `GET /api/appointments/materials/recommendations`
   - **Usage:** Agent gets material suggestions

#### For Orchestrator Execution:

8. **`reserve_materials_for_work_order`**
   - **Purpose:** Reserve materials from inventory for work order
   - **Endpoint:** `POST /api/v1/mm/material-reservations`
   - **Input:** `work_order_id`, `material_id`, `quantity`, `required_date`
   - **Usage:** Orchestrator reserves materials after agent approval

9. **`update_work_order_status`**
   - **Purpose:** Update work order status and notes
   - **Endpoint:** `PATCH /api/v1/work-order-flow/work-orders/{id}`
   - **Input:** `status`, `updated_by`, `notes`
   - **Usage:** Orchestrator updates order status

10. **Existing tools remain:** All 60+ existing tools (tickets, PM, MM, FI, sales, work orders) still available

---

## 2. ServiceNow MCP Server (`/home/pradeep1a/Network-apps/serviceNow/mcp_servicenow.py`)

**Port:** 8093
**Mode:** Mock (uses in-memory data)

### New Tools Added (4 tools)

#### For Orchestrator:

1. **`add_work_note`**
   - **Purpose:** Add work notes to ServiceNow incident
   - **Input:** `incident_id`, `work_note`
   - **Usage:** Orchestrator adds notes about agent decisions and actions

2. **`assign_incident`**
   - **Purpose:** Assign incident to user and set to In Progress
   - **Input:** `incident_id`, `assigned_to`
   - **Usage:** Orchestrator assigns ticket to engineer after agent approval

3. **`link_sap_work_order`**
   - **Purpose:** Link SAP work order ID to ServiceNow incident
   - **Input:** `incident_id`, `sap_work_order_id`
   - **Usage:** Orchestrator links SAP order for tracking

4. **`get_pending_tickets`**
   - **Purpose:** Get incidents in New or In Progress state
   - **Input:** `limit` (optional, default 20)
   - **Usage:** Orchestrator polls for tickets needing processing

5. **Existing tools remain:** All existing incident, change, problem, user, CMDB tools still available

---

## 3. Salesforce MCP Server (`/home/pradeep1a/Network-apps/Salesforce/mcp_server.py`)

**Port:** 8090
**Base URL:** `http://207.180.217.117:4799`

### Status: No changes needed

**Reason:** Salesforce MCP already has comprehensive tools for:
- Contacts, Accounts, Leads, Opportunities, Cases
- Service Appointments (if implemented)
- Authentication and users

**Orchestrator can use existing tools** to update appointment status after SAP order creation.

---

## 4. Unified MCP Server (`/home/pradeep1a/Network-apps/mcp_unified.py`)

**Port:** stdio mode (not HTTP server)
**Purpose:** Cross-application workflows and helper functions

### New Tools Added (5 tools)

#### Notification Tools:

1. **`send_email`**
   - **Purpose:** Send email to engineers, managers, customers
   - **Input:** `to`, `subject`, `body`, `cc`, `bcc`
   - **Usage:** Orchestrator notifies engineer of work order assignment
   - **Mode:** Mock (returns success without actually sending)

2. **`send_sms`**
   - **Purpose:** Send SMS alert for urgent notifications
   - **Input:** `phone`, `message`
   - **Usage:** Orchestrator sends SMS for emergency callouts
   - **Mode:** Mock

#### Helper Tools:

3. **`log_event`**
   - **Purpose:** Log workflow events for audit trail
   - **Input:** `event_type`, `event_data`, `source`
   - **Usage:** Track all orchestrator and agent actions
   - **Mode:** Mock (would write to database/log file in production)

4. **`escalate_to_human`**
   - **Purpose:** Escalate to human when agent can't auto-approve
   - **Input:** `reason`, `priority`, `context`, `notify_managers`
   - **Usage:** Agent/orchestrator escalates complex cases
   - **Mode:** Mock

5. **`get_workflow_status`**
   - **Purpose:** Get current status of workflow execution
   - **Input:** `workflow_id`
   - **Usage:** Monitor progress through Salesforce → ServiceNow → Agent → SAP
   - **Mode:** Mock

6. **Existing tools remain:** Service discovery, health checks, cross-platform sync

---

## Tool Usage by Role

### **Agent Uses (SAP MCP Only):**

```python
# Agent validation workflow
validation = sap_mcp.validate_appointment(
    required_parts="11kV cable, Ring Main Unit",
    required_skills="HV AP, 11kV",
    location="London",
    cost_center_id="CC-UKPN-EMERG",
    estimated_cost=45000.00
)

# Optional: Search for alternatives
alternatives = sap_mcp.search_materials_by_query("11kV cable")

# Return decision to orchestrator
return {
    "decision": "APPROVED" if validation["valid"] else "REJECTED",
    "validation_result": validation
}
```

### **Orchestrator Uses (All MCPs):**

```python
# 1. Get ticket from ServiceNow
ticket = servicenow_mcp.get_incident("INC0010123")

# 2. Send to agent for validation
agent_decision = agent.validate(ticket)

# 3. If approved, create SAP orders
if agent_decision["decision"] == "APPROVED":
    # Create maintenance order
    order = sap_mcp.create_maintenance_order(...)

    # Reserve materials
    sap_mcp.reserve_materials_for_work_order(...)

    # Update ServiceNow
    servicenow_mcp.assign_incident(ticket_id, engineer_name)
    servicenow_mcp.link_sap_work_order(ticket_id, order_id)

    # Send notifications
    unified_mcp.send_email(engineer_email, subject, body)
    unified_mcp.send_sms(engineer_phone, alert_message)

    # Log event
    unified_mcp.log_event("order_created", order_data)
```

---

## Configuration Updates

### SAP MCP Server Base URL Fixed:
```python
# Before
API_BASE_URL = "http://207.180.217.117:2004"

# After
API_BASE_URL = "http://207.180.217.117:4798"
```

---

## How to Restart MCP Servers

```bash
# SAP MCP Server
cd /home/pradeep1a/Network-apps/SAP_clone
pkill -f "mcp_sap.py"
nohup python3 mcp_sap.py > mcp_sap.log 2>&1 &

# ServiceNow MCP Server
cd /home/pradeep1a/Network-apps/serviceNow
pkill -f "mcp_servicenow.py"
nohup python3 mcp_servicenow.py > mcp_servicenow.log 2>&1 &

# Unified MCP (stdio mode - used by orchestrator directly)
# No restart needed - invoked per-use
```

---

## Testing the Tools

### Test SAP Validation:
```bash
# Connect to SAP MCP on port 8092
# Call validate_appointment tool with sample data
```

### Test ServiceNow Tools:
```bash
# Connect to ServiceNow MCP on port 8093
# Call get_pending_tickets tool
```

---

## Summary of Changes

| MCP Server | Tools Added | Purpose |
|------------|-------------|---------|
| **SAP** | 10 new tools | Agent validation + orchestrator order management |
| **ServiceNow** | 4 new tools | Orchestrator ticket management |
| **Salesforce** | 0 (no changes) | Already has needed tools |
| **Unified** | 5 new tools | Notifications, logging, helpers |

**Total:** 19 new tools added to existing MCP servers
**Result:** Complete agent & orchestrator workflow support without creating new MCP servers

---

**Last Updated:** 2026-02-05
**Status:** ✅ All tools added and ready for use
