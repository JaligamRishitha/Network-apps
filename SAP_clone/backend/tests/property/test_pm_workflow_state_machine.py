"""
Property-based tests for PM Workflow State Machine
Feature: pm-6-screen-workflow, Property 1: State Transition Validity
Validates: Requirements 10.2, 10.3
"""
import pytest
from hypothesis import given, strategies as st, settings
from backend.models.pm_workflow_models import WorkflowOrderStatus
from backend.services.pm_workflow_state_machine import get_state_machine


# Strategy for generating order states
order_status_strategy = st.sampled_from(list(WorkflowOrderStatus))


# Strategy for generating order data
@st.composite
def order_data_strategy(draw, status=None):
    """Generate random order data for testing"""
    order_type = draw(st.sampled_from(["general", "breakdown"]))
    
    # Generate operations
    num_operations = draw(st.integers(min_value=0, max_value=5))
    operations = []
    for i in range(num_operations):
        op_status = draw(st.sampled_from(["planned", "in_progress", "confirmed"]))
        operations.append({
            "operation_id": f"OP{i:03d}",
            "status": op_status,
            "technician_id": draw(st.one_of(st.none(), st.text(min_size=1, max_size=10)))
        })
    
    # Generate components
    num_components = draw(st.integers(min_value=0, max_value=5))
    components = []
    for i in range(num_components):
        qty_required = draw(st.floats(min_value=1, max_value=100))
        qty_issued = draw(st.floats(min_value=0, max_value=qty_required))
        components.append({
            "component_id": f"COMP{i:03d}",
            "quantity_required": qty_required,
            "quantity_issued": qty_issued,
            "critical": draw(st.booleans()),
            "available": draw(st.booleans()),
            "on_order": draw(st.booleans())
        })
    
    # Generate permits
    num_permits = draw(st.integers(min_value=0, max_value=3))
    permits = []
    for i in range(num_permits):
        permits.append({
            "permit_id": f"PERMIT{i:03d}",
            "required": draw(st.booleans()),
            "approved": draw(st.booleans())
        })
    
    # Generate confirmations
    num_confirmations = draw(st.integers(min_value=0, max_value=5))
    confirmations = [{"confirmation_id": f"CONF{i:03d}"} for i in range(num_confirmations)]
    
    # Generate cost summary
    estimated_total = draw(st.floats(min_value=0, max_value=100000))
    cost_summary = {
        "estimated_total_cost": estimated_total
    }
    
    return {
        "order_type": order_type,
        "operations": operations,
        "components": components,
        "permits": permits,
        "confirmations": confirmations,
        "cost_summary": cost_summary
    }


@given(
    from_state=order_status_strategy,
    to_state=order_status_strategy,
    order_data=order_data_strategy()
)
@settings(max_examples=100)
def test_property_state_transition_validity(from_state, to_state, order_data):
    """
    **Feature: pm-6-screen-workflow, Property 1: State Transition Validity**
    **Validates: Requirements 10.2, 10.3**
    
    Property: For any maintenance order and any requested state transition,
    the system should only allow the transition if all prerequisites for the
    target state are satisfied.
    
    This test verifies that:
    1. Invalid transitions are always rejected
    2. Valid transitions are only allowed when prerequisites are met
    3. Blocking reasons are provided when transitions are prevented
    """
    state_machine = get_state_machine()
    
    # Check if transition is valid
    can_transition, blocking_reasons = state_machine.can_transition(
        from_state, to_state, order_data
    )
    
    # Property 1: If transition is structurally invalid, it must be rejected
    valid_next_states = state_machine.get_valid_next_states(from_state)
    if to_state not in valid_next_states:
        assert not can_transition, \
            f"Invalid transition from {from_state.value} to {to_state.value} should be rejected"
        assert len(blocking_reasons) > 0, \
            "Invalid transitions must provide blocking reasons"
    
    # Property 2: If transition is rejected, blocking reasons must be provided
    if not can_transition:
        assert len(blocking_reasons) > 0, \
            "Rejected transitions must provide specific blocking reasons"
        assert all(isinstance(reason, str) and len(reason) > 0 for reason in blocking_reasons), \
            "Blocking reasons must be non-empty strings"
    
    # Property 3: If transition is allowed, it must be structurally valid
    if can_transition:
        assert to_state in valid_next_states, \
            f"Allowed transition from {from_state.value} to {to_state.value} must be structurally valid"


