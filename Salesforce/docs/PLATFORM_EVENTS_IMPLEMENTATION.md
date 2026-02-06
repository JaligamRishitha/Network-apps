# Salesforce Platform Event Processing Implementation

## Overview

This implementation provides a comprehensive system for analyzing, validating, normalizing, and storing Salesforce Platform Events related to CRM activities (Cases, Customers, Contacts, Billing, Complaints, SLA events).

## Architecture

### Canonical CRM Event Model

The system normalizes all incoming Salesforce Platform Events into a canonical structure:

```
CanonicalCRMEvent
├── eventMetadata     # Core event information
├── customer         # Customer/Account details
├── crmContext       # Case and CRM-specific context
├── businessContext  # Business and operational context
└── status          # Processing status and lifecycle
```

### Database Schema

The system uses 5 main tables to store normalized event data:

1. **crm_event_metadata** - Core event metadata and audit trail
2. **crm_customer** - Customer information extracted from events
3. **crm_case_context** - Case-related context and SLA information
4. **crm_business_context** - Business context and custom fields
5. **crm_event_status** - Event processing status and lifecycle tracking

Additional tables:
- **crm_event_processing_log** - Detailed processing logs for audit
- **crm_event_validation_rules** - Configurable validation rules

## Key Features

### 1. Event Validation

The system validates incoming events against business rules:

- **Required Fields**: Event_UUID__c, Event_Type__c, Event_Timestamp__c, Severity__c
- **Event Type Validation**: Must be a valid CRM event type
- **Source System**: Must be "Salesforce"
- **Case Events**: Case_Id__c is mandatory for case-related events
- **P1 Priority**: P1 cases must include SLA details
- **Duplicate Prevention**: Rejects duplicate events using event_id

### 2. Event Types Supported

```python
CUSTOMER_CREATED, CUSTOMER_UPDATED, CUSTOMER_BILLING_ADJUSTMENT
CASE_CREATED, CASE_UPDATED, CASE_ESCALATED, CASE_CLOSED
CONTACT_CREATED, CONTACT_UPDATED
BILLING_DISPUTE, BILLING_PAYMENT_RECEIVED
COMPLAINT_FILED, COMPLAINT_RESOLVED
SLA_BREACH, SLA_WARNING, SLA_RESTORED
```

### 3. Processing Pipeline

1. **Validation** - Validate required fields and business rules
2. **Normalization** - Convert to canonical CRM event format
3. **Persistence** - Store in database tables with auditability
4. **Status Tracking** - Track event lifecycle and processing status
5. **Error Handling** - Flag inconsistencies and enable retry logic

## API Endpoints

### Core Processing
- `POST /api/platform-events/process` - Process single event
- `POST /api/platform-events/process-batch` - Process multiple events

### Event Management
- `GET /api/platform-events/status/{event_id}` - Get event status
- `GET /api/platform-events/events/{event_id}` - Get event details
- `GET /api/platform-events/events/{event_id}/logs` - Get processing logs
- `POST /api/platform-events/events/{event_id}/retry` - Retry failed event

### Monitoring
- `GET /api/platform-events/events` - List events with filtering
- `GET /api/platform-events/metrics` - Get processing metrics
- `GET /api/platform-events/health` - Health check

## Event Payload Examples

### Customer Billing Adjustment Event
```json
{
  "Event_UUID__c": "uuid-1234-5678",
  "Event_Type__c": "CUSTOMER_BILLING_ADJUSTMENT",
  "Source_System__c": "Salesforce",
  "Event_Timestamp__c": "2025-01-20T10:45:00Z",
  "Correlation_Id__c": "corr-ukpn-000123",
  "Severity__c": "HIGH",
  "Customer_Id__c": "0015g00000UKPN77",
  "Billing_Account__c": "ISU-88901234",
  "Case_Id__c": "5005g00000CRM88",
  "Case_Type__c": "Billing Dispute",
  "Case_Status__c": "Escalated",
  "Priority__c": "P1",
  "SLA_Target_Hours__c": 48,
  "Target_System__c": "SAP_ISU",
  "Operation__c": "CREATE_BILLING_ADJUSTMENT",
  "Integration_Status__c": "IN_PROGRESS",
  "Billing_Amount__c": 1250.75,
  "Currency_Code__c": "USD"
}
```

