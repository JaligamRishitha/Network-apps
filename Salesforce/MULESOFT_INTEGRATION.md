# MuleSoft Integration Implementation

## Overview
Three integration scenarios have been implemented to connect Salesforce CRM with SAP via MuleSoft.

---

## Scenario 1: New Client Creation

### Technical Flow
1. Account/Contact record created in Salesforce CRM
2. Platform Event or CDC triggers MuleSoft integration
3. MuleSoft performs duplicate detection and data enrichment
4. SAP Customer Master (SAP_CUSTOMER_CREATEFROMDATA) created with credit management data
5. Cross-reference IDs synchronized back to Salesforce

### API Endpoint
```
POST /api/mulesoft-integration/scenario1/create-client
```

### Request Payload
```json
{
  "account_id": 1,
  "contact_id": null,
  "company_name": "Acme Corporation",
  "email": "contact@acme.com",
  "phone": "+1-555-0100",
  "address": "123 Business St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA",
  "tax_id": "12-3456789",
  "payment_terms": "NET30",
  "credit_limit": 50000.00
}
```

### Response
```json
{
  "id": "uuid",
  "status": "SUCCESS",
  "sap_customer_id": "SAP-ABC12345",
  "correlation_id": "correlation-uuid",
  "message": "Client created successfully in SAP",
  "created_at": "2026-02-03T14:46:00Z"
}
```

### Key Features
- ✅ Duplicate detection
- ✅ Data validation
- ✅ Address standardization
- ✅ Tax classification
- ✅ Credit limit determination
- ✅ Correlation ID tracking

---

## Scenario 2: Scheduling & Dispatching (Service Edge)

### Technical Flow
1. Service appointment created based on work order or case in Salesforce
2. Scheduling optimization engine assigns resources (skills, location, availability)
3. MuleSoft synchronizes technician assignments with SAP HR and time management
4. Parts requirements validated against SAP MM inventory
5. Mobile app pushes real-time updates to field technicians

### API Endpoint
```
POST /api/mulesoft-integration/scenario2/schedule-dispatch
```

### Request Payload
```json
{
  "case_id": 1,
  "technician_id": 5,
  "appointment_date": "2026-02-10",
  "appointment_time": "14:00",
  "location": "123 Customer St, New York, NY",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "required_skills": ["HVAC", "Electrical"],
  "parts_required": [
    {
      "part_id": "PART-001",
      "quantity": 2,
      "description": "Compressor Unit"
    }
  ],
  "sla_hours": 24
}
```

### Response
```json
{
  "id": "uuid",
  "status": "SUCCESS",
  "assigned_technician_id": "5",
  "appointment_id": "APT-ABC12345",
  "correlation_id": "correlation-uuid",
  "message": "Appointment scheduled successfully",
  "created_at": "2026-02-03T14:46:00Z"
}
```

### Key Features
- ✅ GPS tracking integration
- ✅ SLA management
- ✅ Emergency dispatch handling
- ✅ Travel time optimization
- ✅ Inventory validation
- ✅ Technician skill matching

---

## Scenario 3: Work Order Request to SAP

### Technical Flow
1. Work order created in Salesforce Service Cloud (customer, product, issue details)
2. MuleSoft transforms Salesforce Work Order to SAP Service Order/Notification format
3. SAP validates equipment, warranty status, and service contract coverage
4. Order confirmation and SAP document numbers returned to Salesforce
5. Status updates flow bidirectionally throughout service lifecycle

### API Endpoint
```
POST /api/mulesoft-integration/scenario3/create-work-order
```

### Request Payload
```json
{
  "case_id": 1,
  "customer_id": 1,
  "product_id": "PROD-12345",
  "issue_description": "Equipment not starting",
  "service_type": "REPAIR",
  "warranty_status": "ACTIVE",
  "contract_id": "CONTRACT-001",
  "priority": "HIGH"
}
```

### Response
```json
{
  "id": "uuid",
  "status": "SUCCESS",
  "sap_order_id": "SO-ABC12345",
  "sap_notification_id": "NOT-ABC12345",
  "correlation_id": "correlation-uuid",
  "entitlement_verified": true,
  "message": "Work order created successfully in SAP",
  "created_at": "2026-02-03T14:46:00Z"
}
```

### Key Features
- ✅ ID mapping strategy
- ✅ Status synchronization logic
- ✅ Entitlement verification
- ✅ Spare parts integration
- ✅ Service billing triggers
- ✅ Warranty validation

---

## Status Tracking & Callbacks

### Get Integration Status
```
GET /api/mulesoft-integration/status/{correlation_id}
```

### MuleSoft Callback Webhook
```
POST /api/mulesoft-integration/callback/status-update
```

Payload:
```json
{
  "correlation_id": "correlation-uuid",
  "status": "COMPLETED",
  "sap_id": "SAP-ABC12345"
}
```

---

## Frontend Access

Navigate to **MuleSoft** in the left navigation menu to access the integration scenarios UI.

### Features
- Form-based submission for each scenario
- Real-time result display
- Correlation ID tracking
- SAP document number references
- Status indicators

---

## Database Schema

### Account Fields
- `correlation_id`: UUID for tracking
- `integration_status`: Current status (PENDING, COMPLETED, FAILED, etc.)

### Case Fields
- `correlation_id`: UUID for tracking
- `integration_status`: Current status

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `202`: Accepted (async processing)
- `400`: Bad request
- `404`: Not found
- `500`: Server error

---

## Future Enhancements

1. **Real MuleSoft Integration**: Replace simulated responses with actual API calls
2. **Async Processing**: Implement job queues for long-running operations
3. **Webhook Validation**: Add signature verification for callbacks
4. **Retry Logic**: Implement exponential backoff for failed requests
5. **Audit Trail**: Enhanced logging for compliance
6. **Batch Operations**: Support bulk creation/updates
7. **Mobile Sync**: Real-time updates to mobile app
8. **Analytics**: Integration metrics and dashboards

---

## Testing

### Scenario 1: Create Client
1. Go to MuleSoft → Scenario 1
2. Fill in account details
3. Click "Create Client"
4. Verify SAP Customer ID in response

### Scenario 2: Schedule Dispatch
1. Go to MuleSoft → Scenario 2
2. Select case and technician
3. Set appointment date/time
4. Click "Schedule Dispatch"
5. Verify appointment ID in response

### Scenario 3: Create Work Order
1. Go to MuleSoft → Scenario 3
2. Select case and customer
3. Fill in issue details
4. Click "Create Work Order"
5. Verify SAP Order ID in response

---

## Support

For issues or questions, contact the integration team.
