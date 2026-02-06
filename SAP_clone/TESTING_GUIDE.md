# SAP ERP Demo - Testing Guide

## Quick Start

### 1. Start the Application

```bash
# Terminal 1 - Start all services
docker-compose up

# Terminal 2 - Start frontend (if not using Docker)
cd frontend
npm install
npm run dev
```

### 2. Access Points
- **Frontend**: http://localhost:3010
- **Backend API**: http://localhost:8100
- **API Documentation**: http://localhost:8100/docs
- **Grafana**: http://localhost:3011 (admin/admin)
- **Prometheus**: http://localhost:9190

## Testing Workflow

### Step 1: Login
1. Navigate to http://localhost:3010
2. You'll be redirected to `/login`
3. Enter credentials:
   - Username: `admin`
   - Password: `admin123`
4. Click "Sign In"
5. You should see the SAP Fiori Dashboard

### Step 2: Dashboard (Fiori Launchpad)
**What to Test:**
- ✅ SAP header with menu, search, notifications, user icon
- ✅ "My Home" title
- ✅ 4 system status tiles showing metrics
- ✅ 3 main module tiles (PM, MM, FI) with icons and counts
- ✅ SAP HANA Resources section (3 tiles)
- ✅ Technology Documentation section (4 tiles)
- ✅ Hover effects on all tiles
- ✅ Click any module tile to navigate

**Expected Behavior:**
- Gradient teal background
- White tiles with shadows
- Smooth hover animations
- Clicking PM/MM/FI navigates to respective modules

### Step 3: Plant Maintenance (PM) Module
**Navigation:** Click 🔧 Plant Maintenance tile from dashboard

**What to Test:**

#### Equipment Tab
1. View equipment list (should show 5 assets)
2. Search for equipment: Type "AST-001" and click Search
3. Click "Details" button on any equipment
4. Create new equipment:
   - Click "🔧 Equipment" button
   - Fill form:
     - Name: "Test Transformer"
     - Type: "Transformer"
     - Location: "Building D"
     - Status: "Operational"
   - Click "Create"
   - Should see success toast
   - New equipment appears in list

#### Work Orders Tab
1. Click "📋 Work Orders" in left navigation
2. View work order statistics (4 cards showing counts)
3. View work order list (should show 4 orders)
4. Create work order:
   - Click "📝 Create Work Order"
   - Fill form:
     - Asset ID: "AST-001"
     - Description: "Test maintenance"
     - Order Type: "Preventive"
     - Priority: "High"
     - Scheduled Date: Select future date
   - Click "Create"
   - Should see success toast

#### Other Tabs
1. Click "📅 Maintenance Schedule" - Should show placeholder
2. Click "📜 History" - Should show placeholder

**Expected Behavior:**
- SAP GUI-style toolbar at top
- Tree navigation on left
- Data tables with proper formatting
- Status badges (green/yellow/red)
- Modal dialogs for creation
- Toast notifications for actions

### Step 4: Materials Management (MM) Module
**Navigation:** Click 📦 Materials Management tile from dashboard

**What to Test:**

#### Material Master Tab
1. View materials list (should show 7 materials)
2. Search by Material Number: Type "MAT-001"
3. Search by Description: Type "Copper"
4. Click Search button
5. Select a material row (should highlight)
6. Click "👁️ Display" button (shows material details)
7. Create new material:
   - Click "📄 Create" button
   - Fill form:
     - Description: "Test Material"
     - Quantity: 100
     - Unit: "PC"
     - Reorder Level: 20
     - Location: "Warehouse A"
   - Click "Create"
   - Should see success toast

#### Purchase Orders Tab
1. Click "Purchase Orders" tab
2. View requisitions list
3. Click "View" on any requisition
4. Should see requisition details dialog

#### Inventory Tab
1. Click "Inventory" tab
2. View 3 statistics cards:
   - Total Stock Value
   - Low Stock Items
   - Out of Stock
3. View inventory movement summary

#### Vendors Tab
1. Click "Vendors" tab
2. Should see placeholder for vendor management

**Expected Behavior:**
- Tabbed interface switches content
- Search works for both fields
- Row selection highlights
- Status indicators show stock levels
- Statistics update dynamically

### Step 5: Financial Accounting (FI) Module
**Navigation:** Click 💰 Financial Accounting tile from dashboard

**What to Test:**

#### Approvals Inbox Tab
1. View pending approvals (should show 2-3 items)
2. Review approval details
3. Approve a request:
   - Click "✓ Approve" button
   - Confirm in dialog
   - Should see success toast
   - Approval disappears from list
4. Reject a request:
   - Click "✗ Reject" button
   - Enter rejection reason
   - Should see success toast

#### Cost Centers Tab
1. Click "Cost Centers" tab
2. View cost centers list (should show 5 centers)
3. View budget summary at bottom (3 statistics)
4. Create cost center:
   - Click "+ Create Cost Center"
   - Fill form:
     - Name: "Test Department"
     - Budget: 50000
     - Fiscal Year: 2025
     - Manager: "Test Manager"
   - Click "Create"
   - Should see success toast

#### General Ledger Tab
1. Click "General Ledger" tab
2. View GL accounts (5 accounts)
3. Note DR/CR indicators
4. Color coding (green for DR, red for CR)
5. Click "View Entries" button

#### Financial Reports Tab
1. Click "Financial Reports" tab
2. View 6 report tiles:
   - Balance Sheet
   - Profit & Loss
   - Cash Flow
   - Trial Balance
   - Budget vs Actual
   - Aging Report
3. Hover over tiles (should highlight)