### Case Escalation Event
```json
{
  "Event_UUID__c": "uuid-case-escalation",
  "Event_Type__c": "CASE_ESCALATED",
  "Source_System__c": "Salesforce",
  "Event_Timestamp__c": "2025-01-20T15:30:00Z",
  "Severity__c": "CRITICAL",
  "Case_Id__c": "5005g00000ESCAL01",
  "Case_Number__c": "CASE-2025-001234",
  "Case_Type__c": "Technical Issue",
  "Case_Status__c": "Escalated",
  "Priority__c": "P1",
  "SLA_Target_Hours__c": 4,
  "Customer_Id__c": "0015g00000CUST001"
}
```

### SLA Breach Event
```json
{
  "Event_UUID__c": "uuid-sla-breach",
  "Event_Type__c": "SLA_BREACH",
  "Source_System__c": "Salesforce",
  "Event_Timestamp__c": "2025-01-20T16:00:00Z",
  "Severity__c": "CRITICAL",
  "Case_Id__c": "5005g00000SLA001",
  "Case_Number__c": "CASE-2025-005678",
  "Priority__c": "P2",
  "SLA_Target_Hours__c": 24,
  "SLA_Due_Date__c": "2025-01-19T16:00:00Z"
}
```

## Field Mapping

### Salesforce → Database Mapping

| Salesforce Field | Database Table | Database Field |
|------------------|----------------|----------------|
| Event_UUID__c | crm_event_metadata | event_id |
| Event_Type__c | crm_event_metadata | event_type |
| Event_Timestamp__c | crm_event_metadata | event_timestamp |
| Severity__c | crm_event_metadata | severity |
| Customer_Id__c | crm_customer | customer_id |
| Account_Id__c | crm_customer | account_id |
| Case_Id__c | crm_case_context | case_id |
| Priority__c | crm_case_context | case_priority |
| SLA_Target_Hours__c | crm_case_context | sla_target_hours |
| Billing_Amount__c | crm_business_context | billing_amount |

## Error Handling

### Validation Errors
- Missing required fields
- Invalid event types
- Invalid source system
- Missing case ID for case events
- Missing SLA for P1 priority cases

### Processing Errors
- Database connection issues
- Data integrity violations
- Unexpected exceptions

### Retry Logic
- Failed events can be retried up to 3 times
- Exponential backoff for retry attempts
- Manual retry capability via API

## Monitoring and Metrics

### Processing Metrics
- Total events processed
- Events by type and status
- Average processing time
- Error rates
- SLA compliance metrics

### Audit Trail
- Complete processing logs
- Status change history
- Error details and stack traces
- Performance metrics

## Testing

Use the provided test script to validate the implementation:

```bash
cd backend
python test_platform_events.py
```

The test script covers:
- Valid event processing
- Validation failures
- Duplicate event handling
- Batch processing
- Status queries
- Metrics collection

## Deployment

### Database Migration
The new tables will be created automatically when the backend starts.

### Backend Updates
1. New models added to `db_models.py`
2. New API routes in `routes/platform_events.py`
3. Core processor in `platform_event_processor.py`
4. Pydantic schemas in `platform_event_schemas.py`

### Configuration
No additional configuration required. The system uses the existing database connection and authentication.

## Integration with Downstream Systems

The system is designed to prepare events for downstream systems without invoking them directly. Integration points include:

- **Target System Tracking**: Events include target_system field
- **Operation Mapping**: Events specify the operation to perform
- **Status Updates**: Integration status tracked per event
- **Retry Capability**: Failed integrations can be retried

## Security Considerations

- All API endpoints use existing authentication
- Event payloads are validated and sanitized
- SQL injection protection via SQLAlchemy ORM
- Audit trail for all processing activities
- Rate limiting can be added for high-volume scenarios

## Performance Considerations

- Database indexes on key fields (event_id, event_type, customer_id, case_id)
- JSON fields for flexible custom data storage
- Batch processing capability for high-volume scenarios
- Asynchronous processing support via FastAPI BackgroundTasks
- Connection pooling via SQLAlchemy

## Future Enhancements

1. **Real-time Notifications**: WebSocket support for real-time event updates
2. **Advanced Analytics**: Event pattern analysis and anomaly detection
3. **Workflow Engine**: Automated actions based on event types
4. **External Integrations**: Direct integration with downstream systems
5. **Event Replay**: Capability to replay events for testing/recovery
6. **Advanced Filtering**: Complex event filtering and routing rules