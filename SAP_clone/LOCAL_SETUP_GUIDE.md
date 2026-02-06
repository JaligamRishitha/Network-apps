# Local Development Setup Guide

## Overview
This guide explains how to run the SAP ERP Demo application locally with both frontend and backend on your machine.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Docker Compose                      │
│                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Postgres │  │   FastAPI    │  │  Frontend │ │
│  │          │  │   Backend    │  │   React   │ │
│  │ :5435    │  │   :2004      │  │   :2003   │ │
│  └──────────┘  └──────────────┘  └───────────┘ │
│       ▲              ▲                  │        │
│       └──────────────┘                  │        │
│                                         │        │
│         Frontend connects to            │        │
│         localhost:2004                  │        │
└─────────────────────────────────────────────────┘
```

---

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```cmd
docker-compose up --build
```

Or use the provided script:
```cmd
start-local.bat
```

**Services will be available at:**
- Frontend: http://localhost:2003
- Backend API: http://localhost:2004
- PostgreSQL: localhost:5435

### Option 2: Run Services Separately

#### 1. Start PostgreSQL
```cmd
docker run -d ^
  --name sap-erp-postgres ^
  -e POSTGRES_USER=sapuser ^
  -e POSTGRES_PASSWORD=sappassword ^
  -e POSTGRES_DB=saperp ^
  -p 5435:5432 ^
  postgres:15-alpine
```

#### 2. Start Backend
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: http://localhost:8000

#### 3. Start Frontend
```cmd
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:2003

---

## Configuration Files

### 1. Frontend Environment (.env)
**File:** `frontend/.env`
```env
VITE_API_URL=http://localhost:2004/api/v1
```

### 2. Backend Environment
**File:** `.env` (root directory)
```env
DATABASE_URL=postgresql+asyncpg://sapuser:sappassword@localhost:5435/saperp
JWT_SECRET=your-secret-key-change-in-production
```

### 3. Docker Compose
**File:** `docker-compose.yml`
- PostgreSQL on port 5435
- Backend on port 2004
- Frontend on port 2003

---

## Stopping Services

### Docker Compose
```cmd
docker-compose down
```

### Individual Services
```cmd
# Stop PostgreSQL
docker stop sap-erp-postgres
docker rm sap-erp-postgres

# Stop Backend (Ctrl+C in terminal)

# Stop Frontend (Ctrl+C in terminal)
```

---

## Database Setup

The database is automatically initialized when you start the services. If you need to reset:

```cmd
# Stop services
docker-compose down

# Remove volumes
docker volume rm sap-clone_postgres_data

# Start fresh
docker-compose up --build
```

---

## Testing the Setup

### 1. Check Backend Health
```cmd
curl http://localhost:2004/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Test Login API
```powershell
Invoke-WebRequest -Uri "http://localhost:2004/api/v1/auth/login" ^
  -Method POST ^
  -Headers @{"Content-Type"="application/json"} ^
  -Body '{"username":"admin","password":"admin123"}' ^
  -UseBasicParsing
```

### 3. Access Frontend
Open browser: http://localhost:2003

**Demo Users:**
- Username: `admin` / Password: `admin123` (Admin)
- Username: `engineer` / Password: `engineer123` (Maintenance Engineer)
- Username: `manager` / Password: `manager123` (Store Manager)
- Username: `finance` / Password: `finance123` (Finance Officer)

---

## Troubleshooting

### Port Already in Use

If ports are already in use, you can change them in `docker-compose.yml`:

```yaml
ports:
  - "5436:5432"  # Change PostgreSQL port
  - "2005:8000"  # Change Backend port
  - "2004:2003"  # Change Frontend port
```

Don't forget to update `frontend/.env`:
```env
VITE_API_URL=http://localhost:2005/api/v1
```

### Database Connection Issues

Check if PostgreSQL is running:
```cmd
docker ps | findstr postgres
```

Check logs:
```cmd
docker logs sap-erp-postgres
```

### Backend Not Starting

Check backend logs:
```cmd
docker logs sap-erp-backend
```

Common issues:
- Database not ready (wait a few seconds)
- Port 2004 already in use
- Missing environment variables

### Frontend Not Connecting

1. Check if backend is running:
   ```cmd
   curl http://localhost:2004/health
   ```

2. Verify `frontend/.env` has correct URL:
   ```env
   VITE_API_URL=http://localhost:2004/api/v1
   ```

3. Restart frontend:
   ```cmd
   docker-compose restart frontend
   ```

---

## Development Workflow

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Changes to files in `frontend/src` will auto-reload
- **Backend**: Changes to files in `backend` will auto-reload (if using `--reload` flag)

### Viewing Logs

```cmd
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

---

## API Documentation

Once the backend is running, access the interactive API docs:

- Swagger UI: http://localhost:2004/docs
- ReDoc: http://localhost:2004/redoc

---

## Files Modified for Local Setup

1. ✅ `docker-compose.yml` - Restored backend and postgres services
2. ✅ `frontend/.env` - Updated to use localhost:2004
3. ✅ `.env.example` - Updated with local configuration
4. ✅ `start-local.bat` - Quick start script

---

## Switching Between Local and Remote

### To use Remote Backend:
See `REMOTE_BACKEND_CONFIGURATION.md`

### To use Local Backend:
Follow this guide (current setup)

---

## Notes

- The setup uses Docker volumes for PostgreSQL data persistence
- Backend runs on port 2004 (mapped from container port 8000)
- Frontend runs on port 2003
- All services run in Docker containers for consistency
- Database is automatically seeded with demo data on first run
