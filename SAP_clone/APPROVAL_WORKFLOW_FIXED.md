# Approval Workflow Fix - Complete

## Issues Fixed

### 1. Invalid State Transition Error ✅
**Problem:** `Invalid transition from Open to Closed. Valid transitions: ['Assigned']`

**Solution:** Updated the FI approval handlers to follow the proper state machine:
- **State Flow:** Open → Assigned → In_Progress → Closed
- The approve/reject handlers now automatically transition through all required states

**Changes Made:**
- `frontend/src/pages/FI.tsx`: Updated `handleApproveTicket()` and `handleRejectTicket()` to handle state transitions based on current ticket status

### 2. MuleSoft Notification ✅
**Problem:** Backend needed to send status updates to MuleSoft after approval/rejection

**Solution:** Added automatic XML notification to MuleSoft when tickets are closed, which is then forwarded to the MuleSoft events API

**Changes Made:**
1. `backend/services/ticket_service.py`:
   - Added `_notify_mulesoft()` method to send XML notifications
   - Integrated notification into `update_status()` method
   - Sends notification when ticket status changes to "Closed" and is related to Load Enhancement

2. `camel/main.py`:
   - Added `/api/ticket-status` endpoint to receive XML status updates
   - Forwards events to MuleSoft events API at `http://host.docker.internal:3001/events`
   - Converts XML to JSON format for the events API

## MuleSoft Events API Integration

### Endpoint
```
POST http://localhost:3001/events
```

### Event Payload Format
```json
{
  "event_type": "ticket_status_update",
  "ticket_id": "TKT-FI-20260121-0001",
  "correlation_id": "SF-REQ-10021",
  "module": "FI",
  "status": "Approved",
  "updated_by": "admin",
  "timestamp": "2026-01-21T12:00:00.000000",
  "comment": "Approved by admin"
}
```

### Event Fields
- **event_type**: Always "ticket_status_update"
- **ticket_id**: SAP ERP ticket ID (e.g., TKT-FI-20260121-0001)
- **correlation_id**: Original request ID from MuleSoft (e.g., SF-REQ-10021)
- **module**: Module that processed the ticket (FI, PM, or MM)
- **status**: "Approved" or "Rejected"
- **updated_by**: Username who approved/rejected
- **timestamp**: ISO 8601 timestamp of the update
- **comment**: Full comment including approval/rejection details

## XML Notification Format (Internal)

When a ticket is approved or rejected, the backend sends this XML to Camel:

```xml
<TicketStatusUpdate>
    <TicketID>TKT-FI-20260121-0001</TicketID>
    <CorrelationID>SF-REQ-10021</CorrelationID>
    <Module>FI</Module>
    <Status>Approved</Status>
    <UpdatedBy>admin</UpdatedBy>
    <UpdatedAt>2026-01-21T12:00:00</UpdatedAt>
    <Comment>Approved by admin</Comment>
</TicketStatusUpdate>
```

## How It Works

### Approval Flow:
1. User clicks "Approve" button in FI module
2. Frontend transitions ticket through states:
   - Open → Assigned
   - Assigned → In_Progress
   - In_Progress → Closed
3. Backend detects ticket closure with "Load Enhancement" in title
4. Backend sends XML notification to Camel service
5. Camel service parses XML and forwards JSON event to `localhost:3001/events`
6. MuleSoft events API receives the status update

### Rejection Flow:
1. User clicks "Reject" button and enters reason
2. Frontend transitions ticket through states (same as approval)
3. Backend sends XML notification with "Rejected" status
4. Camel forwards to MuleSoft events API with rejection reason in comment

## Testing

### Test Approval:
1. Create a Load Enhancement Request
2. Go to FI module → Approvals Inbox tab
3. Click "Approve" on a ticket
4. Check MuleSoft events API at `localhost:3001/events` for the event
5. Check Camel logs: `docker logs sap-erp-camel --tail 20`

### Test Rejection:
1. Go to FI module → Approvals Inbox tab
2. Click "Reject" on a ticket
3. Enter rejection reason
4. Check MuleSoft events API for the event with rejection details

### View Logs:
```bash
# Backend logs
docker logs sap-erp-backend --tail 50

# Camel logs (shows forwarding to MuleSoft)
docker logs sap-erp-camel --tail 50 -f
```

### Test Script:
```bash
# Run the test script
bash test_mulesoft_event.sh
```

## Configuration

### Camel Service (Integration Layer)
The MuleSoft events API endpoint is configured in `camel/main.py`:
```python
mulesoft_events_url = "http://host.docker.internal:3001/events"
```

**Note:** `host.docker.internal` is used to access the host machine from within Docker containers.

### Backend Service
The Camel endpoint is configured in `backend/services/ticket_service.py`:
```python
mulesoft_url = "http://sap-erp-camel:8081/api/ticket-status"
```

## Error Handling

- If MuleSoft events API is unavailable, the error is logged but ticket update succeeds
- If Camel service is down, the error is logged but ticket update succeeds
- Timeout is set to 5 seconds to prevent hanging
- All errors are logged for debugging

## Status

✅ State transition fixed
✅ MuleSoft XML notification implemented
✅ MuleSoft events API integration added
✅ JSON event forwarding configured
✅ Containers restarted with new code
✅ Ready for testing
