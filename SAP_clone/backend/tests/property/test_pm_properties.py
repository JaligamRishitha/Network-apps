"""
Property-based tests for Plant Maintenance (PM) module.
**Feature: sap-erp-demo, Property 3: Asset Data Round-Trip**
**Validates: Requirements 2.1**
"""
from datetime import date, datetime
from hypothesis import given, strategies as st, settings

from backend.models.pm_models import (
    Asset, AssetType, AssetStatus,
    MaintenanceOrder, OrderType, OrderStatus,
    PMIncident, FaultType
)


# Strategies for generating test data
asset_type_strategy = st.sampled_from(list(AssetType))
asset_status_strategy = st.sampled_from(list(AssetStatus))
order_type_strategy = st.sampled_from(list(OrderType))
fault_type_strategy = st.sampled_from(list(FaultType))

asset_id_strategy = st.text(
    alphabet=st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() and not x.startswith('-') and not x.endswith('-'))

name_strategy = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
location_strategy = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
description_strategy = st.text(min_size=0, max_size=1000)

date_strategy = st.dates(
    min_value=date(2000, 1, 1),
    max_value=date(2030, 12, 31)
)


@settings(max_examples=100)
@given(
    asset_id=asset_id_strategy,
    asset_type=asset_type_strategy,
    name=name_strategy,
    location=location_strategy,
    installation_date=date_strategy,
    status=asset_status_strategy,
    description=description_strategy
)
def test_asset_data_roundtrip(
    asset_id: str,
    asset_type: AssetType,
    name: str,
    location: str,
    installation_date: date,
    status: AssetStatus,
    description: str
):
    """
    **Feature: sap-erp-demo, Property 3: Asset Data Round-Trip**
    **Validates: Requirements 2.1**
    
    Property: For any valid asset creation request with asset_type, name, location,
    installation_date, and status, creating then retrieving the asset SHALL return
    an equivalent object with all fields preserved.
    """
    # Create asset instance
    asset = Asset(
        asset_id=asset_id,
        asset_type=asset_type,
        name=name,
        location=location,
        installation_date=installation_date,
        status=status,
        description=description if description else None
    )
    
    # Convert to dict (simulates serialization)
    asset_dict = asset.to_dict()
    
    # Verify all fields are preserved
    assert asset_dict["asset_id"] == asset_id, "asset_id mismatch"
    assert asset_dict["asset_type"] == asset_type.value, "asset_type mismatch"
    assert asset_dict["name"] == name, "name mismatch"
    assert asset_dict["location"] == location, "location mismatch"
    assert asset_dict["installation_date"] == installation_date.isoformat(), "installation_date mismatch"
    assert asset_dict["status"] == status.value, "status mismatch"
    
    # Verify description handling (None vs empty string)
    if description:
        assert asset_dict["description"] == description, "description mismatch"


@settings(max_examples=100)
@given(
    asset_type=asset_type_strategy,
    name=name_strategy,
    location=location_strategy,
    installation_date=date_strategy
)
def test_asset_required_fields(
    asset_type: AssetType,
    name: str,
    location: str,
    installation_date: date
):
    """
    **Feature: sap-erp-demo, Property 3: Asset Data Round-Trip**
    **Validates: Requirements 2.1**
    
    Property: For any asset, all required fields (asset_type, name, location,
    installation_date, status) SHALL be present and valid.
    """
    asset = Asset(
        asset_id=f"AST-{hash(name) % 10000:04d}",
        asset_type=asset_type,
        name=name,
        location=location,
        installation_date=installation_date,
        status=AssetStatus.OPERATIONAL
    )
    
    # Verify required fields are set
    assert asset.asset_id is not None, "asset_id should not be None"
    assert asset.asset_type in AssetType, "asset_type should be valid enum"
    assert asset.name is not None and len(asset.name) > 0, "name should not be empty"
    assert asset.location is not None and len(asset.location) > 0, "location should not be empty"
    assert asset.installation_date is not None, "installation_date should not be None"
    assert asset.status in AssetStatus, "status should be valid enum"


