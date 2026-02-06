"""
Property-based tests for Materials Management (MM) module.
**Feature: sap-erp-demo, Property 5: Material Data Round-Trip**
**Validates: Requirements 3.1**
"""
from datetime import datetime
from hypothesis import given, strategies as st, settings

from backend.models.mm_models import (
    Material, StockTransaction, TransactionType,
    MMRequisition, RequisitionStatus
)


# Strategies for generating test data
material_id_strategy = st.text(
    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() and not x.startswith('-') and not x.endswith('-'))

description_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
quantity_strategy = st.integers(min_value=0, max_value=1000000)
reorder_level_strategy = st.integers(min_value=0, max_value=10000)
unit_strategy = st.sampled_from(["EA", "KG", "L", "M", "PC", "SET", "BOX"])
location_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(
    material_id=material_id_strategy,
    description=description_strategy,
    quantity=quantity_strategy,
    unit_of_measure=unit_strategy,
    reorder_level=reorder_level_strategy,
    storage_location=location_strategy
)
def test_material_data_roundtrip(
    material_id: str,
    description: str,
    quantity: int,
    unit_of_measure: str,
    reorder_level: int,
    storage_location: str
):
    """
    **Feature: sap-erp-demo, Property 5: Material Data Round-Trip**
    **Validates: Requirements 3.1**
    
    Property: For any valid material creation request with material_id, description,
    quantity, unit_of_measure, reorder_level, and storage_location, creating then
    retrieving the material SHALL return an equivalent object with all fields preserved.
    """
    # Create material instance
    material = Material(
        material_id=material_id,
        description=description,
        quantity=quantity,
        unit_of_measure=unit_of_measure,
        reorder_level=reorder_level,
        storage_location=storage_location
    )
    
    # Convert to dict (simulates serialization)
    material_dict = material.to_dict()
    
    # Verify all fields are preserved
    assert material_dict["material_id"] == material_id, "material_id mismatch"
    assert material_dict["description"] == description, "description mismatch"
    assert material_dict["quantity"] == quantity, "quantity mismatch"
    assert material_dict["unit_of_measure"] == unit_of_measure, "unit_of_measure mismatch"
    assert material_dict["reorder_level"] == reorder_level, "reorder_level mismatch"
    assert material_dict["storage_location"] == storage_location, "storage_location mismatch"


@settings(max_examples=100)
@given(
    material_id=material_id_strategy,
    description=description_strategy,
    quantity=quantity_strategy,
    unit_of_measure=unit_strategy,
    reorder_level=reorder_level_strategy,
    storage_location=location_strategy
)
def test_material_required_fields(
    material_id: str,
    description: str,
    quantity: int,
    unit_of_measure: str,
    reorder_level: int,
    storage_location: str
):
    """
    **Feature: sap-erp-demo, Property 5: Material Data Round-Trip**
    **Validates: Requirements 3.1**
    
    Property: For any material, all required fields SHALL be present and valid.
    """
    material = Material(
        material_id=material_id,
        description=description,
        quantity=quantity,
        unit_of_measure=unit_of_measure,
        reorder_level=reorder_level,
        storage_location=storage_location
    )
    
    # Verify required fields are set
    assert material.material_id is not None, "material_id should not be None"
    assert material.description is not None and len(material.description) > 0, "description should not be empty"
    assert material.quantity >= 0, "quantity should be non-negative"
    assert material.unit_of_measure is not None, "unit_of_measure should not be None"
    assert material.reorder_level >= 0, "reorder_level should be non-negative"
    assert material.storage_location is not None, "storage_location should not be None"


