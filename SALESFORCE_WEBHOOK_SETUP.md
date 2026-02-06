# Salesforce → ServiceNow Automatic Ticket Creation

## Overview

Automatically creates ServiceNow tickets when appointments/work orders are created in Salesforce.

**Flow:**
```
Salesforce Appointment/Work Order Created
          ↓
    Webhook Trigger
          ↓
Your Backend (Port 8080)
          ↓
    MCP Unified Hub
          ↓
ServiceNow Ticket Created
          ↓
   Pending Approval
```

---

## Step 1: Start the Webhook Service

```bash
cd /home/pradeep1a/Network-apps

# Using venv Python
/home/pradeep1a/Network-apps/mcp_venv/bin/python3 salesforce_servicenow_webhook.py
```

Output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
✓ Connected to MCP unified-hub
```

---

## Step 2: Configure Salesforce Webhooks

### Option A: Using Salesforce Outbound Messages

1. **Go to Salesforce Setup**
2. **Create Workflow Rule for Appointments:**
   - Setup → Workflow Rules → New Rule
   - Object: `Appointment` (or your custom object)
   - Rule Name: "Create ServiceNow Ticket on Appointment"
   - Evaluation Criteria: "Created"
   - Rule Criteria: Formula evaluates to true: `TRUE`

3. **Add Outbound Message Action:**
   - Workflow Actions → Add Workflow Action → New Outbound Message
   - Name: "Send to ServiceNow Integration"
   - Endpoint URL: `http://149.102.158.71:8080/api/webhooks/salesforce/appointment`
   - Fields to Send:
     - `Id`
     - `Customer_Name__c`
     - `Appointment_Date__c`
     - `Appointment_Time__c`
     - `Service_Type__c`
     - `Location__c`
     - `Notes__c`
     - `Status__c`

4. **Activate Workflow**

5. **Repeat for Work Orders:**
   - Object: `WorkOrder`
   - Endpoint: `http://149.102.158.71:8080/api/webhooks/salesforce/workorder`
   - Fields: Id, Title, Description, Priority, Work_Order_Type__c, etc.

### Option B: Using Salesforce REST API Callout (Apex Trigger)

Create Apex Trigger in Salesforce:

```apex
// Trigger for Appointments
trigger AppointmentTrigger on Appointment__c (after insert) {
    for (Appointment__c apt : Trigger.new) {
        AppointmentWebhookService.sendToServiceNow(apt);
    }
}

// Service Class
public class AppointmentWebhookService {
    @future(callout=true)
    public static void sendToServiceNow(Appointment__c apt) {
        Http http = new Http();
        HttpRequest request = new HttpRequest();
        request.setEndpoint('http://149.102.158.71:8080/api/webhooks/salesforce/appointment');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');

        // Build JSON payload
        Map<String, Object> payload = new Map<String, Object>();
        payload.put('id', apt.Id);
        payload.put('customer_name', apt.Customer_Name__c);
        payload.put('appointment_date', String.valueOf(apt.Appointment_Date__c));
        payload.put('appointment_time', apt.Appointment_Time__c);
        payload.put('service_type', apt.Service_Type__c);
        payload.put('location', apt.Location__c);
        payload.put('notes', apt.Notes__c);
        payload.put('status', apt.Status__c);
        payload.put('created_by', UserInfo.getName());

        request.setBody(JSON.serialize(payload));

        HttpResponse response = http.send(request);

        if (response.getStatusCode() == 200) {
            System.debug('✓ ServiceNow ticket created');
        } else {
            System.debug('✗ Error: ' + response.getBody());
        }
    }
}
```

**Add Remote Site Setting:**
1. Setup → Remote Site Settings → New Remote Site
2. Name: `ServiceNow_Integration`
3. URL: `http://149.102.158.71:8080`
4. Active: ✓

---

## Step 3: Test the Integration

### Test Appointment Webhook

```bash
curl -X POST "http://localhost:8080/api/webhooks/salesforce/appointment" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 123,
    "customer_name": "John Doe",
    "appointment_date": "2026-02-10",
    "appointment_time": "10:00 AM",
    "service_type": "Installation",
    "location": "Customer Site A",
    "notes": "First floor, Building B",
    "status": "scheduled",
    "created_by": "admin"
  }'
```

Expected Response:
```json
{
  "salesforce_id": 123,
  "salesforce_type": "appointment",
  "servicenow_ticket_id": "abc123xyz",
  "servicenow_ticket_number": "INC0010001",
  "ticket_type": "service_request",
  "status": "pending_approval",
  "requires_approval": true,
  "message": "ServiceNow ticket INC0010001 created and awaiting approval"
}
```

### Test Work Order Webhook

