# ServiceNow Backend Integration Guide

## Overview
This guide shows how to integrate your Salesforce frontend with the existing ServiceNow backend application.

---

## 🔧 Architecture

```
Frontend (Local)                Backend (Server)              ServiceNow Backend
     |                                |                              |
     |-- POST /api/service/      --> | -- POST /api/servicenow/ --> |
     |   appointments                 |    incidents                 |
     |                                |                              |
     |-- GET /api/service/       --> | -- GET /api/servicenow/  --> |
     |   scheduling-requests          |    incidents                 |
     |                                |                              |
     |-- POST approve/reject     --> | -- POST /api/servicenow/ --> |
                                      |    approvals/{id}/approve    |
```

---

## 📋 ServiceNow Endpoints Used

### **1. Incidents (Service Appointments & Work Orders)**
```
POST   http://servicenow-backend:4780/api/servicenow/incidents
GET    http://servicenow-backend:4780/api/servicenow/incidents
GET    http://servicenow-backend:4780/api/servicenow/incidents/{id}
PUT    http://servicenow-backend:4780/api/servicenow/incidents/{id}
POST   http://servicenow-backend:4780/api/servicenow/incidents/{id}/close
```

### **2. Approvals (Agent Review)**
```
POST   http://servicenow-backend:4780/api/approvals
GET    http://servicenow-backend:4780/api/servicenow/approvals
POST   http://servicenow-backend:4780/api/servicenow/approvals/{id}/approve
POST   http://servicenow-backend:4780/api/servicenow/approvals/{id}/reject
```

### **3. Testing**
```
GET    http://servicenow-backend:4780/servicenow/test-connection
GET    http://servicenow-backend:4780/health
```

---

## 🔨 CHANGES NEEDED

### **1. Replace servicenow.py on Server**

**On your server (207.180.217.117):**

```bash
# Backup old file
cd /path/to/your/backend
mv app/servicenow.py app/servicenow_old.py

# Copy new file (upload servicenow_updated.py and rename)
mv app/servicenow_updated.py app/servicenow.py
```

### **2. Update .env Configuration**

**File: `backend/.env`**

```bash
# ServiceNow Backend Configuration
SERVICENOW_BACKEND_URL=http://servicenow-backend:4780

# OR if ServiceNow backend is on different server:
# SERVICENOW_BACKEND_URL=http://SERVICENOW_SERVER_IP:4780

# Optional: API Token for authentication
SERVICENOW_API_TOKEN=your_api_token_here

# Existing config
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your-secret-key-here
APP_ENV=production
DEBUG=False
```

### **3. Restart Backend Server**

```bash
# On server
cd /path/to/your/backend
# Stop current process
pkill -f "uvicorn"

# Restart
uvicorn app.main:app --host 0.0.0.0 --port 4799 --reload
```

---

## 🖥️ FRONTEND CHANGES (Already Done ✅)

The frontend is already configured correctly! No changes needed.

**Existing frontend pages:**
- ✅ `ServiceNowScenarios.jsx` - Create appointments/work orders
- ✅ `ServiceNowTracking.jsx` - Track status
- ✅ API calls go to: `http://207.180.217.117:4799`

---

## 🧪 TESTING

### **1. Test ServiceNow Backend Connection**

```bash
# From server or local machine
curl http://servicenow-backend:4780/health
curl http://servicenow-backend:4780/servicenow/test-connection
```

Expected response:
```json
{
  "status": "healthy",
  "message": "ServiceNow backend is running"
}
```

### **2. Test Creating Incident**

```bash
curl -X POST http://servicenow-backend:4780/api/servicenow/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "short_description": "Test Service Appointment",
    "description": "Testing from Salesforce",
    "priority": 3,
    "state": "new",
    "source": "Salesforce"
  }'
```

Expected response:
```json
{
  "incident_id": "INC0010001",
  "number": "INC0010001",
  "state": "new",
  "created_at": "2026-02-05T..."
}
```

