# Electricity Load Request Integration

## Overview

This integration handles electricity load enhancement requests from MuleSoft, automatically creating tickets across multiple SAP modules (PM, FI, MM) and initiating approval workflows.

## Architecture

```
MuleSoft → Integration API → Electricity Service → Ticket Creation → Workflow Initiation
                                                 ↓
                                    PM Ticket (Work Order)
                                    FI Ticket (Cost Approval)
                                    MM Ticket (Equipment Procurement)
```

## API Endpoints

### 1. JSON Endpoint

**POST** `/api/integration/mulesoft/load-request`

**Request Body:**
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

**Response:**
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

### 2. XML Endpoint

**POST** `/api/integration/mulesoft/load-request/xml`

**Request Body:**
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

**Response:** Same as JSON endpoint

## Business Logic

### Priority Determination
- **P1 (4 hours)**: Load increase ≥ 20 kW
- **P2 (8 hours)**: Load increase ≥ 10 kW
- **P3 (24 hours)**: Load increase ≥ 5 kW
- **P4 (72 hours)**: Load increase < 5 kW

### Cost Calculation
```
Base Fee: ₹5,000
Per kW Rate: 
  - Residential: ₹2,500/kW
  - Commercial: ₹3,500/kW

Total Cost = Base Fee + (Load Increase × Per kW Rate)
```

### Ticket Creation Rules

#### PM Ticket (Always Created)
- **Module**: Plant Maintenance
- **Type**: Maintenance
- **Purpose**: Field work order for load enhancement
- **Contains**: Customer details, location, load specifications

#### FI Ticket (Conditional)
- **Created When**: Estimated cost > ₹10,000
- **Module**: Finance
- **Type**: Finance Approval
- **Purpose**: Cost approval before proceeding

#### MM Ticket (Conditional)
- **Created When**: Requested load > 15 kW
- **Module**: Materials Management
- **Type**: Procurement
- **Purpose**: Equipment procurement (meters, cables, breakers)

## Workflow

1. **Request Received** → MuleSoft sends load request
2. **Validation** → System validates request data
3. **Cost Estimation** → Calculate estimated cost
4. **Ticket Creation** → Create PM, FI, MM tickets as needed
5. **Event Logging** → Log integration event
6. **Response** → Return ticket IDs and next steps

## Testing

### Using cURL (JSON)
```bash
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-10021",
    "CustomerID": "CUST-88991",
    "CurrentLoad": 5,
    "RequestedLoad": 10,
    "ConnectionType": "RESIDENTIAL",
    "City": "Hyderabad",
    "PinCode": "500081"
  }'
```

### Using cURL (XML)
```bash
curl -X POST http://localhost:8000/api/integration/mulesoft/load-request/xml \
  -H "Content-Type: application/xml" \
  -d '<ElectricityLoadRequest>
    <RequestID>SF-REQ-10021</RequestID>
    <CustomerID>CUST-88991</CustomerID>
    <CurrentLoad>5</CurrentLoad>
    <RequestedLoad>10</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>Hyderabad</City>
    <PinCode>500081</PinCode>
</ElectricityLoadRequest>'
```

### Using Python Test Script
```bash
cd backend
python tests/test_electricity_integration.py
```

## Integration with Existing Modules

### PM Module
- Work orders visible in `/api/v1/pm/tickets`
- Can be assigned to field technicians
- Tracks site visit and installation

### FI Module
- Approval requests in `/api/v1/fi/tickets`
- Cost tracking and invoice generation
- Payment processing

### MM Module
- Material requisitions in `/api/v1/mm/tickets`
- Inventory checks
- Procurement workflow

## Event Logging

All requests are logged with:
- Event type: `electricity_load_request_received`
- Customer ID
- Load increase amount
- Created ticket IDs
- Estimated cost

View events at: `/api/v1/events`

## Error Handling

- **400 Bad Request**: Invalid XML/JSON format or missing fields
- **500 Internal Server Error**: Database or processing errors

## Files Modified/Created

### New Files
- `backend/services/electricity_service.py` - Core service logic
- `backend/tests/test_electricity_integration.py` - Test script
- `ELECTRICITY_LOAD_INTEGRATION.md` - This documentation

### Modified Files
- `backend/api/routes/integration.py` - Added new endpoints

## Next Steps

1. Start the backend: `docker-compose up backend`
2. Test the endpoints using the test script
3. View created tickets in the frontend
4. Monitor events in Grafana dashboards