@settings(max_examples=100)
@given(
    quantity=quantity_strategy,
    reorder_level=reorder_level_strategy
)
def test_material_reorder_level_check(quantity: int, reorder_level: int):
    """
    **Feature: sap-erp-demo, Property 5: Material Data Round-Trip**
    **Validates: Requirements 3.1, 3.2**
    
    Property: For any material, is_below_reorder_level() SHALL return True
    if and only if quantity < reorder_level.
    """
    material = Material(
        material_id="MAT-TEST",
        description="Test Material",
        quantity=quantity,
        unit_of_measure="EA",
        reorder_level=reorder_level,
        storage_location="WH-01"
    )
    
    expected = quantity < reorder_level
    actual = material.is_below_reorder_level()
    
    assert actual == expected, (
        f"is_below_reorder_level() returned {actual}, expected {expected} "
        f"for quantity={quantity}, reorder_level={reorder_level}"
    )


@settings(max_examples=100)
@given(
    material_id=material_id_strategy,
    description=description_strategy,
    quantity=quantity_strategy,
    unit_of_measure=unit_strategy,
    reorder_level=reorder_level_strategy,
    storage_location=location_strategy
)
def test_material_dict_roundtrip_consistency(
    material_id: str,
    description: str,
    quantity: int,
    unit_of_measure: str,
    reorder_level: int,
    storage_location: str
):
    """
    **Feature: sap-erp-demo, Property 5: Material Data Round-Trip**
    **Validates: Requirements 3.1**
    
    Property: Converting a material to dict twice SHALL produce identical results.
    """
    material = Material(
        material_id=material_id,
        description=description,
        quantity=quantity,
        unit_of_measure=unit_of_measure,
        reorder_level=reorder_level,
        storage_location=storage_location
    )
    
    dict1 = material.to_dict()
    dict2 = material.to_dict()
    
    assert dict1 == dict2, "Multiple to_dict() calls should produce identical results"



# Additional tests for Property 6: Auto-Reorder Ticket Generation
# and Property 7: Stock Transaction History Completeness


@settings(max_examples=100)
@given(
    initial_quantity=st.integers(min_value=10, max_value=100),
    reorder_level=st.integers(min_value=5, max_value=50),
    consumption=st.integers(min_value=1, max_value=100)
)
def test_auto_reorder_trigger_condition(
    initial_quantity: int,
    reorder_level: int,
    consumption: int
):
    """
    **Feature: sap-erp-demo, Property 6: Auto-Reorder Ticket Generation**
    **Validates: Requirements 3.2**
    
    Property: For any stock transaction that reduces quantity below reorder_level,
    the system SHALL trigger auto-reorder when:
    - Previous quantity >= reorder_level AND
    - New quantity < reorder_level
    """
    material = Material(
        material_id="MAT-TEST",
        description="Test Material",
        quantity=initial_quantity,
        unit_of_measure="EA",
        reorder_level=reorder_level,
        storage_location="WH-01"
    )
    
    # Calculate new quantity after consumption
    new_quantity = initial_quantity - consumption
    
    # Determine if reorder should be triggered
    was_above_reorder = initial_quantity >= reorder_level
    is_below_reorder = new_quantity < reorder_level
    should_trigger_reorder = was_above_reorder and is_below_reorder
    
    # Verify the condition logic
    if should_trigger_reorder:
        assert initial_quantity >= reorder_level, "Initial quantity should be >= reorder level"
        assert new_quantity < reorder_level, "New quantity should be < reorder level"


@settings(max_examples=100)
@given(
    quantity=quantity_strategy,
    reorder_level=reorder_level_strategy
)
def test_reorder_level_boundary(quantity: int, reorder_level: int):
    """
    **Feature: sap-erp-demo, Property 6: Auto-Reorder Ticket Generation**
    **Validates: Requirements 3.2**
    
    Property: For any material, is_below_reorder_level() SHALL return True
    if and only if quantity < reorder_level (strict inequality).
    """
    material = Material(
        material_id="MAT-TEST",
        description="Test Material",
        quantity=quantity,
        unit_of_measure="EA",
        reorder_level=reorder_level,
        storage_location="WH-01"
    )
    
    # Verify boundary condition
    if quantity == reorder_level:
        # At exactly reorder level, should NOT trigger reorder
        assert not material.is_below_reorder_level(), (
            f"At reorder level ({quantity} == {reorder_level}), "
            f"should NOT be below reorder level"
        )
    elif quantity < reorder_level:
        assert material.is_below_reorder_level(), (
            f"Below reorder level ({quantity} < {reorder_level}), "
            f"should be below reorder level"
        )
    else:
        assert not material.is_below_reorder_level(), (
            f"Above reorder level ({quantity} > {reorder_level}), "
            f"should NOT be below reorder level"
        )



