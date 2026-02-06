# API Endpoints for Frontend

## Quick Reference

| Service | Base URL | Port |
|---------|----------|------|
| Ticket Orchestrator | `http://localhost:5001` | 5001 |
| Mistral Agent API | `http://localhost:5000` | 5000 |
| Salesforce-ServiceNow Webhook | `http://localhost:8080` | 8080 |

---

## 1. Ticket Orchestrator API (Port 5001)

### List All Tickets
```http
GET http://localhost:5001/api/tickets
```

**Query Parameters:**
- `status` (optional): `received`, `classified`, `assigned_to_agent`, `in_progress`, `resolved`, `failed`, `requires_human`
- `category` (optional): `password_reset`, `user_creation`, `integration_error`, etc.

**Response:**
```json
{
  "total": 10,
  "tickets": [
    {
      "id": "ORCH-000001",
      "servicenow_number": "INC0001234",
      "title": "Password reset for john@example.com",
      "category": "password_reset",
      "status": "resolved",
      "priority": "P2",
      "created_at": "2026-02-04T10:30:00",
      "resolution_log": [...]
    }
  ]
}
```

**Example (Fetch all tickets):**
```javascript
fetch('http://localhost:5001/api/tickets')
  .then(res => res.json())
  .then(data => console.log(data.tickets));
```

**Example (Filter by status):**
```javascript
fetch('http://localhost:5001/api/tickets?status=in_progress')
  .then(res => res.json())
  .then(data => console.log(data.tickets));
```

---

### Get Specific Ticket
```http
GET http://localhost:5001/api/tickets/{ticket_id}
```

**Example:**
```bash
curl http://localhost:5001/api/tickets/ORCH-000001
```

**Response:**
```json
{
  "id": "ORCH-000001",
  "servicenow_id": "abc123",
  "servicenow_number": "INC0001234",
  "title": "Password reset for john@example.com",
  "description": "User cannot login",
  "priority": "P2",
  "category": "password_reset",
  "status": "resolved",
  "created_at": "2026-02-04T10:30:00",
  "updated_at": "2026-02-04T10:35:00",
  "resolution_log": [
    {
      "timestamp": "2026-02-04T10:32:00",
      "actions": ["logged_into_salesforce", "found_user_123"],
      "result": {"status": "success"}
    }
  ]
}
```

**Frontend Code:**
```javascript
async function getTicket(ticketId) {
  const response = await fetch(`http://localhost:5001/api/tickets/${ticketId}`);
  return await response.json();
}
```

---

### Get Statistics
```http
GET http://localhost:5001/api/stats
```

**Response:**
```json
{
  "total_tickets": 25,
  "by_status": {
    "resolved": 15,
    "in_progress": 5,
    "failed": 2,
    "requires_human": 3
  },
  "by_category": {
    "password_reset": 10,
    "user_creation": 8,
    "integration_error": 7
  },
  "auto_resolved": 15,
  "requires_human": 3
}
```

**Frontend Code (React Example):**
```jsx
import React, { useState, useEffect } from 'react';

function TicketStats() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5001/api/stats')
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);

  if (!stats) return <div>Loading...</div>;

  return (
    <div>
      <h2>Total Tickets: {stats.total_tickets}</h2>
      <p>Resolved: {stats.by_status.resolved}</p>
      <p>In Progress: {stats.by_status.in_progress}</p>
      <p>Failed: {stats.by_status.failed}</p>
    </div>
  );
}
```

---

### Retry Failed Ticket
```http
POST http://localhost:5001/api/tickets/{ticket_id}/retry
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/tickets/ORCH-000005/retry
```

**Response:**
```json
{
  "status": "retry_scheduled",
  "ticket_id": "ORCH-000005"
}
```

**Frontend Code:**
```javascript
async function retryTicket(ticketId) {
  const response = await fetch(
    `http://localhost:5001/api/tickets/${ticketId}/retry`,
    { method: 'POST' }
  );
  return await response.json();
}
```

---

### Assign to Human
```http
POST http://localhost:5001/api/tickets/{ticket_id}/assign-to-human
Content-Type: application/json

