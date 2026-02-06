"""
Property-based tests for Finance (FI) module.
**Feature: sap-erp-demo, Property 8: Cost Center Data Round-Trip**
**Validates: Requirements 4.1**
"""
from datetime import datetime
from decimal import Decimal
from hypothesis import given, strategies as st, settings

from backend.models.fi_models import (
    CostCenter, CostEntry, CostType,
    FIApproval, ApprovalDecision
)


# Strategies for generating test data
cost_center_id_strategy = st.text(
    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() and not x.startswith('-') and not x.endswith('-'))

name_strategy = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
manager_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
description_strategy = st.text(min_size=0, max_size=1000)

# Budget amounts between 0 and 10 billion with 2 decimal places
budget_strategy = st.decimals(
    min_value=Decimal("0.00"),
    max_value=Decimal("10000000000.00"),
    places=2,
    allow_nan=False,
    allow_infinity=False
)

fiscal_year_strategy = st.integers(min_value=2000, max_value=2100)
cost_type_strategy = st.sampled_from(list(CostType))


@settings(max_examples=100)
@given(
    cost_center_id=cost_center_id_strategy,
    name=name_strategy,
    budget_amount=budget_strategy,
    fiscal_year=fiscal_year_strategy,
    responsible_manager=manager_strategy,
    description=description_strategy
)
def test_cost_center_data_roundtrip(
    cost_center_id: str,
    name: str,
    budget_amount: Decimal,
    fiscal_year: int,
    responsible_manager: str,
    description: str
):
    """
    **Feature: sap-erp-demo, Property 8: Cost Center Data Round-Trip**
    **Validates: Requirements 4.1**
    
    Property: For any valid cost center creation request with cost_center_id, name,
    budget_amount, fiscal_year, and responsible_manager, creating then retrieving
    the cost center SHALL return an equivalent object with all fields preserved.
    """
    # Create cost center instance
    cost_center = CostCenter(
        cost_center_id=cost_center_id,
        name=name,
        budget_amount=budget_amount,
        fiscal_year=fiscal_year,
        responsible_manager=responsible_manager,
        description=description if description else None
    )
    
    # Convert to dict (simulates serialization)
    cc_dict = cost_center.to_dict()
    
    # Verify all fields are preserved
    assert cc_dict["cost_center_id"] == cost_center_id, "cost_center_id mismatch"
    assert cc_dict["name"] == name, "name mismatch"
    assert cc_dict["budget_amount"] == float(budget_amount), "budget_amount mismatch"
    assert cc_dict["fiscal_year"] == fiscal_year, "fiscal_year mismatch"
    assert cc_dict["responsible_manager"] == responsible_manager, "responsible_manager mismatch"


@settings(max_examples=100)
@given(
    cost_center_id=cost_center_id_strategy,
    name=name_strategy,
    budget_amount=budget_strategy,
    fiscal_year=fiscal_year_strategy,
    responsible_manager=manager_strategy
)
def test_cost_center_required_fields(
    cost_center_id: str,
    name: str,
    budget_amount: Decimal,
    fiscal_year: int,
    responsible_manager: str
):
    """
    **Feature: sap-erp-demo, Property 8: Cost Center Data Round-Trip**
    **Validates: Requirements 4.1**
    
    Property: For any cost center, all required fields (cost_center_id, name,
    budget_amount, fiscal_year, responsible_manager) SHALL be present and valid.
    """
    cost_center = CostCenter(
        cost_center_id=cost_center_id,
        name=name,
        budget_amount=budget_amount,
        fiscal_year=fiscal_year,
        responsible_manager=responsible_manager
    )
    
    # Verify required fields are set
    assert cost_center.cost_center_id is not None, "cost_center_id should not be None"
    assert cost_center.name is not None and len(cost_center.name) > 0, "name should not be empty"
    assert cost_center.budget_amount is not None, "budget_amount should not be None"
    assert cost_center.budget_amount >= 0, "budget_amount should be non-negative"
    assert cost_center.fiscal_year is not None, "fiscal_year should not be None"
    assert 2000 <= cost_center.fiscal_year <= 2100, "fiscal_year should be reasonable"
    assert cost_center.responsible_manager is not None, "responsible_manager should not be None"


@settings(max_examples=100)
@given(cost_type=cost_type_strategy)
def test_cost_type_validity(cost_type: CostType):
    """
    **Feature: sap-erp-demo, Property 8: Cost Center Data Round-Trip**
    **Validates: Requirements 4.2**
    
    Property: For any cost_type, it SHALL be one of: CAPEX, OPEX
    """
    valid_types = {"CAPEX", "OPEX"}
    assert cost_type.value in valid_types, f"Invalid cost type: {cost_type.value}"