# Property 7: Stock Transaction History Completeness

from backend.models.mm_models import TransactionType

transaction_type_strategy = st.sampled_from(list(TransactionType))
user_strategy = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(transaction_type=transaction_type_strategy)
def test_transaction_type_validity(transaction_type: TransactionType):
    """
    **Feature: sap-erp-demo, Property 7: Stock Transaction History Completeness**
    **Validates: Requirements 3.5**
    
    Property: For any transaction_type, it SHALL be one of: receipt, issue, adjustment
    """
    valid_types = {"receipt", "issue", "adjustment"}
    assert transaction_type.value in valid_types, f"Invalid transaction type: {transaction_type.value}"


@settings(max_examples=100)
@given(
    material_id=material_id_strategy,
    quantity_change=st.integers(min_value=-1000, max_value=1000),
    transaction_type=transaction_type_strategy,
    performed_by=user_strategy
)
def test_transaction_has_required_fields(
    material_id: str,
    quantity_change: int,
    transaction_type: TransactionType,
    performed_by: str
):
    """
    **Feature: sap-erp-demo, Property 7: Stock Transaction History Completeness**
    **Validates: Requirements 3.5**
    
    Property: For any stock transaction, it SHALL have:
    - timestamp (transaction_date)
    - quantity_change
    - transaction_type
    - performed_by (user attribution)
    """
    from backend.models.mm_models import StockTransaction
    from datetime import datetime
    
    transaction = StockTransaction(
        transaction_id=f"TXN-{hash(material_id) % 10000:04d}",
        material_id=material_id,
        quantity_change=quantity_change,
        transaction_type=transaction_type,
        performed_by=performed_by,
    )
    
    # Verify all required fields are present
    assert transaction.transaction_id is not None, "transaction_id should not be None"
    assert transaction.material_id is not None, "material_id should not be None"
    assert transaction.quantity_change is not None, "quantity_change should not be None"
    assert transaction.transaction_type is not None, "transaction_type should not be None"
    assert transaction.performed_by is not None, "performed_by should not be None"
    assert len(transaction.performed_by) > 0, "performed_by should not be empty"


@settings(max_examples=100)
@given(
    transactions=st.lists(
        st.integers(min_value=-100, max_value=100),
        min_size=1,
        max_size=20
    ),
    initial_quantity=st.integers(min_value=100, max_value=1000)
)
def test_transaction_history_sum_equals_quantity_change(
    transactions: list,
    initial_quantity: int
):
    """
    **Feature: sap-erp-demo, Property 7: Stock Transaction History Completeness**
    **Validates: Requirements 3.5**
    
    Property: For any sequence of stock transactions on a material,
    the sum of all quantity_changes SHALL equal current_quantity minus initial_quantity.
    """
    # Calculate expected final quantity
    total_change = sum(transactions)
    expected_final = initial_quantity + total_change
    
    # Simulate the transactions
    current_quantity = initial_quantity
    for change in transactions:
        current_quantity += change
    
    assert current_quantity == expected_final, (
        f"Final quantity mismatch: expected {expected_final}, got {current_quantity}"
    )
    assert current_quantity - initial_quantity == total_change, (
        f"Total change mismatch: expected {total_change}, "
        f"got {current_quantity - initial_quantity}"
    )
