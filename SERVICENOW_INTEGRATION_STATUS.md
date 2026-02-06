# ServiceNow Integration Status & Solution

## 🔴 Current Issue

**Salesforce appointments are NOT automatically appearing in ServiceNow**

### What's Happening:
1. ✅ Appointments ARE created successfully in Salesforce
2. ✅ Appointment numbers ARE generated (APT-YYYYMMDD-XXXXXXXX)
3. ❌ ServiceNow ticket creation FAILS
4. ❌ `servicenow_ticket: null` in all responses

---

## 🔍 Root Cause

The Salesforce backend's ServiceNow client has **two major issues**:

### Issue 1: Wrong API Format
- **Salesforce sends**: JSON body `{"short_description": "...", "description": "..."}`
- **ServiceNow expects**: Query parameters `?short_description=...&description=...`
- **Result**: 422 Unprocessable Entity error

### Issue 2: No Authentication
- **Salesforce ServiceNow client**: Doesn't authenticate
- **ServiceNow API**: Requires Bearer token
- **Result**: 401 Unauthorized error

---

## ✅ **BEST SOLUTION: Use the Working Demo Script**

The easiest solution is to use the demo script which correctly handles both systems:

```bash
cd /home/pradeep1a/Network-apps
python3 COMPLETE_APPOINTMENT_DEMO.py
```

This script:
1. ✅ Creates appointment in Salesforce
2. ✅ Authenticates with ServiceNow
3. ✅ Creates ServiceNow ticket with correct format
4. ✅ Links them by appointment number

**Output Example:**
```
✅ Salesforce Appointment: APT-20260205-97E6A2B8
✅ ServiceNow Ticket: INC7239331
✅ Integration Status: Success
```

---

## 🎯 Frontend Integration

### For Your Frontend, Use TWO Separate Endpoints:

### 1. Create Appointment in Salesforce

```javascript
// POST to Salesforce
const appointmentResponse = await fetch(
  'http://149.102.158.71:4799/api/service/appointments',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${salesforceToken}`
    },
    body: JSON.stringify({
      account_id: 8,
      subject: 'Emergency Repair',
      description: 'Issue description',
      appointment_type: 'Emergency Repair',
      priority: 'Urgent',
      location: 'London',
      required_skills: 'HV Technician',
      required_parts: 'Cable',
      scheduled_start: '2026-02-08T10:00:00',
      scheduled_end: '2026-02-08T14:00:00'
    })
  }
);

const appointment = await appointmentResponse.json();
const appointmentNumber = appointment.appointment.appointment_number;
```

### 2. Manually Create ServiceNow Ticket

```javascript
// Get ServiceNow token
const snowTokenResponse = await fetch(
  'http://149.102.158.71:4780/token',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin@company.com&password=admin123'
  }
);
const { access_token } = await snowTokenResponse.json();

