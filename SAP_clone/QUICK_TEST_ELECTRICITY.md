# Quick Test Guide - Electricity Load Integration

## Start the Application

```bash
docker-compose up backend
```

Wait for: `Application startup complete`

## Test Option 1: Using Windows Batch Script

```bash
test_electricity_api.bat
```

## Test Option 2: Using Python Script

```bash
cd backend
python tests/test_electricity_integration.py
```

## Test Option 3: Using Swagger UI

1. Open browser: http://localhost:8000/docs
2. Navigate to **Integration** section
3. Find `POST /api/integration/mulesoft/load-request`
4. Click "Try it out"
5. Use this payload:

```json
{
  "RequestID": "SF-REQ-10021",
  "CustomerID": "CUST-88991",
  "CurrentLoad": 5,
  "RequestedLoad": 10,
  "ConnectionType": "RESIDENTIAL",
  "City": "Hyderabad",
  "PinCode": "500081"
}
```

6. Click "Execute"

## Expected Response

```json
{
  "status": "accepted",
  "request_id": "SF-REQ-10021",
  "customer_id": "CUST-88991",
  "estimated_cost": 17500.0,
  "priority": "P3",
  "tickets_created": {
    "pm_ticket": "TKT-PM-20260120-0001",
    "fi_ticket": "TKT-FI-20260120-0001",
    "mm_ticket": null
  },
  "workflow_status": "initiated",
  "next_steps": [
    "Site survey scheduled",
    "Financial approval pending",
    "No equipment needed"
  ]
}
```

## Verify Tickets Created

### View PM Ticket
```bash
curl http://localhost:8000/api/v1/pm/tickets
```

### View FI Ticket
```bash
curl http://localhost:8000/api/v1/fi/tickets
```

### View MM Ticket
```bash
curl http://localhost:8000/api/v1/mm/tickets
```

## Test Different Scenarios

### Small Load Increase (No FI/MM tickets)
```json
{
  "RequestID": "SF-REQ-10023",
  "CustomerID": "CUST-88993",
  "CurrentLoad": 3,
  "RequestedLoad": 5,
  "ConnectionType": "RESIDENTIAL",
  "City": "Mumbai",
  "PinCode": "400001"
}
```
Expected: Only PM ticket created

### Large Load Increase (All tickets)
```json
{
  "RequestID": "SF-REQ-10024",
  "CustomerID": "CUST-88994",
  "CurrentLoad": 5,
  "RequestedLoad": 30,
  "ConnectionType": "COMMERCIAL",
  "City": "Delhi",
  "PinCode": "110001"
}
```
Expected: PM + FI + MM tickets created

## Troubleshooting

**Connection refused?**
- Ensure backend is running: `docker-compose ps`
- Check logs: `docker-compose logs backend`

**Database errors?**
- Run migrations: `docker-compose exec backend alembic upgrade head`

**Import errors?**
- Restart backend: `docker-compose restart backend`
