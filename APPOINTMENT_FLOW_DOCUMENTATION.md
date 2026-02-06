# 📋 Service Appointment Flow: Salesforce → ServiceNow → Agent → SAP

## Overview

This document describes the complete flow for creating service appointments with immediate appointment number tracking and automated integration across Salesforce, ServiceNow, and SAP.

---

## 🎯 Flow Summary

```
User Request (Salesforce)
    ↓
Generate Appointment Number (APT-YYYYMMDD-XXXXXXXX) ← IMMEDIATE RETURN
    ↓
Create ServiceNow Ticket (Status: "Pending Agent Review")
    ↓
Agent Reviews & Approves
    ↓
Create SAP Maintenance Order (Automatic)
    ↓
Complete ✓
```

---

## 🔄 Step-by-Step Process

### Step 1: Create Service Appointment

**Endpoint:** `POST /api/service/appointments`

**Request:**
```json
{
  "account_id": 1,
  "subject": "HVAC System Maintenance",
  "description": "Routine maintenance check for HVAC system",
  "appointment_type": "Maintenance",
  "scheduled_start": "2026-02-07T09:00:00",
  "scheduled_end": "2026-02-07T11:00:00",
  "priority": "High",
  "location": "Building A, Floor 3, Room 305",
  "required_skills": "HVAC Certified",
  "required_parts": "Air filter, Coolant"
}
```

**Response (IMMEDIATE):**
```json
{
  "appointment": {
    "id": 1,
    "appointment_number": "APT-20260205-A7B3C9D2",  ← YOUR TRACKING NUMBER
    "account_id": 1,
    "subject": "HVAC System Maintenance",
    "description": "Routine maintenance check for HVAC system",
    "appointment_type": "Maintenance",
    "scheduled_start": "2026-02-07T09:00:00",
    "scheduled_end": "2026-02-07T11:00:00",
    "priority": "High",
    "location": "Building A, Floor 3, Room 305",
    "required_skills": "HVAC Certified",
    "required_parts": "Air filter, Coolant",
    "status": "Pending Agent Review",
    "owner_id": 1,
    "created_at": "2026-02-05T10:30:00"
  },
  "scheduling_request": {
    "id": 1,
    "appointment_id": 1,
    "appointment_number": "APT-20260205-A7B3C9D2",
    "request_type": "SCHEDULE",
    "status": "PENDING_AGENT_REVIEW",
    "correlation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "mulesoft_transaction_id": "INC0010123",  ← ServiceNow Ticket Number
    "requested_by_id": 1,
    "created_at": "2026-02-05T10:30:00"
  },
  "servicenow_ticket": "INC0010123",
  "message": "Service appointment created and ticket sent to ServiceNow for agent review"
}
```

✅ **What you get immediately:**
- Appointment Number: `APT-20260205-A7B3C9D2`
- ServiceNow Ticket: `INC0010123`
- Status: `Pending Agent Review`
- Tracking ID for polling

---

### Step 2: Poll for Status Updates

**Endpoint:** `GET /api/service/scheduling-requests`

**Query Parameters:**
- `status` (optional): Filter by status (e.g., `PENDING_AGENT_REVIEW`, `AGENT_APPROVED`)
- `skip` (optional): Pagination offset
- `limit` (optional): Results per page

**Response:**
```json
[
  {
    "id": 1,
    "appointment_id": 1,
    "appointment_number": "APT-20260205-A7B3C9D2",
    "request_type": "SCHEDULE",
    "status": "PENDING_AGENT_REVIEW",  ← Current Status
    "integration_status": null,
    "correlation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "mulesoft_transaction_id": "INC0010123",
    "requested_by_id": 1,
    "assigned_technician_id": null,
    "technician_name": null,
    "parts_available": null,
    "sap_hr_response": null,
    "sap_inventory_response": null,
    "error_message": null,
    "created_at": "2026-02-05T10:30:00",
    "updated_at": "2026-02-05T10:30:00"
  }
]
```

**Polling Logic:**
```python
import requests
import time

def poll_until_approved(token, appointment_number, max_attempts=30):
    """Poll every 5 seconds until approved or timeout"""
    for i in range(max_attempts):
        response = requests.get(
            "http://localhost:4777/api/service/scheduling-requests",
            headers={"Authorization": f"Bearer {token}"}
        )

        for req in response.json():
            if req['appointment_number'] == appointment_number:
                if req['status'] == 'AGENT_APPROVED':
                    return req  # Approved!
                elif req['status'] == 'AGENT_REJECTED':
                    raise Exception("Appointment rejected")

        time.sleep(5)  # Wait 5 seconds before next poll

    raise TimeoutError("Approval timeout")
```

---

### Step 3: Agent Approval (Automatic or Manual)

**Endpoint:** `POST /api/service/scheduling-requests/{request_id}/approve`

**Query Parameters:**
- `technician_id` (required): Technician ID to assign
- `technician_name` (required): Technician name

**Example:**
```bash
POST /api/service/scheduling-requests/1/approve?technician_id=101&technician_name=John%20Smith
```