```bash
curl -X POST "http://localhost:8080/api/webhooks/salesforce/workorder" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 456,
    "title": "HVAC System Maintenance",
    "description": "Annual maintenance check for HVAC system",
    "priority": "High",
    "assigned_to": "Tech Team A",
    "due_date": "2026-02-15",
    "work_order_type": "maintenance",
    "status": "new",
    "created_by": "admin"
  }'
```

Expected Response:
```json
{
  "salesforce_id": 456,
  "salesforce_type": "work_order",
  "servicenow_ticket_id": "def456uvw",
  "servicenow_ticket_number": "CHG0030001",
  "ticket_type": "change_request",
  "status": "pending_approval",
  "requires_approval": true,
  "message": "ServiceNow change_request CHG0030001 created and awaiting approval"
}
```

---

## Step 4: Approval Workflow

### Approve Appointment

```bash
curl -X POST "http://localhost:8080/api/approvals/appointments/123/approve?approver=manager@company.com"
```

Response:
```json
{
  "status": "approved",
  "appointment_id": 123,
  "servicenow_ticket": "INC0010001",
  "approved_by": "manager@company.com",
  "message": "Appointment approved and ticket updated"
}
```

### Approve Work Order

```bash
curl -X POST "http://localhost:8080/api/approvals/workorders/456/approve?approver=supervisor@company.com"
```

### Reject Work Order

```bash
curl -X POST "http://localhost:8080/api/approvals/workorders/456/reject?approver=supervisor@company.com&reason=Resource+unavailable"
```

---

## Step 5: Monitor Integration

### Check Integration Status

```bash
curl http://localhost:8080/api/integration/status
```

Response:
```json
{
  "status": "healthy",
  "mcp_connection": "connected",
  "servicenow_status": "healthy",
  "salesforce_status": "healthy",
  "timestamp": "2026-02-04T15:30:00"
}
```

### List Pending Approvals

```bash
curl http://localhost:8080/api/integration/pending-approvals
```

Response:
```json
{
  "total": 3,
  "tickets": [
    {
      "servicenow_number": "INC0010001",
      "short_description": "Service Appointment: Installation for John Doe",
      "priority": "3",
      "created": "2026-02-04 15:00:00",
      "sys_id": "abc123"
    }
  ]
}
```

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/webhooks/salesforce/appointment` | POST | Receive appointment webhook |
| `/api/webhooks/salesforce/workorder` | POST | Receive work order webhook |
| `/api/approvals/appointments/{id}/approve` | POST | Approve appointment |
| `/api/approvals/workorders/{id}/approve` | POST | Approve work order |
| `/api/approvals/workorders/{id}/reject` | POST | Reject work order |
| `/api/integration/status` | GET | Check integration health |
| `/api/integration/pending-approvals` | GET | List pending tickets |
| `/api/health` | GET | Health check |

---

## Ticket Type Mapping

| Salesforce Action | ServiceNow Ticket Type | Priority Mapping |
|-------------------|----------------------|------------------|
| Appointment (any type) | Service Request (Incident) | Medium (3) |
| Work Order (maintenance) | Change Request | High=2, Med=3, Low=4 |
| Work Order (installation) | Incident | High=1, Med=2, Low=3 |
| Work Order (repair) | Incident | High=1, Med=2, Low=3 |

---

## Production Deployment

### Run as Systemd Service

Create `/etc/systemd/system/salesforce-servicenow-integration.service`:

```ini
[Unit]
Description=Salesforce ServiceNow Integration
After=network.target

[Service]
Type=simple
User=pradeep1a
WorkingDirectory=/home/pradeep1a/Network-apps
Environment="PATH=/home/pradeep1a/Network-apps/mcp_venv/bin"
ExecStart=/home/pradeep1a/Network-apps/mcp_venv/bin/python3 salesforce_servicenow_webhook.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable salesforce-servicenow-integration
sudo systemctl start salesforce-servicenow-integration
sudo systemctl status salesforce-servicenow-integration
```

---

## Troubleshooting

### Issue: Webhook not receiving data

**Check:**
1. Service is running: `curl http://localhost:8080/api/health`
2. Firewall allows port 8080
3. Salesforce can reach your server IP
4. Webhook URL is correct in Salesforce

### Issue: ServiceNow ticket not created

**Check:**
1. MCP connection: `curl http://localhost:8080/api/integration/status`
2. ServiceNow credentials in mcp_unified.py
3. Logs: `sudo journalctl -u salesforce-servicenow-integration -f`

### Issue: Approval not working

**Check:**
1. Correct appointment/work order ID
2. ServiceNow ticket exists
3. Ticket is in "On Hold" state

---

## Next Steps

1. ✅ Start webhook service
2. ✅ Configure Salesforce webhooks
3. ✅ Test with sample data
4. ✅ Set up approval workflow
5. ✅ Monitor pending approvals
6. ✅ Deploy to production

All set! Your Salesforce appointments and work orders will now automatically create ServiceNow tickets with approval workflow.
