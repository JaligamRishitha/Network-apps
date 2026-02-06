"""
Property-based tests for ticket creation validity and state machine.
**Feature: sap-erp-demo, Property 1: Ticket Creation Validity**
**Feature: sap-erp-demo, Property 2: Ticket State Machine Enforcement**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
"""
import re
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

from backend.models.ticket_models import Module, Priority, TicketType, TicketStatus
from backend.services.ticket_utils import (
    generate_ticket_id,
    validate_ticket_id,
    calculate_sla_deadline,
    is_valid_ticket_type,
    create_ticket_data,
    SLA_HOURS,
    TICKET_ID_PATTERN,
)
from backend.services.ticket_service import (
    is_valid_transition,
    VALID_TRANSITIONS,
)


# Strategies for generating test data
module_strategy = st.sampled_from(list(Module))
priority_strategy = st.sampled_from(list(Priority))
ticket_type_strategy = st.sampled_from(list(TicketType))
sequence_strategy = st.integers(min_value=1, max_value=9999)
date_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31)
)
title_strategy = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
user_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(
    module=module_strategy,
    date=date_strategy,
    sequence=sequence_strategy
)
def test_ticket_id_format_validity(module: Module, date: datetime, sequence: int):
    """
    **Feature: sap-erp-demo, Property 1: Ticket Creation Validity**
    **Validates: Requirements 1.1**
    
    Property: For any valid module, date, and sequence, the generated ticket ID
    SHALL match the format TKT-{MODULE}-{YYYYMMDD}-{SEQUENCE}
    """
    ticket_id = generate_ticket_id(module, date, sequence)
    
    # Verify format matches pattern
    assert TICKET_ID_PATTERN.match(ticket_id), f"Ticket ID '{ticket_id}' does not match expected pattern"
    
    # Verify components
    parts = ticket_id.split("-")
    assert len(parts) == 4, f"Expected 4 parts, got {len(parts)}"
    assert parts[0] == "TKT", f"Expected 'TKT' prefix, got '{parts[0]}'"
    assert parts[1] == module.value, f"Expected module '{module.value}', got '{parts[1]}'"
    assert parts[2] == date.strftime("%Y%m%d"), f"Expected date '{date.strftime('%Y%m%d')}', got '{parts[2]}'"
    assert parts[3] == f"{sequence:04d}", f"Expected sequence '{sequence:04d}', got '{parts[3]}'"


@settings(max_examples=100)
@given(
    module=module_strategy,
    date=date_strategy,
    sequence=sequence_strategy
)
def test_ticket_id_validation_roundtrip(module: Module, date: datetime, sequence: int):
    """
    **Feature: sap-erp-demo, Property 1: Ticket Creation Validity**
    **Validates: Requirements 1.1**
    
    Property: For any generated ticket ID, validation SHALL return True
    """
    ticket_id = generate_ticket_id(module, date, sequence)
    is_valid, error = validate_ticket_id(ticket_id)
    
    assert is_valid, f"Generated ticket ID '{ticket_id}' failed validation: {error}"
    assert error == "", f"Expected empty error message, got '{error}'"


@settings(max_examples=100)
@given(ticket_type=ticket_type_strategy)
def test_ticket_type_validity(ticket_type: TicketType):
    """
    **Feature: sap-erp-demo, Property 1: Ticket Creation Validity**
    **Validates: Requirements 1.2**
    
    Property: For any ticket type from the set {Incident, Maintenance, Procurement, Finance_Approval},
    the type SHALL be valid
    """
    assert is_valid_ticket_type(ticket_type), f"Ticket type '{ticket_type}' should be valid"
    
    # Verify it's one of the expected values
    valid_types = {"Incident", "Maintenance", "Procurement", "Finance_Approval"}
    assert ticket_type.value in valid_types, f"Ticket type '{ticket_type.value}' not in expected set"


@settings(max_examples=100)
@given(
    priority=priority_strategy,
    created_at=date_strategy
)
def test_sla_deadline_calculation(priority: Priority, created_at: datetime):
    """
    **Feature: sap-erp-demo, Property 1: Ticket Creation Validity**
    **Validates: Requirements 1.3**
    
    Property: For any priority level, the SLA deadline SHALL be calculated correctly:
    P1: +4 hours, P2: +8 hours, P3: +24 hours, P4: +72 hours
    """
    sla_deadline = calculate_sla_deadline(priority, created_at)
    expected_hours = SLA_HOURS[priority]
    expected_deadline = created_at + timedelta(hours=expected_hours)
    
    assert sla_deadline == expected_deadline, (
        f"SLA deadline mismatch for {priority}: "
        f"expected {expected_deadline}, got {sla_deadline}"
    )


