# Button & API Connection Audit

## Executive Summary

**Status**: ⚠️ **PARTIALLY CONNECTED** - UI is complete, but most buttons use mock data instead of real API calls.

**What Works**:
- ✅ Home page loads real tickets from API
- ✅ Authentication system fully functional
- ✅ API service layer complete with all endpoints

**What Needs Connection**:
- ❌ PM, MM, FI pages use mock data
- ❌ Create/Edit/Delete buttons not connected
- ❌ Approval actions not connected
- ❌ Sales Quotation not connected to backend

---

## Page-by-Page Audit

### 1. Home Page (`/`)
**Status**: ✅ **50% CONNECTED**

| Button/Action | API Connected | Database | Notes |
|--------------|---------------|----------|-------|
| Load To-Dos | ✅ YES | ✅ YES | Uses `ticketsApi.list()` |
| Show More | ✅ YES | ✅ YES | Calls `loadTodos()` |
| View Details | ✅ YES | ✅ YES | Navigates to ticket detail |
| Action Button | ❌ NO | ❌ NO | No handler implemented |
| Add Content | ❌ NO | ❌ NO | No handler implemented |
| My Home Settings | ❌ NO | ❌ NO | Navigates to non-existent route |
| App Tiles | ❌ NO | ❌ NO | Navigate to non-existent routes |

**Fix Required**:
```typescript
// Add action handler
const handleTodoAction = async (todoId: string) => {
  try {
    await ticketsApi.updateStatus(todoId, 'in_progress', user.username);
    loadTodos();
  } catch (error) {
    alert('Failed to update ticket');
  }
};
```

---

### 2. Plant Maintenance (`/pm`)
**Status**: ❌ **0% CONNECTED** - All mock data

| Button/Action | API Connected | Database | Notes |
|--------------|---------------|----------|-------|
| Create Work Order | ❌ NO | ❌ NO | Alert only |
| Schedule | ❌ NO | ❌ NO | No handler |
| Equipment | ❌ NO | ❌ NO | No handler |
| Reports | ❌ NO | ❌ NO | No handler |
| Analytics | ❌ NO | ❌ NO | No handler |
| Search Equipment | ❌ NO | ❌ NO | No handler |
| Details Button | ❌ NO | ❌ NO | No handler |
| Create New WO | ❌ NO | ❌ NO | No handler |
| Open Button | ❌ NO | ❌ NO | No handler |

**Equipment Data**: Mock array (5 items)
**Work Orders Data**: Mock array (4 items)

**Fix Required**:
```typescript
// Replace mock data with API calls
useEffect(() => {
  const loadData = async () => {
    try {
      const [equipmentRes, workOrdersRes] = await Promise.all([
        pmApi.listAssets(),
        pmApi.listMaintenanceOrders()
      ]);
      setEquipment(equipmentRes.data.assets || []);
      setWorkOrders(workOrdersRes.data.orders || []);
    } catch (error) {
      console.error('Failed to load PM data:', error);
    }
  };
  loadData();
}, []);

// Add create handler
const handleCreateWorkOrder = async (data) => {
  try {
    await pmApi.createMaintenanceOrder(data);
    loadData();
  } catch (error) {
    alert('Failed to create work order');
  }
};
```

---

### 3. Materials Management (`/mm`)
**Status**: ❌ **0% CONNECTED** - All mock data

| Button/Action | API Connected | Database | Notes |
|--------------|---------------|----------|-------|
| Create | ❌ NO | ❌ NO | No handler |
| Change | ❌ NO | ❌ NO | No handler |
| Display | ❌ NO | ❌ NO | No handler |
| Find | ❌ NO | ❌ NO | No handler |
| Print | ❌ NO | ❌ NO | No handler |
| Report | ❌ NO | ❌ NO | No handler |
| Search | ❌ NO | ❌ NO | No handler |
| View (PO) | ❌ NO | ❌ NO | No handler |

**Materials Data**: Mock array (5 items)
**Purchase Orders Data**: Mock array (3 items)

**Fix Required**:
```typescript
// Load materials from API
useEffect(() => {
  const loadMaterials = async () => {
    try {
      const response = await mmApi.listMaterials();
      setMaterials(response.data.materials || []);
    } catch (error) {
      console.error('Failed to load materials:', error);
    }
  };
  loadMaterials();
}, []);

// Add create handler
const handleCreateMaterial = async (data) => {
  try {
    await mmApi.createMaterial(data);
    loadMaterials();
  } catch (error) {
    alert('Failed to create material');
  }
};
```

---

### 4. Financial Accounting (`/fi`)
**Status**: ❌ **0% CONNECTED** - All mock data

| Button/Action | API Connected | Database | Notes |
|--------------|---------------|----------|-------|
| Post Document | ❌ NO | ❌ NO | No handler |
| Display | ❌ NO | ❌ NO | No handler |
| Change | ❌ NO | ❌ NO | No handler |
| Reports | ❌ NO | ❌ NO | No handler |
| Analysis | ❌ NO | ❌ NO | No handler |
| Print | ❌ NO | ❌ NO | No handler |
| Approve | ❌ NO | ❌ NO | No handler |
| Reject | ❌ NO | ❌ NO | No handler |
| Create Cost Center | ❌ NO | ❌ NO | No handler |
| Search Account | ❌ NO | ❌ NO | No handler |
| View Entries | ❌ NO | ❌ NO | No handler |

