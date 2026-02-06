# MuleSoft XML API Specification for SAP ERP Integration

This document describes all XML formats that the SAP ERP application expects from MuleSoft for various request types.

## Table of Contents
1. [Electricity Load Enhancement Request](#1-electricity-load-enhancement-request)
2. [General Ticket Creation](#2-general-ticket-creation)
3. [Material Requisition Request](#3-material-requisition-request)
4. [Financial Approval Request](#4-financial-approval-request)
5. [Maintenance Work Order Request](#5-maintenance-work-order-request)

---

## 1. Electricity Load Enhancement Request

### Endpoint
```
POST http://localhost:2004/api/integration/mulesoft/load-request/xml
```

### XML Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ElectricityLoadRequest>
    <RequestID>SF-REQ-10021</RequestID>
    <CustomerID>CUST-88991</CustomerID>
    <CurrentLoad>5.0</CurrentLoad>
    <RequestedLoad>10.0</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>Hyderabad</City>
    <PinCode>500081</PinCode>
</ElectricityLoadRequest>
```

### Field Descriptions
| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| RequestID | String | Yes | Unique request identifier from MuleSoft | Any string (e.g., SF-REQ-10021) |
| CustomerID | String | Yes | Customer identifier | Any string (e.g., CUST-88991) |
| CurrentLoad | Decimal | Yes | Current electricity load in kW | Positive number |
| RequestedLoad | Decimal | Yes | Requested electricity load in kW | Positive number > CurrentLoad |
| ConnectionType | String | Yes | Type of connection | RESIDENTIAL, COMMERCIAL |
| City | String | Yes | Customer city | Any string |
| PinCode | String | Yes | Postal/ZIP code | Any string |

### Response Format
```json
{
  "status": "accepted",
  "request_id": "SF-REQ-10021",
  "customer_id": "CUST-88991",
  "estimated_cost": 22500.00,
  "priority": "P3",
  "tickets_created": {
    "pm_ticket": "TKT-PM-20260121-0001",
    "fi_ticket": "TKT-FI-20260121-0001",
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

### Example cURL Command
```bash
curl -X POST http://localhost:2004/api/integration/mulesoft/load-request/xml \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<ElectricityLoadRequest>
    <RequestID>SF-REQ-10021</RequestID>
    <CustomerID>CUST-88991</CustomerID>
    <CurrentLoad>5.0</CurrentLoad>
    <RequestedLoad>10.0</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>Hyderabad</City>
    <PinCode>500081</PinCode>
</ElectricityLoadRequest>'
```

---

## 2. General Ticket Creation

### Endpoint
```
POST http://localhost:2004/api/v1/tickets
```

### XML Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TicketRequest>
    <Module>PM</Module>
    <TicketType>Maintenance</TicketType>
    <Priority>P2</Priority>
    <Title>Equipment Maintenance Required</Title>
    <Description>Transformer T-101 requires scheduled maintenance</Description>
    <CreatedBy>mulesoft_integration</CreatedBy>
    <CorrelationID>EXT-REQ-12345</CorrelationID>
</TicketRequest>
```

### Field Descriptions
| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| Module | String | Yes | Target module | PM, MM, FI |
| TicketType | String | Yes | Type of ticket | Incident, Maintenance, Procurement, Finance_Approval |
| Priority | String | Yes | Priority level | P1 (4h), P2 (8h), P3 (24h), P4 (72h) |
| Title | String | Yes | Ticket title | Any string (max 255 chars) |
| Description | String | No | Detailed description | Any string |
| CreatedBy | String | Yes | Creator identifier | Any string |
| CorrelationID | String | No | External reference ID | Any string |

### Response Format
```json
{
  "ticket_id": "TKT-PM-20260121-0001",
  "status": "Open",
  "sla_deadline": "2026-01-21T17:00:00Z",
  "created_at": "2026-01-21T09:00:00Z"
}
```

---

## 3. Material Requisition Request

### Endpoint
```
POST http://localhost:2004/api/integration/mulesoft/material-request/xml
```

### XML Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<MaterialRequisitionRequest>
    <RequestID>MAT-REQ-5001</RequestID>
    <MaterialID>MAT-001</MaterialID>
    <MaterialDescription>High Voltage Cable 11kV</MaterialDescription>
    <Quantity>100</Quantity>
    <UnitOfMeasure>M</UnitOfMeasure>
    <RequiredBy>2026-01-25</RequiredBy>
    <Justification>Load enhancement project requirement</Justification>
    <RequestedBy>field_engineer</RequestedBy>
    <CostCenter>CC-1001</CostCenter>
    <Priority>High</Priority>
</MaterialRequisitionRequest>
```

### Field Descriptions
| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| RequestID | String | Yes | Unique requisition ID | Any string |
| MaterialID | String | No | Material code if known | Any string |
| MaterialDescription | String | Yes | Description of material | Any string |
| Quantity | Integer | Yes | Quantity required | Positive integer |
| UnitOfMeasure | String | Yes | Unit of measurement | KG, L, PC, M, TON |
| RequiredBy | Date | Yes | Required delivery date | YYYY-MM-DD |
| Justification | String | Yes | Reason for requisition | Any string |
| RequestedBy | String | Yes | Requester identifier | Any string |
| CostCenter | String | No | Cost center code | Any string |
| Priority | String | Yes | Priority level | Low, Medium, High, Critical |

---

## 4. Financial Approval Request

### Endpoint
```
POST http://localhost:2004/api/integration/mulesoft/financial-approval/xml
```

### XML Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<FinancialApprovalRequest>
    <RequestID>FIN-APP-2001</RequestID>
    <Amount>50000.00</Amount>
    <Currency>INR</Currency>
    <Justification>Equipment procurement for load enhancement</Justification>
    <RequestedBy>project_manager</RequestedBy>
    <CostCenter>CC-1001</CostCenter>
    <ProjectCode>PROJ-2026-001</ProjectCode>
    <Category>CAPEX</Category>
    <RequiredBy>2026-01-30</RequiredBy>
    <RelatedTicket>TKT-PM-20260121-0001</RelatedTicket>
</FinancialApprovalRequest>
```

### Field Descriptions
| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| RequestID | String | Yes | Unique approval request ID | Any string |
| Amount | Decimal | Yes | Amount requiring approval | Positive number |
| Currency | String | Yes | Currency code | INR, USD, EUR, etc. |
| Justification | String | Yes | Reason for expenditure | Any string |
| RequestedBy | String | Yes | Requester identifier | Any string |
| CostCenter | String | Yes | Cost center code | Any string |
| ProjectCode | String | No | Project reference | Any string |
| Category | String | Yes | Expenditure category | CAPEX, OPEX |
| RequiredBy | Date | Yes | Required approval date | YYYY-MM-DD |
| RelatedTicket | String | No | Related ticket ID | TKT-XX-YYYYMMDD-NNNN |

---

## 5. Maintenance Work Order Request

### Endpoint
```
POST http://localhost:2004/api/integration/mulesoft/work-order/xml
```

### XML Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<WorkOrderRequest>
    <RequestID>WO-REQ-3001</RequestID>
    <AssetID>ASSET-T101</AssetID>
    <AssetDescription>Transformer T-101, Substation A</AssetDescription>
    <WorkType>Preventive</WorkType>
    <Priority>High</Priority>
    <Description>Scheduled maintenance for transformer</Description>
    <ScheduledDate>2026-01-25</ScheduledDate>
    <EstimatedDuration>4</EstimatedDuration>
    <RequiredSkills>Electrical Engineer, Technician</RequiredSkills>
    <Location>Substation A, Hyderabad</Location>
    <RequestedBy>maintenance_supervisor</RequestedBy>
</WorkOrderRequest>
```

### Field Descriptions
| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| RequestID | String | Yes | Unique work order request ID | Any string |
| AssetID | String | Yes | Asset/Equipment identifier | Any string |
| AssetDescription | String | Yes | Asset description | Any string |
| WorkType | String | Yes | Type of maintenance | Preventive, Corrective, Breakdown |
| Priority | String | Yes | Priority level | Low, Medium, High, Critical |
| Description | String | Yes | Work description | Any string |
| ScheduledDate | Date | Yes | Scheduled work date | YYYY-MM-DD |
| EstimatedDuration | Integer | Yes | Duration in hours | Positive integer |
| RequiredSkills | String | No | Required skills/roles | Any string |
| Location | String | Yes | Work location | Any string |
| RequestedBy | String | Yes | Requester identifier | Any string |

---

## Common Response Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success - Request processed |
| 201 | Created - New resource created |
| 400 | Bad Request - Invalid XML format or missing required fields |
| 422 | Unprocessable Entity - Valid XML but business logic error |
| 500 | Internal Server Error - Server-side error |

---

## Error Response Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ErrorResponse>
    <Status>Error</Status>
    <Code>400</Code>
    <Message>Invalid XML format: Missing required field CustomerID</Message>
    <Timestamp>2026-01-21T12:00:00Z</Timestamp>
</ErrorResponse>
```

---

## Testing Examples

### Test with PowerShell
```powershell
$xml = @"
<?xml version="1.0" encoding="UTF-8"?>
<ElectricityLoadRequest>
    <RequestID>TEST-001</RequestID>
    <CustomerID>CUST-TEST</CustomerID>
    <CurrentLoad>5.0</CurrentLoad>
    <RequestedLoad>10.0</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>TestCity</City>
    <PinCode>123456</PinCode>
</ElectricityLoadRequest>
"@

Invoke-WebRequest -Uri "http://localhost:2004/api/integration/mulesoft/load-request/xml" `
    -Method POST `
    -ContentType "application/xml" `
    -Body $xml
```

### Test with Python
```python
import requests

xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<ElectricityLoadRequest>
    <RequestID>TEST-001</RequestID>
    <CustomerID>CUST-TEST</CustomerID>
    <CurrentLoad>5.0</CurrentLoad>
    <RequestedLoad>10.0</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>TestCity</City>
    <PinCode>123456</PinCode>
</ElectricityLoadRequest>"""

response = requests.post(
    "http://localhost:2004/api/integration/mulesoft/load-request/xml",
    data=xml_payload,
    headers={"Content-Type": "application/xml"}
)

print(response.json())
```

---

## Notes

1. **Character Encoding**: All XML requests must use UTF-8 encoding
2. **XML Declaration**: The `<?xml version="1.0" encoding="UTF-8"?>` declaration is optional but recommended
3. **Whitespace**: Extra whitespace and line breaks are ignored
4. **Case Sensitivity**: XML element names are case-sensitive
5. **Correlation IDs**: Use CorrelationID to track requests across systems
6. **Timestamps**: All timestamps are in ISO 8601 format (UTC)

---

## Support

For issues or questions about the XML API:
- Check logs: `docker logs sap-erp-backend --tail 50`
- View API docs: `http://localhost:2004/docs`
- Integration logs: `docker logs sap-erp-camel --tail 50`
