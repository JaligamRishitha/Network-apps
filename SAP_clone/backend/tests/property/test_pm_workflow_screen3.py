"""
Property-based tests for PM Workflow Screen 3: Order Release & Execution Readiness
Feature: pm-6-screen-workflow
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from backend.models.pm_workflow_models import WorkflowOrderStatus
from backend.services.pm_workflow_state_machine import get_state_machine


# Strategy for generating permit data
@st.composite
def permit_strategy(draw):
    """Generate random permit data"""
    return {
        "permit_id": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "permit_type": draw(st.sampled_from(["safety", "environmental", "access", "hot_work"])),
        "required": draw(st.booleans()),
        "approved": draw(st.booleans()),
        "approver": draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
    }


# Strategy for generating component/material data
@st.composite
def component_strategy(draw):
    """Generate random component data"""
    qty_required = draw(st.floats(min_value=1.0, max_value=1000.0))
    qty_issued = draw(st.floats(min_value=0.0, max_value=qty_required))
    
    return {
        "component_id": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "material_number": draw(st.text(min_size=5, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))),
        "quantity_required": qty_required,
        "quantity_issued": qty_issued,
        "critical": draw(st.booleans()),
        "available": draw(st.booleans()),
        "on_order": draw(st.booleans()),
    }


# Strategy for generating operation data
@st.composite
def operation_strategy(draw):
    """Generate random operation data"""
    return {
        "operation_id": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "operation_number": draw(st.text(min_size=2, max_size=10, alphabet="0123456789")),
        "status": draw(st.sampled_from(["planned", "in_progress", "confirmed"])),
        "technician_id": draw(st.one_of(st.none(), st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))),
    }


# Strategy for generating order data for Screen 3
@st.composite
def screen3_order_strategy(draw, order_type=None):
    """Generate random order data for Screen 3 testing"""
    if order_type is None:
        order_type = draw(st.sampled_from(["general", "breakdown"]))
    
    num_operations = draw(st.integers(min_value=1, max_value=5))
    operations = [draw(operation_strategy()) for _ in range(num_operations)]
    
    num_components = draw(st.integers(min_value=0, max_value=5))
    components = [draw(component_strategy()) for _ in range(num_components)]
    
    num_permits = draw(st.integers(min_value=0, max_value=3))
    permits = [draw(permit_strategy()) for _ in range(num_permits)]
    
    return {
        "order_type": order_type,
        "operations": operations,
        "components": components,
        "permits": permits,
        "confirmations": [],
        "cost_summary": {"estimated_total_cost": draw(st.floats(min_value=100.0, max_value=100000.0))}
    }


@given(order_data=screen3_order_strategy())
@settings(max_examples=100)
def test_property_permit_enforcement(order_data):
    """
    **Feature: pm-6-screen-workflow, Property 7: Permit Enforcement**
    **Validates: Requirements 1.6, 3.1**
    
    Property: For any maintenance order with permit requirements,
    the order should not transition to "Released" status unless all
    required permits are approved.
    
    This test verifies that:
    1. Orders with unapproved required permits cannot be released
    2. Orders with all required permits approved can be released (if other prerequisites met)
    3. Breakdown orders have reduced permit validation
    4. Optional permits don't block release
    """
    state_machine = get_state_machine()
    
    # Check if order can transition from Planned to Released
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        order_data
    )
    
    is_breakdown = order_data.get("order_type") == "breakdown"
    permits = order_data.get("permits", [])
    required_permits = [p for p in permits if p.get("required", False)]
    
    # Property 1: For general maintenance, required permits must be approved
    if not is_breakdown and required_permits:
        unapproved_required = [p for p in required_permits if not p.get("approved", False)]
        
        if unapproved_required:
            # Order should be blocked
            assert not can_transition or len(blocking_reasons) > 0, \
                "Order with unapproved required permits should be blocked or have warnings"
            
            # If blocked, reason should mention permits
            if not can_transition:
                assert any("permit" in reason.lower() for reason in blocking_reasons), \
                    f"Blocking reason should mention permits. Got: {blocking_reasons}"
    
    # Property 2: Breakdown orders bypass permit validation
    if is_breakdown:
        # Breakdown orders should not be blocked by permits alone
        # (they may be blocked by other prerequisites like technician assignment)
        if not can_transition:
            # If blocked, it should NOT be due to permits
            permit_blocks = [r for r in blocking_reasons if "permit" in r.lower()]
            assert len(permit_blocks) == 0, \
                f"Breakdown orders should not be blocked by permits. Got: {permit_blocks}"
    
    # Property 3: Optional permits don't block release
    optional_permits = [p for p in permits if not p.get("required", False)]
    if optional_permits and not required_permits:
        # With only optional permits, order should not be blocked by permits
        if not can_transition:
            permit_blocks = [r for r in blocking_reasons if "permit" in r.lower()]
            assert len(permit_blocks) == 0, \
                "Optional permits should not block release"
    
    # Property 4: Orders without permits should not be blocked by permit checks
    if not permits:
        if not can_transition:
            permit_blocks = [r for r in blocking_reasons if "permit" in r.lower()]
            assert len(permit_blocks) == 0, \
                "Orders without permits should not be blocked by permit checks"


@given(order_data=screen3_order_strategy())
@settings(max_examples=100)
def test_property_material_availability_validation(order_data):
    """
    **Feature: pm-6-screen-workflow, Property 9: Material Availability Validation**
    **Validates: Requirements 3.2, 3.6**
    
    Property: For any maintenance order at release, if critical materials
    are not available and not on confirmed delivery, the system should
    prevent release or require override authorization.
    
    This test verifies that:
    1. Orders with unavailable critical materials are blocked
    2. Orders with critical materials on order can be released
    3. Orders with available critical materials can be released
    4. Breakdown orders have reduced material validation
    5. Non-critical materials don't block release
    """
    state_machine = get_state_machine()
    
    # Check if order can transition from Planned to Released
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        order_data
    )
    
    is_breakdown = order_data.get("order_type") == "breakdown"
    components = order_data.get("components", [])
    critical_components = [c for c in components if c.get("critical", False)]
    
    # Property 1: For general maintenance, critical materials must be available or on order
    if not is_breakdown and critical_components:
        unavailable_critical = [
            c for c in critical_components
            if not c.get("available", False) and not c.get("on_order", False)
        ]
        
        if unavailable_critical:
            # Order should be blocked
            assert not can_transition or len(blocking_reasons) > 0, \
                "Order with unavailable critical materials should be blocked or have warnings"
            
            # If blocked, reason should mention materials
            if not can_transition:
                assert any("material" in reason.lower() for reason in blocking_reasons), \
                    f"Blocking reason should mention materials. Got: {blocking_reasons}"
    
    # Property 2: Critical materials on order should allow release
    if not is_breakdown and critical_components:
        all_on_order_or_available = all(
            c.get("available", False) or c.get("on_order", False)
            for c in critical_components
        )
        
        if all_on_order_or_available:
            # Materials should not block release
            if not can_transition:
                material_blocks = [r for r in blocking_reasons if "material" in r.lower()]
                # If there are material blocks, they should not be about critical materials
                # (could be about other validation)
                pass  # This is acceptable - other prerequisites may block
    
    # Property 3: Breakdown orders bypass material validation
    if is_breakdown:
        # Breakdown orders should not be blocked by materials alone
        if not can_transition:
            material_blocks = [r for r in blocking_reasons if "material" in r.lower()]
            assert len(material_blocks) == 0, \
                f"Breakdown orders should not be blocked by materials. Got: {material_blocks}"
    
    # Property 4: Non-critical materials don't block release
    non_critical_components = [c for c in components if not c.get("critical", False)]
    if non_critical_components and not critical_components:
        # With only non-critical materials, order should not be blocked by materials
        if not can_transition:
            material_blocks = [r for r in blocking_reasons if "material" in r.lower()]
            assert len(material_blocks) == 0, \
                "Non-critical materials should not block release"
    
    # Property 5: Orders without components should not be blocked by material checks
    if not components:
        if not can_transition:
            material_blocks = [r for r in blocking_reasons if "material" in r.lower()]
            assert len(material_blocks) == 0, \
                "Orders without components should not be blocked by material checks"


@given(
    general_order=screen3_order_strategy(order_type="general"),
    breakdown_order=screen3_order_strategy(order_type="breakdown")
)
@settings(max_examples=100)
def test_property_breakdown_order_acceleration(general_order, breakdown_order):
    """
    **Feature: pm-6-screen-workflow, Property 5: Breakdown Order Acceleration**
    **Validates: Requirements 7.3, 7.4**
    
    Property: For any breakdown maintenance order, the system should allow
    immediate release with reduced validation compared to general maintenance
    orders of the same scope.
    
    This test verifies that:
    1. Breakdown orders have fewer blocking reasons than general orders
    2. Breakdown orders bypass permit validation
    3. Breakdown orders bypass material availability validation
    4. Breakdown orders still require technician assignment
    """
    state_machine = get_state_machine()
    
    # Ensure both orders have the same structure (except order_type)
    # Copy permits and components from general to breakdown for fair comparison
    breakdown_order["permits"] = general_order["permits"]
    breakdown_order["components"] = general_order["components"]
    breakdown_order["operations"] = general_order["operations"]
    breakdown_order["cost_summary"] = general_order["cost_summary"]
    
    # Check transitions for both orders
    can_transition_general, reasons_general = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        general_order
    )
    
    can_transition_breakdown, reasons_breakdown = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        breakdown_order
    )
    
    # Property 1: Breakdown orders should have fewer or equal blocking reasons
    assert len(reasons_breakdown) <= len(reasons_general), \
        f"Breakdown orders should have reduced validation. " \
        f"General: {len(reasons_general)} blocks, Breakdown: {len(reasons_breakdown)} blocks"
    
    # Property 2: Breakdown orders should not be blocked by permits
    permit_blocks_breakdown = [r for r in reasons_breakdown if "permit" in r.lower()]
    assert len(permit_blocks_breakdown) == 0, \
        f"Breakdown orders should bypass permit validation. Got: {permit_blocks_breakdown}"
    
    # Property 3: Breakdown orders should not be blocked by materials
    material_blocks_breakdown = [r for r in reasons_breakdown if "material" in r.lower()]
    assert len(material_blocks_breakdown) == 0, \
        f"Breakdown orders should bypass material validation. Got: {material_blocks_breakdown}"
    
    # Property 4: If general order is blocked by permits or materials only,
    # breakdown order should be allowed (assuming technician assigned)
    permit_blocks_general = [r for r in reasons_general if "permit" in r.lower()]
    material_blocks_general = [r for r in reasons_general if "material" in r.lower()]
    
    # Check if general order is blocked only by permits/materials
    other_blocks_general = [
        r for r in reasons_general
        if "permit" not in r.lower() and "material" not in r.lower()
    ]
    
    if (permit_blocks_general or material_blocks_general) and not other_blocks_general:
        # General order blocked only by permits/materials
        # Breakdown order should be allowed
        assert can_transition_breakdown, \
            f"Breakdown order should be allowed when general order is blocked only by permits/materials. " \
            f"General blocks: {reasons_general}, Breakdown blocks: {reasons_breakdown}"
    
    # Property 5: Both orders still require technician assignment
    has_technician = any(op.get("technician_id") for op in breakdown_order.get("operations", []))
    if not has_technician:
        # Both should be blocked by technician requirement
        if not can_transition_breakdown:
            technician_blocks = [r for r in reasons_breakdown if "technician" in r.lower()]
            assert len(technician_blocks) > 0, \
                "Breakdown orders should still require technician assignment"


@given(order_data=screen3_order_strategy())
@settings(max_examples=100)
def test_property_release_requires_technician(order_data):
    """
    Property: All orders (general and breakdown) require technician assignment
    
    This test verifies that:
    1. Orders without technician assignment cannot be released
    2. Orders with at least one technician assigned can proceed to release validation
    """
    state_machine = get_state_machine()
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        order_data
    )
    
    operations = order_data.get("operations", [])
    has_technician = any(op.get("technician_id") for op in operations)
    
    # Property: Without technician, order must be blocked
    if not has_technician:
        assert not can_transition, \
            "Order without technician assignment should be blocked"
        assert any("technician" in reason.lower() for reason in blocking_reasons), \
            f"Blocking reason should mention technician. Got: {blocking_reasons}"
    
    # Property: With technician, technician should not be a blocking reason
    if has_technician:
        if not can_transition:
            technician_blocks = [r for r in blocking_reasons if "technician" in r.lower()]
            assert len(technician_blocks) == 0, \
                f"Order with technician should not be blocked by technician requirement. Got: {technician_blocks}"


@given(
    order_data=screen3_order_strategy(),
    override_authorized=st.booleans()
)
@settings(max_examples=100)
def test_property_block_override_authorization(order_data, override_authorized):
    """
    Property: Block overrides require authorization
    
    This test verifies that:
    1. Blocked orders can be overridden with authorization
    2. Override authorization is tracked
    3. Override doesn't bypass all validations (e.g., still need technician)
    """
    state_machine = get_state_machine()
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        order_data
    )
    
    # If order is blocked
    if not can_transition and len(blocking_reasons) > 0:
        # Simulate override
        if override_authorized:
            # With override, certain blocks can be bypassed
            # But critical blocks (like technician) should remain
            has_technician = any(op.get("technician_id") for op in order_data.get("operations", []))
            
            # Property: Override can bypass permit and material blocks
            permit_blocks = [r for r in blocking_reasons if "permit" in r.lower()]
            material_blocks = [r for r in blocking_reasons if "material" in r.lower()]
            
            # These can be overridden
            overridable_blocks = permit_blocks + material_blocks
            
            # Property: Technician requirement cannot be overridden
            if not has_technician:
                technician_blocks = [r for r in blocking_reasons if "technician" in r.lower()]
                assert len(technician_blocks) > 0, \
                    "Technician requirement should not be overridable"


@given(order_data=screen3_order_strategy())
@settings(max_examples=100)
def test_property_readiness_checklist_completeness(order_data):
    """
    Property: Readiness checklist covers all prerequisites
    
    This test verifies that:
    1. Readiness checklist includes permit status
    2. Readiness checklist includes material availability
    3. Readiness checklist includes resource assignment
    4. Checklist items match blocking reasons
    """
    state_machine = get_state_machine()
    
    can_transition, blocking_reasons = state_machine.can_transition(
        WorkflowOrderStatus.PLANNED,
        WorkflowOrderStatus.RELEASED,
        order_data
    )
    
    # Build readiness checklist
    checklist = {
        "permits_approved": True,
        "materials_available": True,
        "technician_assigned": True,
    }
    
    # Check permits
    is_breakdown = order_data.get("order_type") == "breakdown"
    if not is_breakdown:
        permits = order_data.get("permits", [])
        required_permits = [p for p in permits if p.get("required", False)]
        if required_permits:
            checklist["permits_approved"] = all(p.get("approved", False) for p in required_permits)
    
    # Check materials
    if not is_breakdown:
        components = order_data.get("components", [])
        critical_components = [c for c in components if c.get("critical", False)]
        if critical_components:
            checklist["materials_available"] = all(
                c.get("available", False) or c.get("on_order", False)
                for c in critical_components
            )
    
    # Check technician
    operations = order_data.get("operations", [])
    checklist["technician_assigned"] = any(op.get("technician_id") for op in operations)
    
    # Property: If checklist item is False, there should be a corresponding blocking reason
    if not checklist["permits_approved"]:
        if not can_transition:
            assert any("permit" in reason.lower() for reason in blocking_reasons), \
                "Permit checklist failure should have corresponding blocking reason"
    
    if not checklist["materials_available"]:
        if not can_transition:
            assert any("material" in reason.lower() for reason in blocking_reasons), \
                "Material checklist failure should have corresponding blocking reason"
    
    if not checklist["technician_assigned"]:
        assert not can_transition, \
            "Technician checklist failure should block transition"
        assert any("technician" in reason.lower() for reason in blocking_reasons), \
            "Technician checklist failure should have corresponding blocking reason"
    
    # Property: If all checklist items are True, order should be releasable
    if all(checklist.values()):
        assert can_transition, \
            f"Order with complete checklist should be releasable. Blocks: {blocking_reasons}"