**Approvals Data**: Mock array (3 items)
**Cost Centers Data**: Mock array (4 items)
**GL Accounts Data**: Mock array (5 items)

**Fix Required**:
```typescript
// Load approvals from API
useEffect(() => {
  const loadApprovals = async () => {
    try {
      const response = await fiApi.listApprovals({ decision: 'pending' });
      setApprovals(response.data || []);
    } catch (error) {
      console.error('Failed to load approvals:', error);
    }
  };
  loadApprovals();
}, []);

// Add approve handler
const handleApprove = async (approvalId: string) => {
  try {
    await fiApi.approveRequest(approvalId, user.username, 'Approved');
    loadApprovals();
    alert('Request approved successfully');
  } catch (error) {
    alert('Failed to approve request');
  }
};

// Add reject handler
const handleReject = async (approvalId: string) => {
  try {
    await fiApi.rejectRequest(approvalId, user.username, 'Rejected');
    loadApprovals();
    alert('Request rejected');
  } catch (error) {
    alert('Failed to reject request');
  }
};
```

---

### 5. Dashboard (`/dashboard`)
**Status**: ❌ **0% CONNECTED** - All mock data

| Button/Action | API Connected | Database | Notes |
|--------------|---------------|----------|-------|
| N/A | ❌ NO | ❌ NO | Display only, no buttons |

**All Data**: Mock arrays

**Fix Required**:
```typescript
// Load real dashboard data
useEffect(() => {
  const loadDashboardData = async () => {
    try {
      const [ticketsRes, pmRes, mmRes, fiRes] = await Promise.all([
        ticketsApi.list({ limit: 10 }),
        pmApi.listAssets(),
        mmApi.listMaterials(),
        fiApi.listApprovals()
      ]);
      // Update state with real data
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };
  loadDashboardData();
}, []);
```

---

### 6. Sales Quotation (`/quotation/:id`)
**Status**: ❌ **0% CONNECTED** - All mock data

| Button/Action | API Connected | Database | Notes |
|--------------|---------------|----------|-------|
| Edit | ❌ NO | ❌ NO | Sets state only |
| Save | ❌ NO | ❌ NO | Alert only |
| Create Subsequent Order | ❌ NO | ❌ NO | Alert only |
| Update Prices | ❌ NO | ❌ NO | Alert only |
| Reject All Items | ❌ NO | ❌ NO | Alert only |
| Display Change Log | ❌ NO | ❌ NO | Alert only |
| Create Item | ❌ NO | ❌ NO | No handler |
| Delete Item | ❌ NO | ❌ NO | No handler |
| Edit Item | ❌ NO | ❌ NO | No handler |

**All Data**: Mock state

**Fix Required**:
Need to create sales API endpoints first, then:
```typescript
// Load quotation from API
useEffect(() => {
  if (id) {
    const loadQuotation = async () => {
      try {
        const response = await salesApi.getQuotation(id);
        setQuotation(response.data);
      } catch (error) {
        console.error('Failed to load quotation:', error);
      }
    };
    loadQuotation();
  }
}, [id]);

// Add save handler
const handleSave = async () => {
  try {
    await salesApi.updateQuotation(quotation.id, quotation);
    setIsEditing(false);
    alert('Quotation saved successfully!');
  } catch (error) {
    alert('Failed to save quotation');
  }
};
```

---

## API Endpoints Available

### ✅ Working Endpoints

1. **Auth API**
   - `POST /api/v1/auth/login` ✅
   - `POST /api/v1/auth/refresh` ✅

2. **Tickets API**
   - `GET /api/v1/tickets` ✅
   - `POST /api/v1/tickets` ✅
   - `GET /api/v1/tickets/{id}` ✅
   - `PATCH /api/v1/tickets/{id}/status` ✅
   - `GET /api/v1/tickets/{id}/audit` ✅

3. **PM API**
   - `POST /api/v1/pm/assets` ✅
   - `GET /api/v1/pm/assets` ✅
   - `GET /api/v1/pm/assets/{id}` ✅
   - `POST /api/v1/pm/maintenance-orders` ✅
   - `GET /api/v1/pm/maintenance-orders` ✅
   - `POST /api/v1/pm/incidents` ✅

4. **MM API**
   - `POST /api/v1/mm/materials` ✅
   - `GET /api/v1/mm/materials` ✅
   - `GET /api/v1/mm/materials/{id}` ✅
   - `POST /api/v1/mm/stock-transactions` ✅
   - `GET /api/v1/mm/materials/{id}/transactions` ✅
   - `POST /api/v1/mm/purchase-requisitions` ✅
   - `GET /api/v1/mm/purchase-requisitions` ✅

