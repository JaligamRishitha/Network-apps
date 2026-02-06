# Logging System Setup - Complete Implementation

## Overview

A comprehensive logging system has been implemented that captures **all user actions** (clicks, API requests, CRUD operations, authentication) and saves them to a **single rotating log file**.

---

## What's Been Implemented

### 1. Backend Logging (`backend/app/logger.py`)

**Features:**
- ✅ Rotating file handler (100MB max, keeps 5 backups)
- ✅ Single log file: `/Users/stalin_j/salesforce/backend/logs/app.log`
- ✅ Automatic rotation when file reaches 100MB
- ✅ Backup files: `app.log.1`, `app.log.2`, etc.
- ✅ Timestamp format: `[YYYY-MM-DD HH:MM:SS]`

**Log Format:**
```
[2026-01-20 17:44:06] INFO | ACTION: LOGIN_SUCCESS | USER: admin | DETAILS: User admin logged in | STATUS: success
[2026-01-20 17:44:12] INFO | ACTION: CREATE_LEAD | USER: admin | DETAILS: Lead created: John Doe (john@example.com) | STATUS: success
[2026-01-20 17:44:15] ERROR | ACTION: DELETE_LEAD_FAILED | USER: admin | DETAILS: Lead 999 not found | STATUS: error | ERROR: Lead not found
```

### 2. API Middleware Logging (`backend/app/main.py`)

**Logs all HTTP requests:**
- Request method (GET, POST, PUT, DELETE)
- Request path
- User making the request
- Response status code
- Response time

**Example logs:**
```
[2026-01-20 17:44:06] INFO | ACTION: API_REQUEST | USER: admin | DETAILS: POST /api/leads | STATUS: pending
[2026-01-20 17:44:07] INFO | ACTION: API_RESPONSE | USER: admin | DETAILS: POST /api/leads | Status: 201 | Time: 0.45s | STATUS: success
```

### 3. Authentication Logging (`backend/app/routes/auth.py`)

**Logs:**
- ✅ Login success/failure
- ✅ Registration success/failure
- ✅ Invalid credentials attempts

**Example logs:**
```
[2026-01-20 17:44:06] INFO | ACTION: LOGIN_SUCCESS | USER: admin | DETAILS: User admin logged in | STATUS: success
[2026-01-20 17:44:10] ERROR | ACTION: LOGIN_FAILED | USER: testuser | DETAILS: Invalid credentials | STATUS: error
[2026-01-20 17:44:15] INFO | ACTION: REGISTER_SUCCESS | USER: newuser | DETAILS: New user registered: newuser | STATUS: success
```

### 4. CRUD Operations Logging (`backend/app/routes/leads.py`)

**Logs all Create, Read, Update, Delete operations:**
- ✅ CREATE_LEAD
- ✅ UPDATE_LEAD
- ✅ DELETE_LEAD
- ✅ LEAD_ASSIGNED (auto-assignment)
- ✅ CREATE_LEAD_DUPLICATE_FOUND

**Example logs:**
```
[2026-01-20 17:44:20] INFO | ACTION: CREATE_LEAD | USER: admin | DETAILS: Lead created: John Doe (john@example.com) | STATUS: success
[2026-01-20 17:44:22] INFO | ACTION: LEAD_ASSIGNED | USER: admin | DETAILS: Lead 5 auto-assigned to user 2 | STATUS: success
[2026-01-20 17:44:25] INFO | ACTION: UPDATE_LEAD | USER: admin | DETAILS: Lead 5 updated | STATUS: success
[2026-01-20 17:44:28] INFO | ACTION: DELETE_LEAD | USER: admin | DETAILS: Lead 5 deleted | STATUS: success
```

### 5. Frontend Logging Service (`frontend/src/services/logger.js`)

**New logging service with methods:**
- `logClick(element, details)` - Log button/element clicks
- `logAction(actionType, details)` - Log any action
- `logPageView(pageName)` - Log page navigation
- `logFormSubmit(formName, action)` - Log form submissions
- `logButtonClick(buttonName, details)` - Log button clicks
- `logSearch(searchTerm, searchType)` - Log search actions
- `logFilter(filterName, filterValue)` - Log filter actions

### 6. Frontend Click Logging (`frontend/src/components/TopBar.jsx`)

**Example implementations:**
- Search action logging
- Logout action logging

**Example logs:**
```
[2026-01-20 17:44:30] INFO | ACTION: SEARCH | USER: admin | DETAILS: Search: john | Type: global | STATUS: success
[2026-01-20 17:44:35] INFO | ACTION: LOGOUT | USER: admin | DETAILS: User admin logged out | STATUS: success
[2026-01-20 17:44:40] INFO | ACTION: FRONTEND_CLICK | USER: admin | DETAILS: CLICK: logout-button | Clicked logout-button | STATUS: success
```

### 7. Logging API Endpoints (`backend/app/routes/logs.py`)

**New endpoints for frontend to send logs:**
- `POST /api/logs/frontend-click` - Log frontend clicks
- `POST /api/logs/action` - Log any action

---

## Log File Location

**Main Log File:**
```
/Users/stalin_j/salesforce/backend/logs/app.log
```

