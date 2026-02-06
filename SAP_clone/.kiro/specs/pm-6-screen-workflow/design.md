# Design Document: 6-Screen PM Workflow

## Overview

This design consolidates SAP PM's 20+ transaction codes into 6 lifecycle-phase screens, creating a modern, state-driven maintenance workflow. The system maintains full enterprise compliance, auditability, and cost traceability while dramatically simplifying the user experience. Each screen represents a distinct phase in the maintenance lifecycle, with AI agents providing intelligent automation throughout.

## Architecture

### State Machine Design

The workflow operates as a finite state machine with the following states:

```
Created → Planned → Released → In Progress → Confirmed → TECO
```

Each state transition has specific prerequisites and triggers automated business logic. The system prevents invalid transitions and provides clear feedback on blocking conditions.

### Single Source of Truth

All maintenance data is stored in a unified order document that evolves through lifecycle phases. Related documents (POs, GRs, GIs, confirmations) are linked through a document flow graph, ensuring complete traceability.

### AI Agent Integration

AI agents operate at each screen, performing:
- Validation and prerequisite checking
- Intelligent suggestions based on historical data
- Automated alerts for exceptions
- Next-action recommendations
- Cost variance analysis

## The 6 Screens

### Screen 1: Order Planning & Initiation

**Purpose:** Create and plan maintenance orders with complete scope definition

**User Actions:**
- Create new general maintenance order
- Create breakdown order from notification
- Define operations (PM01, PM02, PM03) with work centers
- Add components (materials with/without master data)
- Estimate costs by element (material, labor, external)
- Request permits and safety approvals
- Save order in "Created" status

**Data Captured:**
- Order header: type, equipment, functional location, priority, dates
- Operations: sequence, work center, duration, skill requirements
- Components: material number/description, quantity, unit cost
- Cost estimate: breakdown by cost element
- Permit requirements: type, approver, status
- Breakdown notification reference (if applicable)

**Validation Rules:**
- Equipment or functional location is mandatory
- At least one operation must be defined
- Component quantities must be positive
- Estimated costs must be calculated before proceeding
- High-priority orders require justification

**Status Transitions:**
- Entry: None (initial screen)
- Exit: Created → Planned (when all required data is entered)

**AI Agent Assistance:**
- Suggests similar historical orders with cost benchmarks
- Auto-populates operations based on equipment type
- Recommends components from previous similar work
- Validates material availability in real-time
- Flags cost estimates that deviate from historical averages
- Pre-fills breakdown order details from notification

**Breakdown vs General Maintenance:**
- Breakdown: Auto-created from notification, highest priority, pre-populated equipment
- General: Manual creation, normal priority, full planning required

---

### Screen 2: Procurement & Material Planning

**Purpose:** Procure materials and services required for order execution

**User Actions:**
- Review component requirements from planning
- Create purchase orders for materials
- Create purchase orders for external services
- Create combined POs (service + material)
- Track PO status and delivery dates
- View procurement document flow
- Mark procurement complete

**Data Captured:**
- Purchase orders: PO number, vendor, items, quantities, prices, delivery dates
- PO type: material only, service only, or combined
- Service specifications: scope of work, cost limits, acceptance criteria
- Procurement status: ordered, partially delivered, fully delivered
- Vendor details: name, contact, performance rating

**Validation Rules:**
- PO must reference maintenance order
- Service POs require scope of work description
- Delivery dates must align with order planned dates
- PO total must not exceed order budget (warning if exceeded)
- At least one PO must be created for non-stock materials

**Status Transitions:**
- Entry: Planned
- Exit: Planned → Released (when critical materials are procured or on order)

**AI Agent Assistance:**
- Suggests preferred vendors based on historical performance
- Auto-generates PO drafts from component list
- Alerts on long lead-time materials
- Recommends alternative materials if primary is unavailable
- Tracks PO delivery status and alerts on delays
- Calculates optimal order quantities based on usage patterns

**Breakdown vs General Maintenance:**
- Breakdown: Expedited procurement, emergency stock usage, reduced approval requirements
- General: Standard procurement cycle, full approval workflow