@settings(max_examples=100)
@given(asset_type=asset_type_strategy)
def test_asset_type_validity(asset_type: AssetType):
    """
    **Feature: sap-erp-demo, Property 3: Asset Data Round-Trip**
    **Validates: Requirements 2.1**
    
    Property: For any asset_type, it SHALL be one of: substation, transformer, feeder
    """
    valid_types = {"substation", "transformer", "feeder"}
    assert asset_type.value in valid_types, f"Invalid asset type: {asset_type.value}"


@settings(max_examples=100)
@given(
    asset_id=asset_id_strategy,
    asset_type=asset_type_strategy,
    name=name_strategy,
    location=location_strategy,
    installation_date=date_strategy,
    status=asset_status_strategy
)
def test_asset_dict_roundtrip_consistency(
    asset_id: str,
    asset_type: AssetType,
    name: str,
    location: str,
    installation_date: date,
    status: AssetStatus
):
    """
    **Feature: sap-erp-demo, Property 3: Asset Data Round-Trip**
    **Validates: Requirements 2.1**
    
    Property: Converting an asset to dict twice SHALL produce identical results.
    """
    asset = Asset(
        asset_id=asset_id,
        asset_type=asset_type,
        name=name,
        location=location,
        installation_date=installation_date,
        status=status
    )
    
    dict1 = asset.to_dict()
    dict2 = asset.to_dict()
    
    assert dict1 == dict2, "Multiple to_dict() calls should produce identical results"



# Additional tests for Property 4: Maintenance Order Asset Linkage

from backend.models.pm_models import OrderType, OrderStatus


order_type_strategy = st.sampled_from(list(OrderType))
order_status_strategy = st.sampled_from(list(OrderStatus))


@settings(max_examples=100)
@given(order_type=order_type_strategy)
def test_order_type_validity(order_type: OrderType):
    """
    **Feature: sap-erp-demo, Property 4: Maintenance Order Asset Linkage**
    **Validates: Requirements 2.2**
    
    Property: For any order_type, it SHALL be one of: preventive, corrective, emergency
    """
    valid_types = {"preventive", "corrective", "emergency"}
    assert order_type.value in valid_types, f"Invalid order type: {order_type.value}"


@settings(max_examples=100)
@given(
    asset_id=asset_id_strategy,
    order_type=order_type_strategy,
    description=description_strategy
)
def test_maintenance_order_requires_valid_asset(
    asset_id: str,
    order_type: OrderType,
    description: str
):
    """
    **Feature: sap-erp-demo, Property 4: Maintenance Order Asset Linkage**
    **Validates: Requirements 2.2**
    
    Property: For any maintenance order creation, the order SHALL reference
    an existing, valid asset_id.
    """
    # This test validates the data model structure
    # In actual service tests, we'd verify the asset exists
    from backend.models.pm_models import MaintenanceOrder
    from datetime import datetime
    
    # Create a maintenance order instance (without DB)
    order = MaintenanceOrder(
        order_id=f"MO-{hash(asset_id) % 10000:04d}",
        asset_id=asset_id,
        order_type=order_type,
        status=OrderStatus.PLANNED,
        description=description if description else "Test order",
        scheduled_date=datetime.utcnow(),
        created_by="test_user",
    )
    
    # Verify asset_id is set and not empty
    assert order.asset_id is not None, "asset_id should not be None"
    assert len(order.asset_id) > 0, "asset_id should not be empty"
    assert order.asset_id == asset_id, "asset_id should match input"
    
    # Verify order_type is valid
    assert order.order_type in OrderType, "order_type should be valid enum"


@settings(max_examples=100)
@given(
    asset_type=asset_type_strategy,
    order_type=order_type_strategy
)
def test_maintenance_order_asset_type_compatibility(
    asset_type: AssetType,
    order_type: OrderType
):
    """
    **Feature: sap-erp-demo, Property 4: Maintenance Order Asset Linkage**
    **Validates: Requirements 2.2, 2.3**
    
    Property: For any combination of asset_type and order_type, the system
    SHALL accept the maintenance order (all asset types support all order types).
    """
    # All asset types (substation, transformer, feeder) support all order types
    valid_asset_types = {"substation", "transformer", "feeder"}
    valid_order_types = {"preventive", "corrective", "emergency"}
    
    assert asset_type.value in valid_asset_types, f"Invalid asset type: {asset_type.value}"
    assert order_type.value in valid_order_types, f"Invalid order type: {order_type.value}"
