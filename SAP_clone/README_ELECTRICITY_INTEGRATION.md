# 🔌 Electricity Load Request Integration

Complete MuleSoft integration for processing electricity load enhancement requests in SAP ERP system.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Business Rules](#business-rules)
- [Testing](#testing)
- [Architecture](#architecture)
- [Files](#files)

## 🎯 Overview

When a customer requests to increase their electricity connection load (e.g., from 5kW to 10kW), this integration:

1. ✅ Receives the request from MuleSoft (JSON or XML)
2. ✅ Calculates estimated cost and priority
3. ✅ Creates tickets across SAP modules (PM, FI, MM)
4. ✅ Initiates approval workflows
5. ✅ Returns ticket IDs and next steps

## 🚀 Quick Start

### 1. Start the Backend

```bash
docker-compose up backend
```

### 2. Test the Integration

**Option A: Windows Batch Script**
```bash
test_electricity_api.bat
```

**Option B: Python Script**
```bash
cd backend
python tests/test_electricity_integration.py
```

**Option C: Swagger UI**
- Open: http://localhost:8000/docs
- Navigate to: Integration → POST `/api/integration/mulesoft/load-request`
- Try it out with sample payload

**Option D: Postman**
- Import: `Electricity_Load_API.postman_collection.json`
- Run any request

## 📡 API Endpoints

### JSON Endpoint

**POST** `/api/integration/mulesoft/load-request`

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

### XML Endpoint

**POST** `/api/integration/mulesoft/load-request/xml`

```xml
<ElectricityLoadRequest>
    <RequestID>SF-REQ-10021</RequestID>
    <CustomerID>CUST-88991</CustomerID>
    <CurrentLoad>5</CurrentLoad>
    <RequestedLoad>10</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>Hyderabad</City>
    <PinCode>500081</PinCode>
</ElectricityLoadRequest>
```

### Response

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

## 📊 Business Rules

### Priority Assignment

| Load Increase | Priority | SLA | Use Case |
|--------------|----------|-----|----------|
| ≥ 20 kW | P1 | 4 hours | Critical/Industrial |
| ≥ 10 kW | P2 | 8 hours | Large Commercial |
| ≥ 5 kW | P3 | 24 hours | Small Commercial |
| < 5 kW | P4 | 72 hours | Residential |

### Cost Calculation

```
Base Processing Fee: ₹5,000

Per kW Rates:
- Residential: ₹2,500/kW
- Commercial: ₹3,500/kW

Total Cost = Base Fee + (Load Increase × Rate)
```

**Examples:**
- 5kW increase (Residential): ₹5,000 + (5 × ₹2,500) = ₹17,500
- 20kW increase (Commercial): ₹5,000 + (20 × ₹3,500) = ₹75,000

### Ticket Creation Logic

| Condition | Ticket | Module | Purpose |
|-----------|--------|--------|---------|
| **Always** | Work Order | PM | Field installation |
| Cost > ₹10,000 | Approval | FI | Financial approval |
| Load > 15 kW | Procurement | MM | Equipment purchase |

## 🧪 Testing

### Test Scenarios

#### Scenario 1: Minimal Load (No Approvals)
```bash
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-001",
    "CustomerID": "CUST-001",
    "CurrentLoad": 3,
    "RequestedLoad": 5,
    "ConnectionType": "RESIDENTIAL",
    "City": "Mumbai",
    "PinCode": "400001"
  }'
```
**Expected:** PM ticket only (Cost: ₹10,000)

#### Scenario 2: Medium Load (Financial Approval)
```bash
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-002",
    "CustomerID": "CUST-002",
    "CurrentLoad": 5,
    "RequestedLoad": 10,
    "ConnectionType": "RESIDENTIAL",
    "City": "Delhi",
    "PinCode": "110001"
  }'
```
**Expected:** PM + FI tickets (Cost: ₹17,500)

#### Scenario 3: Large Load (All Approvals)
```bash
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-003",
    "CustomerID": "CUST-003",
    "CurrentLoad": 10,
    "RequestedLoad": 30,
    "ConnectionType": "COMMERCIAL",
    "City": "Bangalore",
    "PinCode": "560001"
  }'
```
**Expected:** PM + FI + MM tickets (Cost: ₹75,000)

### Verify Tickets

```bash
# View PM tickets
curl http://localhost:8000/api/v1/pm/tickets

# View FI tickets
curl http://localhost:8000/api/v1/fi/tickets

# View MM tickets
curl http://localhost:8000/api/v1/mm/tickets
```

## 🏗️ Architecture

```
MuleSoft → Integration API → Electricity Service
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
                PM Ticket       FI Ticket       MM Ticket
              (Work Order)   (Cost Approval)  (Equipment)
```

### Components

1. **Integration API** (`backend/api/routes/integration.py`)
   - Receives JSON/XML requests
   - Validates payload
   - Routes to service

2. **Electricity Service** (`backend/services/electricity_service.py`)
   - Business logic
   - Cost calculation
   - Priority determination
   - Ticket orchestration

3. **Ticket Service** (`backend/services/ticket_service.py`)
   - Creates tickets with proper IDs
   - Manages SLA deadlines
   - Handles state transitions

4. **Event Service** (`backend/services/event_service.py`)
   - Logs integration events
   - Audit trail

## 📁 Files

### Created Files

```
backend/
├── services/
│   └── electricity_service.py          # Core business logic
├── api/routes/
│   └── integration.py                  # Updated with new endpoints
└── tests/
    └── test_electricity_integration.py # Python test script

Documentation/
├── ELECTRICITY_LOAD_INTEGRATION.md     # Technical docs
├── ELECTRICITY_INTEGRATION_SUMMARY.md  # Implementation summary
├── ELECTRICITY_FLOW_DIAGRAM.md         # Visual diagrams
├── QUICK_TEST_ELECTRICITY.md           # Quick start guide
└── README_ELECTRICITY_INTEGRATION.md   # This file

Testing/
├── test_electricity_api.bat            # Windows test script
└── Electricity_Load_API.postman_collection.json  # Postman collection
```

## 🔍 Monitoring

### View Events
```bash
curl http://localhost:8000/api/v1/events?event_type=electricity_load_request_received
```

### Check Logs
```bash
docker-compose logs backend | grep electricity
```

### Grafana Dashboard
- Open: http://localhost:3000
- View: Ticket metrics and integration events

## 🐛 Troubleshooting

### Connection Refused
```bash
# Check if backend is running
docker-compose ps

# View logs
docker-compose logs backend
```

### Database Errors
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Restart backend
docker-compose restart backend
```

### Import Errors
```bash
# Rebuild container
docker-compose up --build backend
```

## 📚 Additional Documentation

- **Technical Details**: See `ELECTRICITY_LOAD_INTEGRATION.md`
- **Flow Diagrams**: See `ELECTRICITY_FLOW_DIAGRAM.md`
- **Quick Testing**: See `QUICK_TEST_ELECTRICITY.md`
- **Implementation Summary**: See `ELECTRICITY_INTEGRATION_SUMMARY.md`

## 🎯 Next Steps

### For Development
- [ ] Add authentication (API keys)
- [ ] Implement rate limiting
- [ ] Add customer validation
- [ ] Create notification system

### For Production
- [ ] Set up monitoring alerts
- [ ] Configure backup/recovery
- [ ] Add load balancing
- [ ] Implement caching

## 💡 Example Use Cases

1. **Residential Upgrade**: Homeowner adds AC, needs 5kW more
2. **Business Expansion**: Shop adds equipment, needs 15kW more
3. **Industrial Setup**: Factory setup, needs 50kW connection
4. **EV Charging**: Installing EV charger, needs 10kW more

## 📞 Support

For questions or issues:
1. Check API docs: http://localhost:8000/docs
2. View logs: `docker-compose logs backend`
3. Test endpoints: Use Postman collection
4. Review tickets: Frontend dashboard

---

**Built with**: FastAPI, SQLAlchemy, PostgreSQL, Docker
**Integration**: MuleSoft, SAP ERP modules (PM, FI, MM)