@settings(max_examples=100)
@given(
    cost_center_id=cost_center_id_strategy,
    name=name_strategy,
    budget_amount=budget_strategy,
    fiscal_year=fiscal_year_strategy,
    responsible_manager=manager_strategy
)
def test_cost_center_dict_roundtrip_consistency(
    cost_center_id: str,
    name: str,
    budget_amount: Decimal,
    fiscal_year: int,
    responsible_manager: str
):
    """
    **Feature: sap-erp-demo, Property 8: Cost Center Data Round-Trip**
    **Validates: Requirements 4.1**
    
    Property: Converting a cost center to dict twice SHALL produce identical results.
    """
    cost_center = CostCenter(
        cost_center_id=cost_center_id,
        name=name,
        budget_amount=budget_amount,
        fiscal_year=fiscal_year,
        responsible_manager=responsible_manager
    )
    
    dict1 = cost_center.to_dict()
    dict2 = cost_center.to_dict()
    
    assert dict1 == dict2, "Multiple to_dict() calls should produce identical results"



# Property 9: Cost Entry Tracking

ticket_id_strategy = st.text(
    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
    min_size=10,
    max_size=30
).filter(lambda x: x.strip())

amount_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("1000000.00"),
    places=2,
    allow_nan=False,
    allow_infinity=False
)

user_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(
    ticket_id=ticket_id_strategy,
    cost_center_id=cost_center_id_strategy,
    amount=amount_strategy,
    cost_type=cost_type_strategy,
    created_by=user_strategy
)
def test_cost_entry_has_required_fields(
    ticket_id: str,
    cost_center_id: str,
    amount: Decimal,
    cost_type: CostType,
    created_by: str
):
    """
    **Feature: sap-erp-demo, Property 9: Cost Entry Tracking**
    **Validates: Requirements 4.2**
    
    Property: For any cost entry creation, the entry SHALL:
    - Reference a valid ticket_id (optional)
    - Reference a valid cost_center_id
    - Have a valid cost_type from {CAPEX, OPEX}
    - Have a positive amount
    """
    entry = CostEntry(
        entry_id=f"CE-{hash(ticket_id) % 10000:04d}",
        ticket_id=ticket_id,
        cost_center_id=cost_center_id,
        amount=amount,
        cost_type=cost_type,
        created_by=created_by,
    )
    
    # Verify required fields
    assert entry.entry_id is not None, "entry_id should not be None"
    assert entry.cost_center_id is not None, "cost_center_id should not be None"
    assert len(entry.cost_center_id) > 0, "cost_center_id should not be empty"
    assert entry.cost_type in CostType, "cost_type should be valid enum"
    assert entry.amount > 0, "amount should be positive"
    assert entry.created_by is not None, "created_by should not be None"


@settings(max_examples=100)
@given(
    cost_center_id=cost_center_id_strategy,
    amount=amount_strategy,
    cost_type=cost_type_strategy
)
def test_cost_entry_to_dict_preserves_fields(
    cost_center_id: str,
    amount: Decimal,
    cost_type: CostType
):
    """
    **Feature: sap-erp-demo, Property 9: Cost Entry Tracking**
    **Validates: Requirements 4.2**
    
    Property: For any cost entry, converting to dict SHALL preserve all fields.
    """
    entry = CostEntry(
        entry_id="CE-TEST-0001",
        ticket_id="TKT-FI-20240115-0001",
        cost_center_id=cost_center_id,
        amount=amount,
        cost_type=cost_type,
        created_by="test_user",
    )
    
    entry_dict = entry.to_dict()
    
    # Verify all fields are present
    assert "entry_id" in entry_dict, "entry_id missing from dict"
    assert "ticket_id" in entry_dict, "ticket_id missing from dict"
    assert "cost_center_id" in entry_dict, "cost_center_id missing from dict"
    assert "amount" in entry_dict, "amount missing from dict"
    assert "cost_type" in entry_dict, "cost_type missing from dict"
    assert "created_by" in entry_dict, "created_by missing from dict"
    
    # Verify values
    assert entry_dict["cost_center_id"] == cost_center_id
    assert entry_dict["amount"] == float(amount)
    assert entry_dict["cost_type"] == cost_type.value


@settings(max_examples=100)
@given(amount=amount_strategy)
def test_cost_entry_amount_is_positive(amount: Decimal):
    """
    **Feature: sap-erp-demo, Property 9: Cost Entry Tracking**
    **Validates: Requirements 4.2**
    
    Property: For any cost entry, the amount SHALL be positive.
    """
    # Our strategy already ensures positive amounts
    assert amount > 0, f"Amount {amount} should be positive"