@settings(max_examples=100)
@given(
    module=module_strategy,
    ticket_type=ticket_type_strategy,
    priority=priority_strategy,
    title=title_strategy,
    created_by=user_strategy,
    sequence=sequence_strategy,
    created_at=date_strategy
)
def test_complete_ticket_creation(
    module: Module,
    ticket_type: TicketType,
    priority: Priority,
    title: str,
    created_by: str,
    sequence: int,
    created_at: datetime
):
    """
    **Feature: sap-erp-demo, Property 1: Ticket Creation Validity**
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    Property: For any valid ticket creation request, the generated ticket SHALL have:
    - A unique Ticket_ID matching the format TKT-{MODULE}-{YYYYMMDD}-{SEQUENCE}
    - A valid ticket_type from the set {Incident, Maintenance, Procurement, Finance_Approval}
    - An SLA deadline calculated correctly based on priority
    """
    ticket_data = create_ticket_data(
        module=module,
        ticket_type=ticket_type,
        priority=priority,
        title=title,
        created_by=created_by,
        sequence=sequence,
        created_at=created_at
    )
    
    # Verify ticket ID format (Requirement 1.1)
    is_valid, error = validate_ticket_id(ticket_data["ticket_id"])
    assert is_valid, f"Invalid ticket ID: {error}"
    
    # Verify ticket type (Requirement 1.2)
    assert is_valid_ticket_type(ticket_data["ticket_type"]), "Invalid ticket type"
    
    # Verify SLA deadline (Requirement 1.3)
    expected_deadline = calculate_sla_deadline(priority, created_at)
    assert ticket_data["sla_deadline"] == expected_deadline, "SLA deadline mismatch"
    
    # Verify initial status is Open
    assert ticket_data["status"] == TicketStatus.OPEN, "Initial status should be Open"
    
    # Verify all required fields are present
    required_fields = [
        "ticket_id", "ticket_type", "module", "priority", 
        "status", "title", "sla_deadline", "created_at", "created_by"
    ]
    for field in required_fields:
        assert field in ticket_data, f"Missing required field: {field}"



# Strategies for state machine tests
status_strategy = st.sampled_from(list(TicketStatus))


@settings(max_examples=100)
@given(
    current_status=status_strategy,
    target_status=status_strategy
)
def test_state_machine_valid_transitions(current_status: TicketStatus, target_status: TicketStatus):
    """
    **Feature: sap-erp-demo, Property 2: Ticket State Machine Enforcement**
    **Validates: Requirements 1.4, 1.5**
    
    Property: For any ticket and any attempted status transition, the system SHALL:
    - Accept transitions following the valid path: Open → Assigned → In_Progress → Closed
    - Reject any transition that violates this sequence
    """
    is_valid = is_valid_transition(current_status, target_status)
    
    # Define the expected valid transitions
    expected_valid = {
        (TicketStatus.OPEN, TicketStatus.ASSIGNED): True,
        (TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS): True,
        (TicketStatus.IN_PROGRESS, TicketStatus.CLOSED): True,
    }
    
    expected = expected_valid.get((current_status, target_status), False)
    
    assert is_valid == expected, (
        f"Transition from {current_status.value} to {target_status.value}: "
        f"expected {expected}, got {is_valid}"
    )


@settings(max_examples=100)
@given(current_status=status_strategy)
def test_state_machine_no_backward_transitions(current_status: TicketStatus):
    """
    **Feature: sap-erp-demo, Property 2: Ticket State Machine Enforcement**
    **Validates: Requirements 1.5**
    
    Property: For any ticket status, backward transitions SHALL be rejected.
    The valid path is strictly forward: Open → Assigned → In_Progress → Closed
    """
    status_order = [TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED]
    current_index = status_order.index(current_status)
    
    # Check that all backward transitions are invalid
    for i in range(current_index):
        backward_status = status_order[i]
        assert not is_valid_transition(current_status, backward_status), (
            f"Backward transition from {current_status.value} to {backward_status.value} "
            f"should be invalid"
        )


@settings(max_examples=100)
@given(current_status=status_strategy)
def test_state_machine_no_skip_transitions(current_status: TicketStatus):
    """
    **Feature: sap-erp-demo, Property 2: Ticket State Machine Enforcement**
    **Validates: Requirements 1.5**
    
    Property: For any ticket status, skipping states SHALL be rejected.
    E.g., Open → In_Progress is invalid (must go through Assigned)
    """
    status_order = [TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED]
    current_index = status_order.index(current_status)
    
    # Check that skipping states is invalid (jumping more than 1 step)
    for i in range(current_index + 2, len(status_order)):
        skip_status = status_order[i]
        assert not is_valid_transition(current_status, skip_status), (
            f"Skip transition from {current_status.value} to {skip_status.value} "
            f"should be invalid"
        )


@settings(max_examples=100)
@given(current_status=status_strategy)
def test_closed_status_is_terminal(current_status: TicketStatus):
    """
    **Feature: sap-erp-demo, Property 2: Ticket State Machine Enforcement**
    **Validates: Requirements 1.5**
    
    Property: Once a ticket is Closed, no further transitions SHALL be allowed.
    """
    if current_status == TicketStatus.CLOSED:
        for target_status in TicketStatus:
            assert not is_valid_transition(TicketStatus.CLOSED, target_status), (
                f"Transition from Closed to {target_status.value} should be invalid"
            )
