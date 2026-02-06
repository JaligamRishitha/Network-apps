# Logging System - Quick Start

## ✅ What's Done

All user actions are now logged to a **single file** with **automatic rotation at 100MB**.

## 📁 Log File Location

```
/Users/stalin_j/salesforce/backend/logs/app.log
```

## 🚀 Start Using It

### 1. Start the backend server
```bash
cd /Users/stalin_j/salesforce/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Start the frontend
```bash
cd /Users/stalin_j/salesforce/frontend
npm run dev
```

### 3. View logs in real-time
```bash
tail -f /Users/stalin_j/salesforce/backend/logs/app.log
```

## 📊 What Gets Logged

| Action | Example Log |
|--------|-------------|
| **Login** | `[2026-01-20 17:44:06] INFO \| ACTION: LOGIN_SUCCESS \| USER: admin \| DETAILS: User admin logged in \| STATUS: success` |
| **Create Lead** | `[2026-01-20 17:44:20] INFO \| ACTION: CREATE_LEAD \| USER: admin \| DETAILS: Lead created: John Doe (john@example.com) \| STATUS: success` |
| **Update Lead** | `[2026-01-20 17:44:25] INFO \| ACTION: UPDATE_LEAD \| USER: admin \| DETAILS: Lead 5 updated \| STATUS: success` |
| **Delete Lead** | `[2026-01-20 17:44:28] INFO \| ACTION: DELETE_LEAD \| USER: admin \| DETAILS: Lead 5 deleted \| STATUS: success` |
| **Search** | `[2026-01-20 17:44:30] INFO \| ACTION: SEARCH \| USER: admin \| DETAILS: Search: john \| Type: global \| STATUS: success` |
| **Logout** | `[2026-01-20 17:44:35] INFO \| ACTION: LOGOUT \| USER: admin \| DETAILS: User admin logged out \| STATUS: success` |
| **API Request** | `[2026-01-20 17:44:06] INFO \| ACTION: API_REQUEST \| USER: admin \| DETAILS: POST /api/leads \| STATUS: pending` |
| **API Response** | `[2026-01-20 17:44:07] INFO \| ACTION: API_RESPONSE \| USER: admin \| DETAILS: POST /api/leads \| Status: 201 \| Time: 0.45s \| STATUS: success` |
| **Error** | `[2026-01-20 17:44:10] ERROR \| ACTION: LOGIN_FAILED \| USER: testuser \| DETAILS: Invalid credentials \| STATUS: error` |

## 🔍 Search Logs

```bash
# View all login attempts
grep "LOGIN" /Users/stalin_j/salesforce/backend/logs/app.log

# View all errors
grep "ERROR" /Users/stalin_j/salesforce/backend/logs/app.log

# View all actions by a user
grep "USER: admin" /Users/stalin_j/salesforce/backend/logs/app.log

# View all CREATE operations
grep "CREATE_" /Users/stalin_j/salesforce/backend/logs/app.log

# Count actions by type
grep -o "ACTION: [A-Z_]*" /Users/stalin_j/salesforce/backend/logs/app.log | sort | uniq -c
```

## 📈 Log Rotation

- **Max file size:** 100MB
- **Backup files:** 5 (app.log.1 through app.log.5)
- **Total storage:** ~600MB max
- **Automatic:** No manual intervention needed

## 🔧 Files Modified/Created

### Backend
- ✅ `backend/app/logger.py` - Logger configuration
- ✅ `backend/app/main.py` - API middleware logging
- ✅ `backend/app/routes/auth.py` - Authentication logging
- ✅ `backend/app/routes/leads.py` - CRUD logging (example)
- ✅ `backend/app/routes/logs.py` - Logging endpoints

### Frontend
- ✅ `frontend/src/services/logger.js` - Logger service
- ✅ `frontend/src/components/TopBar.jsx` - Click logging (example)

## 💡 Usage Examples

### Backend - Log an action
```python
from app.logger import log_action

log_action(
    action_type="CREATE_ACCOUNT",
    user="admin",
    details="Account 'Acme Corp' created",
    status="success"
)
```

### Frontend - Log a click
```javascript
import { loggerService } from '../services/logger';

loggerService.logClick('create-button', 'Clicked create new lead');
loggerService.logSearch('john', 'global');
loggerService.logAction('LOGOUT', 'User logged out');
```

## ✨ Features

✅ Single log file  
✅ Automatic rotation at 100MB  
✅ All API requests logged  
✅ All CRUD operations logged  
✅ Authentication events logged  
✅ Frontend clicks logged  
✅ Errors logged  
✅ User tracking  
✅ Timestamp on every entry  
✅ Easy to search and filter  

## 🎯 Next Steps

1. **Test it:** Perform actions in the app and check logs
2. **Extend it:** Add logging to other routes/components
3. **Monitor it:** Set up log monitoring/alerts
4. **Archive it:** Implement log archival strategy

---

**Log file:** `/Users/stalin_j/salesforce/backend/logs/app.log`

**View logs:** `tail -f /Users/stalin_j/salesforce/backend/logs/app.log`