**What happens:**
1. ✅ Updates status to `AGENT_APPROVED`
2. ✅ Assigns technician to appointment
3. ✅ **Automatically creates SAP Maintenance Order**
4. ✅ Updates integration status to `SENT_TO_SAP`
5. ✅ Returns SAP order details

**Response:**
```json
{
  "message": "Scheduling request approved by agent and sent to SAP successfully",
  "scheduling_request": {
    "id": 1,
    "appointment_id": 1,
    "appointment_number": "APT-20260205-A7B3C9D2",
    "status": "AGENT_APPROVED",
    "integration_status": "SENT_TO_SAP",
    "assigned_technician_id": 101,
    "technician_name": "John Smith - HVAC Specialist",
    "parts_available": true,
    "sap_hr_response": "SAP Maintenance Order: 4500012345",
    "sap_inventory_response": "SAP Order ID: 1001",
    "updated_at": "2026-02-05T10:35:00"
  },
  "sap_order_number": "4500012345",  ← SAP Maintenance Order Number
  "sap_order_id": 1001
}
```

---

### Step 4: Track Complete Status

After agent approval, poll again to see final status:

**Endpoint:** `GET /api/service/scheduling-requests`

**Response (After Approval):**
```json
[
  {
    "id": 1,
    "appointment_number": "APT-20260205-A7B3C9D2",
    "status": "AGENT_APPROVED",  ← Updated Status
    "integration_status": "SENT_TO_SAP",  ← SAP Integration Complete
    "technician_name": "John Smith - HVAC Specialist",
    "parts_available": true,
    "sap_hr_response": "SAP Maintenance Order: 4500012345",
    "sap_inventory_response": "SAP Order ID: 1001",
    "mulesoft_transaction_id": "INC0010123",
    "updated_at": "2026-02-05T10:35:00"
  }
]
```

---

## 📊 Status Flow

```
PENDING_AGENT_REVIEW  →  AGENT_APPROVED  →  SENT_TO_SAP
        ↓
  AGENT_REJECTED
```

**Status Definitions:**

| Status | Description |
|--------|-------------|
| `PENDING_AGENT_REVIEW` | Waiting for agent/AI to review and approve |
| `AGENT_APPROVED` | Agent approved, sent to SAP |
| `AGENT_REJECTED` | Agent rejected (with reason in `error_message`) |

**Integration Status:**

| Status | Description |
|--------|-------------|
| `null` | Not yet sent to SAP |
| `SENT_TO_SAP` | Successfully sent to SAP |
| `SAP_ERROR` | SAP integration failed (see `error_message`) |
| `REJECTED_BY_AGENT` | Agent rejected before SAP |

---

## 🧪 Testing the Flow

### Prerequisites
1. Salesforce backend running on port 4777
2. ServiceNow backend running on port 4780
3. SAP backend running on port 4772

### Run Test Script

```bash
cd /home/pradeep1a/Network-apps
python3 TEST_APPOINTMENT_FLOW.py
```

This will:
1. ✅ Create appointment → Get number immediately
2. ✅ Show ServiceNow ticket creation
3. ✅ Poll for status
4. ✅ Simulate agent approval
5. ✅ Show SAP order creation
6. ✅ Display final status

---

## 🔑 Key Takeaways

### ✅ Appointment Number is IMMEDIATE
- Generated: `APT-YYYYMMDD-XXXXXXXX`
- Returned in response body within milliseconds
- No waiting for agent or SAP
- Use for tracking throughout the process

### ✅ ServiceNow Ticket Created Automatically
- Ticket number returned in `servicenow_ticket` field
- Stored in `scheduling_request.mulesoft_transaction_id`
- Visible in ServiceNow system immediately

### ✅ Status Tracking via Polling
- Endpoint: `/api/service/scheduling-requests`
- Filter by appointment number
- Real-time status updates
- No need to query multiple systems

### ✅ SAP Order Created Automatically
- Happens when agent approves
- No manual SAP integration needed
- Order number returned in approval response
- Maintenance Order type: `PM01`

---

## 🌐 Integration Architecture