---

### Screen 3: Order Release & Execution Readiness

**Purpose:** Validate prerequisites and release orders for execution

**User Actions:**
- Review order readiness checklist
- Verify permit approvals
- Confirm material availability
- Assign technicians/crew
- Release order for execution
- View blocking reasons if release fails
- Override blocks with authorization (if permitted)

**Data Captured:**
- Readiness checklist: permits, materials, resources, tools
- Permit approvals: approver, date, conditions
- Material availability: on-hand, on-order, shortages
- Resource assignments: technician, crew, shift
- Release details: releaser, timestamp, authorization level
- Block overrides: reason, approver, risk acceptance

**Validation Rules:**
- All required permits must be approved
- Critical materials must be available or on confirmed delivery
- At least one technician must be assigned
- Work center capacity must be available
- Safety conditions must be met
- Order cannot be released if in "Created" status (must be "Planned")

**Status Transitions:**
- Entry: Planned
- Exit: Planned → Released (when all validations pass)

**AI Agent Assistance:**
- Performs automated prerequisite validation
- Highlights blocking conditions with resolution suggestions
- Recommends optimal technician assignments based on skills and availability
- Predicts work center capacity conflicts
- Suggests alternative execution dates if resources unavailable
- Auto-approves low-risk releases based on rules
- Sends notifications to assigned technicians

**Breakdown vs General Maintenance:**
- Breakdown: Reduced validation, emergency permits accepted, immediate release possible
- General: Full validation required, standard permit process

---

### Screen 4: Material Receipt & Service Entry

**Purpose:** Record goods receipts and service sheet entries

**User Actions:**
- Record goods receipt (GR) for delivered materials
- Enter service sheet for external work performed
- Link GR/service entry to PO and maintenance order
- Verify quantities and quality
- Post GR/service entry to update inventory and costs
- View receipt/entry document flow

**Data Captured:**
- Goods receipt: PO reference, material, quantity received, receipt date, storage location
- Service entry: PO reference, service description, hours/units, acceptance date, acceptor
- Quality inspection: pass/fail, inspector, notes
- Delivery variances: quantity differences, damage, returns
- Cost updates: actual costs vs. PO prices
- Document numbers: GR document, service entry document

**Validation Rules:**
- GR must reference valid PO
- Received quantity cannot exceed PO quantity (warning if exceeded)
- Service entry must reference service PO
- Service hours must be within PO cost limits (warning if exceeded)
- Quality inspection required for critical materials
- Acceptor must be authorized for service acceptance

**Status Transitions:**
- Entry: Released (or Planned if early delivery)
- Exit: No status change (supporting transaction)

**AI Agent Assistance:**
- Auto-matches deliveries to POs using barcode/RFID
- Flags quantity variances and suggests resolution
- Validates service entry against PO scope
- Alerts on cost overruns before posting
- Recommends storage locations based on material type
- Auto-posts routine GRs with standard parameters
- Tracks partial deliveries and alerts on completion

**Breakdown vs General Maintenance:**
- Breakdown: Emergency stock GR without PO, simplified service entry
- General: Full PO-based GR, detailed service sheet

---

### Screen 5: Work Execution & Confirmation

**Purpose:** Issue materials, execute work, and confirm completion

**User Actions:**
- Issue materials (GI) to order before work starts
- Confirm internal work completion with actual hours
- Confirm external work completion with vendor reference
- Report malfunctions with cause codes
- Enter work notes and findings
- Attach photos/documents
- Submit confirmation

**Data Captured:**
- Goods issue: material, quantity issued, issue date, cost center
- Internal confirmation: operation, actual hours, completion date, technician, work performed
- External confirmation: operation, vendor, acceptance date, acceptor, service quality
- Malfunction report: cause code, description, root cause, corrective action
- Work notes: findings, observations, recommendations
- Attachments: photos, test results, inspection reports