// Create ServiceNow ticket
const ticketResponse = await fetch(
  `http://149.102.158.71:4780/api/servicenow/incidents?${new URLSearchParams({
    short_description: `Service Appointment: ${appointment.appointment.subject}`,
    description: `Appointment ${appointmentNumber}\n${appointment.appointment.description}`,
    category: 'request',
    priority: appointment.appointment.priority === 'Urgent' ? '1' : '2'
  })}`,
  {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${access_token}` }
  }
);

const ticket = await ticketResponse.json();
const ticketNumber = ticket.result.number; // e.g., INC7239331
```

---

## 📋 Complete React Component

```jsx
import React, { useState } from 'react';

const SALESFORCE_API = 'http://149.102.158.71:4799';
const SERVICENOW_API = 'http://149.102.158.71:4780';

function AppointmentCreator() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function createAppointmentWithTicket(appointmentData) {
    setLoading(true);
    try {
      // Step 1: Authenticate with Salesforce
      const sfAuth = await fetch(`${SALESFORCE_API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      const { access_token: sfToken } = await sfAuth.json();

      // Step 2: Create Salesforce appointment
      const appointmentResponse = await fetch(`${SALESFORCE_API}/api/service/appointments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sfToken}`
        },
        body: JSON.stringify(appointmentData)
      });
      const appointment = await appointmentResponse.json();

      // Step 3: Authenticate with ServiceNow
      const snowAuth = await fetch(`${SERVICENOW_API}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'username=admin@company.com&password=admin123'
      });
      const { access_token: snowToken } = await snowAuth.json();

      // Step 4: Create ServiceNow ticket
      const priorityMap = { 'Normal': '3', 'High': '2', 'Urgent': '1' };
      const ticketParams = new URLSearchParams({
        short_description: `Service Appointment: ${appointment.appointment.subject}`,
        description: `Appointment Number: ${appointment.appointment.appointment_number}\n\n${appointment.appointment.description}`,
        category: 'request',
        priority: priorityMap[appointment.appointment.priority] || '3'
      });

      const ticketResponse = await fetch(
        `${SERVICENOW_API}/api/servicenow/incidents?${ticketParams}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${snowToken}` }
        }
      );
      const ticket = await ticketResponse.json();

      setResult({
        appointmentNumber: appointment.appointment.appointment_number,
        ticketNumber: ticket.result.number,
        status: 'success'
      });

      alert(`✅ Success!\nAppointment: ${appointment.appointment.appointment_number}\nTicket: ${ticket.result.number}`);

    } catch (error) {
      console.error('Error:', error);
      alert('❌ Failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const appointmentData = {
      account_id: 8,
      subject: formData.get('subject'),
      description: formData.get('description'),
      appointment_type: formData.get('appointment_type'),
      priority: formData.get('priority'),
      location: formData.get('location'),
      required_skills: formData.get('required_skills'),
      required_parts: formData.get('required_parts'),
      scheduled_start: formData.get('scheduled_start'),
      scheduled_end: formData.get('scheduled_end')
    };

    await createAppointmentWithTicket(appointmentData);
  }

  return (
    <div className="appointment-form">
      <h2>Create Service Appointment</h2>

      <form onSubmit={handleSubmit}>
        <input name="subject" placeholder="Subject" required />
        <textarea name="description" placeholder="Description" required />
        <input name="location" placeholder="Location" required />

        <select name="appointment_type" required>
          <option value="Emergency Repair">Emergency Repair</option>
          <option value="Maintenance">Maintenance</option>
          <option value="Installation">Installation</option>
        </select>

        <select name="priority" required>
          <option value="Urgent">Urgent</option>
          <option value="High">High</option>
          <option value="Normal">Normal</option>
        </select>

        <input name="required_skills" placeholder="Required Skills" />
        <input name="required_parts" placeholder="Required Parts" />
        <input name="scheduled_start" type="datetime-local" required />
        <input name="scheduled_end" type="datetime-local" required />

        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Appointment & Ticket'}
        </button>
      </form>

      {result && (
        <div className="result">
          <h3>✅ Created Successfully!</h3>
          <p><strong>Appointment:</strong> {result.appointmentNumber}</p>
          <p><strong>ServiceNow Ticket:</strong> {result.ticketNumber}</p>
        </div>
      )}
    </div>
  );
}

export default AppointmentCreator;
```

---

## 📊 View Appointments & Tickets

### View Salesforce Appointments

```javascript
async function getAppointments() {
  // Login first
  const auth = await fetch('http://149.102.158.71:4799/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
  });
  const { access_token } = await auth.json();

  // Get appointments
  const response = await fetch(
    'http://149.102.158.71:4799/api/service/scheduling-requests',
    { headers: { 'Authorization': `Bearer ${access_token}` } }
  );

  return await response.json();
}
```

### View ServiceNow Tickets

```javascript
async function getServiceNowTickets() {
  // Login
  const auth = await fetch('http://149.102.158.71:4780/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin@company.com&password=admin123'
  });
  const { access_token } = await auth.json();

  // Get tickets
  const response = await fetch(
    'http://149.102.158.71:4780/tickets/',
    { headers: { 'Authorization': `Bearer ${access_token}` } }
  );

  return await response.json();
}
```

---

## 🎯 **ANSWER TO YOUR QUESTION**

### "Should I use webhook to post to ServiceNow from Salesforce?"

**NO - Use frontend-side integration instead**

Why:
1. ✅ **Simpler**: No backend modifications needed
2. ✅ **More control**: You see exactly what's created
3. ✅ **Better error handling**: Can retry or show error to user
4. ✅ **Works immediately**: No need to fix broken Salesforce backend

The webhook approach (port 8080) requires additional setup and MCP configuration. The frontend approach above works RIGHT NOW.

---

## 📝 Summary

### Current State:
- **Salesforce**: ✅ Working (creates appointments)
- **ServiceNow**: ✅ Working (creates tickets)
- **Automatic Integration**: ❌ Broken (wrong format + no auth)

### Solution:
**Use the React component above** which:
1. Creates appointment in Salesforce
2. Manually creates ServiceNow ticket
3. Links them by appointment number

### Quick Test:
```bash
python3 COMPLETE_APPOINTMENT_DEMO.py
```

---

## 🔧 Optional: Fix the Backend (Advanced)

If you REALLY want to fix the Salesforce backend:

1. **Update `/home/pradeep1a/Network-apps/Salesforce/backend/app/servicenow.py`**
2. **Add authentication** (get token from ServiceNow)
3. **Change request format** (use query params, not JSON body)
4. **Rebuild Docker image**: `docker-compose build salesforce-backend`
5. **Restart**: `docker-compose restart salesforce-backend`

But the frontend solution above is **much easier and works now**.

---

**Recommendation**: Use the frontend integration approach. It's cleaner, more maintainable, and gives you full control over the integration flow.
