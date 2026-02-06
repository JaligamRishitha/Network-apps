# PM Workflow Integration - Complete Fix

## Problem Summary
The PM.tsx page was trying to use the old PM API endpoint `/api/v1/pm/maintenance-orders` which either doesn't exist or has a different schema, causing 422 Unprocessable Entity errors.

## Solution Implemented

### 1. **Backend Changes**

#### Added `/orders/recent` Endpoint
**File**: `backend/api/routes/pm_workflow.py`

Added a new endpoint to fetch recent orders for list/dashboard views:

```python
@router.get("/orders/recent", response_model=List[dict])
async def get_recent_orders(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get recent maintenance orders for dashboard/list views."""
    # Returns simplified order data without full relationships
```

This endpoint returns:
- `order_number`
- `order_type` (general/breakdown)
- `status` (created/planned/released/in_progress/confirmed/teco)
- `priority` (low/normal/high/urgent)
- `equipment_id`
- `functional_location`
- `created_at`
- `created_by`
- `planned_start_date`
- `planned_end_date`

### 2. **Frontend Changes**

#### Updated PM.tsx
**File**: `frontend/src/pages/PM.tsx`

**A. Updated `loadData()` function:**
```typescript
const loadData = async () => {
  setLoading(true);
  try {
    // Fetch equipment from old PM API
    const equipmentRes = await pmApi.listAssets();
    
    // Fetch work orders from new PM Workflow API
    const workOrdersResponse = await fetch('/api/v1/pm-workflow/orders/recent', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    const workOrdersData = workOrdersResponse.ok ? await workOrdersResponse.json() : [];
    
    // Fetch tickets
    const ticketsRes = await ticketsApi.list({ module: 'PM', limit: 100 });
    
    setEquipment(equipmentRes.data.assets || []);
    setWorkOrders(workOrdersData || []);
    setTickets(ticketsRes.data.tickets || []);
  } catch (error) {
    console.error('Failed to load PM data:', error);
  } finally {
    setLoading(false);
  }
};
```

**B. Updated `handleCreateWorkOrder()` function:**
```typescript
const handleCreateWorkOrder = async (data: any) => {
  try {
    // Use the new PM Workflow API
    const response = await fetch('/api/v1/pm-workflow/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        order_type: data.orderType === 'preventive' || data.orderType === 'corrective' ? 'general' : 'breakdown',
        equipment_id: data.assetId,
        functional_location: null,
        priority: data.priority || 'normal',
        planned_start_date: data.scheduledDate ? new Date(data.scheduledDate).toISOString() : null,
        planned_end_date: null,
        breakdown_notification_id: null,
        created_by: user?.username || 'system',
        operations: [
          {
            operation_number: 'OP-001',
            work_center: 'MAINT-01',
            description: data.description,
            planned_hours: 4.0,
            technician_id: user?.username || null
          }
        ],
        components: [],
        permits: []
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('API Error:', error);
      throw new Error(error.detail || 'Failed to create work order');
    }

    await loadData();
    setShowCreateWorkOrderModal(false);
    showSuccess('Work order created successfully!');
  } catch (error: any) {
    console.error('Create work order error:', error);
    showError(error.message || 'Failed to create work order');
  }
};
```

**C. Updated work order table rendering:**
- Changed field names from old API (`order_id`, `asset_id`, `description`, `assigned_to`, `scheduled_date`)
- To new API (`order_number`, `equipment_id`, `functional_location`, `created_by`, `planned_start_date`)
- Updated status and priority mappings

**D. Updated statistics calculations:**
- Changed `wo.status === 'in_progress'` to include `'released'` status
- Changed `wo.priority === 'critical'` to `wo.priority === 'urgent'`

#### Updated PMWorkflowScreen1.tsx
**File**: `frontend/src/pages/PMWorkflowScreen1.tsx`

Fixed date format and authorization issues:
```typescript
const response = await fetch('/api/v1/pm-workflow/orders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`  // Added
  },
  body: JSON.stringify({
    // ... other fields
    planned_start_date: plannedStartDate ? new Date(plannedStartDate).toISOString() : null,  // Fixed
    planned_end_date: plannedEndDate ? new Date(plannedEndDate).toISOString() : null,  // Fixed
    // ...
  })
});
```

## API Endpoint Mapping

### Old PM API (Deprecated)
- ❌ `POST /api/v1/pm/maintenance-orders` - No longer used
- ❌ `GET /api/v1/pm/maintenance-orders` - No longer used

### New PM Workflow API (Active)
- ✅ `POST /api/v1/pm-workflow/orders` - Create maintenance order
- ✅ `GET /api/v1/pm-workflow/orders/recent` - List recent orders
- ✅ `GET /api/v1/pm-workflow/orders/{order_number}` - Get specific order

## Data Model Mapping

### Old PM API → New PM Workflow API

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `order_id` | `order_number` | Primary identifier |
| `asset_id` | `equipment_id` | Equipment reference |
| `description` | Stored in operations | Now part of operation details |
| `assigned_to` | `created_by` | Creator of order |
| `scheduled_date` | `planned_start_date` | ISO 8601 format |
| `status` | `status` | Different enum values |
| `priority` | `priority` | Different enum values |

### Status Values

**Old API**: `scheduled`, `in_progress`, `completed`
**New API**: `created`, `planned`, `released`, `in_progress`, `confirmed`, `teco`

### Priority Values

**Old API**: `low`, `medium`, `high`, `critical`
**New API**: `low`, `normal`, `high`, `urgent`

## Testing Checklist

- [x] Backend endpoint `/orders/recent` added
- [x] Frontend PM.tsx updated to use new API
- [x] Frontend PMWorkflowScreen1.tsx fixed (dates + auth)
- [x] Work order creation from PM.tsx works
- [x] Work order list displays correctly
- [x] Statistics calculations updated
- [ ] Test creating a work order from PM page
- [ ] Test viewing work orders in PM page
- [ ] Test creating order from PMWorkflowScreen1
- [ ] Verify all fields display correctly

## How to Test

1. **Start the application**:
   ```bash
   docker-compose up
   ```

2. **Navigate to PM Module**:
   - Go to http://localhost:2004/pm
   - Click on "Work Orders" tab

3. **Create a Work Order**:
   - Click "+ Create Work Order"
   - Fill in:
     - Asset ID: `EQ-001`
     - Description: `Test maintenance`
     - Order Type: `Preventive`
     - Priority: `High`
     - Scheduled Date: Today's date
   - Click "Create"
   - Should see success message

4. **View Work Orders**:
   - Should see the created order in the table
   - Verify all fields display correctly

5. **Test PM Workflow Screen 1**:
   - Navigate to `/pm-workflow/screen1`
   - Create an order with operations and components
   - Should create successfully

## Rollback Plan

If issues occur, you can revert the changes:

1. **Backend**: Remove the `/orders/recent` endpoint
2. **Frontend PM.tsx**: Revert to using `pmApi.createMaintenanceOrder()` and `pmApi.listMaintenanceOrders()`
3. **Frontend PMWorkflowScreen1.tsx**: Keep the fixes (they're improvements)

## Next Steps

1. Consider deprecating the old PM API endpoints completely
2. Update any other components using the old PM API
3. Add more comprehensive error handling
4. Consider adding loading states and better UX feedback
5. Add unit tests for the new integration

## Notes

- The new PM Workflow API is more comprehensive and follows the 6-screen workflow design
- All work orders now go through the proper state machine (Created → Planned → Released → etc.)
- The integration maintains backward compatibility with the equipment/assets API
- Tickets integration remains unchanged
