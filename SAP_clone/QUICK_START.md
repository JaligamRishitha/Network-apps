# SAP ERP Demo - Quick Start Guide

## ✅ System is Running!

All services are now up and running successfully.

## Access Points

### Main Application
- **Frontend**: http://localhost:3010
- **Backend API**: http://localhost:8100
- **API Documentation**: http://localhost:8100/docs

### Monitoring & Tools
- **Grafana**: http://localhost:3011 (admin/admin)
- **Prometheus**: http://localhost:9190
- **Kong Gateway**: http://localhost:8180

### Mock Services
- **ITSM Mock**: http://localhost:8182
- **ERP Mock**: http://localhost:8183
- **CRM Mock**: http://localhost:8184
- **Camel Integration**: http://localhost:8181

## Login Credentials

```
Username: admin
Password: admin123
```

## Quick Test

1. **Open Frontend**: http://localhost:3010
2. **Login** with admin/admin123
3. **View Dashboard** - You should see the SAP HANA launchpad with:
   - 4 system status tiles at the top
   - SAP HANA Resources section (3 tiles)
   - SAP HANA Technology Documentation (4 tiles)
   - SAP ERP Modules (3 clickable tiles)

4. **Test Modules**:
   - Click 🔧 **Plant Maintenance** → View equipment and work orders
   - Click 📦 **Materials Management** → View materials and inventory
   - Click 💰 **Financial Accounting** → View approvals and cost centers

## Container Status

Check all containers are running:
```bash
docker ps
```

You should see 10 containers:
- ✅ sap-erp-frontend
- ✅ sap-erp-backend
- ✅ sap-erp-postgres
- ✅ sap-erp-kong
- ✅ sap-erp-camel
- ✅ sap-erp-itsm-mock
- ✅ sap-erp-erp-mock
- ✅ sap-erp-crm-mock
- ✅ sap-erp-prometheus
- ✅ sap-erp-grafana

## Troubleshooting

### Frontend not loading?
```bash
docker logs sap-erp-frontend
```

### Backend errors?
```bash
docker logs sap-erp-backend
```

### Database issues?
```bash
docker logs sap-erp-postgres
```

### Restart everything
```bash
docker-compose restart
```

### Stop everything
```bash
docker-compose down
```

### Start again
```bash
docker-compose up
```

## What's Working

### ✅ Dashboard (SAP HANA Launchpad)
- Full-width layout matching SAP design
- System status tiles with metrics
- Resource and documentation sections
- Clickable module tiles

### ✅ Plant Maintenance (PM)
- Equipment master data
- Work order management
- Create/view equipment
- Create/view work orders
- Status tracking

### ✅ Materials Management (MM)
- Material master data (7 materials)
- Purchase requisitions
- Inventory tracking
- Stock level monitoring
- Search and filter

### ✅ Financial Accounting (FI)
- Approvals inbox (approve/reject workflow)
- Cost center management (5 cost centers)
- General Ledger accounts
- Financial reports section
- Budget tracking

### ✅ Data Consistency
All data is aligned:
- Materials: MAT-001 to MAT-005
- Customers: CUST-001 to CUST-003
- Sales Orders: SO-2024-00001, SO-2024-00002
- Equipment: AST-001 to AST-005
- Cost Centers: CC-001 to CC-005

## API Testing

### Test Backend Health
```bash
curl http://localhost:8100/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "sap-erp-backend",
  "version": "1.0.0"
}
```

### Test Authentication
```bash
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Test Data Endpoints
```bash
# Get customers
curl http://localhost:8100/api/customers

# Get materials
curl http://localhost:8100/api/v1/mm/materials

# Get sales orders
curl http://localhost:8100/api/sales/orders

# Get inventory
curl http://localhost:8100/api/inventory/stock
```

## Development Workflow

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart a Service
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all
docker-compose build
docker-compose up
```

## Database Access

### Connect to PostgreSQL
```bash
docker exec -it sap-erp-postgres psql -U sapuser -d saperp
```

### View Tables
```sql
-- List all schemas
\dn

-- List tables in PM schema
\dt pm.*

-- List tables in MM schema
\dt mm.*

-- List tables in FI schema
\dt fi.*

-- Query data
SELECT * FROM pm.assets;
SELECT * FROM mm.materials;
SELECT * FROM fi.cost_centers;
```

### Run Migrations
```bash
docker exec sap-erp-backend alembic upgrade head
```

## Performance Monitoring

### Grafana Dashboards
1. Open http://localhost:3011
2. Login: admin/admin
3. View pre-configured dashboards
4. Monitor system metrics

### Prometheus Metrics
1. Open http://localhost:9190
2. Query metrics
3. View targets

## Next Steps

1. ✅ **Explore the Dashboard** - Navigate through all tiles
2. ✅ **Test CRUD Operations** - Create equipment, materials, cost centers
3. ✅ **Test Approval Workflow** - Approve/reject FI requests
4. ✅ **View API Documentation** - http://localhost:8100/docs
5. ✅ **Monitor Performance** - Check Grafana dashboards

## Support

### Common Issues

**Port already in use?**
```bash
# Check what's using the port
netstat -ano | findstr :3010
netstat -ano | findstr :8100

# Kill the process or change ports in docker-compose.yml
```

**Out of memory?**
```bash
# Increase Docker memory in Docker Desktop settings
# Recommended: 4GB minimum
```

**Slow performance?**
```bash
# Clean up Docker
docker system prune -a

# Restart Docker Desktop
```

## Status: ✅ READY

Your SAP ERP Demo application is fully operational!

**Start exploring at:** http://localhost:3010
