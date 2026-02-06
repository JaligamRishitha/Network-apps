# PM Equipment Not Displaying - Troubleshooting & Fix

## Issue
Equipment is not being displayed in the PM Equipment Master tab even after creation.

## Potential Causes

1. **Default Pagination Limit**: The API has a default limit of 20 items
2. **Response Structure Mismatch**: The response might have a different structure
3. **Authentication Issues**: Token might not be included in requests
4. **Data Not Refreshing**: Page needs to reload after creation

## Fixes Applied

### 1. Increased Pagination Limit
**File**: `frontend/src/pages/PM.tsx`

Changed from default limit (20) to 100:
```typescript
const equipmentRes = await pmApi.listAssets({ limit: 100 });
```

### 2. Better Response Parsing
Added fallback parsing for different response structures:
```typescript
const equipmentData = equipmentRes.data?.assets || equipmentRes.data || [];
setEquipment(equipmentData);
```

### 3. Enhanced Logging
Added comprehensive console logging to debug:
```typescript
console.log('Equipment API response:', equipmentRes);
console.log('Parsed equipment data:', equipmentData);
console.log('Error details:', error.response?.data);
```

### 4. Added Refresh Button
Added a manual refresh button in the "No equipment found" message:
```typescript
<button className="sap-toolbar-button" onClick={loadData}>
  Refresh
</button>
```

### 5. Better Error Handling
Improved error messages with more details:
```typescript
catch (error: any) {
  console.error('Failed to load PM data:', error);
  console.error('Error details:', error.response?.data);
  showError('Failed to load PM data. Please check console for details.');
}
```

## Debugging Steps

### Step 1: Check Browser Console
Open browser DevTools (F12) and look for:
```
Equipment API response: { data: { assets: [...], total: X } }
Parsed equipment data: [...]
```

### Step 2: Check Network Tab
1. Open DevTools → Network tab
2. Look for request to `/api/v1/pm/assets`
3. Check:
   - Status code (should be 200)
   - Response body
   - Request headers (Authorization header present?)

### Step 3: Check Backend Logs
```bash
docker logs sap-erp-backend | grep assets
```

Look for:
- Any errors
- The actual response being sent

### Step 4: Verify Equipment Was Created
Check the database directly:
```bash
docker exec -it sap-erp-db psql -U postgres -d sap_erp
SELECT * FROM pm.assets;
```

## Common Issues & Solutions

### Issue 1: "No equipment found" but equipment exists in DB
**Solution**: Click the "Refresh" button or reload the page

### Issue 2: Equipment created but not showing
**Cause**: Pagination limit too low
**Solution**: Already fixed - limit increased to 100

### Issue 3: Console shows "Failed to load PM data"
**Cause**: Authentication or API error
**Solution**: 
1. Check if you're logged in
2. Check browser console for detailed error
3. Verify backend is running

### Issue 4: Response structure is different
**Cause**: API returns data in unexpected format
**Solution**: Already fixed - added fallback parsing

## API Response Structure

### Expected Response
```json
{
  "assets": [
    {
      "asset_id": "ASSET-001",
      "asset_type": "transformer",
      "name": "Main Transformer",
      "location": "Building A",
      "installation_date": "2024-01-01",
      "status": "operational",
      "description": "Primary transformer"
    }
  ],
  "total": 1
}
```

### Axios Response Wrapper
```typescript
{
  data: {
    assets: [...],
    total: 1
  },
  status: 200,
  statusText: "OK",
  headers: {...},
  config: {...}
}
```

## Testing Checklist

- [ ] Open PM module
- [ ] Click "Equipment Master" tab
- [ ] Check browser console for logs
- [ ] If no equipment shown, click "Refresh" button
- [ ] Create new equipment
- [ ] Verify it appears in the list immediately
- [ ] Check that all fields display correctly

## Quick Fix Commands

### Restart Frontend (if needed)
```bash
docker-compose restart frontend
```

### Clear Browser Cache
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

### Check if Equipment Exists
```bash
# Via API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:2004/api/v1/pm/assets

# Via Database
docker exec -it sap-erp-db psql -U postgres -d sap_erp -c "SELECT * FROM pm.assets;"
```

## Expected Behavior After Fix

1. ✅ Equipment loads on page mount
2. ✅ Equipment displays in table with all fields
3. ✅ New equipment appears immediately after creation
4. ✅ Refresh button works if manual reload needed
5. ✅ Console shows detailed logs for debugging
6. ✅ Error messages are clear and actionable

## Next Steps

1. Open the PM module and check the browser console
2. Look for the log messages added
3. If equipment still doesn't show, share the console output
4. Check the Network tab for the actual API response