{
  "assignee": "john.doe@company.com"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/tickets/ORCH-000003/assign-to-human \
  -H "Content-Type: application/json" \
  -d '{"assignee": "john.doe@company.com"}'
```

**Frontend Code:**
```javascript
async function assignToHuman(ticketId, assignee) {
  const response = await fetch(
    `http://localhost:5001/api/tickets/${ticketId}/assign-to-human`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assignee })
    }
  );
  return await response.json();
}
```

---

## 2. Salesforce-ServiceNow Integration API (Port 8080)

### List Pending Approvals
```http
GET http://localhost:8080/api/integration/pending-approvals
```

**Response:**
```json
{
  "total": 3,
  "tickets": [
    {
      "servicenow_number": "INC0010001",
      "short_description": "Service Appointment: Installation for John Doe",
      "priority": "3",
      "created": "2026-02-04 10:00:00",
      "sys_id": "abc123"
    }
  ]
}
```

**Frontend Code:**
```javascript
async function getPendingApprovals() {
  const response = await fetch('http://localhost:8080/api/integration/pending-approvals');
  return await response.json();
}
```

---

### Approve Appointment
```http
POST http://localhost:8080/api/approvals/appointments/{appointment_id}/approve?approver={email}
```

**Example:**
```bash
curl -X POST "http://localhost:8080/api/approvals/appointments/123/approve?approver=manager@company.com"
```

**Frontend Code:**
```javascript
async function approveAppointment(appointmentId, approverEmail) {
  const response = await fetch(
    `http://localhost:8080/api/approvals/appointments/${appointmentId}/approve?approver=${approverEmail}`,
    { method: 'POST' }
  );
  return await response.json();
}
```

---

### Approve Work Order
```http
POST http://localhost:8080/api/approvals/workorders/{workorder_id}/approve?approver={email}
```

**Example:**
```bash
curl -X POST "http://localhost:8080/api/approvals/workorders/456/approve?approver=supervisor@company.com"
```

---

### Reject Work Order
```http
POST http://localhost:8080/api/approvals/workorders/{workorder_id}/reject?approver={email}&reason={text}
```

**Example:**
```bash
curl -X POST "http://localhost:8080/api/approvals/workorders/456/reject?approver=supervisor@company.com&reason=Resources+unavailable"
```

**Frontend Code:**
```javascript
async function rejectWorkOrder(workOrderId, approver, reason) {
  const response = await fetch(
    `http://localhost:8080/api/approvals/workorders/${workOrderId}/reject?approver=${approver}&reason=${encodeURIComponent(reason)}`,
    { method: 'POST' }
  );
  return await response.json();
}
```

---

### Integration Status
```http
GET http://localhost:8080/api/integration/status
```

**Response:**
```json
{
  "status": "healthy",
  "mcp_connection": "connected",
  "servicenow_status": "healthy",
  "salesforce_status": "healthy",
  "timestamp": "2026-02-04T15:30:00"
}
```

---

## 3. Complete Frontend Example (React)

```jsx
import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:5001';

