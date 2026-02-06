# Fix Docker Build Error

## The Problem
Docker build cache is corrupted, causing the frontend build to fail with:
```
parent snapshot does not exist: not found
```

## Solution

### Option 1: Clean Docker Cache (Recommended)
```bash
# Stop all containers
docker-compose down

# Remove all stopped containers, networks, and dangling images
docker system prune -a

# Remove volumes (optional - will delete database data)
docker volume prune

# Rebuild without cache
docker-compose build --no-cache

# Start services
docker-compose up
```

### Option 2: Clean Only Frontend
```bash
# Stop containers
docker-compose down

# Remove frontend image
docker rmi sap-clone-frontend

# Remove build cache
docker builder prune -a

# Rebuild frontend only
docker-compose build --no-cache frontend

# Start all services
docker-compose up
```

### Option 3: Run Frontend Locally (Quick Fix)
Instead of using Docker for frontend, run it locally:

```bash
# Stop Docker services (keep backend running)
docker-compose up postgres backend kong camel itsm-mock erp-mock crm-mock prometheus grafana

# In a new terminal, run frontend locally
cd frontend
npm install
npm run dev
```

Then access:
- Frontend: http://localhost:5173 (Vite default) or http://localhost:3000
- Backend: http://localhost:8100

### Option 4: Complete Reset
If nothing else works:

```bash
# Stop everything
docker-compose down -v

# Remove all Docker data
docker system prune -a --volumes

# Remove node_modules
rm -rf frontend/node_modules

# Rebuild everything
docker-compose build --no-cache
docker-compose up
```

## Recommended Approach

**For Development (Fastest):**
```bash
# Terminal 1 - Backend services only
docker-compose up postgres backend kong camel itsm-mock erp-mock crm-mock

# Terminal 2 - Frontend locally
cd frontend
npm install
npm run dev
```

**For Production/Demo:**
```bash
# Clean rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

## Why This Happens
- Docker layer cache corruption
- Interrupted previous builds
- Disk space issues
- Docker Desktop updates

## Prevention
1. Regularly clean Docker cache: `docker system prune`
2. Use `.dockerignore` files
3. Don't interrupt builds
4. Keep Docker Desktop updated
