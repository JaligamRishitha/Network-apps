# Frontend Appointment Creation Guide

## 🎯 Frontend Endpoint for Creating Appointments

### **Salesforce Appointment Creation Endpoint**

```
POST http://149.102.158.71:4799/api/service/appointments
```

**OR if accessing locally:**
```
POST http://localhost:4777/api/service/appointments
```

---

## 📋 Complete Frontend Integration

### Step 1: Authenticate

**Endpoint:**
```
POST http://149.102.158.71:4799/api/auth/login
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Step 2: Create Appointment

**Endpoint:**
```
POST http://149.102.158.71:4799/api/service/appointments
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {your_access_token}
```

**Request Body:**
```json
{
  "account_id": 8,
  "subject": "Emergency HV Cable Fault - London",
  "description": "11kV underground cable fault requiring immediate repair",
  "appointment_type": "Emergency Repair",
  "priority": "Urgent",
  "location": "Paddington Substation, London W2 1HQ",
  "required_skills": "HV Authorised Person, Cable Jointing",
  "required_parts": "11kV XLPE cable, Cable joints",
  "scheduled_start": "2026-02-07T09:00:00",
  "scheduled_end": "2026-02-07T14:00:00"
}
```

**Response:**
```json
{
  "appointment": {
    "id": 8,
    "appointment_number": "APT-20260205-97E6A2B8",
    "subject": "Emergency HV Cable Fault - London",
    "status": "Pending Agent Review",
    "priority": "Urgent",
    "location": "Paddington Substation, London W2 1HQ",
    "scheduled_start": "2026-02-07T09:00:00+00:00",
    "scheduled_end": "2026-02-07T14:00:00+00:00",
    "created_at": "2026-02-05T22:08:52.062133+00:00"
  },
  "scheduling_request": {
    "id": 7,
    "appointment_number": "APT-20260205-97E6A2B8",
    "status": "PENDING_AGENT_REVIEW",
    "correlation_id": "2582d313-6187-4f65-923d-8356f4fc59b9"
  },
  "servicenow_ticket": null,
  "message": "Service appointment created and ticket sent to ServiceNow for agent review"
}
```

---

## 🔍 View ServiceNow Tickets/Incidents

### Why You Don't See Appointments in ServiceNow

The automatic integration from Salesforce → ServiceNow is **currently not working** due to a configuration issue. The tickets are being created in a different table/system.

### Available ServiceNow Endpoints:

#### 1. **List All Incidents (Standard ServiceNow)**
```
GET http://149.102.158.71:4780/incidents/
Authorization: Bearer {servicenow_token}
```

#### 2. **List All Tickets (ServiceNow ITSM)**
```
GET http://149.102.158.71:4780/tickets/
Authorization: Bearer {servicenow_token}
```

#### 3. **Get ServiceNow Token**
```
POST http://149.102.158.71:4780/token
Content-Type: application/x-www-form-urlencoded

