# Database Migration Fix - January 28, 2026

## Problem
The PM Workflow API was returning 500 errors because:
1. Database tables didn't exist
2. Enum values were case-sensitive causing validation errors

Error messages:
```
sqlalchemy.exc.ProgrammingError: relation "pm_workflow.workflow_maintenance_orders" does not exist
sqlalchemy.exc.DBAPIError: invalid input value for enum pm_workflow.workflow_order_type_enum: "GENERAL"
```

## Root Cause
1. Docker build cache was corrupted, causing frontend build failures
2. Database migrations had not been run after container restart
3. Migration 008 had incorrect revision reference ('007' instead of '007_create_pm_workflow_tables')
4. Enum values in the API were case-sensitive (expected lowercase but could receive uppercase)

## Solution Applied

### 1. Fixed Docker Build Cache
```bash
docker system prune -f  # Reclaimed 9.7GB
docker-compose build --no-cache frontend
```

### 2. Fixed Migration Dependencies
- Removed conflicting migration 008 (indexes already created in migration 007)
- Migration 007 already creates all necessary tables and indexes

### 3. Ran Database Migrations
```bash
docker-compose exec -w /app/backend backend sh -c "PYTHONPATH=/app alembic upgrade head"
```

### 4. Fixed Enum Case Sensitivity
Modified `backend/api/routes/pm_workflow.py` to convert enum values to lowercase before validation:
```python
order_type = WorkflowOrderType(request.order_type.lower())
priority = Priority(request.priority.lower())
```

This allows the API to accept both uppercase and lowercase enum values.

## Tables Created
The following tables were created in the `pm_workflow` schema:
- workflow_maintenance_orders
- workflow_operations
- workflow_components
- workflow_purchase_orders
- workflow_goods_receipts
- workflow_goods_issues
- workflow_confirmations
- workflow_malfunction_reports
- workflow_document_flow
- workflow_cost_summaries

## Status
✅ Database migrations completed successfully
✅ Backend health check passing
✅ PM Workflow API endpoints now functional
✅ CORS properly configured
✅ Enum case sensitivity fixed

## Next Steps
The frontend should now be able to successfully create work orders and interact with the PM Workflow API.