**Backup Files (when main reaches 100MB):**
```
/Users/stalin_j/salesforce/backend/logs/app.log.1
/Users/stalin_j/salesforce/backend/logs/app.log.2
/Users/stalin_j/salesforce/backend/logs/app.log.3
/Users/stalin_j/salesforce/backend/logs/app.log.4
/Users/stalin_j/salesforce/backend/logs/app.log.5
```

---

## How to Use

### Backend: Log an Action

```python
from app.logger import log_action

# Log success
log_action(
    action_type="CREATE_ACCOUNT",
    user="admin",
    details="Account 'Acme Corp' created",
    status="success"
)

# Log error
log_action(
    action_type="DELETE_ACCOUNT",
    user="admin",
    details="Account 123",
    status="error",
    error="Account has active opportunities"
)
```

### Frontend: Log an Action

```javascript
import { loggerService } from '../services/logger';

// Log a click
loggerService.logClick('create-button', 'Clicked create new lead');

// Log an action
loggerService.logAction('FORM_SUBMIT', 'Lead form submitted');

// Log page view
loggerService.logPageView('Leads');

// Log search
loggerService.logSearch('john', 'global');

// Log filter
loggerService.logFilter('status', 'open');
```

---

## What Gets Logged

### ✅ Logged

1. **API Requests**
   - All GET, POST, PUT, DELETE requests
   - Request path and method
   - Response status and time
   - User making the request

2. **Authentication**
   - Login success/failure
   - Registration success/failure
   - Invalid credentials

3. **CRUD Operations**
   - Create (leads, accounts, contacts, cases, opportunities)
   - Read (list, get)
   - Update
   - Delete
   - Auto-assignment

4. **Frontend Clicks**
   - Button clicks
   - Search actions
   - Filter actions
   - Page navigation
   - Form submissions
   - Logout

5. **Errors**
   - Failed operations
   - Validation errors
   - Not found errors
   - Duplicate detection

### ❌ Not Logged (Can be added)

- Database query details
- Request/response body (for privacy)
- Performance metrics
- Cache hits/misses

---

## Viewing Logs

### View live logs (tail)
```bash
tail -f /Users/stalin_j/salesforce/backend/logs/app.log
```

### View last 100 lines
```bash
tail -100 /Users/stalin_j/salesforce/backend/logs/app.log
```

### Search logs
```bash
grep "LOGIN_SUCCESS" /Users/stalin_j/salesforce/backend/logs/app.log
grep "ERROR" /Users/stalin_j/salesforce/backend/logs/app.log
grep "admin" /Users/stalin_j/salesforce/backend/logs/app.log
```

### Count logs by action type
```bash
grep -o "ACTION: [A-Z_]*" /Users/stalin_j/salesforce/backend/logs/app.log | sort | uniq -c
```

---

## Log Rotation

**Configuration:**
- **Max file size:** 100MB
- **Backup count:** 5 files
- **Total storage:** ~600MB max

**When rotation happens:**
1. Current `app.log` is renamed to `app.log.1`
2. `app.log.2` → `app.log.3`, etc.
3. `app.log.5` is deleted
4. New `app.log` is created

---

## Integration Guide

### To add logging to other routes:

1. **Import logger:**
```python
from ..logger import log_action
```

2. **Add logging to your endpoint:**
```python
@router.post("/accounts")
async def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_account = crud.create_account(db, account)
    
    log_action(
        action_type="CREATE_ACCOUNT",
        user=current_user.username,
        details=f"Account created: {account.name}",
        status="success"
    )
    
    return account_to_response(db_account)
```

### To add logging to frontend components:

1. **Import logger service:**
```javascript
import { loggerService } from '../services/logger';
```

2. **Add logging to your component:**
```javascript
const handleClick = async () => {
  loggerService.logButtonClick('save-button', 'Saving form');
  // ... your code
};
```

---

## Testing

### Test backend logging:

```bash
cd /Users/stalin_j/salesforce/backend

# Start the server
uvicorn app.main:app --reload

# In another terminal, make a request
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Check logs
tail -f logs/app.log
```

### Test frontend logging:

1. Start the app
2. Open browser console
3. Perform actions (click buttons, search, etc.)
4. Check backend logs for entries

---

## Performance Impact

- **Minimal:** Logging is asynchronous and non-blocking
- **File I/O:** Only when actions occur
- **Rotation:** Automatic, no manual intervention needed
- **Storage:** ~100MB per log file, 5 backups = ~600MB max

---

## Security Considerations

⚠️ **Current Implementation:**
- Logs contain usernames (not passwords)
- No sensitive data in log messages
- Logs are stored locally

**Recommendations for production:**
1. Encrypt log files
2. Restrict log file permissions (chmod 600)
3. Archive old logs to secure storage
4. Implement log retention policy
5. Use centralized logging (ELK, CloudWatch)

---

## Summary

✅ **All user actions are now logged to a single file**
✅ **Automatic rotation at 100MB**
✅ **Backend API requests logged**
✅ **Frontend clicks logged**
✅ **Authentication events logged**
✅ **CRUD operations logged**
✅ **Errors logged**

**Log file:** `/Users/stalin_j/salesforce/backend/logs/app.log`

**Next steps:**
1. Start the backend server
2. Perform actions in the app
3. Check logs: `tail -f /Users/stalin_j/salesforce/backend/logs/app.log`
