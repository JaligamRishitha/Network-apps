# PM Workflow 422 Error - Troubleshooting Guide

## Issue
Getting `422 Unprocessable Entity` when creating a maintenance order from Screen 1.

## Root Cause Analysis

The 422 error indicates the request payload doesn't match the expected schema. Looking at the code:

### Backend Expects (from `OrderCreateRequest`):
```python
class OrderCreateRequest(BaseModel):
    order_type: str  # "general" or "breakdown"
    equipment_id: Optional[str] = None
    functional_location: Optional[str] = None
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    breakdown_notification_id: Optional[str] = None
    created_by: str
    operations: List[OperationRequest] = []
    components: List[ComponentRequest] = []
    permits: List[PermitRequest] = []
```

### Frontend Sends (from `PMWorkflowScreen1.tsx`):
```typescript
{
  order_type: orderType,  // ✓ Correct
  equipment_id: equipmentId || null,  // ✓ Correct
  functional_location: functionalLocation || null,  // ✓ Correct
  priority,  // ✓ Correct
  planned_start_date: plannedStartDate || null,  // ✓ Correct
  planned_end_date: plannedEndDate || null,  // ✓ Correct
  breakdown_notification_id: breakdownNotificationId || null,  // ✓ Correct
  created_by: user?.username || 'system',  // ✓ Correct
  operations,  // ✓ Correct
  components,  // ✓ Correct
  permits: []  // ✓ Correct
}
```

## Potential Issues

### 1. **Date Format Issue**
The frontend uses `datetime-local` input which returns a string like `"2024-01-28T10:30"`.
FastAPI expects ISO 8601 format with timezone info.

**Solution**: Convert dates to ISO format before sending:

```typescript
// In handleCreateOrder function, before fetch:
const payload = {
  order_type: orderType,
  equipment_id: equipmentId || null,
  functional_location: functionalLocation || null,
  priority,
  planned_start_date: plannedStartDate ? new Date(plannedStartDate).toISOString() : null,
  planned_end_date: plannedEndDate ? new Date(plannedEndDate).toISOString() : null,
  breakdown_notification_id: breakdownNotificationId || null,
  created_by: user?.username || 'system',
  operations,
  components,
  permits: []
};
```

### 2. **Missing Authorization Header**
The backend might require authentication.

**Current Code**:
```typescript
const response = await fetch('/api/v1/pm-workflow/orders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({...})
});
```

**Should Include**:
```typescript
const response = await fetch('/api/v1/pm-workflow/orders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({...})
});
```

### 3. **Empty Operations Array**
The validation requires at least one operation, but the frontend allows creating orders without operations.

**Frontend Validation** (already present):
```typescript
if (operations.length === 0) {
  showError('At least one operation is required');
  return;
}
```

This is correct, but make sure it's being triggered.

## Quick Fix Steps

1. **Add date conversion** in `frontend/src/pages/PMWorkflowScreen1.tsx`:

```typescript
const handleCreateOrder = async () => {
  // Validation
  if (!equipmentId && !functionalLocation) {
    showError('Either Equipment ID or Functional Location is required');
    return;
  }
  if (operations.length === 0) {
    showError('At least one operation is required');
    return;
  }

  setLoading(true);
  try {
    const response = await fetch('/api/v1/pm-workflow/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`  // ADD THIS
      },
      body: JSON.stringify({
        order_type: orderType,
        equipment_id: equipmentId || null,
        functional_location: functionalLocation || null,
        priority,
        planned_start_date: plannedStartDate ? new Date(plannedStartDate).toISOString() : null,  // FIX THIS
        planned_end_date: plannedEndDate ? new Date(plannedEndDate).toISOString() : null,  // FIX THIS
        breakdown_notification_id: breakdownNotificationId || null,
        created_by: user?.username || 'system',
        operations,
        components,
        permits: []
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('API Error:', error);  // ADD THIS for debugging
      throw new Error(error.detail || 'Failed to create order');
    }

    const data = await response.json();
    showSuccess(`Order created successfully: ${data.order_number}`);
    
    // Reset form
    resetForm();
  } catch (error: any) {
    console.error('Create order error:', error);  // ADD THIS for debugging
    showError(error.message || 'Failed to create order');
  } finally {
    setLoading(false);
  }
};
```

## Testing Steps

1. Open browser DevTools (F12)
2. Go to Network tab
3. Try creating an order
4. Check the request payload in the Network tab
5. Check the response body for detailed error message
6. Look at Console tab for any JavaScript errors

## Expected Error Messages

If you see specific validation errors, they'll look like:
```json
{
  "detail": [
    {
      "loc": ["body", "planned_start_date"],
      "msg": "invalid datetime format",
      "type": "value_error.datetime"
    }
  ]
}
```

This will tell you exactly which field is causing the issue.

## Alternative: Check Backend Logs

The backend logs should show the exact validation error:
```bash
docker logs sap-erp-backend
```

Look for FastAPI validation errors that show which field failed validation.
