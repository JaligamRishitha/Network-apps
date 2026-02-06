# Requirements Document: 6-Screen PM Workflow

## Introduction

This specification defines a modern, state-driven maintenance workflow system that consolidates traditional SAP PM transaction screens into 6 lifecycle-phase screens. The system supports both General Maintenance and Breakdown Maintenance workflows while maintaining full compliance, auditability, and cost traceability. The design enables AI agent automation for validation, alerts, and intelligent actions.

## Glossary

- **PM System**: Plant Maintenance System - the application managing maintenance orders and workflows
- **Maintenance Order**: A work order document tracking maintenance activities, costs, and status
- **Breakdown Notification**: An urgent notification triggering immediate maintenance response
- **Operation**: A specific task within a maintenance order (e.g., PM01, PM02, PM03)
- **Component**: Materials required for maintenance, with or without master data
- **GR**: Goods Receipt - confirmation of material delivery
- **GI**: Goods Issue - material consumption from inventory
- **Service Sheet**: Document for recording external service work (ML81N equivalent)
- **TECO**: Technical Completion - final status indicating work completion
- **AI Agent**: Automated system performing validation, alerts, and workflow assistance
- **Document Flow**: Complete audit trail of all related transactions and status changes
- **Cost Element**: Classification of costs (material, labor, external service)
- **Permit**: Safety approval required before work execution
- **Purchase Order (PO)**: Procurement document for materials or services

## Requirements

### Requirement 1: Order Planning & Initiation

**User Story:** As a maintenance planner, I want to create and plan maintenance orders with all required details, so that work can be properly scoped and authorized.

#### Acceptance Criteria

1. WHEN a user creates a general maintenance order THEN the PM System SHALL capture order type, equipment, functional location, priority, and planned dates
2. WHEN a breakdown notification is received THEN the PM System SHALL automatically create a high-priority maintenance order with notification reference
3. WHEN operations are added to an order THEN the PM System SHALL validate operation sequence and capture work center, duration, and skill requirements
4. WHEN components are added THEN the PM System SHALL support both master data materials and non-stock items with quantity and cost estimates
5. WHEN cost estimation is requested THEN the PM System SHALL calculate total estimated costs across materials, labor, and external services
6. WHERE permit requirements exist THEN the PM System SHALL enforce permit approval before order release
7. WHEN an order is saved THEN the PM System SHALL assign a unique order number and set status to "Created"

### Requirement 2: Procurement & Material Planning

**User Story:** As a maintenance planner, I want to procure materials and services required for maintenance work, so that resources are available when needed.

#### Acceptance Criteria

1. WHEN materials without stock are identified THEN the PM System SHALL enable creation of purchase orders with material details, quantity, and delivery date
2. WHEN external services are required THEN the PM System SHALL create service purchase orders with scope of work and cost limits
3. WHEN external services with material are needed THEN the PM System SHALL create combined purchase orders linking service and material components
4. WHEN a purchase order is created THEN the PM System SHALL link it to the maintenance order and update procurement status
5. WHEN purchase order status changes THEN the PM System SHALL update the maintenance order document flow
6. WHEN all required materials are procured THEN the PM System SHALL enable order release for execution

### Requirement 3: Order Release & Execution Readiness

**User Story:** As a maintenance supervisor, I want to release orders for execution only when all prerequisites are met, so that work can proceed safely and efficiently.

#### Acceptance Criteria

1. WHEN an order release is requested THEN the PM System SHALL validate that all required permits are approved
2. WHEN an order release is requested THEN the PM System SHALL validate that critical materials are available or on order
3. WHEN validation passes THEN the PM System SHALL change order status to "Released" and make it available for execution
4. WHEN an order is released THEN the PM System SHALL notify assigned technicians and update the work queue
5. IF validation fails THEN the PM System SHALL display specific blocking reasons and prevent release
6. WHEN an order is released THEN the PM System SHALL record release timestamp and user for audit purposes

### Requirement 4: Material Receipt & Service Entry

**User Story:** As a warehouse operator, I want to record goods receipts and service entries, so that materials and services are properly documented and available for use.

#### Acceptance Criteria

1. WHEN materials are delivered THEN the PM System SHALL record goods receipt with PO reference, quantity, and receipt date
2. WHEN goods receipt is posted THEN the PM System SHALL update inventory and link to maintenance order
3. WHEN external services are performed THEN the PM System SHALL enable service sheet entry with hours, description, and acceptance
4. WHEN service entry is posted THEN the PM System SHALL update order costs and create invoice verification basis
5. WHEN goods receipt or service entry is posted THEN the PM System SHALL update document flow with timestamps and user details

### Requirement 5: Work Execution & Confirmation

**User Story:** As a maintenance technician, I want to confirm completed work and issue materials, so that actual effort and consumption are accurately recorded.