**Validation Rules:**
- Goods issue (GI) must be posted before confirmation
- Actual hours must be positive
- All operations must be confirmed before TECO
- Malfunction reporting mandatory for breakdown orders
- External confirmations require vendor reference
- Confirmation date cannot be before order release date

**Status Transitions:**
- Entry: Released
- Exit: Released → In Progress (first confirmation) → Confirmed (all operations confirmed)

**AI Agent Assistance:**
- Enforces GI-before-confirmation rule with clear messaging
- Suggests material quantities based on planned consumption
- Auto-fills confirmation data from mobile device timestamps
- Validates actual hours against estimates and alerts on variances
- Recommends cause codes based on malfunction description
- Captures voice notes and converts to text
- Flags incomplete confirmations before submission

**Breakdown vs General Maintenance:**
- Breakdown: Mandatory malfunction reporting, expedited confirmation process
- General: Optional malfunction reporting, standard confirmation

---

### Screen 6: Completion & Cost Settlement

**Purpose:** Technically complete orders and settle final costs

**User Actions:**
- Review completion checklist
- View final actual costs by element
- Compare estimated vs. actual costs
- Analyze cost variances
- View complete document flow
- Technically complete order (TECO)
- Settle costs to cost center/equipment
- Generate completion report

**Data Captured:**
- Completion checklist: all operations confirmed, all GIs posted, all costs captured
- Final costs: material actual, labor actual, external actual, total actual
- Cost variance: estimated vs. actual by element, variance percentage
- Document flow: chronological list of all related transactions
- Settlement: cost center, equipment, WBS element, settlement date
- Completion report: summary, findings, recommendations, lessons learned

**Validation Rules:**
- All operations must be confirmed
- All goods movements (GI) must be posted
- All service entries must be accepted
- No open purchase orders or reservations
- Cost settlement target must be valid
- TECO cannot be reversed without authorization

**Status Transitions:**
- Entry: Confirmed
- Exit: Confirmed → TECO (when all validations pass)

**AI Agent Assistance:**
- Performs automated completion validation
- Highlights incomplete steps with resolution actions
- Calculates cost variances and flags significant deviations
- Suggests variance explanations based on historical patterns
- Auto-generates completion reports with key metrics
- Recommends cost settlement targets based on order type
- Identifies lessons learned from similar orders
- Triggers post-completion review for breakdown orders

**Breakdown vs General Maintenance:**
- Breakdown: Mandatory post-completion review, root cause analysis required
- General: Standard completion, optional review

---

## Screen Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAINTENANCE LIFECYCLE                         │
└─────────────────────────────────────────────────────────────────┘

[1] Order Planning & Initiation
    │
    │ Create order, define operations, add components,
    │ estimate costs, request permits
    │
    ├─→ Breakdown: Auto-created from notification
    │
    ▼
[2] Procurement & Material Planning
    │
    │ Create POs for materials/services,
    │ track delivery status
    │
    ├─→ Breakdown: Expedited procurement, emergency stock
    │
    ▼
[3] Order Release & Execution Readiness
    │
    │ Validate permits, materials, resources,
    │ release for execution
    │
    ├─→ Breakdown: Reduced validation, immediate release
    │
    ▼
[4] Material Receipt & Service Entry
    │
    │ Record GR for materials, enter service sheets,
    │ update inventory and costs
    │
    ├─→ Breakdown: Emergency stock GR without PO
    │
    ▼
[5] Work Execution & Confirmation
    │
    │ Issue materials (GI), execute work,
    │ confirm completion, report malfunctions
    │
    ├─→ Breakdown: Mandatory malfunction reporting
    │
    ▼
[6] Completion & Cost Settlement
    │
    │ Review costs, analyze variances,
    │ TECO order, settle costs
    │
    └─→ Breakdown: Mandatory post-completion review

═══════════════════════════════════════════════════════════════════

STATE TRANSITIONS:

Created → Planned → Released → In Progress → Confirmed → TECO