username=admin@company.com&password=admin123
```

### Example: Complete Flow to View Tickets

```bash
# 1. Get ServiceNow token
TOKEN=$(curl -s -X POST http://149.102.158.71:4780/token \
  -d "username=admin@company.com&password=admin123" | \
  python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

# 2. View all incidents
curl -H "Authorization: Bearer $TOKEN" \
  http://149.102.158.71:4780/incidents/

# 3. View all tickets
curl -H "Authorization: Bearer $TOKEN" \
  http://149.102.158.71:4780/tickets/
```

---

## 🌐 React Frontend Example

### Complete Appointment Creation Component

```jsx
import React, { useState } from 'react';

const SALESFORCE_API = 'http://149.102.158.71:4799';
const SERVICENOW_API = 'http://149.102.158.71:4780';

function AppointmentCreator() {
  const [formData, setFormData] = useState({
    account_id: 8,
    subject: '',
    description: '',
    appointment_type: 'Maintenance',
    priority: 'Normal',
    location: '',
    required_skills: '',
    required_parts: '',
    scheduled_start: '',
    scheduled_end: ''
  });

  const [salesforceToken, setSalesforceToken] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Step 1: Login to Salesforce
  async function loginToSalesforce() {
    try {
      const response = await fetch(`${SALESFORCE_API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'admin',
          password: 'admin123'
        })
      });

      const data = await response.json();
      setSalesforceToken(data.access_token);
      alert('✅ Logged in to Salesforce');
    } catch (error) {
      alert('❌ Login failed: ' + error.message);
    }
  }

  // Step 2: Create Appointment
  async function createAppointment() {
    if (!salesforceToken) {
      alert('Please login first');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${SALESFORCE_API}/api/service/appointments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${salesforceToken}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      setResult(data);
      alert(`✅ Appointment Created: ${data.appointment.appointment_number}`);
    } catch (error) {
      alert('❌ Failed to create appointment: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="appointment-creator">
      <h2>Create Service Appointment</h2>

      {!salesforceToken ? (
        <button onClick={loginToSalesforce}>
          🔐 Login to Salesforce
        </button>
      ) : (
        <div className="form">
          <div className="form-group">
            <label>Subject:</label>
            <input
              type="text"
              value={formData.subject}
              onChange={(e) => setFormData({...formData, subject: e.target.value})}
              placeholder="Emergency HV Cable Fault"
            />
          </div>

          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Detailed description of the issue"
              rows="4"
            />
          </div>

          <div className="form-group">
            <label>Location:</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              placeholder="Paddington Substation, London"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Appointment Type:</label>
              <select
                value={formData.appointment_type}
                onChange={(e) => setFormData({...formData, appointment_type: e.target.value})}
              >
                <option value="Maintenance">Maintenance</option>
                <option value="Emergency Repair">Emergency Repair</option>
                <option value="Installation">Installation</option>
                <option value="Inspection">Inspection</option>
              </select>
            </div>

            <div className="form-group">
              <label>Priority:</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
              >
                <option value="Normal">Normal</option>
                <option value="High">High</option>
                <option value="Urgent">Urgent</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Required Skills:</label>
            <input
              type="text"
              value={formData.required_skills}
              onChange={(e) => setFormData({...formData, required_skills: e.target.value})}
              placeholder="HV Authorised Person, Cable Jointing"
            />
          </div>

          <div className="form-group">
            <label>Required Parts:</label>
            <input
              type="text"
              value={formData.required_parts}
              onChange={(e) => setFormData({...formData, required_parts: e.target.value})}
              placeholder="11kV XLPE cable, Cable joints"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Scheduled Start:</label>
              <input
                type="datetime-local"
                value={formData.scheduled_start}
                onChange={(e) => setFormData({...formData, scheduled_start: e.target.value})}
              />
            </div>

            <div className="form-group">
              <label>Scheduled End:</label>
              <input
                type="datetime-local"
                value={formData.scheduled_end}
                onChange={(e) => setFormData({...formData, scheduled_end: e.target.value})}
              />
            </div>
          </div>

          <button
            onClick={createAppointment}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? '⏳ Creating...' : '✅ Create Appointment'}
          </button>
        </div>
      )}

      {result && (
        <div className="result">
          <h3>✅ Appointment Created Successfully!</h3>
          <div className="result-details">
            <p><strong>Appointment Number:</strong> {result.appointment.appointment_number}</p>
            <p><strong>Status:</strong> {result.appointment.status}</p>
            <p><strong>Subject:</strong> {result.appointment.subject}</p>
            <p><strong>Priority:</strong> {result.appointment.priority}</p>
            <p><strong>Location:</strong> {result.appointment.location}</p>
            {result.servicenow_ticket && (
              <p><strong>ServiceNow Ticket:</strong> {result.servicenow_ticket}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AppointmentCreator;
```

### CSS Styles

```css
.appointment-creator {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.btn-primary {
  background-color: #007bff;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.btn-primary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.result {
  margin-top: 20px;
  padding: 15px;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
}

.result-details p {
  margin: 5px 0;
}
```

---

## 📊 View Appointments (Frontend)

### Salesforce - List All Appointments

```javascript
async function getAppointments(token) {
  const response = await fetch(
    'http://149.102.158.71:4799/api/service/appointments',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
}
```

### Salesforce - Get Scheduling Requests (Pending Appointments)

```javascript
async function getSchedulingRequests(token) {
  const response = await fetch(
    'http://149.102.158.71:4799/api/service/scheduling-requests',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
}
```

### Filter by Status

```javascript
// Get only pending appointments
async function getPendingAppointments(token) {
  const response = await fetch(
    'http://149.102.158.71:4799/api/service/scheduling-requests?status=PENDING_AGENT_REVIEW',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
}
```

---

## 🔧 Testing with curl

### Complete Test Flow

```bash
#!/bin/bash

# 1. Login to Salesforce
echo "🔐 Logging in to Salesforce..."
TOKEN=$(curl -s -X POST http://149.102.158.71:4799/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

echo "✅ Token: ${TOKEN:0:20}..."

# 2. Create Appointment
echo ""
echo "📋 Creating appointment..."
APPOINTMENT=$(curl -s -X POST http://149.102.158.71:4799/api/service/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "account_id": 8,
    "subject": "Test Appointment from Frontend",
    "description": "Testing appointment creation",
    "appointment_type": "Maintenance",
    "priority": "Normal",
    "location": "Test Location",
    "required_skills": "Technician",
    "required_parts": "Tools",
    "scheduled_start": "2026-02-08T10:00:00",
    "scheduled_end": "2026-02-08T12:00:00"
  }')

echo "$APPOINTMENT" | python3 -m json.tool

# 3. Extract appointment number
APPT_NUMBER=$(echo $APPOINTMENT | python3 -c "import json, sys; print(json.load(sys.stdin)['appointment']['appointment_number'])")

echo ""
echo "✅ Appointment Number: $APPT_NUMBER"

# 4. List all appointments
echo ""
echo "📋 Listing all scheduling requests..."
curl -s -X GET http://149.102.158.71:4799/api/service/scheduling-requests \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Save this as `test_frontend_appointment.sh` and run:
```bash
chmod +x test_frontend_appointment.sh
./test_frontend_appointment.sh
```

---

## ⚠️ Important Notes

### Why Appointments Don't Appear in ServiceNow

The automatic Salesforce → ServiceNow integration is **partially broken**. When you create an appointment:

1. ✅ **Appointment IS created** in Salesforce
2. ✅ **Appointment number IS generated** immediately
3. ✅ **Scheduling request IS created**
4. ❌ **ServiceNow ticket creation FAILS** (see error in logs)

**Reason**: The Salesforce backend's ServiceNow client uses the wrong request format.

### Workaround

Use the complete demo script to manually create both:
```bash
python3 COMPLETE_APPOINTMENT_DEMO.py
```

This script:
1. Creates appointment in Salesforce ✅
2. Manually creates ServiceNow ticket ✅
3. Both are linked by appointment number ✅

---

## 📱 Quick Reference

### Salesforce Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login` | Login |
| POST | `/api/service/appointments` | Create appointment |
| GET | `/api/service/appointments` | List appointments |
| GET | `/api/service/scheduling-requests` | List scheduling requests |
| GET | `/api/service/scheduling-requests?status=PENDING_AGENT_REVIEW` | Filter by status |

### ServiceNow Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/token` | Get access token |
| GET | `/incidents/` | List incidents |
| GET | `/tickets/` | List tickets |
| POST | `/api/servicenow/incidents` | Create incident (query params) |

### Account IDs

Available accounts in Salesforce:
- **ID 6**: Quantum Cloud
- **ID 7**: TechCorp Solutions
- **ID 8**: Global Energy Corp ⭐ (Recommended)

---

## 🚀 Next Steps

1. **Use the frontend endpoint**: `POST http://149.102.158.71:4799/api/service/appointments`
2. **Copy the React component** above into your frontend
3. **Test with curl** using the provided scripts
4. **View appointments**: Use `GET /api/service/scheduling-requests`

The appointments ARE being created - you just need to use the correct Salesforce endpoint, not the ServiceNow endpoint directly!
