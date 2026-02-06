# MuleSoft Integration Tracking Implementation

## Overview
Enhanced the Salesforce backend to automatically track MuleSoft integration requests whenever an Account is created. This provides a complete audit trail and enables future async processing or approval workflows.

## Changes Made

### 1. Database Model - `backend/app/db_models.py`
Added new `MulesoftRequest` model:
- **Table**: `mulesoft_requests`
- **Fields**:
  - `id` (Integer, PK)
  - `account_id` (ForeignKey to accounts.id, nullable)
  - `request_type` (String: create | update | delete)
  - `status` (String: pending | sent | approved | rejected | failed, default=pending)
  - `mulesoft_response` (Text, nullable)
  - `error_message` (Text, nullable)
  - `created_at` (DateTime, auto-set)
  - `updated_at` (DateTime, auto-updated)
- **Relationship**: Many-to-One with Account (backref: mulesoft_requests)

### 2. MuleSoft API Routes - `backend/app/routes/mulesoft.py` (NEW)
Created new router with prefix `/api/mulesoft` and tag `mulesoft`:

**Endpoint 1: List MuleSoft Requests**
- **Route**: `GET /api/mulesoft/requests`
- **Auth**: Protected by `get_current_user`
- **Query Parameters**:
  - `status` (optional): Filter by status
  - `page` (default=1): Pagination page
  - `page_size` (default=25, max=100): Items per page
- **Response**: PaginatedMulesoftResponse with items, total, page, page_size, pages

**Endpoint 2: Get MuleSoft Request by ID**
- **Route**: `GET /api/mulesoft/requests/{request_id}`
- **Auth**: Protected by `get_current_user`
- **Response**: MulesoftRequestResponse or 404 if not found

### 3. Account Creation Hook - `backend/app/crud.py`
Updated `create_account()` function:
- After account creation and commit, automatically creates a `MulesoftRequest` record
- Sets:
  - `account_id` = newly created account ID
  - `request_type` = "create"
  - `status` = "pending"
  - `created_at` and `updated_at` = current datetime
- Commits transaction to persist tracking record

### 4. Router Registration - `backend/app/main.py`
- Imported `mulesoft` module from routes
- Registered router with `app.include_router(mulesoft.router)`

## Database Migration
The new `mulesoft_requests` table is created automatically on application startup via SQLAlchemy's `Base.metadata.create_all()` in the lifespan context manager.

## API Usage Examples

### List all pending MuleSoft requests
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:4799/api/mulesoft/requests?status=pending"
```

### List MuleSoft requests with pagination
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:4799/api/mulesoft/requests?page=1&page_size=10"
```

### Get specific MuleSoft request
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:4799/api/mulesoft/requests/1"
```

## Architecture Benefits
- **Clean Separation**: Integration tracking is separate from account creation logic
- **Audit Trail**: Every account creation automatically generates a tracking record
- **Future-Ready**: Supports async processing, approval workflows, and status updates
- **Secure**: All endpoints protected by authentication
- **Scalable**: Pagination support for large datasets
- **Consistent**: Follows existing project patterns and conventions

## Next Steps (Optional)
- Implement async MuleSoft API calls to update request status
- Add webhook endpoints for MuleSoft callbacks
- Create approval workflow for pending requests
- Add status update endpoints for integration feedback