AI AGENT TOUCHPOINTS (at every screen):
- Validation & prerequisite checking
- Intelligent suggestions
- Automated alerts
- Next-action recommendations
- Cost variance analysis
```

## Breakdown Maintenance Workflow Differences

### Key Differentiators

| Aspect | General Maintenance | Breakdown Maintenance |
|--------|-------------------|---------------------|
| **Initiation** | Manual creation | Auto-created from notification |
| **Priority** | Normal/Low | Highest |
| **Planning** | Full planning required | Pre-populated from notification |
| **Procurement** | Standard cycle | Expedited, emergency stock |
| **Release** | Full validation | Reduced validation, emergency permits |
| **Material Issue** | Standard GI process | Emergency stock without PO |
| **Confirmation** | Optional malfunction | Mandatory malfunction reporting |
| **Completion** | Standard TECO | Mandatory post-review & root cause |

### Workflow Acceleration

Breakdown maintenance follows an accelerated path:
1. **Screen 1:** Auto-populated, minimal planning
2. **Screen 2:** Emergency stock usage, skip if materials available
3. **Screen 3:** Immediate release with emergency permits
4. **Screen 4:** Simplified GR/service entry
5. **Screen 5:** Expedited confirmation, mandatory malfunction
6. **Screen 6:** Standard TECO + mandatory review

## Components and Interfaces

### Core Components

**Order Management Engine**
- Maintains order state machine
- Enforces transition rules
- Manages document flow graph
- Handles breakdown vs. general logic

**Procurement Integration**
- Creates and tracks purchase orders
- Links POs to maintenance orders
- Monitors delivery status
- Handles service POs

**Inventory Integration**
- Posts goods receipts (GR)
- Posts goods issues (GI)
- Updates stock levels
- Tracks material consumption

**Cost Management**
- Calculates estimated costs
- Captures actual costs
- Computes variances
- Settles costs to targets

**AI Agent Framework**
- Validation engine
- Suggestion engine
- Alert engine
- Analytics engine

### External Interfaces

**SAP MM (Materials Management)**
- Material master data
- Purchase order creation
- Goods receipt posting
- Inventory updates

**SAP FI (Financial Accounting)**
- Cost element master data
- Cost center validation
- Cost settlement posting
- Variance accounting

**SAP HR (Human Resources)**
- Technician master data
- Skill profiles
- Availability calendars
- Labor cost rates

**Notification System**
- Breakdown notification creation
- Alert distribution
- Mobile notifications
- Email notifications

## Data Models

### Maintenance Order

```
MaintenanceOrder {
  order_number: string (PK)
  order_type: enum (General, Breakdown)
  status: enum (Created, Planned, Released, InProgress, Confirmed, TECO)
  equipment_id: string (FK)
  functional_location: string
  priority: enum (Low, Normal, High, Urgent)
  planned_start_date: datetime
  planned_end_date: datetime
  actual_start_date: datetime
  actual_end_date: datetime
  breakdown_notification_id: string (FK, nullable)
  created_by: string
  created_at: datetime
  released_by: string (nullable)
  released_at: datetime (nullable)
  completed_by: string (nullable)
  completed_at: datetime (nullable)
}
```

### Operation

```
Operation {
  operation_id: string (PK)
  order_number: string (FK)
  operation_number: string
  work_center: string
  description: string
  planned_hours: decimal
  actual_hours: decimal (nullable)
  status: enum (Planned, InProgress, Confirmed)
  technician_id: string (FK, nullable)
  confirmation_date: datetime (nullable)
}
```

### Component

```
Component {
  component_id: string (PK)
  order_number: string (FK)
  material_number: string (nullable)
  description: string
  quantity_required: decimal
  quantity_issued: decimal
  unit_of_measure: string
  estimated_cost: decimal
  actual_cost: decimal (nullable)
  has_master_data: boolean
  reservation_number: string (nullable)
}
```

### Purchase Order

```
PurchaseOrder {
  po_number: string (PK)
  order_number: string (FK)
  po_type: enum (Material, Service, Combined)
  vendor_id: string (FK)
  total_value: decimal
  delivery_date: datetime
  status: enum (Created, Ordered, PartiallyDelivered, Delivered)
  created_at: datetime
}
```

### Goods Receipt

```
GoodsReceipt {
  gr_document: string (PK)
  po_number: string (FK)
  order_number: string (FK)
  material_number: string
  quantity_received: decimal
  receipt_date: datetime
  storage_location: string
  received_by: string
}
```

### Goods Issue

```
GoodsIssue {
  gi_document: string (PK)
  order_number: string (FK)
  component_id: string (FK)
  material_number: string
  quantity_issued: decimal
  issue_date: datetime
  cost_center: string
  issued_by: string
}
```

### Confirmation

```
Confirmation {
  confirmation_id: string (PK)
  order_number: string (FK)
  operation_id: string (FK)
  confirmation_type: enum (Internal, External)
  actual_hours: decimal
  confirmation_date: datetime
  technician_id: string (FK, nullable)
  vendor_id: string (FK, nullable)
  work_notes: text
  confirmed_by: string
}
```

### Malfunction Report

```
MalfunctionReport {
  report_id: string (PK)
  order_number: string (FK)
  cause_code: string
  description: text
  root_cause: text
  corrective_action: text
  reported_by: string
  reported_at: datetime
}
```

### Document Flow

```
DocumentFlow {
  flow_id: string (PK)
  order_number: string (FK)
  document_type: enum (Order, PO, GR, GI, Confirmation, ServiceEntry, TECO)
  document_number: string
  transaction_date: datetime
  user_id: string
  status: string
  related_document: string (nullable)
}
```

### Cost Summary

```
CostSummary {
  order_number: string (PK, FK)
  estimated_material_cost: decimal
  estimated_labor_cost: decimal
  estimated_external_cost: decimal
  estimated_total_cost: decimal
  actual_material_cost: decimal
  actual_labor_cost: decimal
  actual_external_cost: decimal
  actual_total_cost: decimal
  material_variance: decimal
  labor_variance: decimal
  external_variance: decimal
  total_variance: decimal
  variance_percentage: decimal
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: State Transition Validity

*For any* maintenance order and any requested state transition, the system should only allow the transition if all prerequisites for the target state are satisfied.

**Validates: Requirements 10.2, 10.3**

### Property 2: GI-Before-Confirmation Enforcement

*For any* maintenance order operation, if a confirmation is posted, then all required goods issues for that operation must have been posted prior to the confirmation timestamp.

**Validates: Requirements 5.1, 5.6**

### Property 3: Cost Accumulation Consistency

*For any* maintenance order, the sum of all individual cost postings (GR costs + GI costs + confirmation labor costs + service entry costs) should equal the total actual cost in the cost summary.

**Validates: Requirements 1.5, 6.4**

### Property 4: Document Flow Completeness

*For any* maintenance order in TECO status, the document flow should contain at least one entry for each mandatory transaction type (Order creation, Release, GI, Confirmation, TECO).

**Validates: Requirements 9.1, 9.2**

### Property 5: Breakdown Order Acceleration

*For any* breakdown maintenance order, the system should allow immediate release with reduced validation compared to general maintenance orders of the same scope.

**Validates: Requirements 7.3, 7.4**

### Property 6: TECO Prerequisite Validation

*For any* maintenance order, technical completion (TECO) should only be allowed if all operations are confirmed and all goods movements are posted.

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 7: Permit Enforcement

*For any* maintenance order with permit requirements, the order should not transition to "Released" status unless all required permits are approved.

**Validates: Requirements 1.6, 3.1**

### Property 8: PO-Order Linkage

*For any* purchase order created for a maintenance order, the PO should maintain a valid reference to the maintenance order throughout its lifecycle.

**Validates: Requirements 2.4, 2.5**

### Property 9: Material Availability Validation

*For any* maintenance order at release, if critical materials are not available and not on confirmed delivery, the system should prevent release or require override authorization.

**Validates: Requirements 3.2, 3.6**

### Property 10: Audit Trail Immutability

*For any* document flow entry, once posted, the entry should not be modifiable or deletable, ensuring audit trail integrity.

**Validates: Requirements 9.1, 9.3**

## Error Handling

### Validation Errors

**State Transition Failures**
- Display specific blocking conditions
- Provide resolution suggestions
- Allow authorized overrides with justification
- Log all override attempts

**Data Validation Errors**
- Highlight invalid fields with clear messages
- Prevent submission until corrected
- Suggest valid values where applicable
- Maintain user-entered data during correction

### System Errors

**Integration Failures**
- Retry with exponential backoff
- Queue transactions for later processing
- Alert administrators on persistent failures
- Maintain data consistency across systems

**Concurrency Conflicts**
- Detect concurrent modifications
- Implement optimistic locking
- Prompt user to refresh and retry
- Preserve user changes where possible

### Business Rule Violations

**Cost Overruns**
- Warn on budget exceedance
- Require approval for significant overruns
- Track approval chain
- Alert cost controllers

**Timeline Violations**
- Alert on missed planned dates
- Suggest rescheduling options
- Track delay reasons
- Escalate critical delays

## Testing Strategy

### Unit Testing

**State Machine Logic**
- Test all valid state transitions
- Test blocking of invalid transitions
- Test prerequisite validation for each state
- Test state-specific action enablement

**Cost Calculations**
- Test cost accumulation from multiple sources
- Test variance calculations
- Test cost settlement logic
- Test rounding and precision

**Validation Rules**
- Test each validation rule independently
- Test combination of validation rules
- Test validation error messages
- Test override authorization logic

### Property-Based Testing

The system will use **Hypothesis** (Python) for property-based testing to verify correctness properties across randomly generated maintenance scenarios.

**Test Configuration:**
- Minimum 100 iterations per property test
- Generate diverse order types, statuses, and transaction combinations
- Use shrinking to find minimal failing examples
- Tag each test with corresponding design property

**Property Test Coverage:**
- Property 1: Generate random state transitions and verify prerequisite enforcement
- Property 2: Generate random confirmations and verify GI precedence
- Property 3: Generate random cost postings and verify accumulation
- Property 4: Generate random TECO orders and verify document flow completeness
- Property 5: Generate breakdown vs. general orders and verify acceleration rules
- Property 6: Generate random TECO attempts and verify prerequisites
- Property 7: Generate orders with permits and verify release blocking
- Property 8: Generate POs and verify order linkage integrity
- Property 9: Generate release attempts and verify material availability checks
- Property 10: Generate document flow entries and verify immutability

### Integration Testing

**End-to-End Workflows**
- Test complete general maintenance lifecycle
- Test complete breakdown maintenance lifecycle
- Test procurement integration (PO → GR → GI)
- Test cost settlement integration (Order → FI posting)

**AI Agent Integration**
- Test validation automation
- Test suggestion accuracy
- Test alert triggering
- Test next-action recommendations

### User Acceptance Testing

**Screen Usability**
- Test each screen with real users
- Validate data entry efficiency
- Verify error message clarity
- Assess AI agent helpfulness

**Workflow Efficiency**
- Measure time to complete orders
- Compare to traditional SAP transaction flow
- Identify bottlenecks
- Gather user feedback

## Implementation Notes

### Technology Stack

**Frontend:** React with TypeScript, SAP Fiori design system
**Backend:** Python FastAPI with SQLAlchemy ORM
**Database:** PostgreSQL with full audit logging
**AI Agents:** LangChain with GPT-4 for intelligent assistance
**Integration:** REST APIs for SAP MM/FI/HR integration

### Performance Considerations

- Cache frequently accessed master data
- Implement lazy loading for document flow
- Use database indexes on order_number, status, dates
- Optimize cost calculation queries
- Implement real-time updates via WebSockets

### Security Considerations

- Role-based access control for each screen
- Authorization checks for state transitions
- Audit logging of all transactions
- Encryption of sensitive data
- Secure API authentication

### Scalability Considerations

- Horizontal scaling of API servers
- Database read replicas for reporting
- Message queue for async processing
- Caching layer for master data
- CDN for static assets
