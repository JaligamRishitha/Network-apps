"""
Integration tests for PM Workflow Screen 3: Order Release & Execution Readiness
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.pm_workflow_service import PMWorkflowService
from backend.models.pm_workflow_models import (
    WorkflowOrderType, WorkflowOrderStatus, Priority
)


@pytest.mark.asyncio
async def test_release_order_success(db: AsyncSession):
    """Test successful order release"""
    service = PMWorkflowService(db)
    
    # Create order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="EQ-001",
        functional_location="FL-001",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=datetime.utcnow() + timedelta(days=7),
        breakdown_notification_id=None,
        created_by="test_user"
    )
    
    # Add operation with technician
    await service.add_operation(
        order_number=order.order_number,
        operation_number="10",
        work_center="WC-001",
        description="Test operation",
        planned_hours=Decimal("8.0"),
        technician_id="TECH-001"
    )
    
    # Add component
    await service.add_component(
        order_number=order.order_number,
        material_number="MAT-001",
        description="Test material",
        quantity_required=Decimal("10.0"),
        unit_of_measure="EA",
        estimated_cost=Decimal("100.0"),
        has_master_data=True
    )
    
    # Calculate costs
    await service.calculate_cost_estimate(order.order_number)
    
    await db.commit()
    
    # Transition to Planned
    order.status = WorkflowOrderStatus.PLANNED
    await db.commit()
    
    # Release order
    success, error, released_order = await service.release_order(
        order_number=order.order_number,
        released_by="test_user",
        override_blocks=False
    )
    
    assert success is True
    assert error is None
    assert released_order is not None
    assert released_order.status == WorkflowOrderStatus.RELEASED
    assert released_order.released_by == "test_user"
    assert released_order.released_at is not None


@pytest.mark.asyncio
async def test_release_order_without_technician_fails(db: AsyncSession):
    """Test that order release fails without technician assignment"""
    service = PMWorkflowService(db)
    
    # Create order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="EQ-002",
        functional_location="FL-002",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=datetime.utcnow() + timedelta(days=7),
        breakdown_notification_id=None,
        created_by="test_user"
    )
    
    # Add operation WITHOUT technician
    await service.add_operation(
        order_number=order.order_number,
        operation_number="10",
        work_center="WC-001",
        description="Test operation",
        planned_hours=Decimal("8.0"),
        technician_id=None  # No technician
    )
    
    # Calculate costs
    await service.calculate_cost_estimate(order.order_number)
    
    await db.commit()
    
    # Transition to Planned
    order.status = WorkflowOrderStatus.PLANNED
    await db.commit()
    
    # Try to release order
    success, error, released_order = await service.release_order(
        order_number=order.order_number,
        released_by="test_user",
        override_blocks=False
    )
    
    assert success is False
    assert error is not None
    assert "technician" in error.lower()
    assert released_order is None


@pytest.mark.asyncio
async def test_release_breakdown_order_with_reduced_validation(db: AsyncSession):
    """Test that breakdown orders have reduced validation"""
    service = PMWorkflowService(db)
    
    # Create breakdown order
    order = await service.create_order(
        order_type=WorkflowOrderType.BREAKDOWN,
        equipment_id="EQ-003",
        functional_location="FL-003",
        priority=Priority.URGENT,
        planned_start_date=datetime.utcnow(),
        planned_end_date=datetime.utcnow() + timedelta(days=1),
        breakdown_notification_id="NOTIF-001",
        created_by="test_user"
    )
    
    # Add operation with technician
    await service.add_operation(
        order_number=order.order_number,
        operation_number="10",
        work_center="WC-001",
        description="Emergency repair",
        planned_hours=Decimal("4.0"),
        technician_id="TECH-001"
    )
    
    # Calculate costs
    await service.calculate_cost_estimate(order.order_number)
    
    await db.commit()
    
    # Transition to Planned
    order.status = WorkflowOrderStatus.PLANNED
    await db.commit()
    
    # Release order (should succeed even without permits/materials)
    success, error, released_order = await service.release_order(
        order_number=order.order_number,
        released_by="test_user",
        override_blocks=False
    )
    
    assert success is True
    assert error is None
    assert released_order is not None
    assert released_order.status == WorkflowOrderStatus.RELEASED


@pytest.mark.asyncio
async def test_get_readiness_checklist(db: AsyncSession):
    """Test readiness checklist generation"""
    service = PMWorkflowService(db)
    
    # Create order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="EQ-004",
        functional_location="FL-004",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=datetime.utcnow() + timedelta(days=7),
        breakdown_notification_id=None,
        created_by="test_user"
    )
    
    # Add operation with technician
    await service.add_operation(
        order_number=order.order_number,
        operation_number="10",
        work_center="WC-001",
        description="Test operation",
        planned_hours=Decimal("8.0"),
        technician_id="TECH-001"
    )
    
    # Calculate costs
    await service.calculate_cost_estimate(order.order_number)
    
    await db.commit()
    
    # Transition to Planned
    order.status = WorkflowOrderStatus.PLANNED
    await db.commit()
    
    # Get readiness checklist
    checklist = await service.get_readiness_checklist(order.order_number)
    
    assert checklist is not None
    assert "order_number" in checklist
    assert checklist["order_number"] == order.order_number
    assert "can_release" in checklist
    assert "blocking_reasons" in checklist
    assert "checklist" in checklist
    assert "permits" in checklist["checklist"]
    assert "materials" in checklist["checklist"]
    assert "technician" in checklist["checklist"]


@pytest.mark.asyncio
async def test_assign_technician(db: AsyncSession):
    """Test technician assignment to operation"""
    service = PMWorkflowService(db)
    
    # Create order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="EQ-005",
        functional_location="FL-005",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=datetime.utcnow() + timedelta(days=7),
        breakdown_notification_id=None,
        created_by="test_user"
    )
    
    # Add operation without technician
    operation = await service.add_operation(
        order_number=order.order_number,
        operation_number="10",
        work_center="WC-001",
        description="Test operation",
        planned_hours=Decimal("8.0"),
        technician_id=None
    )
    
    await db.commit()
    
    # Assign technician
    updated_operation = await service.assign_technician(
        operation_id=operation.operation_id,
        technician_id="TECH-002",
        assigned_by="test_user"
    )
    
    assert updated_operation is not None
    assert updated_operation.technician_id == "TECH-002"


@pytest.mark.asyncio
async def test_release_with_override(db: AsyncSession):
    """Test order release with override"""
    service = PMWorkflowService(db)
    
    # Create order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="EQ-006",
        functional_location="FL-006",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=datetime.utcnow() + timedelta(days=7),
        breakdown_notification_id=None,
        created_by="test_user"
    )
    
    # Add operation with technician
    await service.add_operation(
        order_number=order.order_number,
        operation_number="10",
        work_center="WC-001",
        description="Test operation",
        planned_hours=Decimal("8.0"),
        technician_id="TECH-001"
    )
    
    # Calculate costs
    await service.calculate_cost_estimate(order.order_number)
    
    await db.commit()
    
    # Transition to Planned
    order.status = WorkflowOrderStatus.PLANNED
    await db.commit()
    
    # Release with override (even if there are blocking reasons)
    success, error, released_order = await service.release_order(
        order_number=order.order_number,
        released_by="test_user",
        override_blocks=True,
        override_reason="Emergency maintenance required"
    )
    
    assert success is True
    assert error is None
    assert released_order is not None
    assert released_order.status == WorkflowOrderStatus.RELEASED