### **3. Test from Frontend**

1. Start frontend locally:
   ```bash
   cd frontend
   npm run dev
   ```

2. Navigate to "ServiceNow" in left menu

3. Create a Service Appointment:
   - Fill form
   - Click "Create Appointment"
   - Check browser console for API calls
   - Check "Tracking" page for incident number

4. Test Agent Approval:
   - Go to "ServiceNow" page
   - See pending requests in right panel
   - Click "Approve" or "Reject"

---

## 📊 COMPLETE WORKFLOW

### **Service Appointment Flow:**

1. **User creates appointment (Frontend)**
   ```
   Frontend → POST http://207.180.217.117:4799/api/service/appointments
   ```

2. **Backend creates ServiceNow incident**
   ```
   Backend → POST http://servicenow-backend:4780/api/servicenow/incidents
   ```

3. **ServiceNow responds**
   ```
   ServiceNow Backend → Backend: {incident_id: "INC0010001"}
   ```

4. **Backend stores incident info**
   ```
   Database: appointment_id, servicenow_incident_id, status="PENDING_AGENT_REVIEW"
   ```

5. **Frontend shows in tracking**
   ```
   Frontend → GET http://207.180.217.117:4799/api/service/scheduling-requests
   ```

6. **Agent approves**
   ```
   Frontend → POST http://207.180.217.117:4799/api/service/scheduling-requests/{id}/approve
   Backend → POST http://servicenow-backend:4780/api/servicenow/approvals/{id}/approve
   ```

---

## ⚙️ CONFIGURATION OPTIONS

### **Option 1: ServiceNow Backend on Same Server**

```bash
SERVICENOW_BACKEND_URL=http://localhost:4780
```

### **Option 2: ServiceNow Backend on Different Server**

```bash
SERVICENOW_BACKEND_URL=http://192.168.1.100:4780
```

### **Option 3: ServiceNow Backend with Authentication**

```bash
SERVICENOW_BACKEND_URL=http://servicenow-backend:4780
SERVICENOW_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🔍 TROUBLESHOOTING

### **Issue: Connection Refused**

```bash
# Check if ServiceNow backend is running
curl http://servicenow-backend:4780/health

# Check network connectivity
ping servicenow-backend

# Check firewall rules
sudo iptables -L
```

### **Issue: 401 Unauthorized**

```bash
# Add API token to .env
SERVICENOW_API_TOKEN=your_token

# Restart backend
```

### **Issue: Incidents Not Created**

```bash
# Check backend logs
tail -f backend/logs/app.log

# Test ServiceNow backend directly
curl -X POST http://servicenow-backend:4780/api/servicenow/incidents \
  -H "Content-Type: application/json" \
  -d '{"short_description": "Test", "description": "Test incident"}'
```

---

## 📝 SUMMARY

### **What You Need to Do:**

1. ✅ **Replace servicenow.py** with servicenow_updated.py
2. ✅ **Update .env** with ServiceNow backend URL
3. ✅ **Restart backend server**
4. ✅ **Test connection** using curl
5. ✅ **Test from frontend**

### **No Frontend Changes Needed:**
- Frontend is already configured ✅
- All API endpoints are correct ✅
- Just start with `npm run dev` ✅

---

## 🚀 QUICK START

```bash
# 1. On Server - Update backend
cd /path/to/backend
mv app/servicenow.py app/servicenow_old.py
# Upload servicenow_updated.py
mv app/servicenow_updated.py app/servicenow.py

# 2. Update .env
echo "SERVICENOW_BACKEND_URL=http://servicenow-backend:4780" >> .env

# 3. Restart
pkill -f "uvicorn" && uvicorn app.main:app --host 0.0.0.0 --port 4799 &

# 4. On Local Machine - Start frontend
cd frontend
npm run dev
```

**Done!** Open browser to http://localhost:5173 and test.