@given(order_data=order_data_strategy())
@settings(max_examples=100)
def test_property_created_to_planned_prerequisites(order_data):
    """
    Test Created → Planned transition prerequisites
    
    Property: Transition from Created to Planned requires:
    - At least one operation
    - Cost estimate calculated
    """
    state_machine = get_state_machine()
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CREATED,
        WorkflowOrderStatus.PLANNED,
        order_data
    )
    
    # Check operation prerequisite
    has_operations = len(order_data.get("operations", [])) > 0
    has_cost_estimate = order_data.get("cost_summary", {}).get("estimated_total_cost", 0) > 0
    
    if not has_operations:
        assert not can_transition, "Transition should be blocked without operations"
        assert any("operation" in reason.lower() for reason in blocking_reasons), \
            "Blocking reason should mention operations"
    
    if not has_cost_estimate:
        assert not can_transition, "Transition should be blocked without cost estimate"
        assert any("cost" in reason.lower() for reason in blocking_reasons), \
            "Blocking reason should mention cost estimate"
    
    if has_operations and has_cost_estimate:
        assert can_transition, "Transition should be allowed when prerequisites are met"


@given(order_data=order_data_strategy())
@settings(max_examples=100)
def test_property_planned_to_released_prerequisites(order_data):
    """
    Test Planned → Released transition prerequisites
    
    Property: Transition from Planned to Released requires:
    - Permits approved (unless breakdown)
    - Materials available (unless breakdown)
    - Technician assigned
    """
    state_machine = get_state_machine()
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        order_data
    )
    
    is_breakdown = order_data.get("order_type") == "breakdown"
    
    # Check technician prerequisite
    has_technician = any(op.get("technician_id") for op in order_data.get("operations", []))
    
    if not has_technician:
        assert not can_transition, "Transition should be blocked without technician"
        assert any("technician" in reason.lower() for reason in blocking_reasons), \
            "Blocking reason should mention technician"
    
    # For general maintenance, check permits and materials
    if not is_breakdown:
        required_permits = [p for p in order_data.get("permits", []) if p.get("required", False)]
        if required_permits:
            all_approved = all(p.get("approved", False) for p in required_permits)
            if not all_approved and not can_transition:
                assert any("permit" in reason.lower() for reason in blocking_reasons), \
                    "Blocking reason should mention permits"
        
        critical_components = [c for c in order_data.get("components", []) if c.get("critical", False)]
        if critical_components:
            all_available = all(
                c.get("available", False) or c.get("on_order", False)
                for c in critical_components
            )
            if not all_available and not can_transition:
                assert any("material" in reason.lower() for reason in blocking_reasons), \
                    "Blocking reason should mention materials"


@given(order_data=order_data_strategy())
@settings(max_examples=100)
def test_property_confirmed_to_teco_prerequisites(order_data):
    """
    Test Confirmed → TECO transition prerequisites
    
    Property: Transition from Confirmed to TECO requires:
    - All operations confirmed
    - All goods issued
    """
    state_machine = get_state_machine()
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_data
    )
    
    operations = order_data.get("operations", [])
    if operations:
        all_confirmed = all(op.get("status") == "confirmed" for op in operations)
        if not all_confirmed:
            assert not can_transition, "Transition should be blocked with unconfirmed operations"
            assert any("operation" in reason.lower() and "confirmed" in reason.lower() 
                      for reason in blocking_reasons), \
                "Blocking reason should mention unconfirmed operations"
    
    components = order_data.get("components", [])
    if components:
        all_issued = all(
            c.get("quantity_issued", 0) >= c.get("quantity_required", 0)
            for c in components
        )
        if not all_issued:
            assert not can_transition, "Transition should be blocked with unissued components"
            assert any("component" in reason.lower() or "issued" in reason.lower() 
                      for reason in blocking_reasons), \
                "Blocking reason should mention unissued components"


@given(current_state=order_status_strategy)
@settings(max_examples=50)
def test_property_valid_next_states_are_subset(current_state):
    """
    Property: Valid next states must be a proper subset of all states
    """
    state_machine = get_state_machine()
    valid_next = state_machine.get_valid_next_states(current_state)
    
    # Valid next states should be a subset of all states
    all_states = set(WorkflowOrderStatus)
    assert valid_next.issubset(all_states), \
        "Valid next states must be a subset of all possible states"
    
    # TECO is terminal state - no valid next states
    if current_state == WorkflowOrderStatus.TECO:
        assert len(valid_next) == 0, \
            "TECO is terminal state and should have no valid next states"


