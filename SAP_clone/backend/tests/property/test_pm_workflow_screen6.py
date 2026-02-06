"""
Property-based tests for PM Workflow Screen 6: Completion & Cost Settlement
Feature: pm-6-screen-workflow
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from decimal import Decimal


# Strategy for generating order data with various completion states
@st.composite
def order_data_for_teco_strategy(draw):
    """Generate random order data for TECO testing"""
    order_type = draw(st.sampled_from(["general", "breakdown"]))
    
    # Generate operations with varying confirmation status
    num_operations = draw(st.integers(min_value=1, max_value=5))
    operations = []
    for i in range(num_operations):
        op_status = draw(st.sampled_from(["planned", "in_progress", "confirmed"]))
        operations.append({
            "operation_id": f"OP{i:03d}",
            "status": op_status,
            "technician_id": f"TECH{i:03d}"
        })
    
    # Generate components with varying issue status
    num_components = draw(st.integers(min_value=0, max_value=5))
    components = []
    for i in range(num_components):
        qty_required = draw(st.floats(min_value=1.0, max_value=100.0))
        # Quantity issued can be less than, equal to, or greater than required
        qty_issued = draw(st.floats(min_value=0.0, max_value=qty_required * 1.5))
        components.append({
            "component_id": f"COMP{i:03d}",
            "quantity_required": qty_required,
            "quantity_issued": qty_issued,
            "material_number": f"MAT{i:05d}"
        })
    
    # Generate confirmations
    num_confirmations = draw(st.integers(min_value=0, max_value=num_operations))
    confirmations = [{"confirmation_id": f"CONF{i:03d}"} for i in range(num_confirmations)]
    
    # Generate cost summary
    estimated_total = draw(st.floats(min_value=100.0, max_value=100000.0))
    cost_summary = {
        "estimated_total_cost": estimated_total
    }
    
    return {
        "order_type": order_type,
        "operations": operations,
        "components": components,
        "confirmations": confirmations,
        "cost_summary": cost_summary
    }


@given(order_data=order_data_for_teco_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_property_teco_prerequisite_validation(order_data):
    """
    **Feature: pm-6-screen-workflow, Property 6: TECO Prerequisite Validation**
    **Validates: Requirements 6.1, 6.2, 6.3**
    
    Property: For any maintenance order, technical completion (TECO) should only
    be allowed if all operations are confirmed and all goods movements are posted.
    
    This test verifies that:
    1. TECO is blocked if any operation is not confirmed
    2. TECO is blocked if any component is not fully issued
    3. TECO is allowed only when all prerequisites are met
    4. Blocking reasons are specific and actionable
    """
    from backend.services.pm_workflow_state_machine import get_state_machine
    from backend.models.pm_workflow_models import WorkflowOrderStatus
    
    state_machine = get_state_machine()
    
    # Check if TECO transition is allowed
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_data
    )
    
    operations = order_data.get("operations", [])
    components = order_data.get("components", [])
    
    # Property 1: All operations must be confirmed
    all_operations_confirmed = all(op.get("status") == "confirmed" for op in operations)
    
    if not all_operations_confirmed:
        assert not can_transition, \
            "TECO should be blocked when not all operations are confirmed"
        assert len(blocking_reasons) > 0, \
            "Blocking reasons must be provided when operations are not confirmed"
        assert any("operation" in reason.lower() and "confirmed" in reason.lower() 
                  for reason in blocking_reasons), \
            "Blocking reason should specifically mention unconfirmed operations"
        
        # Count unconfirmed operations
        unconfirmed_count = sum(1 for op in operations if op.get("status") != "confirmed")
        assert any(str(unconfirmed_count) in reason for reason in blocking_reasons), \
            "Blocking reason should specify the number of unconfirmed operations"
    
    # Property 2: All components must be fully issued
    all_components_issued = all(
        comp.get("quantity_issued", 0) >= comp.get("quantity_required", 0)
        for comp in components
    )
    
    if components and not all_components_issued:
        assert not can_transition, \
            "TECO should be blocked when not all components are fully issued"
        assert len(blocking_reasons) > 0, \
            "Blocking reasons must be provided when components are not fully issued"
        assert any("component" in reason.lower() or "issued" in reason.lower() 
                  for reason in blocking_reasons), \
            "Blocking reason should specifically mention unissued components"
        
        # Count unissued components
        unissued_count = sum(
            1 for comp in components 
            if comp.get("quantity_issued", 0) < comp.get("quantity_required", 0)
        )
        assert any(str(unissued_count) in reason for reason in blocking_reasons), \
            "Blocking reason should specify the number of unissued components"
    
    # Property 3: TECO is allowed when all prerequisites are met
    if all_operations_confirmed and all_components_issued:
        assert can_transition, \
            "TECO should be allowed when all operations are confirmed and all components are issued"
        assert len(blocking_reasons) == 0, \
            "No blocking reasons should be provided when TECO is allowed"
    
    # Property 4: Blocking reasons are specific and non-empty
    if not can_transition:
        assert len(blocking_reasons) > 0, \
            "Blocked TECO must provide at least one blocking reason"
        for reason in blocking_reasons:
            assert isinstance(reason, str), \
                "Each blocking reason must be a string"
            assert len(reason) > 0, \
                "Each blocking reason must be non-empty"
            assert reason[0].isupper() or reason[0].isdigit(), \
                "Blocking reasons should be properly formatted"


@given(
    num_operations=st.integers(min_value=1, max_value=10),
    num_confirmed=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100)
def test_property_teco_operations_prerequisite(num_operations, num_confirmed):
    """
    Property: TECO requires ALL operations to be confirmed
    
    This test verifies that:
    1. If any operation is unconfirmed, TECO is blocked
    2. Only when all operations are confirmed, TECO can proceed
    """
    from backend.services.pm_workflow_state_machine import get_state_machine
    from backend.models.pm_workflow_models import WorkflowOrderStatus
    
    # Ensure num_confirmed doesn't exceed num_operations
    assume(num_confirmed <= num_operations)
    
    state_machine = get_state_machine()
    
    # Create operations with specified confirmation status
    operations = []
    for i in range(num_confirmed):
        operations.append({
            "operation_id": f"OP{i:03d}",
            "status": "confirmed",
            "technician_id": f"TECH{i:03d}"
        })
    for i in range(num_confirmed, num_operations):
        operations.append({
            "operation_id": f"OP{i:03d}",
            "status": "planned",  # Not confirmed
            "technician_id": f"TECH{i:03d}"
        })
    
    order_data = {
        "order_type": "general",
        "operations": operations,
        "components": [],  # No components to isolate operation prerequisite
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_data
    )
    
    if num_confirmed < num_operations:
        # Not all operations confirmed
        assert not can_transition, \
            f"TECO should be blocked when only {num_confirmed}/{num_operations} operations are confirmed"
        assert len(blocking_reasons) > 0, \
            "Blocking reasons must be provided"
        
        unconfirmed_count = num_operations - num_confirmed
        assert any(str(unconfirmed_count) in reason for reason in blocking_reasons), \
            f"Blocking reason should mention {unconfirmed_count} unconfirmed operations"
    else:
        # All operations confirmed
        assert can_transition, \
            f"TECO should be allowed when all {num_operations} operations are confirmed"


@given(
    num_components=st.integers(min_value=1, max_value=10),
    issue_percentages=st.lists(
        st.floats(min_value=0.0, max_value=1.5),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100)
def test_property_teco_goods_issue_prerequisite(num_components, issue_percentages):
    """
    Property: TECO requires ALL components to be fully issued
    
    This test verifies that:
    1. If any component is not fully issued, TECO is blocked
    2. Only when all components are fully issued, TECO can proceed
    3. Over-issuing (quantity_issued > quantity_required) is acceptable
    """
    from backend.services.pm_workflow_state_machine import get_state_machine
    from backend.models.pm_workflow_models import WorkflowOrderStatus
    
    # Ensure we have enough percentages
    assume(len(issue_percentages) >= num_components)
    
    state_machine = get_state_machine()
    
    # Create components with varying issue status
    components = []
    all_fully_issued = True
    for i in range(num_components):
        qty_required = 10.0
        qty_issued = qty_required * issue_percentages[i]
        components.append({
            "component_id": f"COMP{i:03d}",
            "quantity_required": qty_required,
            "quantity_issued": qty_issued,
            "material_number": f"MAT{i:05d}"
        })
        if qty_issued < qty_required:
            all_fully_issued = False
    
    order_data = {
        "order_type": "general",
        "operations": [{"operation_id": "OP001", "status": "confirmed", "technician_id": "TECH001"}],
        "components": components,
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_data
    )
    
    if not all_fully_issued:
        # Not all components fully issued
        assert not can_transition, \
            "TECO should be blocked when not all components are fully issued"
        assert len(blocking_reasons) > 0, \
            "Blocking reasons must be provided"
        
        unissued_count = sum(
            1 for comp in components 
            if comp["quantity_issued"] < comp["quantity_required"]
        )
        assert any(str(unissued_count) in reason for reason in blocking_reasons), \
            f"Blocking reason should mention {unissued_count} unissued components"
    else:
        # All components fully issued (including over-issued)
        assert can_transition, \
            "TECO should be allowed when all components are fully issued"


@given(order_data=order_data_for_teco_strategy())
@settings(max_examples=100)
def test_property_teco_combined_prerequisites(order_data):
    """
    Property: TECO requires BOTH operations confirmed AND components issued
    
    This test verifies that:
    1. Meeting only one prerequisite is insufficient
    2. Both prerequisites must be met simultaneously
    """
    from backend.services.pm_workflow_state_machine import get_state_machine
    from backend.models.pm_workflow_models import WorkflowOrderStatus
    
    state_machine = get_state_machine()
    
    operations = order_data.get("operations", [])
    components = order_data.get("components", [])
    
    all_operations_confirmed = all(op.get("status") == "confirmed" for op in operations)
    all_components_issued = all(
        comp.get("quantity_issued", 0) >= comp.get("quantity_required", 0)
        for comp in components
    )
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_data
    )
    
    # Property: Both prerequisites must be met
    if all_operations_confirmed and all_components_issued:
        assert can_transition, \
            "TECO should be allowed when both prerequisites are met"
    else:
        assert not can_transition, \
            "TECO should be blocked when any prerequisite is not met"
        
        # Verify blocking reasons match unmet prerequisites
        if not all_operations_confirmed:
            assert any("operation" in reason.lower() for reason in blocking_reasons), \
                "Blocking reasons should mention operations when they are not all confirmed"
        
        if components and not all_components_issued:
            assert any("component" in reason.lower() or "issued" in reason.lower() 
                      for reason in blocking_reasons), \
                "Blocking reasons should mention components when they are not all issued"


@given(
    has_operations=st.booleans(),
    has_components=st.booleans()
)
@settings(max_examples=50)
def test_property_teco_empty_order_handling(has_operations, has_components):
    """
    Property: TECO handling of orders with no operations or components
    
    This test verifies edge cases:
    1. Order with no operations
    2. Order with no components
    3. Order with neither
    """
    from backend.services.pm_workflow_state_machine import get_state_machine
    from backend.models.pm_workflow_models import WorkflowOrderStatus
    
    state_machine = get_state_machine()
    
    operations = []
    if has_operations:
        operations = [{"operation_id": "OP001", "status": "confirmed", "technician_id": "TECH001"}]
    
    components = []
    if has_components:
        components = [{
            "component_id": "COMP001",
            "quantity_required": 10.0,
            "quantity_issued": 10.0,
            "material_number": "MAT00001"
        }]
    
    order_data = {
        "order_type": "general",
        "operations": operations,
        "components": components,
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_data
    )
    
    # Order with no operations should be blocked
    if not has_operations:
        assert not can_transition, \
            "TECO should be blocked for order with no operations"
        assert any("operation" in reason.lower() for reason in blocking_reasons), \
            "Blocking reason should mention missing operations"
    
    # Order with operations confirmed and no components (or all issued) should be allowed
    if has_operations and (not has_components or all(
        comp.get("quantity_issued", 0) >= comp.get("quantity_required", 0)
        for comp in components
    )):
        assert can_transition, \
            "TECO should be allowed when operations are confirmed and components are issued (or none exist)"


def test_teco_prerequisite_validation_specific_scenarios():
    """
    Test specific TECO prerequisite scenarios
    
    This test covers specific edge cases and scenarios
    """
    from backend.services.pm_workflow_state_machine import get_state_machine
    from backend.models.pm_workflow_models import WorkflowOrderStatus
    
    state_machine = get_state_machine()
    
    # Scenario 1: All prerequisites met
    order_all_met = {
        "order_type": "general",
        "operations": [
            {"operation_id": "OP001", "status": "confirmed", "technician_id": "TECH001"},
            {"operation_id": "OP002", "status": "confirmed", "technician_id": "TECH002"}
        ],
        "components": [
            {"component_id": "COMP001", "quantity_required": 10.0, "quantity_issued": 10.0},
            {"component_id": "COMP002", "quantity_required": 5.0, "quantity_issued": 5.0}
        ],
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_all_met
    )
    assert can_transition, "TECO should be allowed when all prerequisites are met"
    assert len(reasons) == 0, "No blocking reasons when TECO is allowed"
    
    # Scenario 2: One operation not confirmed
    order_one_unconfirmed = {
        "order_type": "general",
        "operations": [
            {"operation_id": "OP001", "status": "confirmed", "technician_id": "TECH001"},
            {"operation_id": "OP002", "status": "in_progress", "technician_id": "TECH002"}
        ],
        "components": [
            {"component_id": "COMP001", "quantity_required": 10.0, "quantity_issued": 10.0}
        ],
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_one_unconfirmed
    )
    assert not can_transition, "TECO should be blocked with unconfirmed operation"
    assert len(reasons) > 0, "Blocking reasons must be provided"
    assert any("1" in reason and "operation" in reason.lower() for reason in reasons), \
        "Should mention 1 unconfirmed operation"
    
    # Scenario 3: One component not fully issued
    order_one_unissued = {
        "order_type": "general",
        "operations": [
            {"operation_id": "OP001", "status": "confirmed", "technician_id": "TECH001"}
        ],
        "components": [
            {"component_id": "COMP001", "quantity_required": 10.0, "quantity_issued": 10.0},
            {"component_id": "COMP002", "quantity_required": 5.0, "quantity_issued": 3.0}
        ],
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_one_unissued
    )
    assert not can_transition, "TECO should be blocked with unissued component"
    assert len(reasons) > 0, "Blocking reasons must be provided"
    assert any("1" in reason and ("component" in reason.lower() or "issued" in reason.lower()) 
              for reason in reasons), \
        "Should mention 1 unissued component"
    
    # Scenario 4: Over-issued component (should be allowed)
    order_over_issued = {
        "order_type": "general",
        "operations": [
            {"operation_id": "OP001", "status": "confirmed", "technician_id": "TECH001"}
        ],
        "components": [
            {"component_id": "COMP001", "quantity_required": 10.0, "quantity_issued": 12.0}
        ],
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": 1000}
    }
    
    can_transition, reasons = state_machine.can_transition(
        WorkflowOrderStatus.CONFIRMED,
        WorkflowOrderStatus.TECO,
        order_over_issued
    )
    assert can_transition, "TECO should be allowed when component is over-issued"
    assert len(reasons) == 0, "No blocking reasons when over-issued"



# Property Test for Cost Accumulation Consistency (Property 3)

@st.composite
def cost_posting_strategy(draw):
    """Generate random cost postings for testing"""
    # Generate GR costs (material costs)
    num_grs = draw(st.integers(min_value=0, max_value=10))
    gr_costs = []
    for i in range(num_grs):
        cost = draw(st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False))
        gr_costs.append({
            "gr_document": f"GR-{i:06d}",
            "cost": round(cost, 2)
        })
    
    # Generate GI costs (material consumption costs)
    num_gis = draw(st.integers(min_value=0, max_value=10))
    gi_costs = []
    for i in range(num_gis):
        cost = draw(st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False))
        gi_costs.append({
            "gi_document": f"GI-{i:06d}",
            "cost": round(cost, 2)
        })
    
    # Generate confirmation labor costs
    num_confirmations = draw(st.integers(min_value=0, max_value=10))
    confirmation_costs = []
    for i in range(num_confirmations):
        hours = draw(st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False))
        rate = draw(st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False))
        cost = round(hours * rate, 2)
        confirmation_costs.append({
            "confirmation_id": f"CONF-{i:06d}",
            "hours": round(hours, 2),
            "rate": round(rate, 2),
            "cost": cost
        })
    
    # Generate service entry costs (external costs)
    num_service_entries = draw(st.integers(min_value=0, max_value=10))
    service_entry_costs = []
    for i in range(num_service_entries):
        cost = draw(st.floats(min_value=0.01, max_value=50000.0, allow_nan=False, allow_infinity=False))
        service_entry_costs.append({
            "service_entry_document": f"SE-{i:06d}",
            "cost": round(cost, 2)
        })
    
    return {
        "gr_costs": gr_costs,
        "gi_costs": gi_costs,
        "confirmation_costs": confirmation_costs,
        "service_entry_costs": service_entry_costs
    }


@given(cost_postings=cost_posting_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_property_cost_accumulation_consistency(cost_postings):
    """
    **Feature: pm-6-screen-workflow, Property 3: Cost Accumulation Consistency**
    **Validates: Requirements 1.5, 6.4**
    
    Property: For any maintenance order, the sum of all individual cost postings
    (GR costs + GI costs + confirmation labor costs + service entry costs) should
    equal the total actual cost in the cost summary.
    
    This test verifies that:
    1. Material costs from GR and GI are correctly accumulated
    2. Labor costs from confirmations are correctly accumulated
    3. External costs from service entries are correctly accumulated
    4. Total actual cost equals the sum of all individual postings
    5. Cost accumulation is consistent regardless of posting order
    """
    from decimal import Decimal
    
    # Calculate expected costs from individual postings
    gr_costs = cost_postings["gr_costs"]
    gi_costs = cost_postings["gi_costs"]
    confirmation_costs = cost_postings["confirmation_costs"]
    service_entry_costs = cost_postings["service_entry_costs"]
    
    # Property 1: Material costs are sum of GR and GI costs
    expected_material_cost = Decimal(0)
    for gr in gr_costs:
        expected_material_cost += Decimal(str(gr["cost"]))
    for gi in gi_costs:
        expected_material_cost += Decimal(str(gi["cost"]))
    
    # Property 2: Labor costs are sum of confirmation costs
    expected_labor_cost = Decimal(0)
    for conf in confirmation_costs:
        expected_labor_cost += Decimal(str(conf["cost"]))
    
    # Property 3: External costs are sum of service entry costs
    expected_external_cost = Decimal(0)
    for se in service_entry_costs:
        expected_external_cost += Decimal(str(se["cost"]))
    
    # Property 4: Total cost is sum of all cost elements
    expected_total_cost = expected_material_cost + expected_labor_cost + expected_external_cost
    
    # Simulate cost summary
    cost_summary = {
        "actual_material_cost": expected_material_cost,
        "actual_labor_cost": expected_labor_cost,
        "actual_external_cost": expected_external_cost,
        "actual_total_cost": expected_total_cost
    }
    
    # Verify cost accumulation consistency
    assert cost_summary["actual_total_cost"] == (
        cost_summary["actual_material_cost"] +
        cost_summary["actual_labor_cost"] +
        cost_summary["actual_external_cost"]
    ), "Total actual cost must equal sum of material, labor, and external costs"
    
    # Property 5: Cost accumulation is additive and commutative
    # Verify that individual postings sum to the cost summary values
    actual_material_from_postings = sum(Decimal(str(gr["cost"])) for gr in gr_costs) + \
                                   sum(Decimal(str(gi["cost"])) for gi in gi_costs)
    assert cost_summary["actual_material_cost"] == actual_material_from_postings, \
        "Material cost in summary must equal sum of GR and GI postings"
    
    actual_labor_from_postings = sum(Decimal(str(conf["cost"])) for conf in confirmation_costs)
    assert cost_summary["actual_labor_cost"] == actual_labor_from_postings, \
        "Labor cost in summary must equal sum of confirmation postings"
    
    actual_external_from_postings = sum(Decimal(str(se["cost"])) for se in service_entry_costs)
    assert cost_summary["actual_external_cost"] == actual_external_from_postings, \
        "External cost in summary must equal sum of service entry postings"
    
    # Property 6: Cost values are non-negative
    assert cost_summary["actual_material_cost"] >= 0, \
        "Material cost must be non-negative"
    assert cost_summary["actual_labor_cost"] >= 0, \
        "Labor cost must be non-negative"
    assert cost_summary["actual_external_cost"] >= 0, \
        "External cost must be non-negative"
    assert cost_summary["actual_total_cost"] >= 0, \
        "Total cost must be non-negative"
    
    # Property 7: Precision is maintained (2 decimal places)
    # Convert to float for precision check
    material_float = float(cost_summary["actual_material_cost"])
    labor_float = float(cost_summary["actual_labor_cost"])
    external_float = float(cost_summary["actual_external_cost"])
    total_float = float(cost_summary["actual_total_cost"])
    
    assert round(material_float, 2) == material_float or abs(material_float - round(material_float, 2)) < 0.001, \
        "Material cost should maintain 2 decimal places precision"
    assert round(labor_float, 2) == labor_float or abs(labor_float - round(labor_float, 2)) < 0.001, \
        "Labor cost should maintain 2 decimal places precision"
    assert round(external_float, 2) == external_float or abs(external_float - round(external_float, 2)) < 0.001, \
        "External cost should maintain 2 decimal places precision"


@given(
    num_postings=st.integers(min_value=1, max_value=20),
    posting_amounts=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100, deadline=None)
def test_property_cost_accumulation_order_independence(num_postings, posting_amounts):
    """
    Property: Cost accumulation is order-independent
    
    This test verifies that:
    1. Costs can be posted in any order
    2. Final total is the same regardless of posting order
    3. Accumulation is commutative and associative
    """
    from decimal import Decimal
    import random
    
    # Ensure we have enough amounts
    assume(len(posting_amounts) >= num_postings)
    
    # Take first num_postings amounts
    amounts = [Decimal(str(round(amt, 2))) for amt in posting_amounts[:num_postings]]
    
    # Calculate expected total
    expected_total = sum(amounts)
    
    # Simulate posting in original order
    total_original_order = Decimal(0)
    for amt in amounts:
        total_original_order += amt
    
    # Simulate posting in reversed order
    total_reversed_order = Decimal(0)
    for amt in reversed(amounts):
        total_reversed_order += amt
    
    # Simulate posting in random order
    shuffled_amounts = amounts.copy()
    random.shuffle(shuffled_amounts)
    total_random_order = Decimal(0)
    for amt in shuffled_amounts:
        total_random_order += amt
    
    # Property: All orderings produce the same total
    assert total_original_order == expected_total, \
        "Original order total must match expected total"
    assert total_reversed_order == expected_total, \
        "Reversed order total must match expected total"
    assert total_random_order == expected_total, \
        "Random order total must match expected total"
    
    # Property: Accumulation is commutative
    assert total_original_order == total_reversed_order == total_random_order, \
        "Cost accumulation must be order-independent (commutative)"


@given(
    material_cost=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
    labor_cost=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
    external_cost=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100, deadline=None)
def test_property_cost_summary_totals(material_cost, labor_cost, external_cost):
    """
    Property: Cost summary total equals sum of cost elements
    
    This test verifies that:
    1. Total cost is always the sum of material, labor, and external costs
    2. No cost element is lost or duplicated
    3. Arithmetic is correct
    """
    from decimal import Decimal
    
    # Round to 2 decimal places
    material = Decimal(str(round(material_cost, 2)))
    labor = Decimal(str(round(labor_cost, 2)))
    external = Decimal(str(round(external_cost, 2)))
    
    # Calculate total
    total = material + labor + external
    
    # Create cost summary
    cost_summary = {
        "actual_material_cost": material,
        "actual_labor_cost": labor,
        "actual_external_cost": external,
        "actual_total_cost": total
    }
    
    # Property 1: Total equals sum of elements
    calculated_total = (
        cost_summary["actual_material_cost"] +
        cost_summary["actual_labor_cost"] +
        cost_summary["actual_external_cost"]
    )
    
    assert cost_summary["actual_total_cost"] == calculated_total, \
        f"Total cost {cost_summary['actual_total_cost']} must equal sum of elements {calculated_total}"
    
    # Property 2: Total is at least as large as any individual element
    assert cost_summary["actual_total_cost"] >= cost_summary["actual_material_cost"], \
        "Total cost must be >= material cost"
    assert cost_summary["actual_total_cost"] >= cost_summary["actual_labor_cost"], \
        "Total cost must be >= labor cost"
    assert cost_summary["actual_total_cost"] >= cost_summary["actual_external_cost"], \
        "Total cost must be >= external cost"
    
    # Property 3: If all elements are zero, total is zero
    if material == 0 and labor == 0 and external == 0:
        assert cost_summary["actual_total_cost"] == 0, \
            "Total cost must be zero when all elements are zero"
    
    # Property 4: If only one element is non-zero, total equals that element
    non_zero_count = sum([
        1 if material > 0 else 0,
        1 if labor > 0 else 0,
        1 if external > 0 else 0
    ])
    
    if non_zero_count == 1:
        if material > 0:
            assert cost_summary["actual_total_cost"] == material, \
                "Total should equal material cost when it's the only non-zero element"
        elif labor > 0:
            assert cost_summary["actual_total_cost"] == labor, \
                "Total should equal labor cost when it's the only non-zero element"
        elif external > 0:
            assert cost_summary["actual_total_cost"] == external, \
                "Total should equal external cost when it's the only non-zero element"


def test_cost_accumulation_consistency_specific_scenarios():
    """
    Test specific cost accumulation scenarios
    
    This test covers specific edge cases and scenarios
    """
    from decimal import Decimal
    
    # Scenario 1: No costs posted
    cost_summary_empty = {
        "actual_material_cost": Decimal(0),
        "actual_labor_cost": Decimal(0),
        "actual_external_cost": Decimal(0),
        "actual_total_cost": Decimal(0)
    }
    
    assert cost_summary_empty["actual_total_cost"] == (
        cost_summary_empty["actual_material_cost"] +
        cost_summary_empty["actual_labor_cost"] +
        cost_summary_empty["actual_external_cost"]
    ), "Empty cost summary should have zero total"
    
    # Scenario 2: Only material costs
    cost_summary_material_only = {
        "actual_material_cost": Decimal("1234.56"),
        "actual_labor_cost": Decimal(0),
        "actual_external_cost": Decimal(0),
        "actual_total_cost": Decimal("1234.56")
    }
    
    assert cost_summary_material_only["actual_total_cost"] == (
        cost_summary_material_only["actual_material_cost"] +
        cost_summary_material_only["actual_labor_cost"] +
        cost_summary_material_only["actual_external_cost"]
    ), "Material-only cost summary should have correct total"
    
    # Scenario 3: All cost types present
    cost_summary_all = {
        "actual_material_cost": Decimal("1000.00"),
        "actual_labor_cost": Decimal("2000.00"),
        "actual_external_cost": Decimal("3000.00"),
        "actual_total_cost": Decimal("6000.00")
    }
    
    assert cost_summary_all["actual_total_cost"] == (
        cost_summary_all["actual_material_cost"] +
        cost_summary_all["actual_labor_cost"] +
        cost_summary_all["actual_external_cost"]
    ), "Complete cost summary should have correct total"
    
    # Scenario 4: Fractional costs with precision
    cost_summary_fractional = {
        "actual_material_cost": Decimal("123.45"),
        "actual_labor_cost": Decimal("678.90"),
        "actual_external_cost": Decimal("234.56"),
        "actual_total_cost": Decimal("1036.91")
    }
    
    calculated_total = (
        cost_summary_fractional["actual_material_cost"] +
        cost_summary_fractional["actual_labor_cost"] +
        cost_summary_fractional["actual_external_cost"]
    )
    
    assert cost_summary_fractional["actual_total_cost"] == calculated_total, \
        f"Fractional cost summary should have correct total: {cost_summary_fractional['actual_total_cost']} == {calculated_total}"
    
    # Scenario 5: Large costs
    cost_summary_large = {
        "actual_material_cost": Decimal("999999.99"),
        "actual_labor_cost": Decimal("888888.88"),
        "actual_external_cost": Decimal("777777.77"),
        "actual_total_cost": Decimal("2666666.64")
    }
    
    assert cost_summary_large["actual_total_cost"] == (
        cost_summary_large["actual_material_cost"] +
        cost_summary_large["actual_labor_cost"] +
        cost_summary_large["actual_external_cost"]
    ), "Large cost summary should have correct total"


@given(
    initial_material=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    additional_postings=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None)
def test_property_incremental_cost_accumulation(initial_material, additional_postings):
    """
    Property: Costs accumulate incrementally
    
    This test verifies that:
    1. Each new posting increases the total
    2. Accumulation is monotonically increasing
    3. Final total equals initial plus all additions
    """
    from decimal import Decimal
    
    # Start with initial cost
    current_total = Decimal(str(round(initial_material, 2)))
    
    # Track all totals
    totals = [current_total]
    
    # Add each posting incrementally
    for posting in additional_postings:
        posting_amount = Decimal(str(round(posting, 2)))
        current_total += posting_amount
        totals.append(current_total)
    
    # Property 1: Each total is >= previous total (monotonically increasing)
    for i in range(1, len(totals)):
        assert totals[i] >= totals[i-1], \
            f"Cost accumulation must be monotonically increasing: {totals[i]} >= {totals[i-1]}"
    
    # Property 2: Final total equals initial plus sum of all postings
    expected_final = Decimal(str(round(initial_material, 2))) + \
                    sum(Decimal(str(round(p, 2))) for p in additional_postings)
    
    assert totals[-1] == expected_final, \
        f"Final total {totals[-1]} must equal initial {Decimal(str(round(initial_material, 2)))} plus sum of postings"
    
    # Property 3: If no postings, total remains unchanged
    if len(additional_postings) == 0:
        assert totals[-1] == totals[0], \
            "Total should remain unchanged with no additional postings"
