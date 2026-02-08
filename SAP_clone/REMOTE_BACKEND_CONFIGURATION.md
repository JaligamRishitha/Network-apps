# Remote Backend Configuration Guide

## Overview
This guide explains how to configure your SAP ERP Demo application to use a remote backend server instead of running the backend locally in Docker.

## What We Changed

### Architecture Before
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
│         (Frontend connects to           │        │
│          localhost:2004)                │        │
└─────────────────────────────────────────────────┘
```

### Architecture After
```
┌─────────────────────────────────────────────────┐
│              Docker Compose                      │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │         Frontend (React + Vite)          │   │
│  │         :2003                            │   │
│  │  (connects to remote backend)            │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                      │
                      │ HTTP Requests
                      ▼
┌──────────────────────────────────────────────────┐
│   Remote Backend Server                          │
│   http://207.180.217.117:4798                     │
│                                                  │
│   FastAPI + PostgreSQL                           │
└──────────────────────────────────────────────────┘
```

---

## Step-by-Step Configuration

### Step 1: Remove Backend from Docker Compose

**File:** `docker-compose.yml`

**Removed these services:**
```yaml
# PostgreSQL Database - REMOVED
postgres:
  image: postgres:15-alpine
  container_name: sap-erp-postgres
  ...

# FastAPI Backend - REMOVED
backend:
  build:
    context: ./backend
  ...
```

**Result:** Only the frontend service remains in docker-compose.yml

---

### Step 2: Update Frontend Environment Variable

**File:** `docker-compose.yml`

**Updated the frontend service:**
```yaml
services:
  # React Frontend (connects to remote backend)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: sap-erp-frontend
    ports:
      - "2003:2003"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://207.180.217.117:4798/api/v1  # Remote backend URL
```

**Key Points:**
- `VITE_API_URL` is used by Vite at build time
- Must point to your remote backend URL
- Include `/api/v1` path as that's where the API routes are mounted

---

### Step 3: Create Frontend .env File

**File:** `frontend/.env` (newly created)

```env
VITE_API_URL=http://207.180.217.117:4798/api/v1
```

**Why this is needed:**
- The `.env` file overrides default values in the code
- Vite reads this file during development and build
- This ensures the frontend always connects to the remote backend

---

### Step 4: Update .env.example

**File:** `.env.example`

**Updated the frontend section:**
```env
# Frontend (pointing to remote backend)
VITE_API_URL=http://207.180.217.117:4798/api/v1
```

---

## How to Use

### Option 1: Run with Docker Compose

```cmd
docker-compose down
docker-compose up --build
```

The frontend will be available at: `http://localhost:2003`

### Option 2: Run Frontend Directly (Development)

```cmd
cd frontend
npm install
npm run dev
```

The frontend will be available at: `http://localhost:2003`

---

## Verification Steps

### 1. Check Frontend is Running
Open your browser to `http://localhost:2003`

### 2. Check Network Requests
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try to login or perform any action
4. Verify requests are going to `http://207.180.217.117:4798/api/v1/*`

### 3. Test Login
Use one of the demo users:
- Username: `admin` / Password: `admin123`
- Username: `engineer` / Password: `engineer123`
- Username: `manager` / Password: `manager123`

---

## Troubleshooting

### Issue: Frontend still connects to localhost

**Solution:**
1. Make sure `frontend/.env` file exists with correct URL
2. Rebuild the Docker container: `docker-compose up --build`
3. Or restart the dev server if running with npm

### Issue: CORS errors

**Solution:**
The remote backend needs to allow CORS from your frontend origin. Check that the backend has CORS middleware configured:

```python
# backend/main.py should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Connection refused

**Solution:**
1. Verify the remote backend is running: `curl http://207.180.217.117:4798/health`
2. Check firewall rules allow incoming connections on port 4798
3. Verify the backend is listening on `0.0.0.0` not just `127.0.0.1`

---

## API Endpoints

The frontend connects to these remote endpoints:

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### Tickets
- `GET /api/v1/tickets` - List tickets
- `POST /api/v1/tickets` - Create ticket
- `PATCH /api/v1/tickets/{id}/status` - Update ticket status

### Modules
- `GET /api/v1/pm/*` - Plant Maintenance endpoints
- `GET /api/v1/mm/*` - Materials Management endpoints
- `GET /api/v1/fi/*` - Financial Accounting endpoints

### Users (Admin only)
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `DELETE /api/v1/users/{username}` - Delete user

---

## Files Modified

1. ✅ `docker-compose.yml` - Removed backend and postgres services
2. ✅ `frontend/.env` - Created with remote backend URL
3. ✅ `.env.example` - Updated with remote backend URL

---

## Reverting to Local Backend

If you need to switch back to running the backend locally:

1. Restore the backend and postgres services in `docker-compose.yml`
2. Update `frontend/.env`:
   ```env
   VITE_API_URL=http://localhost:2004/api/v1
   ```
3. Rebuild: `docker-compose up --build`

---

## Notes

- The remote backend URL is: `http://207.180.217.117:4798`
- The API base path is: `/api/v1`
- Frontend runs on port: `2003`
- Make sure the remote backend is accessible from your network
- For production, use HTTPS instead of HTTP
