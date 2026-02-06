# Development Workflow: Salesforce CRM Application

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR LOCAL LAPTOP                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Frontend Development Server                       │  │
│  │         (React 19 + Vite + TailwindCSS)                  │  │
│  │         http://localhost:5173                            │  │
│  │                                                           │  │
│  │  - Hot Module Reloading (Vite)                           │  │
│  │  - Live Code Changes                                     │  │
│  │  - Browser DevTools + React DevTools                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           │ API Requests (Axios)                 │
│                           │ VITE_API_URL → http://149.102.158.71:4799
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │ Internet
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    CONTABO SERVER                                │
│                    149.102.158.71                                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         FastAPI Backend (Port 4799)                        │ │
│  │         (Python 3.11 + Uvicorn)                            │ │
│  │         Container: salesforce-backend                      │ │
│  │                                                            │ │
│  │  API Routes:                                              │ │
│  │  - /api/auth/* (Authentication)                           │ │
│  │  - /api/accounts/* (Account Management)                   │ │
│  │  - /api/contacts/* (Contact Management)                   │ │
│  │  - /api/leads/* (Lead Management)                         │ │
│  │  - /api/opportunities/* (Opportunity Pipeline)            │ │
│  │  - /api/cases/* (Case Management)                         │ │
│  │  - /api/dashboard/* (Dashboard Stats)                     │ │
│  │  - /api/activities/* (Activity Logging)                   │ │
│  │  - /api/service/* (Service Management)                    │ │
│  │  - /api/platform-events/* (Platform Events)               │ │
│  │  - /api/sap/* (SAP Integration)                           │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │              PostgreSQL Databases                          │ │
│  │                                                            │ │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐ │ │
│  │  │ salesforce-db   │ │ mulesoft-db     │ │servicenow-db │ │ │
│  │  │ Port: 4791      │ │ Port: 4792      │ │ Port: 4793   │ │ │
│  │  │ salesforce_crm  │ │ mulesoft_integ  │ │servicenow_it │ │ │
│  │  └─────────────────┘ └─────────────────┘ └──────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Port Reference

| Service | Port | Container Port | Description |
|---------|------|----------------|-------------|
| Frontend (Local Dev) | 5173 | - | Vite dev server |
| Frontend (Production) | 5173 | 80 | Nginx serving React build |
| Backend API | 4799 | 8000 | FastAPI + Uvicorn |
| Salesforce DB | 4791 | 5432 | PostgreSQL - CRM data |
| MuleSoft DB | 4792 | 5432 | PostgreSQL - Integration data |
| ServiceNow DB | 4793 | 5432 | PostgreSQL - ITSM data |

---

## Daily Development Workflow

### Morning Setup

```
┌─────────────────────────────────────────────────────────┐
│ 1. CHECK DOCKER CONTAINERS ON SERVER                     │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 2. START LOCAL FRONTEND                                  │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ 3. BEGIN DEVELOPMENT                                     │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step Daily Workflow

#### Step 1: Check Server Status

```bash
# SSH into your server
ssh root@149.102.158.71

# Check if all containers are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE                    STATUS          PORTS
# xxxxx          salesforce-backend       Up X hours      0.0.0.0:4799->8000/tcp
# xxxxx          salesforce-frontend      Up X hours      0.0.0.0:5173->80/tcp
# xxxxx          postgres:16-alpine       Up X hours      0.0.0.0:4791->5432/tcp
# xxxxx          postgres:16-alpine       Up X hours      0.0.0.0:4792->5432/tcp
# xxxxx          postgres:16-alpine       Up X hours      0.0.0.0:4793->5432/tcp

# Check backend logs (last 50 lines)
docker logs salesforce-backend --tail 50

# Check if backend is healthy
curl http://localhost:4799/api/health
# Expected: {"status":"healthy"}

# Exit server
exit
```

**Quick Test from Local Machine:**
```bash
# Test API connectivity from your laptop
curl http://149.102.158.71:4799/api/health
# Expected response: {"status":"healthy"}

# Test API docs are accessible
curl http://149.102.158.71:4799/docs
```

#### Step 2: Start Local Frontend

```bash
# Navigate to your Salesforce project
cd ~/Network-apps/Salesforce/frontend

# Create .env file if not exists (one-time setup)
echo "VITE_API_URL=http://149.102.158.71:4799" > .env

# Install dependencies (if needed)
npm install

# Start Vite development server
npm run dev

# Output:
#   VITE v7.x.x  ready in xxx ms
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: http://192.168.x.x:5173/
```

**Open Browser:**
- Navigate to `http://localhost:5173`
- Open DevTools (F12)
- Check Console and Network tabs for any errors

#### Step 3: Begin Development

You're ready to code! Changes to React components will hot-reload automatically.

---

## Feature Development Workflow

### Scenario: Adding a New Feature

```
┌──────────────────────────────────────────────────────────────┐
│ PLAN FEATURE                                                  │
│ - Frontend changes needed?                                    │
│ - Backend changes needed?                                     │
│ - Database changes needed?                                    │
└────────────────────┬─────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│   BACKEND     │         │   FRONTEND    │
│   FIRST       │         │   ONLY        │
└───────┬───────┘         └───────┬───────┘
        │                         │
        ▼                         ▼
┌──────────────────────────────────────────┐
│ TEST INTEGRATION                          │
└──────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│ COMMIT & DEPLOY                           │
└──────────────────────────────────────────┘
```

### Example: Adding a "Reports" Feature

#### Phase 1: Backend Development (on Server)

```bash
# SSH into server
ssh root@149.102.158.71

# Navigate to project directory
cd /path/to/Salesforce

# Create a new route file
nano backend/app/routes/reports.py
```

**Add new API endpoint:**
```python
# backend/app/routes/reports.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/sales-summary")
async def get_sales_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Your report logic here
    return {"total_opportunities": 0, "total_value": 0}
```

**Register the router in main.py:**
```bash
nano backend/app/main.py
```

Add:
```python
from .routes import reports
app.include_router(reports.router)
```

**Rebuild and restart the backend:**
```bash
# Rebuild the container
docker-compose build backend

# Restart just the backend service
docker-compose up -d backend

# Check logs
docker logs salesforce-backend --tail 50

# Test the new endpoint
curl http://localhost:4799/api/reports/sales-summary
```

**Exit server:**
```bash
exit
```

**Test from local machine:**
```bash
curl http://149.102.158.71:4799/api/reports/sales-summary
```

#### Phase 2: Frontend Development (on Local Laptop)

```bash
# Already in your frontend directory
cd ~/Network-apps/Salesforce/frontend
```

**Add API service method in `src/services/api.js`:**
```javascript
// Reports
export const reportsAPI = {
  getSalesSummary: () => api.get('/api/reports/sales-summary'),
};
```

**Create new component:**
```javascript
// src/pages/Reports.jsx
import { useState, useEffect } from 'react';
import { reportsAPI } from '../services/api';

export default function Reports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchReport() {
      try {
        const response = await reportsAPI.getSalesSummary();
        setData(response.data);
      } catch (error) {
        console.error('Failed to load report:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchReport();
  }, []);

  if (loading) return <div>Loading...</div>;
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Sales Summary</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
```

**Add route in `src/App.jsx`:**
```javascript
import Reports from './pages/Reports';
// Add to routes:
<Route path="/reports" element={<Reports />} />
```

**Test in browser:**
1. Save files (Vite hot-reloads automatically)
2. Navigate to `http://localhost:5173/reports`
3. Check DevTools Network tab to verify API call

---

## Code Change Workflow

### Frontend Changes Only

```
┌─────────────────────────────────────────┐
│ Edit frontend code locally               │
│ (Changes auto-reload in browser)        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Test in browser at localhost:5173       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Commit changes                           │
│ git add frontend/                        │
│ git commit -m "message"                  │
│ git push origin main                     │
└─────────────────────────────────────────┘
```

### Backend Changes Only

```
┌─────────────────────────────────────────┐
│ SSH into server                          │
│ ssh root@149.102.158.71                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Edit backend code                        │
│ cd /path/to/Salesforce                   │
│ nano backend/app/routes/example.py       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Restart backend container                │
│ docker-compose restart backend           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Test from local frontend                 │
│ Check browser at localhost:5173         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Commit changes                           │
│ git add backend/                         │
│ git commit -m "message"                  │
│ git push origin main                     │
└─────────────────────────────────────────┘
```

### Database Schema Changes

```
┌─────────────────────────────────────────┐
│ SSH into server                          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Backup database (IMPORTANT!)             │
│ docker exec salesforce-db pg_dump \      │
│   -U salesforce salesforce_crm > backup.sql
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Update SQLAlchemy models in             │
│ backend/app/db_models.py                │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Rebuild & restart backend                │
│ docker-compose up -d --build backend    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Update frontend types/interfaces         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Test full stack                          │
└─────────────────────────────────────────┘
```

---

## Debugging Workflow

### Frontend Debugging

```
Issue occurs in browser
         │
         ▼
┌─────────────────────────────────────────┐
│ Open Browser DevTools (F12)              │
│ - Check Console for errors               │
│ - Check Network tab for failed requests  │
│ - Check React DevTools components        │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌──────────────┐    ┌──────────────┐
│ Frontend     │    │ Backend      │
│ Issue        │    │ Issue        │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
Fix locally          Debug on server
```

### Backend Debugging

```bash
# SSH into server
ssh root@149.102.158.71

# Check if containers are running
docker ps

# View live backend logs
docker logs -f salesforce-backend

# View last 100 lines of backend logs
docker logs salesforce-backend --tail 100

# View error logs only
docker logs salesforce-backend 2>&1 | grep -i error

# Check backend health
curl http://localhost:4799/api/health

# Interactive shell into backend container
docker exec -it salesforce-backend /bin/bash

# Check server resources
htop
df -h
free -m
```

### Database Debugging

```bash
# SSH into server
ssh root@149.102.158.71

# Connect to Salesforce database
docker exec -it salesforce-db psql -U salesforce -d salesforce_crm

# Useful PostgreSQL commands:
\dt                          # List all tables
\d+ accounts                 # Describe accounts table
SELECT COUNT(*) FROM users;  # Count users
SELECT * FROM accounts LIMIT 10;
\q                           # Quit

# Connect to MuleSoft database
docker exec -it mulesoft-db psql -U mulesoft -d mulesoft_integration

# Connect to ServiceNow database
docker exec -it servicenow-db psql -U servicenow -d servicenow_itsm
```

### Common Issues and Solutions

**Issue 1: CORS Error**
```
Access to fetch at 'http://149.102.158.71:4799/api/...'
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solution:** CORS is already configured in `backend/app/main.py`. If you need to add a new origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://149.102.158.71:5173",
        "http://149.102.158.71:4799",
        # Add new origins here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issue 2: API Not Responding**
```bash
# Check if backend container is running
ssh root@149.102.158.71
docker ps | grep backend

# If not running, start all services
docker-compose up -d

# Check for errors in startup
docker logs salesforce-backend

# Check if port is accessible
curl http://localhost:4799/api/health
```

**Issue 3: Database Connection Error**
```bash
# Check if database container is running
docker ps | grep salesforce-db

# Check database logs
docker logs salesforce-db

# Restart database
docker-compose restart salesforce-db

# Wait for healthy status, then restart backend
docker-compose restart backend
```

---

## Docker Commands Reference

### Container Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart salesforce-db

# Rebuild and restart backend
docker-compose up -d --build backend

# View running containers
docker ps

# View all containers (including stopped)
docker ps -a
```

### Logs

```bash
# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs salesforce-db

# Follow logs in real-time
docker-compose logs -f backend

# View last N lines
docker-compose logs --tail 50 backend
```

### Database Operations

```bash
# Backup Salesforce database
docker exec salesforce-db pg_dump -U salesforce salesforce_crm > backup_$(date +%Y%m%d).sql

# Restore Salesforce database
docker exec -i salesforce-db psql -U salesforce salesforce_crm < backup.sql

# Run seed data
docker-compose --profile seed up seed

# Connect to database shell
docker exec -it salesforce-db psql -U salesforce -d salesforce_crm
```

---

## Git Workflow

### Recommended Branch Strategy

```
main (production)
  │
  ├── develop (staging)
  │     │
  │     ├── feature/reports-dashboard
  │     ├── feature/email-integration
  │     └── bugfix/login-error
  │
  └── hotfix/critical-bug
```

### Daily Git Workflow

```bash
# Morning: Pull latest changes
cd ~/Network-apps/Salesforce
git pull origin main

# Create feature branch
git checkout -b feature/new-feature

# Work on your feature...
# Make multiple commits as you progress

git add .
git commit -m "Add reports API endpoint"

# Push to remote
git push origin feature/new-feature

# When feature is complete, merge back
git checkout main
git merge feature/new-feature
git push origin main
```

### Deploying Changes to Server

```bash
# SSH into server
ssh root@149.102.158.71

# Navigate to project
cd /path/to/Salesforce

# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker-compose up -d --build

# Monitor startup
docker-compose logs -f

# Exit
exit
```

---

## Testing Workflow

### Quick Testing Checklist

**Frontend:**
- [ ] Components render correctly
- [ ] Forms validate properly
- [ ] Navigation works
- [ ] API calls succeed (check Network tab)
- [ ] No console errors
- [ ] Responsive design works

**Backend:**
- [ ] API endpoints return correct data
- [ ] Authentication works (`/api/auth/login`)
- [ ] Error handling returns proper status codes
- [ ] Health check passes (`/api/health`)

**Integration:**
- [ ] Frontend successfully calls backend
- [ ] CORS is configured correctly
- [ ] Authentication flows work end-to-end
- [ ] Data persists in database

### Testing API Endpoints

```bash
# Health check
curl http://149.102.158.71:4799/api/health

# Login (get token)
curl -X POST http://149.102.158.71:4799/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token for authenticated requests
curl http://149.102.158.71:4799/api/accounts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Check API documentation
# Open in browser: http://149.102.158.71:4799/docs
```

---

## Environment Configuration

### Local Development (.env in frontend/)

```bash
# frontend/.env
VITE_API_URL=http://149.102.158.71:4799
```

### Server (.env in project root)

```bash
# .env (on server)
SECRET_KEY=your-super-secret-key-change-in-production

# Database passwords
SALESFORCE_DB_PASSWORD=salesforce_secret
MULESOFT_DB_PASSWORD=mulesoft_secret
SERVICENOW_DB_PASSWORD=servicenow_secret

# External integrations (optional)
MULESOFT_CLIENT_ID=your-mulesoft-client-id
MULESOFT_CLIENT_SECRET=your-mulesoft-client-secret
```

---

## End of Day Workflow

```
┌─────────────────────────────────────────┐
│ 1. Commit all changes                    │
│    git add .                             │
│    git commit -m "EOD: description"      │
│    git push origin main                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 2. Stop local frontend                   │
│    Ctrl+C in terminal                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 3. Check server status (optional)        │
│    ssh root@149.102.158.71               │
│    docker ps                             │
│    exit                                  │
└─────────────────────────────────────────┘
```

---

## Emergency Procedures

### Backend Container is Down

```bash
# Quick restart
ssh root@149.102.158.71
docker-compose restart backend
docker logs salesforce-backend --tail 50
exit
```

### All Services Down

```bash
ssh root@149.102.158.71
cd /path/to/Salesforce
docker-compose up -d
docker ps
exit
```

### Database Connection Lost

```bash
ssh root@149.102.158.71

# Check database status
docker ps | grep db

# Restart database containers
docker-compose restart salesforce-db mulesoft-db servicenow-db

# Wait for healthy status
docker-compose ps

# Restart backend to reconnect
docker-compose restart backend
```

### Server Unresponsive

1. Try SSH: `ssh root@149.102.158.71`
2. If SSH works:
   ```bash
   htop          # Check resources
   df -h         # Check disk space
   docker-compose restart  # Restart all services
   ```
3. If SSH doesn't work: Use Contabo control panel to restart the VPS

---

## Quick Reference Commands

### LOCAL (Your Laptop)

```bash
# Frontend Development
cd ~/Network-apps/Salesforce/frontend
npm run dev                    # Start Vite dev server
npm run build                  # Build for production
npm run lint                   # Run ESLint

# Git
git status                     # Check status
git add .                      # Stage changes
git commit -m "msg"            # Commit
git push origin main           # Push to remote
git pull origin main           # Pull latest

# Test API
curl http://149.102.158.71:4799/api/health
```

### SERVER (149.102.158.71)

```bash
# Connect
ssh root@149.102.158.71

# Docker
docker ps                              # List running containers
docker-compose up -d                   # Start all services
docker-compose down                    # Stop all services
docker-compose restart backend         # Restart backend
docker-compose up -d --build backend   # Rebuild & restart
docker logs salesforce-backend -f      # Follow logs

# Database
docker exec -it salesforce-db psql -U salesforce -d salesforce_crm

# Exit
exit
```

---

## Project Structure

```
Salesforce/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # Database connection
│   │   ├── db_models.py         # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── auth.py              # Authentication
│   │   ├── logger.py            # Logging utility
│   │   ├── services.py          # Business logic
│   │   ├── routes/              # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── accounts.py
│   │   │   ├── contacts.py
│   │   │   ├── leads.py
│   │   │   ├── opportunities.py
│   │   │   ├── cases.py
│   │   │   ├── dashboard.py
│   │   │   ├── activities.py
│   │   │   ├── service.py
│   │   │   └── ...
│   │   └── integrations/        # External integrations
│   │       ├── mulesoft_client.py
│   │       └── sap_integration_service.py
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile
│   └── seed.py                  # Database seeding
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── main.jsx             # Entry point
│   │   ├── index.css            # Global styles
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Page components
│   │   ├── services/
│   │   │   └── api.js           # Axios API client
│   │   └── context/             # React context
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── database/
│   ├── salesforce/init/         # Salesforce DB init scripts
│   ├── mulesoft/init/           # MuleSoft DB init scripts
│   └── servicenow/init/         # ServiceNow DB init scripts
│
├── docker-compose.yml           # Docker orchestration
├── .env.example                 # Environment template
└── README.md
```

---

## Tips for Smooth Workflow

1. **Keep containers running 24/7** - Docker containers auto-restart unless stopped
2. **Use environment variables** - Never hardcode API URLs or secrets
3. **Monitor logs regularly** - `docker logs -f salesforce-backend`
4. **Commit frequently** - Small, focused commits are easier to debug
5. **Test as you go** - Don't wait until the end to test
6. **Backup database before schema changes** - Always create a backup first
7. **Use FastAPI docs** - Visit `http://149.102.158.71:4799/docs` for interactive API testing
8. **Check CORS** - If API calls fail, CORS is often the culprit