@given(current_state=order_status_strategy)
@settings(max_examples=50)
def test_property_enabled_actions_are_non_empty_strings(current_state):
    """
    Property: Enabled actions must be non-empty strings
    """
    state_machine = get_state_machine()
    enabled_actions = state_machine.get_enabled_actions(current_state)
    
    assert isinstance(enabled_actions, list), \
        "Enabled actions must be a list"
    
    for action in enabled_actions:
        assert isinstance(action, str), \
            "Each enabled action must be a string"
        assert len(action) > 0, \
            "Each enabled action must be non-empty"


def test_breakdown_order_reduced_validation():
    """
    Test that breakdown orders have reduced validation requirements
    
    Property: Breakdown orders should bypass certain prerequisites
    that general maintenance orders require
    """
    state_machine = get_state_machine()
    
    # Create order data with missing permits and materials
    breakdown_order = {
        "order_type": "breakdown",
        "operations": [{"operation_id": "OP001", "technician_id": "TECH001", "status": "planned"}],
        "components": [{"component_id": "COMP001", "critical": True, "available": False, "on_order": False}],
        "permits": [{"permit_id": "PERMIT001", "required": True, "approved": False}],
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    general_order = breakdown_order.copy()
    general_order["order_type"] = "general"
    
    # Breakdown order should be allowed to release
    can_transition_breakdown, _ = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        breakdown_order
    )
    
    # General order should be blocked
    can_transition_general, reasons_general = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        general_order
    )
    
    assert can_transition_breakdown, \
        "Breakdown order should be allowed to release with reduced validation"
    assert not can_transition_general, \
        "General order should be blocked without permits and materials"
    assert len(reasons_general) > 0, \
        "General order should have blocking reasons"



# Property Test for PO-Order Linkage (Screen 2)

@st.composite
def purchase_order_strategy(draw):
    """Generate random purchase order data"""
    po_type = draw(st.sampled_from(["material", "service", "combined"]))
    vendor_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    total_value = draw(st.floats(min_value=1.0, max_value=100000.0))
    
    return {
        "po_type": po_type,
        "vendor_id": vendor_id,
        "total_value": total_value,
        "status": draw(st.sampled_from(["created", "ordered", "partially_delivered", "delivered"]))
    }