#### Acceptance Criteria

1. WHEN work begins THEN the PM System SHALL require goods issue for planned components before confirmation
2. WHEN goods issue is posted THEN the PM System SHALL reduce inventory, update order costs, and record consumption details
3. WHEN internal work is completed THEN the PM System SHALL capture confirmation with actual hours, date, and technician
4. WHEN external work is completed THEN the PM System SHALL capture external confirmation with vendor reference and acceptance
5. IF malfunction is detected THEN the PM System SHALL enable malfunction reporting with cause code and description
6. WHEN confirmation is posted THEN the PM System SHALL validate that goods issue preceded confirmation
7. WHEN all operations are confirmed THEN the PM System SHALL enable technical completion

### Requirement 6: Completion & Cost Settlement

**User Story:** As a maintenance controller, I want to technically complete orders and view final costs, so that work is properly closed and costs are settled.

#### Acceptance Criteria

1. WHEN technical completion is requested THEN the PM System SHALL validate that all operations are confirmed
2. WHEN technical completion is requested THEN the PM System SHALL validate that all goods movements are posted
3. WHEN validation passes THEN the PM System SHALL set order status to "TECO" and prevent further postings
4. WHEN an order is completed THEN the PM System SHALL display final actual costs by cost element (material, labor, external)
5. WHEN an order is completed THEN the PM System SHALL display complete document flow showing all related transactions
6. WHEN an order is completed THEN the PM System SHALL calculate variance between estimated and actual costs
7. WHEN cost settlement is triggered THEN the PM System SHALL post costs to appropriate cost centers or equipment

### Requirement 7: Breakdown Maintenance Differentiation

**User Story:** As a maintenance manager, I want breakdown maintenance to follow an accelerated workflow, so that urgent issues are resolved quickly while maintaining compliance.

#### Acceptance Criteria

1. WHEN a breakdown notification is created THEN the PM System SHALL automatically generate a maintenance order with highest priority
2. WHEN a breakdown order is created THEN the PM System SHALL pre-populate equipment, functional location, and notification details
3. WHEN a breakdown order is created THEN the PM System SHALL enable immediate release with reduced validation (emergency permits)
4. WHEN a breakdown order is released THEN the PM System SHALL allow goods issue from emergency stock without full procurement cycle
5. WHEN a breakdown order is confirmed THEN the PM System SHALL require malfunction reporting as mandatory
6. WHEN a breakdown order is completed THEN the PM System SHALL flag for post-completion review and root cause analysis

### Requirement 8: AI Agent Assistance

**User Story:** As a system user, I want AI agents to automate validations and provide intelligent assistance, so that workflows are efficient and error-free.

#### Acceptance Criteria

1. WHEN an order is created THEN the AI Agent SHALL suggest similar historical orders with cost estimates
2. WHEN components are added THEN the AI Agent SHALL validate material availability and suggest alternatives if out of stock
3. WHEN procurement delays occur THEN the AI Agent SHALL alert planners and suggest expediting actions
4. WHEN order release is attempted THEN the AI Agent SHALL perform automated validation and highlight blocking issues
5. WHEN goods issue is missing THEN the AI Agent SHALL prevent confirmation and display mandatory prerequisite message
6. WHEN cost variance exceeds threshold THEN the AI Agent SHALL alert controllers and request variance explanation
7. WHEN document flow is viewed THEN the AI Agent SHALL highlight incomplete steps and suggest next actions

### Requirement 9: Document Flow & Auditability

**User Story:** As an auditor, I want complete visibility into all transactions and status changes, so that compliance and traceability are ensured.

#### Acceptance Criteria

1. WHEN any transaction is posted THEN the PM System SHALL record timestamp, user, and transaction type in document flow
2. WHEN document flow is viewed THEN the PM System SHALL display chronological sequence of all related documents
3. WHEN status changes occur THEN the PM System SHALL record old status, new status, reason, and approver
4. WHEN costs are posted THEN the PM System SHALL link cost documents to source transactions (GR, GI, confirmation)
5. WHEN an order is queried THEN the PM System SHALL provide complete audit trail from creation to completion

### Requirement 10: State-Driven Workflow Engine

**User Story:** As a system administrator, I want the workflow to be state-driven with clear transitions, so that the system enforces business rules consistently.

#### Acceptance Criteria

1. THE PM System SHALL define discrete states: Created, Planned, Released, In Progress, Confirmed, TECO
2. WHEN a state transition is requested THEN the PM System SHALL validate all prerequisites for that transition
3. WHEN prerequisites are not met THEN the PM System SHALL prevent transition and display specific blocking reasons
4. WHEN a state transition occurs THEN the PM System SHALL execute all associated business logic (notifications, cost updates, inventory movements)
5. WHEN a state is active THEN the PM System SHALL enable only valid actions for that state and disable invalid actions
