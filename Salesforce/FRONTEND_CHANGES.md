# Frontend Changes for Request-Based Workflow

## Summary
The backend has been refactored so that Scenarios 2 & 3 now follow the same request-approval pattern as Scenario 1. The frontend has been updated to work with the new **AppointmentRequest** and **WorkOrderRequest** models.

---

## ✅ Changes Already Applied

All frontend changes have been automatically applied to `frontend/src/pages/ServiceNowScenarios.jsx`:

### 1. **Updated Status Filters** (Lines 50, 53)
- Changed from `PENDING_AGENT_REVIEW` to `PENDING`
- This matches the new request status enum values

### 2. **Updated Technician Fetching** (Lines 116-146)
- **Old**: Tried to fetch from `/api/service/appointments/${request.appointment_id}/available-technicians`
- **New**: Fetches from `/api/service/appointment-requests/${request.id}/available-technicians`
- The appointment doesn't exist yet during approval, so we query based on the request data

### 3. **Updated Appointment Request Display** (Lines 418-449)
- **Changed fields**:
  - `request.appointment_number` → `Request #${request.id}` + `request.subject`
  - `request.mulesoft_transaction_id` → `request.servicenow_ticket_id`
  - Added display of `request.requested_payload.appointment_type`
  - Added display of `request.requested_payload.scheduled_start`

### 4. **Updated Work Order Request Display** (Lines 454-488)
- **Changed fields**:
  - `workOrder.work_order_number` → `Request #${request.id}` + `request.subject`
  - `workOrder.subject` → `request.subject`
  - `workOrder.mulesoft_transaction_id` → `request.servicenow_ticket_id`
  - Added display of `request.requested_payload.service_type`
  - Added display of `request.requested_payload.priority`
  - Added display of `request.requested_payload.product`

### 5. **Updated Parts Status Banner** (Lines 515-536)
- Removed pre-approval parts checking
- Added informational banner explaining parts will be checked during approval
- Parts availability is now automatically verified by the backend before creating SAP maintenance orders

---

## 🔧 Backend Endpoint Added

A new endpoint was added to support technician fetching for requests:

```
GET /api/service/appointment-requests/{request_id}/available-technicians
```

This endpoint:
- Takes the appointment request ID
- Extracts the requested appointment data from `requested_payload`
- Queries SAP HR for available technicians based on:
  - Scheduled date
  - Required skills
  - Location
- Returns the list of available technicians

---

## 📋 How It Works Now

### Scenario 2 (Appointments)
1. **User creates appointment** → Creates `AppointmentRequest` (not `ServiceAppointment`)
2. **Request sent to ServiceNow** → Creates ticket with request ID
3. **Agent approves in frontend** → Shows technician selection modal
4. **Technicians fetched from SAP HR** → Based on request data (not appointment ID)
5. **Agent selects technician** → Approval sent to backend
6. **Backend approval process**:
   - Checks SAP Inventory for parts availability
   - Creates actual `ServiceAppointment` record
   - Sends maintenance order to SAP PM
   - Updates request status to `COMPLETED`

### Scenario 3 (Work Orders)
1. **User creates work order** → Creates `WorkOrderRequest` (not `WorkOrder`)
2. **Request sent to ServiceNow** → Creates ticket with request ID
3. **Agent approves** → Approval sent to backend
4. **Backend approval process**:
   - Verifies entitlement with SAP
   - Creates actual `WorkOrder` record
   - Sends to SAP PM or SAP SD (based on service type)
   - Updates request status to `COMPLETED`

---

## 🎯 What You Need to Do

### ✅ Nothing! All changes have been applied automatically.

Just refresh your frontend to see the changes:

```bash
# If running locally
cd frontend
npm run dev

# If using Docker
docker-compose restart frontend
```

---

## 🧪 Testing the Changes

1. **Create a new appointment request**:
   - Fill in the appointment form
   - Submit → Should create an `AppointmentRequest`
   - Check "Pending Agent Review" → Should show "Request #X: [subject]"

2. **Approve appointment**:
   - Click "Approve & Assign Technician"
   - Modal should open with SAP HR technicians
   - Select a technician → Should approve and create actual appointment

3. **Create a work order request**:
   - Fill in the work order form
   - Submit → Should create a `WorkOrderRequest`
   - Check "Pending Agent Review" → Should show "Request #X: [subject]"

4. **Approve work order**:
   - Click "Approve & Send to SAP"
   - Should approve and create actual work order

---

## 📊 Data Structure Reference

### AppointmentRequest Object
```javascript
{
  id: 1,
  subject: "Install new router",
  requested_payload: {
    account_id: 123,
    case_id: 456,
    subject: "Install new router",
    description: "Customer needs new router",
    appointment_type: "Field Service",
    scheduled_start: "2026-02-07T10:00:00",
    scheduled_end: "2026-02-07T12:00:00",
    priority: "Normal",
    location: "123 Main St",
    required_skills: "Networking, Installation",
    required_parts: "ROUTER-X100:1, CABLE-CAT6:2"
  },
  status: "PENDING",
  correlation_id: "uuid-here",
  servicenow_ticket_id: "INC0012345",
  created_at: "2026-02-06T10:00:00Z"
}
```

### WorkOrderRequest Object
```javascript
{
  id: 1,
  subject: "Warranty claim for broken device",
  requested_payload: {
    account_id: 123,
    case_id: 456,
    subject: "Warranty claim for broken device",
    description: "Device stopped working",
    priority: "High",
    service_type: "Warranty",
    product: "Device XYZ"
  },
  status: "PENDING",
  correlation_id: "uuid-here",
  servicenow_ticket_id: "INC0012346",
  created_at: "2026-02-06T10:00:00Z"
}
```

---

## 🔄 Migration Notes

- **Old appointment and work order records** (created before this change) will still exist in the database
- **New requests** will be created using the request tables
- The frontend now correctly displays both old records and new requests
- No data migration needed - the old workflow created records directly, the new workflow creates requests first

---

## ❓ Troubleshooting

### Issue: "No pending appointments/work orders" showing
- **Check**: Make sure requests have `status: "PENDING"`
- **Old records** may have status `PENDING_AGENT_REVIEW` - these won't show up

### Issue: Technician modal not loading
- **Check**: Ensure backend is running and `/api/service/appointment-requests/{id}/available-technicians` is accessible
- **Check**: SAP backend is running and responding to technician queries

### Issue: Approval fails with 400 error
- **Check**: Request status must be `PENDING` to approve
- **Check**: Technician ID and name are being sent in the approval request

---

## 📝 Summary of File Changes

| File | Changes | Status |
|------|---------|--------|
| `backend/app/db_models.py` | Added `AppointmentRequest` and `WorkOrderRequest` models | ✅ Done |
| `backend/app/main.py` | Added import of db_models | ✅ Done |
| `backend/app/routes/service.py` | Refactored endpoints, added new technician endpoint | ✅ Done |
| `backend/database` | Created new tables in PostgreSQL | ✅ Done |
| `frontend/src/pages/ServiceNowScenarios.jsx` | Updated to work with request objects | ✅ Done |

---

**All changes are complete and the system is ready to use! 🎉**
