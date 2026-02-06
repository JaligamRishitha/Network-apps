"""
Unit tests for PM Workflow Screen 1: Order Planning & Initiation
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.pm_workflow_service import PMWorkflowService
from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder, WorkflowOperation, WorkflowComponent,
    WorkflowOrderType, WorkflowOrderStatus, Priority, OperationStatus
)


@pytest.mark.asyncio
class TestOrderCreation:
    """Test general maintenance order creation - Requirement 1.1"""
    
    async def test_create_general_maintenance_order(self, db: AsyncSession):
        """Test creating a general maintenance order"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=datetime.utcnow() + timedelta(days=1),
            planned_end_date=datetime.utcnow() + timedelta(days=2),
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        await db.commit()
        
        assert order is not None
        assert order.order_type == WorkflowOrderType.GENERAL
        assert order.status == WorkflowOrderStatus.CREATED
        assert order.equipment_id == "EQ-12345"
        assert order.priority == Priority.NORMAL
        assert order.created_by == "test_user"
        assert order.order_number.startswith("PM-")
    
    async def test_create_order_with_functional_location(self, db: AsyncSession):
        """Test creating order with functional location instead of equipment"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id=None,
            functional_location="PLANT-01-AREA-A",
            priority=Priority.HIGH,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        await db.commit()
        
        assert order.functional_location == "PLANT-01-AREA-A"
        assert order.equipment_id is None


@pytest.mark.asyncio
class TestBreakdownOrderCreation:
    """Test breakdown order auto-creation - Requirement 1.2"""
    
    async def test_create_breakdown_order(self, db: AsyncSession):
        """Test creating a breakdown maintenance order"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.BREAKDOWN,
            equipment_id="EQ-99999",
            functional_location=None,
            priority=Priority.URGENT,
            planned_start_date=datetime.utcnow(),
            planned_end_date=None,
            breakdown_notification_id="NOTIF-12345",
            created_by="system"
        )
        
        await db.commit()
        
        assert order.order_type == WorkflowOrderType.BREAKDOWN
        assert order.priority == Priority.URGENT
        assert order.breakdown_notification_id == "NOTIF-12345"
        assert order.order_number.startswith("BD-")
    
    async def test_breakdown_order_has_notification_reference(self, db: AsyncSession):
        """Test that breakdown order references notification"""
        service = PMWorkflowService(db)
        
        notification_id = "NOTIF-URGENT-001"
        order = await service.create_order(
            order_type=WorkflowOrderType.BREAKDOWN,
            equipment_id="EQ-CRITICAL",
            functional_location=None,
            priority=Priority.URGENT,
            planned_start_date=datetime.utcnow(),
            planned_end_date=None,
            breakdown_notification_id=notification_id,
            created_by="system"
        )
        
        await db.commit()
        
        assert order.breakdown_notification_id == notification_id


@pytest.mark.asyncio
class TestOperationsManagement:
    """Test operations management - Requirement 1.3"""
    
    async def test_add_operation_to_order(self, db: AsyncSession):
        """Test adding an operation to an order"""
        service = PMWorkflowService(db)
        
        # Create order first
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        # Add operation
        operation = await service.add_operation(
            order_number=order.order_number,
            operation_number="PM01",
            work_center="MAINT-01",
            description="Inspect equipment",
            planned_hours=Decimal("2.5"),
            technician_id="TECH-001"
        )
        
        await db.commit()
        
        assert operation is not None
        assert operation.operation_number == "PM01"
        assert operation.work_center == "MAINT-01"
        assert operation.planned_hours == Decimal("2.5")
        assert operation.status == OperationStatus.PLANNED
        assert operation.technician_id == "TECH-001"
    
    async def test_update_operation(self, db: AsyncSession):
        """Test updating an operation"""
        service = PMWorkflowService(db)
        
        # Create order and operation
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        operation = await service.add_operation(
            order_number=order.order_number,
            operation_number="PM01",
            work_center="MAINT-01",
            description="Original description",
            planned_hours=Decimal("2.0"),
            technician_id=None
        )
        
        await db.commit()
        
        # Update operation
        updated = await service.update_operation(
            operation_id=operation.operation_id,
            work_center="MAINT-02",
            description="Updated description",
            planned_hours=Decimal("3.0"),
            technician_id="TECH-002"
        )
        
        await db.commit()
        
        assert updated is not None
        assert updated.work_center == "MAINT-02"
        assert updated.description == "Updated description"
        assert updated.planned_hours == Decimal("3.0")
        assert updated.technician_id == "TECH-002"
    
    async def test_delete_operation(self, db: AsyncSession):
        """Test deleting an operation"""
        service = PMWorkflowService(db)
        
        # Create order and operation
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        operation = await service.add_operation(
            order_number=order.order_number,
            operation_number="PM01",
            work_center="MAINT-01",
            description="To be deleted",
            planned_hours=Decimal("1.0"),
            technician_id=None
        )
        
        await db.commit()
        
        # Delete operation
        success = await service.delete_operation(operation.operation_id)
        await db.commit()
        
        assert success is True
        
        # Verify deletion
        deleted_op = await service.update_operation(
            operation_id=operation.operation_id,
            work_center="MAINT-01",
            description="Should not exist",
            planned_hours=Decimal("1.0"),
            technician_id=None
        )
        
        assert deleted_op is None


