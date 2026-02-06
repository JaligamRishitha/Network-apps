"""
Integration Tests for PM Workflow External System Integration
Requirements: 1.2, 2.1, 4.2, 6.7

Tests the integration service interfaces for:
- SAP MM (Materials Management)
- SAP FI (Financial Accounting)
- SAP HR (Human Resources)
- Notification System
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.pm_workflow_integration_service import (
    SAPMMIntegrationService,
    SAPFIIntegrationService,
    SAPHRIntegrationService,
    NotificationSystemIntegrationService,
    PMWorkflowIntegrationService
)


@pytest.mark.asyncio
async def test_mm_get_material_master_data(db: AsyncSession):
    """Test MM integration - get material master data"""
    mm_service = SAPMMIntegrationService(db)
    
    # Test existing material
    material_data = await mm_service.get_material_master_data("MAT-001")
    assert material_data is not None
    assert material_data["material_number"] == "MAT-001"
    assert material_data["description"] == "Hydraulic Pump Assembly"
    assert material_data["standard_price"] == Decimal("450.00")
    
    # Test non-existent material
    material_data = await mm_service.get_material_master_data("MAT-999")
    assert material_data is None


@pytest.mark.asyncio
async def test_mm_check_material_availability(db: AsyncSession):
    """Test MM integration - check material availability"""
    mm_service = SAPMMIntegrationService(db)
    
    # Test sufficient stock
    available, qty, msg = await mm_service.check_material_availability(
        "MAT-001", Decimal("10")
    )
    assert available is True
    assert qty == Decimal("15")
    
    # Test insufficient stock
    available, qty, msg = await mm_service.check_material_availability(
        "MAT-001", Decimal("20")
    )
    assert available is False
    assert "Short" in msg
    
    # Test non-existent material
    available, qty, msg = await mm_service.check_material_availability(
        "MAT-999", Decimal("1")
    )
    assert available is False
    assert "not found" in msg


@pytest.mark.asyncio
async def test_mm_create_purchase_order(db: AsyncSession):
    """Test MM integration - create purchase order"""
    mm_service = SAPMMIntegrationService(db)
    
    # Test successful PO creation
    success, po_number, error = await mm_service.create_purchase_order_in_mm(
        vendor_id="VENDOR-001",
        material_number="MAT-001",
        quantity=Decimal("10"),
        delivery_date=datetime.utcnow() + timedelta(days=7)
    )
    assert success is True
    assert po_number is not None
    assert po_number.startswith("MM-PO-")
    assert error is None
    
    # Test PO creation for non-existent material
    success, po_number, error = await mm_service.create_purchase_order_in_mm(
        vendor_id="VENDOR-001",
        material_number="MAT-999",
        quantity=Decimal("10"),
        delivery_date=datetime.utcnow() + timedelta(days=7)
    )
    assert success is False
    assert po_number is None
    assert "not found" in error


@pytest.mark.asyncio
async def test_mm_post_goods_receipt(db: AsyncSession):
    """Test MM integration - post goods receipt"""
    mm_service = SAPMMIntegrationService(db)
    
    # Test successful GR posting
    success, mat_doc, error = await mm_service.post_goods_receipt_to_mm(
        po_number="PO-12345",
        material_number="MAT-001",
        quantity=Decimal("10"),
        storage_location="WH01"
    )
    assert success is True
    assert mat_doc is not None
    assert mat_doc.startswith("MM-GR-")
    assert error is None


@pytest.mark.asyncio
async def test_mm_post_goods_issue(db: AsyncSession):
    """Test MM integration - post goods issue"""
    mm_service = SAPMMIntegrationService(db)
    
    # Test successful GI posting
    success, mat_doc, error = await mm_service.post_goods_issue_to_mm(
        material_number="MAT-001",
        quantity=Decimal("5"),
        cost_center="CC-MAINT-001",
        order_number="PM-12345"
    )
    assert success is True
    assert mat_doc is not None
    assert mat_doc.startswith("MM-GI-")
    assert error is None
    
    # Test GI with insufficient stock
    success, mat_doc, error = await mm_service.post_goods_issue_to_mm(
        material_number="MAT-001",
        quantity=Decimal("1000"),  # More than available
        cost_center="CC-MAINT-001",
        order_number="PM-12345"
    )
    assert success is False
    assert mat_doc is None
    assert "Insufficient stock" in error
    
    # Test GI for non-existent material
    success, mat_doc, error = await mm_service.post_goods_issue_to_mm(
        material_number="MAT-999",
        quantity=Decimal("1"),
        cost_center="CC-MAINT-001",
        order_number="PM-12345"
    )
    assert success is False
    assert "not found" in error


@pytest.mark.asyncio
async def test_fi_validate_cost_center(db: AsyncSession):
    """Test FI integration - validate cost center"""
    fi_service = SAPFIIntegrationService(db)
    
    # Test valid cost center
    valid, error = await fi_service.validate_cost_center("CC-MAINT-001")
    assert valid is True
    assert error is None
    
    # Test invalid cost center
    valid, error = await fi_service.validate_cost_center("CC-INVALID")
    assert valid is False
    assert "not found" in error


@pytest.mark.asyncio
async def test_fi_post_cost_settlement(db: AsyncSession):
    """Test FI integration - post cost settlement"""
    fi_service = SAPFIIntegrationService(db)
    
    # Test successful cost settlement
    success, fi_doc, error = await fi_service.post_cost_settlement_to_fi(
        order_number="PM-12345",
        cost_center="CC-MAINT-001",
        material_cost=Decimal("500.00"),
        labor_cost=Decimal("300.00"),
        external_cost=Decimal("200.00"),
        total_cost=Decimal("1000.00"),
        posting_date=datetime.utcnow()
    )
    assert success is True
    assert fi_doc is not None
    assert fi_doc.startswith("FI-DOC-")
    assert error is None
    
    # Test settlement to invalid cost center
    success, fi_doc, error = await fi_service.post_cost_settlement_to_fi(
        order_number="PM-12345",
        cost_center="CC-INVALID",
        material_cost=Decimal("500.00"),
        labor_cost=Decimal("300.00"),
        external_cost=Decimal("200.00"),
        total_cost=Decimal("1000.00"),
        posting_date=datetime.utcnow()
    )
    assert success is False
    assert fi_doc is None
    assert "not found" in error


@pytest.mark.asyncio
async def test_fi_get_cost_element_master_data(db: AsyncSession):
    """Test FI integration - get cost element master data"""
    fi_service = SAPFIIntegrationService(db)
    
    # Test existing cost element
    cost_element_data = await fi_service.get_cost_element_master_data("CE-MAT")
    assert cost_element_data is not None
    assert cost_element_data["cost_element"] == "CE-MAT"
    assert cost_element_data["description"] == "Material Costs"
    
    # Test non-existent cost element
    cost_element_data = await fi_service.get_cost_element_master_data("CE-INVALID")
    assert cost_element_data is None


@pytest.mark.asyncio
async def test_hr_get_technician_master_data(db: AsyncSession):
    """Test HR integration - get technician master data"""
    hr_service = SAPHRIntegrationService(db)
    
    # Test existing technician
    tech_data = await hr_service.get_technician_master_data("TECH-001")
    assert tech_data is not None
    assert tech_data["technician_id"] == "TECH-001"
    assert tech_data["name"] == "John Smith"
    assert tech_data["labor_rate"] == Decimal("50.00")
    assert "Hydraulics" in tech_data["skills"]
    
    # Test non-existent technician
    tech_data = await hr_service.get_technician_master_data("TECH-999")
    assert tech_data is None


@pytest.mark.asyncio
async def test_hr_check_technician_availability(db: AsyncSession):
    """Test HR integration - check technician availability"""
    hr_service = SAPHRIntegrationService(db)
    
    # Test available technician
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=1)
    available, reason = await hr_service.check_technician_availability(
        "TECH-001", start_date, end_date
    )
    assert available is True
    assert reason is None
    
    # Test unavailable technician
    available, reason = await hr_service.check_technician_availability(
        "TECH-003", start_date, end_date
    )
    assert available is False
    assert reason is not None
    
    # Test non-existent technician
    available, reason = await hr_service.check_technician_availability(
        "TECH-999", start_date, end_date
    )
    assert available is False
    assert "not found" in reason


@pytest.mark.asyncio
async def test_hr_get_labor_rate(db: AsyncSession):
    """Test HR integration - get labor rate"""
    hr_service = SAPHRIntegrationService(db)
    
    # Test existing technician
    labor_rate = await hr_service.get_labor_rate("TECH-001")
    assert labor_rate == Decimal("50.00")
    
    # Test non-existent technician
    labor_rate = await hr_service.get_labor_rate("TECH-999")
    assert labor_rate is None


@pytest.mark.asyncio
async def test_notification_get_breakdown_notification(db: AsyncSession):
    """Test notification system - get breakdown notification"""
    notif_service = NotificationSystemIntegrationService(db)
    
    # Test existing notification
    notif_data = await notif_service.get_breakdown_notification("NOTIF-001")
    assert notif_data is not None
    assert notif_data["notification_id"] == "NOTIF-001"
    assert notif_data["equipment_id"] == "EQ-PUMP-001"
    assert notif_data["priority"] == "urgent"
    
    # Test non-existent notification
    notif_data = await notif_service.get_breakdown_notification("NOTIF-999")
    assert notif_data is None


@pytest.mark.asyncio
async def test_notification_send_notification(db: AsyncSession):
    """Test notification system - send notification"""
    notif_service = NotificationSystemIntegrationService(db)
    
    # Test sending notification
    success, error = await notif_service.send_notification(
        recipient="user@example.com",
        subject="Order Released",
        message="Maintenance order PM-12345 has been released",
        notification_type="email"
    )
    assert success is True
    assert error is None


@pytest.mark.asyncio
async def test_notification_update_notification_status(db: AsyncSession):
    """Test notification system - update notification status"""
    notif_service = NotificationSystemIntegrationService(db)
    
    # Test updating existing notification
    success, error = await notif_service.update_notification_status(
        notification_id="NOTIF-001",
        status="in_progress",
        order_number="PM-12345"
    )
    assert success is True
    assert error is None
    
    # Test updating non-existent notification
    success, error = await notif_service.update_notification_status(
        notification_id="NOTIF-999",
        status="in_progress",
        order_number="PM-12345"
    )
    assert success is False
    assert "not found" in error


@pytest.mark.asyncio
async def test_unified_integration_service(db: AsyncSession):
    """Test unified PM workflow integration service"""
    integration_service = PMWorkflowIntegrationService(db)
    
    # Verify all sub-services are initialized
    assert integration_service.mm is not None
    assert integration_service.fi is not None
    assert integration_service.hr is not None
    assert integration_service.notifications is not None


@pytest.mark.asyncio
async def test_validate_order_prerequisites(db: AsyncSession):
    """Test validation of order prerequisites across all systems"""
    integration_service = PMWorkflowIntegrationService(db)
    
    # Test order with valid prerequisites
    order_data = {
        "components": [
            {
                "material_number": "MAT-001",
                "quantity_required": Decimal("5")
            }
        ],
        "operations": [
            {
                "technician_id": "TECH-001"
            }
        ]
    }
    
    all_valid, blocking_reasons = await integration_service.validate_order_prerequisites(order_data)
    assert all_valid is True
    assert len(blocking_reasons) == 0
    
    # Test order with invalid prerequisites
    order_data_invalid = {
        "components": [
            {
                "material_number": "MAT-001",
                "quantity_required": Decimal("1000")  # More than available
            }
        ],
        "operations": [
            {
                "technician_id": "TECH-999"  # Non-existent
            }
        ]
    }
    
    all_valid, blocking_reasons = await integration_service.validate_order_prerequisites(order_data_invalid)
    assert all_valid is False
    assert len(blocking_reasons) > 0