**Expected Behavior:**
- Approval workflow with confirmations
- Budget calculations update
- GL accounts show proper formatting
- Report tiles are interactive

### Step 6: Home Page (S/4HANA Style)
**Navigation:** Use sidebar to navigate to "Home" or go to `/home`

**What to Test:**
1. View hero banner with:
   - Current date
   - Personalized greeting
   - Action buttons
2. To Dos section:
   - View tasks tab (shows open tickets)
   - Click "Situations" tab
   - Task cards show priority
   - Click "View Details" on a task
3. Pages section:
   - 6 colorful app tiles
   - Hover effects
   - Click tiles (navigation)
4. Apps section:
   - 4 tabs (Favourites, Most Used, etc.)
   - Placeholder message

**Expected Behavior:**
- Modern, clean design
- Gradient hero banner
- Interactive task cards
- Smooth animations

### Step 7: Tickets Page
**Navigation:** Sidebar → Tickets

**What to Test:**
1. View all tickets in worklist
2. Filter by status
3. Filter by module
4. View ticket details
5. Update ticket status

## API Testing

### Using Swagger UI
1. Navigate to http://localhost:8100/docs
2. Test endpoints:
   - POST `/api/v1/auth/login`
   - GET `/api/v1/tickets`
   - GET `/api/v1/pm/assets`
   - GET `/api/v1/mm/materials`
   - GET `/api/v1/fi/approvals`
   - GET `/api/customers`
   - GET `/api/sales/orders`
   - GET `/api/inventory/stock`

### Using curl

```bash
# Login
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get customers
curl http://localhost:8100/api/customers

# Get sales orders
curl http://localhost:8100/api/sales/orders

# Get inventory
curl http://localhost:8100/api/inventory/stock
```

## Data Verification

### Check Database
```bash
# Connect to PostgreSQL
docker exec -it sap-erp-postgres psql -U sapuser -d saperp

# View tables
\dt pm.*
\dt mm.*
\dt fi.*

# Query data
SELECT * FROM pm.assets;
SELECT * FROM mm.materials;
SELECT * FROM fi.cost_centers;
```

### Check Mock Services
```bash
# ITSM Mock
curl http://localhost:8182/health

# ERP Mock
curl http://localhost:8183/health

# CRM Mock
curl http://localhost:8184/health
```

## Common Issues & Solutions

### Issue: Frontend won't start
**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Issue: Backend connection refused
**Solution:**
```bash
docker-compose down
docker-compose up --build
```

### Issue: Login fails
**Solution:**
1. Check backend logs: `docker logs sap-erp-backend`
2. Verify database is running: `docker ps | grep postgres`
3. Run migrations: `docker exec sap-erp-backend alembic upgrade head`

### Issue: No data showing
**Solution:**
```bash
# Run seed data migration
docker exec sap-erp-backend alembic upgrade head
```

### Issue: CORS errors
**Solution:**
- Backend already configured for CORS
- Check VITE_API_URL in frontend/.env
- Should be: `VITE_API_URL=http://localhost:8100/api/v1`

## Performance Testing

### Load Testing
```bash
# Install Apache Bench
apt-get install apache2-utils

# Test login endpoint
ab -n 100 -c 10 -p login.json -T application/json \
  http://localhost:8100/api/v1/auth/login

# Test materials endpoint
ab -n 1000 -c 50 http://localhost:8100/api/v1/mm/materials
```

### Monitoring
1. Open Grafana: http://localhost:3011
2. Login: admin/admin
3. View dashboards:
   - System metrics
   - API response times
   - Error rates

## Test Checklist

### Functionality ✅
- [ ] Login/Logout works
- [ ] Dashboard loads with all tiles
- [ ] PM module CRUD operations
- [ ] MM module CRUD operations
- [ ] FI module approval workflow
- [ ] Navigation between pages
- [ ] Search and filter functions
- [ ] Modal dialogs open/close
- [ ] Toast notifications appear
- [ ] Data persists after refresh

### UI/UX ✅
- [ ] SAP Fiori styling consistent
- [ ] Responsive layout
- [ ] Hover effects work
- [ ] Loading states show
- [ ] Error messages clear
- [ ] Forms validate input
- [ ] Tables sortable
- [ ] Status badges colored correctly

### Data Consistency ✅
- [ ] Materials match between DB and API
- [ ] Customers data consistent
- [ ] Sales orders display correctly
- [ ] Inventory levels accurate
- [ ] Cost centers show budgets
- [ ] Approvals workflow complete

### Integration ✅
- [ ] Frontend calls backend APIs
- [ ] Backend queries database
- [ ] Mock services receive events
- [ ] Prometheus collects metrics
- [ ] Grafana displays data

## Success Criteria

✅ **Application is complete when:**
1. All pages load without errors
2. CRUD operations work in all modules
3. Data is consistent across frontend/backend
4. SAP Fiori styling is applied throughout
5. Navigation flows smoothly
6. API endpoints respond correctly
7. Authentication protects routes
8. Error handling works properly

## Demo Script

**For presentations:**

1. **Start** - Show login page, explain SAP-style authentication
2. **Dashboard** - Highlight Fiori launchpad design, system status
3. **PM Module** - Demo equipment management, work order creation
4. **MM Module** - Show material master, inventory tracking
5. **FI Module** - Demo approval workflow, cost center management
6. **API** - Show Swagger docs, explain integration points
7. **Monitoring** - Show Grafana dashboards, metrics

**Time: 10-15 minutes**

---

## Status: ✅ READY FOR TESTING

All features implemented and ready for comprehensive testing!