@pytest.mark.asyncio
class TestComponentsManagement:
    """Test components management - Requirement 1.4"""
    
    async def test_add_component_with_master_data(self, db: AsyncSession):
        """Test adding a component with master data"""
        service = PMWorkflowService(db)
        
        # Create order first
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        # Add component
        component = await service.add_component(
            order_number=order.order_number,
            material_number="MAT-001",
            description="Bearing assembly",
            quantity_required=Decimal("2.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("150.00"),
            has_master_data=True
        )
        
        await db.commit()
        
        assert component is not None
        assert component.material_number == "MAT-001"
        assert component.description == "Bearing assembly"
        assert component.quantity_required == Decimal("2.0")
        assert component.unit_of_measure == "EA"
        assert component.estimated_cost == Decimal("150.00")
        assert component.has_master_data is True
        assert component.quantity_issued == Decimal("0")
    
    async def test_add_component_without_master_data(self, db: AsyncSession):
        """Test adding a non-stock component"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        component = await service.add_component(
            order_number=order.order_number,
            material_number=None,
            description="Custom fabricated part",
            quantity_required=Decimal("1.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("500.00"),
            has_master_data=False
        )
        
        await db.commit()
        
        assert component.material_number is None
        assert component.has_master_data is False
        assert component.description == "Custom fabricated part"
    
    async def test_update_component(self, db: AsyncSession):
        """Test updating a component"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        component = await service.add_component(
            order_number=order.order_number,
            material_number="MAT-001",
            description="Original description",
            quantity_required=Decimal("1.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("100.00"),
            has_master_data=True
        )
        
        await db.commit()
        
        # Update component
        updated = await service.update_component(
            component_id=component.component_id,
            material_number="MAT-002",
            description="Updated description",
            quantity_required=Decimal("3.0"),
            unit_of_measure="KG",
            estimated_cost=Decimal("200.00"),
            has_master_data=True
        )
        
        await db.commit()
        
        assert updated is not None
        assert updated.material_number == "MAT-002"
        assert updated.description == "Updated description"
        assert updated.quantity_required == Decimal("3.0")
        assert updated.estimated_cost == Decimal("200.00")
    
    async def test_delete_component(self, db: AsyncSession):
        """Test deleting a component"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        component = await service.add_component(
            order_number=order.order_number,
            material_number="MAT-001",
            description="To be deleted",
            quantity_required=Decimal("1.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("50.00"),
            has_master_data=True
        )
        
        await db.commit()
        
        # Delete component
        success = await service.delete_component(component.component_id)
        await db.commit()
        
        assert success is True


@pytest.mark.asyncio
class TestCostEstimation:
    """Test cost estimation calculator - Requirement 1.5"""
    
    async def test_calculate_cost_estimate(self, db: AsyncSession):
        """Test calculating cost estimate from operations and components"""
        service = PMWorkflowService(db)
        
        # Create order
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        # Add operations (2 hours @ $50/hour = $100)
        await service.add_operation(
            order_number=order.order_number,
            operation_number="PM01",
            work_center="MAINT-01",
            description="Operation 1",
            planned_hours=Decimal("2.0"),
            technician_id=None
        )
        
        # Add components ($150)
        await service.add_component(
            order_number=order.order_number,
            material_number="MAT-001",
            description="Component 1",
            quantity_required=Decimal("1.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("150.00"),
            has_master_data=True
        )
        
        await db.commit()
        
        # Calculate costs
        cost_summary = await service.calculate_cost_estimate(order.order_number)
        await db.commit()
        
        assert cost_summary is not None
        assert cost_summary.estimated_material_cost == Decimal("150.00")
        assert cost_summary.estimated_labor_cost == Decimal("100.00")  # 2 hours * $50
        assert cost_summary.estimated_external_cost == Decimal("0")
        assert cost_summary.estimated_total_cost == Decimal("250.00")
    
    async def test_cost_estimate_with_multiple_items(self, db: AsyncSession):
        """Test cost estimate with multiple operations and components"""
        service = PMWorkflowService(db)
        
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        # Add multiple operations
        await service.add_operation(
            order_number=order.order_number,
            operation_number="PM01",
            work_center="MAINT-01",
            description="Operation 1",
            planned_hours=Decimal("3.0"),
            technician_id=None
        )
        
        await service.add_operation(
            order_number=order.order_number,
            operation_number="PM02",
            work_center="MAINT-01",
            description="Operation 2",
            planned_hours=Decimal("1.5"),
            technician_id=None
        )
        
        # Add multiple components
        await service.add_component(
            order_number=order.order_number,
            material_number="MAT-001",
            description="Component 1",
            quantity_required=Decimal("2.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("100.00"),
            has_master_data=True
        )
        
        await service.add_component(
            order_number=order.order_number,
            material_number="MAT-002",
            description="Component 2",
            quantity_required=Decimal("1.0"),
            unit_of_measure="EA",
            estimated_cost=Decimal("75.00"),
            has_master_data=True
        )
        
        await db.commit()
        
        # Calculate costs
        cost_summary = await service.calculate_cost_estimate(order.order_number)
        await db.commit()
        
        # Material: 100 + 75 = 175
        # Labor: (3.0 + 1.5) * 50 = 225
        # Total: 400
        assert cost_summary.estimated_material_cost == Decimal("175.00")
        assert cost_summary.estimated_labor_cost == Decimal("225.00")
        assert cost_summary.estimated_total_cost == Decimal("400.00")
