# Electricity Load Request - Data Flow Diagram

## High-Level Flow

```
┌─────────────┐
│  MuleSoft   │
│ Integration │
└──────┬──────┘
       │ XML/JSON Request
       │ (Load Enhancement)
       ▼
┌─────────────────────────────────────────┐
│  Integration API                        │
│  /api/integration/mulesoft/load-request │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Electricity Service     │
│ - Parse request         │
│ - Calculate cost        │
│ - Determine priority    │
│ - Check requirements    │
└──────┬──────────────────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌──────────────┐                  ┌──────────────┐
│ Ticket       │                  │ Event        │
│ Service      │                  │ Service      │
└──────┬───────┘                  └──────────────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
       ▼          ▼          ▼          ▼
   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────────┐
   │ PM  │   │ FI  │   │ MM  │   │ Audit   │
   │Ticket│   │Ticket│   │Ticket│   │ Trail   │
   └─────┘   └─────┘   └─────┘   └─────────┘
```

## Detailed Processing Flow

```
1. REQUEST RECEIVED
   ├─ Validate XML/JSON format
   ├─ Extract customer details
   └─ Parse load requirements

2. BUSINESS LOGIC
   ├─ Calculate load increase
   │  └─ Requested Load - Current Load
   │
   ├─ Determine Priority
   │  ├─ ≥20 kW → P1 (4h SLA)
   │  ├─ ≥10 kW → P2 (8h SLA)
   │  ├─ ≥5 kW  → P3 (24h SLA)
   │  └─ <5 kW  → P4 (72h SLA)
   │
   ├─ Calculate Cost
   │  ├─ Base Fee: ₹5,000
   │  ├─ Residential: ₹2,500/kW
   │  └─ Commercial: ₹3,500/kW
   │
   └─ Check Requirements
      ├─ Equipment needed? (Load > 15kW)
      └─ Approval needed? (Cost > ₹10,000)

3. TICKET CREATION
   ├─ PM Ticket (Always)
   │  ├─ Type: Maintenance
   │  ├─ Module: PM
   │  └─ Purpose: Field work order
   │
   ├─ FI Ticket (If cost > ₹10,000)
   │  ├─ Type: Finance_Approval
   │  ├─ Module: FI
   │  └─ Purpose: Cost approval
   │
   └─ MM Ticket (If load > 15kW)
      ├─ Type: Procurement
      ├─ Module: MM
      └─ Purpose: Equipment procurement

4. EVENT LOGGING
   ├─ Log integration event
   ├─ Record ticket IDs
   └─ Track correlation ID

5. RESPONSE
   ├─ Return ticket IDs
   ├─ Estimated cost
   ├─ Priority level
   └─ Next steps
```

## Module Interaction

```
┌──────────────────────────────────────────────────────┐
│                  Integration Layer                    │
│  (Receives requests from external systems)           │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              Electricity Service                      │
│  (Business logic & orchestration)                    │
└──┬────────────┬────────────┬────────────┬───────────┘
   │            │            │            │
   ▼            ▼            ▼            ▼
┌──────┐   ┌──────┐   ┌──────┐   ┌──────────┐
│  PM  │   │  FI  │   │  MM  │   │  Event   │
│Module│   │Module│   │Module│   │ Service  │
└──┬───┘   └──┬───┘   └──┬───┘   └──────────┘
   │          │          │
   ▼          ▼          ▼
┌────────────────────────────┐
│      Database Layer        │
│  - Tickets                 │
│  - Audit Trail             │
│  - Events                  │
└────────────────────────────┘
```

## Ticket Lifecycle

```
PM TICKET FLOW:
Open → Assigned → In_Progress → Closed
  │       │           │            │
  │       │           │            └─ Work completed
  │       │           └─ Technician on site
  │       └─ Assigned to field technician
  └─ Created from load request

FI TICKET FLOW:
Open → Assigned → In_Progress → Closed
  │       │           │            │
  │       │           │            └─ Payment received
  │       │           └─ Invoice generated
  │       └─ Assigned to finance team
  └─ Created for cost approval

MM TICKET FLOW:
Open → Assigned → In_Progress → Closed
  │       │           │            │
  │       │           │            └─ Equipment delivered
  │       │           └─ Order placed
  │       └─ Assigned to procurement
  └─ Created for equipment
```

## Data Model

```
ElectricityLoadRequest
├─ request_id: string
├─ customer_id: string
├─ current_load: float (kW)
├─ requested_load: float (kW)
├─ connection_type: RESIDENTIAL | COMMERCIAL
├─ city: string
└─ pin_code: string

Response
├─ status: "accepted"
├─ request_id: string
├─ customer_id: string
├─ estimated_cost: float
├─ priority: P1 | P2 | P3 | P4
├─ tickets_created
│  ├─ pm_ticket: string
│  ├─ fi_ticket: string | null
│  └─ mm_ticket: string | null
├─ workflow_status: "initiated"
└─ next_steps: string[]
```

## Example Scenarios

### Scenario A: Small Load (3kW → 5kW)
```
Input: 2kW increase, Residential
  ↓
Priority: P4 (72h)
Cost: ₹10,000
  ↓
Tickets Created:
  ✓ PM (Work Order)
  ✗ FI (Cost ≤ ₹10,000)
  ✗ MM (Load ≤ 15kW)
```

### Scenario B: Medium Load (5kW → 10kW)
```
Input: 5kW increase, Residential
  ↓
Priority: P3 (24h)
Cost: ₹17,500
  ↓
Tickets Created:
  ✓ PM (Work Order)
  ✓ FI (Cost > ₹10,000)
  ✗ MM (Load ≤ 15kW)
```

### Scenario C: Large Load (10kW → 30kW)
```
Input: 20kW increase, Commercial
  ↓
Priority: P1 (4h)
Cost: ₹75,000
  ↓
Tickets Created:
  ✓ PM (Work Order)
  ✓ FI (Cost > ₹10,000)
  ✓ MM (Load > 15kW)
```

## Integration Points

```
External Systems          SAP ERP Modules
─────────────────        ─────────────────
                         
MuleSoft ────────────────► Integration API
                                │
Salesforce ──────────────► Customer Data
                                │
Field Service ───────────► PM Module
                                │
Billing System ──────────► FI Module
                                │
Warehouse ───────────────► MM Module
```
