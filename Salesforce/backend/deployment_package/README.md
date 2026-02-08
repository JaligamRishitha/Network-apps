# Deployment Package for Scenario 2 & 3

This package contains all the files needed to enable Scenario 2 (Scheduling & Dispatching) and Scenario 3 (Work Orders) on the remote server.

## Files Included

| File | Description |
|------|-------------|
| `01_sql_migration.sql` | SQL script to create new database tables |
| `02_db_models_additions.py` | Python models to add to `db_models.py` |
| `03_service.py` | Complete `service.py` file (replace existing) |

---

## Deployment Steps

### Step 1: Run SQL Migration
Connect to your PostgreSQL database and run:

```bash
psql -h <host> -U <user> -d <database> -f 01_sql_migration.sql
```

Or copy/paste the SQL into your database client.

---

### Step 2: Update db_models.py
Add the contents of `02_db_models_additions.py` to the END of your existing `db_models.py` file.

The file adds these 3 models:
- `ServiceAppointment` - For service appointments (Scenario 2)
- `SchedulingRequest` - For MuleSoft scheduling tracking (Scenario 2)
- `WorkOrder` - For work orders (Scenario 3)

---

### Step 3: Replace service.py
Replace your existing `app/routes/service.py` with `03_service.py`.

This file includes all endpoints for:
- Service Accounts, Quotations, Invoices, SLAs (existing)
- Service Appointments (NEW - Scenario 2)
- Scheduling Requests (NEW - Scenario 2)
- Work Orders (NEW - Scenario 3)

---

### Step 4: Restart the Server
```bash
# If using systemd
sudo systemctl restart your-fastapi-service

# If using Docker
docker restart your-container

# If running directly
kill <pid> && python -m uvicorn app.main:app --host 0.0.0.0 --port 4799
```

---

## New API Endpoints

### Scenario 2: Scheduling & Dispatching

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/service/appointments` | List all appointments |
| POST | `/api/service/appointments` | Create appointment |
| GET | `/api/service/appointments/{id}` | Get appointment |
| GET | `/api/service/scheduling-requests` | List scheduling requests |
| POST | `/api/service/scheduling-requests/{id}/mulesoft-callback` | MuleSoft callback |
| POST | `/api/service/scheduling-requests/{id}/approve` | Manual approval |

### Scenario 3: Work Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/service/work-orders` | List all work orders |
| POST | `/api/service/work-orders` | Create work order |
| GET | `/api/service/work-orders/{id}` | Get work order |
| POST | `/api/service/work-orders/{id}/mulesoft-callback` | MuleSoft callback |
| POST | `/api/service/work-orders/{id}/approve` | Manual approval |
| GET | `/api/service/work-orders/{id}/check-entitlement` | Check entitlement |

---

## Testing After Deployment

### Test Scenario 2
```bash
# Check if appointments endpoint works
curl -s "http://207.180.217.117:4799/api/service/appointments" \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# Check if scheduling-requests endpoint works
curl -s "http://207.180.217.117:4799/api/service/scheduling-requests" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### Test Scenario 3
```bash
# Check if work-orders endpoint works
curl -s "http://207.180.217.117:4799/api/service/work-orders" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

---

## MuleSoft Callback Examples

### Scenario 2: Scheduling Callback
```bash
curl -X POST "http://207.180.217.117:4799/api/service/scheduling-requests/1/mulesoft-callback" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "SUCCESS",
    "assigned_technician_id": 101,
    "technician_name": "John Smith",
    "parts_available": true,
    "mulesoft_transaction_id": "MULE-12345",
    "sap_hr_response": "Technician available",
    "sap_inventory_response": "All parts in stock"
  }'
```

### Scenario 3: Work Order Callback
```bash
curl -X POST "http://207.180.217.117:4799/api/service/work-orders/1/mulesoft-callback" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "SUCCESS",
    "entitlement_verified": true,
    "entitlement_type": "Warranty",
    "sap_order_id": "SAP-ORD-12345",
    "sap_notification_id": "SAP-NOT-12345",
    "mulesoft_transaction_id": "MULE-67890"
  }'
```