function TicketDashboard() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      // Load tickets
      const ticketsRes = await fetch(`${API_BASE}/api/tickets`);
      const ticketsData = await ticketsRes.json();
      setTickets(ticketsData.tickets);

      // Load stats
      const statsRes = await fetch(`${API_BASE}/api/stats`);
      const statsData = await statsRes.json();
      setStats(statsData);

      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  }

  async function retryTicket(ticketId) {
    try {
      await fetch(`${API_BASE}/api/tickets/${ticketId}/retry`, {
        method: 'POST'
      });
      alert('Ticket retry scheduled');
      loadData(); // Reload
    } catch (error) {
      alert('Error retrying ticket');
    }
  }

  async function assignToHuman(ticketId) {
    const assignee = prompt('Enter assignee email:');
    if (!assignee) return;

    try {
      await fetch(`${API_BASE}/api/tickets/${ticketId}/assign-to-human`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assignee })
      });
      alert('Ticket assigned to human');
      loadData();
    } catch (error) {
      alert('Error assigning ticket');
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      {/* Stats Section */}
      <div className="stats">
        <h2>Ticket Statistics</h2>
        <div className="stat-cards">
          <div className="card">
            <h3>{stats.total_tickets}</h3>
            <p>Total Tickets</p>
          </div>
          <div className="card">
            <h3>{stats.by_status.resolved}</h3>
            <p>Resolved</p>
          </div>
          <div className="card">
            <h3>{stats.by_status.in_progress}</h3>
            <p>In Progress</p>
          </div>
          <div className="card">
            <h3>{stats.by_status.failed}</h3>
            <p>Failed</p>
          </div>
        </div>
      </div>

      {/* Tickets List */}
      <div className="tickets">
        <h2>Recent Tickets</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Category</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map(ticket => (
              <tr key={ticket.id}>
                <td>{ticket.id}</td>
                <td>{ticket.title}</td>
                <td>{ticket.category}</td>
                <td>
                  <span className={`status-${ticket.status}`}>
                    {ticket.status}
                  </span>
                </td>
                <td>{ticket.priority}</td>
                <td>
                  {ticket.status === 'failed' && (
                    <button onClick={() => retryTicket(ticket.id)}>
                      Retry
                    </button>
                  )}
                  {ticket.status !== 'resolved' && (
                    <button onClick={() => assignToHuman(ticket.id)}>
                      Assign to Human
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TicketDashboard;
```

---

## 4. Approval Dashboard Example

```jsx
import React, { useState, useEffect } from 'react';

const APPROVAL_API = 'http://localhost:8080';

function ApprovalDashboard() {
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [userEmail, setUserEmail] = useState('manager@company.com');

  useEffect(() => {
    loadPendingApprovals();
  }, []);

  async function loadPendingApprovals() {
    const response = await fetch(`${APPROVAL_API}/api/integration/pending-approvals`);
    const data = await response.json();
    setPendingApprovals(data.tickets);
  }

  async function approveTicket(ticketSysId) {
    // Extract appointment/workorder ID from description
    // This is simplified - in production, store the mapping
    try {
      await fetch(
        `${APPROVAL_API}/api/approvals/appointments/${ticketSysId}/approve?approver=${userEmail}`,
        { method: 'POST' }
      );
      alert('Approved!');
      loadPendingApprovals();
    } catch (error) {
      console.error('Error approving:', error);
    }
  }

  return (
    <div className="approval-dashboard">
      <h2>Pending Approvals ({pendingApprovals.length})</h2>

      <div className="user-selector">
        <label>Your Email:</label>
        <input
          type="email"
          value={userEmail}
          onChange={(e) => setUserEmail(e.target.value)}
        />
      </div>

      <table>
        <thead>
          <tr>
            <th>Ticket #</th>
            <th>Description</th>
            <th>Priority</th>
            <th>Created</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {pendingApprovals.map(ticket => (
            <tr key={ticket.sys_id}>
              <td>{ticket.servicenow_number}</td>
              <td>{ticket.short_description}</td>
              <td>{ticket.priority}</td>
              <td>{ticket.created}</td>
              <td>
                <button onClick={() => approveTicket(ticket.sys_id)}>
                  Approve
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 5. Quick Testing with Postman

### Import This Collection:

```json
{
  "info": {
    "name": "Ticket System API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get All Tickets",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5001/api/tickets"
      }
    },
    {
      "name": "Get Ticket Stats",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:5001/api/stats"
      }
    },
    {
      "name": "Retry Failed Ticket",
      "request": {
        "method": "POST",
        "header": [],
        "url": "http://localhost:5001/api/tickets/ORCH-000001/retry"
      }
    },
    {
      "name": "Get Pending Approvals",
      "request": {
        "method": "GET",
        "header": [],
        "url": "http://localhost:8080/api/integration/pending-approvals"
      }
    }
  ]
}
```

---

## 6. CORS Configuration

If you get CORS errors, both services already have CORS enabled. But if you need to modify:

**In `ticket_orchestrator.py`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Summary

**Base URLs:**
- Ticket Orchestrator: `http://localhost:5001`
- Approval System: `http://localhost:8080`
- Mistral Agent: `http://localhost:5000`

**Key Endpoints:**
- `GET /api/tickets` - List all tickets
- `GET /api/tickets/{id}` - Get specific ticket
- `GET /api/stats` - Get statistics
- `POST /api/tickets/{id}/retry` - Retry failed ticket
- `GET /api/integration/pending-approvals` - List pending approvals
- `POST /api/approvals/appointments/{id}/approve` - Approve appointment

Copy these endpoints into your frontend and start building! 🚀