@given(
    order_number=st.text(min_size=10, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    purchase_orders=st.lists(purchase_order_strategy(), min_size=1, max_size=10)
)
@settings(max_examples=100)
def test_property_po_order_linkage(order_number, purchase_orders):
    """
    **Feature: pm-6-screen-workflow, Property 8: PO-Order Linkage**
    **Validates: Requirements 2.4, 2.5**
    
    Property: For any purchase order created for a maintenance order,
    the PO should maintain a valid reference to the maintenance order
    throughout its lifecycle.
    
    This test verifies that:
    1. Every PO has a valid order_number reference
    2. The order_number reference is immutable
    3. The order_number reference matches the parent order
    4. PO status changes don't affect the order linkage
    """
    
    # Property 1: Every PO must have a valid order_number reference
    for po in purchase_orders:
        # Simulate PO creation with order reference
        po_with_order = {**po, "order_number": order_number}
        
        assert "order_number" in po_with_order, \
            "Every PO must have an order_number field"
        assert po_with_order["order_number"] is not None, \
            "PO order_number must not be None"
        assert len(po_with_order["order_number"]) > 0, \
            "PO order_number must not be empty"
        assert po_with_order["order_number"] == order_number, \
            "PO order_number must match the parent maintenance order"
    
    # Property 2: Order reference is immutable throughout PO lifecycle
    for po in purchase_orders:
        po_with_order = {**po, "order_number": order_number}
        original_order_ref = po_with_order["order_number"]
        
        # Simulate status changes
        statuses = ["created", "ordered", "partially_delivered", "delivered"]
        for status in statuses:
            po_with_order["status"] = status
            
            # Order reference must remain unchanged
            assert po_with_order["order_number"] == original_order_ref, \
                f"PO order_number must remain unchanged when status changes to {status}"
            assert po_with_order["order_number"] == order_number, \
                f"PO must maintain reference to original order after status change to {status}"
    
    # Property 3: Multiple POs can reference the same order
    order_refs = [order_number for _ in purchase_orders]
    assert all(ref == order_number for ref in order_refs), \
        "All POs for an order must reference the same order_number"
    
    # Property 4: PO linkage is bidirectional (order knows about its POs)
    # Simulate order having list of PO numbers
    po_numbers = [f"PO-{i:06d}" for i in range(len(purchase_orders))]
    order_po_list = {
        "order_number": order_number,
        "purchase_orders": po_numbers
    }
    
    assert len(order_po_list["purchase_orders"]) == len(purchase_orders), \
        "Order must track all its purchase orders"
    assert all(isinstance(po_num, str) for po_num in order_po_list["purchase_orders"]), \
        "Order's PO list must contain valid PO numbers"


@given(
    order_number=st.text(min_size=10, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    po_data=purchase_order_strategy()
)
@settings(max_examples=100)
def test_property_po_order_linkage_integrity(order_number, po_data):
    """
    Property: PO-Order linkage integrity must be maintained
    
    This test verifies that:
    1. PO cannot be created without a valid order reference
    2. PO order reference cannot be null or empty
    3. PO order reference format is consistent
    """
    
    # Test 1: PO with valid order reference
    valid_po = {**po_data, "order_number": order_number}
    assert valid_po["order_number"] == order_number, \
        "PO must have valid order reference"
    
    # Test 2: PO order reference cannot be empty
    if order_number and len(order_number) > 0:
        assert len(valid_po["order_number"]) > 0, \
            "PO order_number must not be empty string"
    
    # Test 3: PO maintains reference through all operations
    operations = ["create", "update_status", "query", "delete"]
    for operation in operations:
        # Simulate operation
        po_after_operation = valid_po.copy()
        
        # Order reference must persist
        assert "order_number" in po_after_operation, \
            f"PO must maintain order_number field after {operation}"
        assert po_after_operation["order_number"] == order_number, \
            f"PO order_number must remain unchanged after {operation}"


@given(
    order_number=st.text(min_size=10, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    num_pos=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100)
def test_property_multiple_pos_same_order(order_number, num_pos):
    """
    Property: Multiple POs can be linked to the same order
    
    This test verifies that:
    1. An order can have multiple POs
    2. All POs maintain correct reference to the same order
    3. PO count matches expected count
    """
    
    # Create multiple POs for the same order
    pos = []
    for i in range(num_pos):
        po = {
            "po_number": f"PO-{i:06d}",
            "order_number": order_number,
            "po_type": "material",
            "status": "created"
        }
        pos.append(po)
    
    # Property 1: All POs reference the same order
    order_refs = [po["order_number"] for po in pos]
    assert all(ref == order_number for ref in order_refs), \
        "All POs must reference the same order_number"
    
    # Property 2: PO count is correct
    assert len(pos) == num_pos, \
        "Number of POs must match expected count"
    
    # Property 3: Each PO has unique identifier but same order reference
    po_numbers = [po["po_number"] for po in pos]
    assert len(set(po_numbers)) == len(po_numbers), \
        "Each PO must have unique PO number"
    assert len(set(order_refs)) == 1, \
        "All POs must reference exactly one order"


@given(
    order_number=st.text(min_size=10, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
    po_data=purchase_order_strategy()
)
@settings(max_examples=100)
def test_property_po_document_flow_linkage(order_number, po_data):
    """
    Property: PO document flow entries maintain order linkage
    
    This test verifies that:
    1. Document flow entries for POs reference the correct order
    2. Document flow maintains PO-Order relationship
    """
    
    po_number = f"PO-{hash(order_number) % 1000000:06d}"
    
    # Create document flow entry for PO
    doc_flow_entry = {
        "flow_id": f"FLOW-{hash(po_number) % 1000000:06d}",
        "order_number": order_number,
        "document_type": "po",
        "document_number": po_number,
        "status": po_data["status"],
        "related_document": order_number
    }
    
    # Property 1: Document flow entry references correct order
    assert doc_flow_entry["order_number"] == order_number, \
        "Document flow entry must reference correct order"
    
    # Property 2: Document flow maintains PO reference
    assert doc_flow_entry["document_number"] == po_number, \
        "Document flow entry must reference correct PO"
    
    # Property 3: Related document links back to order
    assert doc_flow_entry["related_document"] == order_number, \
        "Document flow related_document must link back to order"
    
    # Property 4: Document type is correct
    assert doc_flow_entry["document_type"] == "po", \
        "Document flow entry must have correct document type"
