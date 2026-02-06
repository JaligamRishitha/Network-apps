# Testing PM API Endpoint

## The Issue
Getting HTML response instead of JSON from `/api/v1/pm/assets`, which means:
- The endpoint doesn't exist (404)
- Or there's a routing issue
- Or the backend isn't running properly

## Quick Tests

### Test 1: Check if Backend is Running
```bash
docker ps | grep backend
```

Should show the backend container running.

### Test 2: Test the Endpoint Directly
```bash
# Get a token first (login)
curl -X POST http://localhost:2004/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Use the token to test the assets endpoint
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:2004/api/v1/pm/assets
```

### Test 3: Check Backend Logs
```bash
docker logs sap-erp-backend | tail -50
```

Look for:
- Any startup errors
- Route registration messages
- 404 errors when accessing /api/v1/pm/assets

### Test 4: Check Available Routes
```bash
curl http://localhost:2004/docs
```

This should show the FastAPI Swagger docs. Check if `/api/v1/pm/assets` is listed.

## Possible Issues & Solutions

### Issue 1: Backend Not Running
**Check:**
```bash
docker-compose ps
```

**Fix:**
```bash
docker-compose up -d backend
```

### Issue 2: PM Routes Not Imported
**Check:** `backend/main.py` should have:
```python
from backend.api.routes import pm
app.include_router(pm.router, prefix="/api/v1")
```

**Already verified** ✅ - This is correct in the code

### Issue 3: PM Router Prefix Conflict
**Check:** `backend/api/routes/pm.py` should have:
```python
router = APIRouter(prefix="/pm", tags=["Plant Maintenance"])
```

This means the full path is: `/api/v1` (from main.py) + `/pm` (from router) = `/api/v1/pm`

### Issue 4: Database Not Initialized
**Check:**
```bash
docker exec -it sap-erp-db psql -U postgres -d sap_erp -c "\dt pm.*"
```

Should show PM tables. If not, run migrations:
```bash
docker exec -it sap-erp-backend alembic upgrade head
```

### Issue 5: CORS or Proxy Issue
The frontend might be hitting the wrong URL.

**Check frontend .env:**
```
VITE_API_URL=http://localhost:2004/api/v1
```

## Immediate Fix to Try

### Option 1: Restart Backend
```bash
docker-compose restart backend
```

Wait 10 seconds, then refresh the browser.

### Option 2: Check Backend Health
```bash
curl http://localhost:2004/health
```

Should return a health check response.

### Option 3: Rebuild Backend
```bash
docker-compose down
docker-compose up -d --build backend
```

## Debug Output Needed

Please run these commands and share the output:

1. **Check if backend is running:**
```bash
docker-compose ps
```

2. **Check backend logs:**
```bash
docker logs sap-erp-backend | tail -100
```

3. **Test the endpoint:**
```bash
curl -v http://localhost:2004/api/v1/pm/assets
```

4. **Check what's actually running on port 2004:**
```bash
curl http://localhost:2004/
```

## Expected vs Actual

### Expected Response (JSON):
```json
{
  "assets": [],
  "total": 0
}
```

### Actual Response (HTML):
```html
<!DOCTYPE html>
<html>
...
</html>
```

This HTML response typically means:
- 404 Not Found page
- Or the frontend dev server is responding instead of the backend
- Or there's a proxy misconfiguration

## Next Steps

1. Run the diagnostic commands above
2. Share the output
3. We'll identify exactly where the routing is breaking