5. **FI API**
   - `POST /api/v1/fi/cost-centers` ✅
   - `GET /api/v1/fi/cost-centers` ✅
   - `GET /api/v1/fi/cost-centers/{id}` ✅
   - `POST /api/v1/fi/cost-entries` ✅
   - `GET /api/v1/fi/cost-entries` ✅
   - `POST /api/v1/fi/approval-requests` ✅
   - `GET /api/v1/fi/approval-requests` ✅
   - `POST /api/v1/fi/approval-requests/{id}/approve` ✅
   - `POST /api/v1/fi/approval-requests/{id}/reject` ✅

### ❌ Missing Endpoints

1. **Sales API** - Not implemented
   - Need: `GET /api/v1/sales/quotations`
   - Need: `POST /api/v1/sales/quotations`
   - Need: `GET /api/v1/sales/quotations/{id}`
   - Need: `PUT /api/v1/sales/quotations/{id}`

---

## Priority Fix List

### 🔴 HIGH PRIORITY (Do First)

1. **Connect FI Approve/Reject Buttons** (30 min)
   - File: `frontend/src/pages/FI.tsx`
   - Add handlers for approve/reject
   - Connect to `fiApi.approveRequest()` and `fiApi.rejectRequest()`

2. **Connect PM Equipment List** (30 min)
   - File: `frontend/src/pages/PM.tsx`
   - Replace mock data with `pmApi.listAssets()`
   - Add loading state

3. **Connect MM Materials List** (30 min)
   - File: `frontend/src/pages/MM.tsx`
   - Replace mock data with `mmApi.listMaterials()`
   - Add loading state

### 🟡 MEDIUM PRIORITY

4. **Add Create Equipment Modal** (1 hour)
   - Create modal component
   - Connect to `pmApi.createAsset()`

5. **Add Create Material Modal** (1 hour)
   - Create modal component
   - Connect to `mmApi.createMaterial()`

6. **Connect Dashboard Data** (1 hour)
   - Load real data from all modules
   - Update KPI calculations

### 🟢 LOW PRIORITY

7. **Implement Sales Quotation Backend** (2-3 hours)
   - Create sales API routes
   - Create sales models
   - Connect frontend

8. **Add Search Functionality** (1-2 hours)
   - Implement search in PM, MM, FI
   - Add filters

---

## Quick Fix Script

Here's what to do RIGHT NOW to connect the most important buttons:

### Step 1: Fix FI Approvals (Copy this code)

```typescript
// In frontend/src/pages/FI.tsx

import { useAuth } from '../contexts/AuthContext';
import { fiApi } from '../services/api';

// Add at top of component
const { user } = useAuth();
const [approvals, setApprovals] = useState([]);
const [loading, setLoading] = useState(true);

// Add useEffect
useEffect(() => {
  loadApprovals();
}, []);

const loadApprovals = async () => {
  try {
    const response = await fiApi.listApprovals({ decision: 'pending' });
    setApprovals(response.data || []);
  } catch (error) {
    console.error('Failed to load approvals:', error);
  } finally {
    setLoading(false);
  }
};

// Replace approve button onClick
const handleApprove = async (approvalId: string) => {
  try {
    await fiApi.approveRequest(approvalId, user?.username || 'system', 'Approved');
    await loadApprovals();
    alert('Request approved successfully!');
  } catch (error) {
    alert('Failed to approve request');
  }
};

// Replace reject button onClick
const handleReject = async (approvalId: string) => {
  try {
    await fiApi.rejectRequest(approvalId, user?.username || 'system', 'Rejected');
    await loadApprovals();
    alert('Request rejected');
  } catch (error) {
    alert('Failed to reject request');
  }
};
```

### Step 2: Fix PM Equipment List

```typescript
// In frontend/src/pages/PM.tsx

import { pmApi } from '../services/api';

// Replace mock data with:
const [equipment, setEquipment] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  loadEquipment();
}, []);

const loadEquipment = async () => {
  try {
    const response = await pmApi.listAssets();
    setEquipment(response.data.assets || []);
  } catch (error) {
    console.error('Failed to load equipment:', error);
  } finally {
    setLoading(false);
  }
};
```

### Step 3: Fix MM Materials List

```typescript
// In frontend/src/pages/MM.tsx

import { mmApi } from '../services/api';

// Replace mock data with:
const [materials, setMaterials] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  loadMaterials();
}, []);

const loadMaterials = async () => {
  try {
    const response = await mmApi.listMaterials();
    setMaterials(response.data.materials || []);
  } catch (error) {
    console.error('Failed to load materials:', error);
  } finally {
    setLoading(false);
  }
};
```

---

## Summary

**Current State**:
- 🎨 UI: 100% Complete
- 🔌 API Layer: 100% Complete
- 🔗 Connections: 10% Complete
- 💾 Database: Ready

**To Make Fully Functional**:
1. Connect 3 main pages (PM, MM, FI) to APIs - **2 hours**
2. Add create/edit modals - **3 hours**
3. Implement sales quotation backend - **3 hours**
4. Add search and filters - **2 hours**

**Total Time to Full Functionality**: ~10 hours of focused work

**Next Step**: Start with the Quick Fix Script above to connect the most critical buttons in 1-2 hours.