```
┌──────────────┐
│  Salesforce  │
│   Frontend   │
└──────┬───────┘
       │ POST /api/service/appointments
       ↓
┌──────────────────────────────────────────────────────┐
│            Salesforce Backend (Port 4777)            │
│                                                      │
│  1. Generate Appointment Number                     │
│     APT-YYYYMMDD-XXXXXXXX                           │
│                                                      │
│  2. Create Appointment Record (DB)                  │
│     status = "Pending Agent Review"                 │
│                                                      │
│  3. Create SchedulingRequest (DB)                   │
│     status = "PENDING_AGENT_REVIEW"                 │
│                                                      │
│  4. Call ServiceNow Client                          │
│     ↓                                                │
│     Create Incident in ServiceNow                   │
│                                                      │
│  5. RETURN IMMEDIATELY ✅                            │
│     - appointment_number                            │
│     - servicenow_ticket                             │
│     - scheduling_request                            │
└──────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────┐
│          ServiceNow Backend (Port 4780)              │
│                                                      │
│  Incident Created:                                   │
│  - Number: INC0010123                               │
│  - Status: New                                      │
│  - Category: Request                                │
│  - Custom Fields:                                   │
│    * u_appointment_number                           │
│    * u_source_system: Salesforce                    │
│    * u_request_type: Service Appointment            │
└──────────────────────────────────────────────────────┘
       ↓
       (Agent/AI Reviews)
       ↓
┌──────────────────────────────────────────────────────┐
│  Agent Approves via:                                 │
│  POST /api/service/scheduling-requests/1/approve     │
│                                                      │
│  Salesforce Backend:                                │
│  1. Update scheduling_request                       │
│     status = "AGENT_APPROVED"                       │
│                                                      │
│  2. Assign technician to appointment                │
│                                                      │
│  3. Call SAP Client                                 │
│     ↓                                                │
│     Create Maintenance Order                        │
│                                                      │
│  4. Store SAP response                              │
│     sap_hr_response = "SAP Order: 4500012345"      │
│                                                      │
│  5. RETURN                                          │
│     - SAP order number                              │
│     - Updated scheduling_request                    │
└──────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────┐
│             SAP Backend (Port 4772)                  │
│                                                      │
│  Maintenance Order Created:                         │
│  - Order Number: 4500012345                         │
│  - Order Type: PM01                                 │
│  - Technician: 101                                  │
│  - Priority: 3                                      │
│  - Description: From Salesforce APT-...             │
└──────────────────────────────────────────────────────┘
```

---

## 📝 API Endpoints Reference

### Service Appointments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/service/appointments` | Create new appointment (returns number immediately) |
| GET | `/api/service/appointments` | List all appointments |
| GET | `/api/service/appointments/{id}` | Get specific appointment |

### Scheduling Requests (Tracking)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/service/scheduling-requests` | List all scheduling requests (for polling) |
| GET | `/api/service/scheduling-requests?status=PENDING_AGENT_REVIEW` | Filter by status |
| POST | `/api/service/scheduling-requests/{id}/approve` | Agent approves (triggers SAP) |
| POST | `/api/service/scheduling-requests/{id}/reject` | Agent rejects |

---

## 🚀 Example Frontend Integration

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ServiceAppointmentCreator() {
  const [appointmentNumber, setAppointmentNumber] = useState(null);
  const [status, setStatus] = useState('');
  const [sapOrder, setSapOrder] = useState(null);

  const createAppointment = async () => {
    // Step 1: Create appointment
    const response = await axios.post('/api/service/appointments', {
      account_id: 1,
      subject: 'HVAC Maintenance',
      description: 'System check',
      appointment_type: 'Maintenance',
      priority: 'High',
      scheduled_start: '2026-02-07T09:00:00',
      scheduled_end: '2026-02-07T11:00:00',
      location: 'Building A'
    });

    // Step 2: Get appointment number IMMEDIATELY
    const appointmentNum = response.data.appointment.appointment_number;
    setAppointmentNumber(appointmentNum);
    setStatus('Pending Agent Review');

    // Step 3: Start polling for status
    pollStatus(appointmentNum);
  };

  const pollStatus = async (appointmentNum) => {
    const interval = setInterval(async () => {
      const response = await axios.get('/api/service/scheduling-requests');

      const request = response.data.find(
        r => r.appointment_number === appointmentNum
      );

      if (request) {
        setStatus(request.status);

        if (request.status === 'AGENT_APPROVED') {
          setSapOrder(request.sap_hr_response);
          clearInterval(interval); // Stop polling
        }
      }
    }, 5000); // Poll every 5 seconds
  };

  return (
    <div>
      <button onClick={createAppointment}>
        Create Service Appointment
      </button>

      {appointmentNumber && (
        <div>
          <h3>Appointment Created!</h3>
          <p>Tracking Number: <strong>{appointmentNumber}</strong></p>
          <p>Status: <strong>{status}</strong></p>
          {sapOrder && (
            <p>SAP Order: <strong>{sapOrder}</strong></p>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## ❓ FAQ

**Q: Is the appointment number returned immediately?**
A: Yes! The appointment number is generated and returned in the same API call, within milliseconds.

**Q: Do I need to wait for ServiceNow or SAP before getting the number?**
A: No! The appointment number is generated locally and returned immediately. ServiceNow ticket creation happens asynchronously.

**Q: How do I track the status?**
A: Poll `/api/service/scheduling-requests` and filter by your appointment number.

**Q: When is the SAP order created?**
A: Automatically when an agent approves the scheduling request via `/api/service/scheduling-requests/{id}/approve`.

**Q: Can the agent be automated?**
A: Yes! You can integrate an AI agent (like Mistral) to automatically review and approve appointments based on business rules.

**Q: What if SAP integration fails?**
A: The `integration_status` will be set to `SAP_ERROR` and the `error_message` field will contain details.

---

## 📞 Support

For issues or questions:
- Check logs in `/home/pradeep1a/Network-apps/Salesforce/backend/`
- Test ServiceNow connection: `GET /servicenow/test-connection`
- Test SAP connection: Check SAP backend logs

---

**Last Updated:** 2026-02-05
**Version:** 1.0.0
