
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.pm_workflow_service import PMWorkflowService
from backend.models.pm_workflow_models import WorkflowOrderType, Priority, WorkflowMaintenanceOrder, WorkflowOperation, WorkflowComponent
from backend.services.fi_service import FIService, CostCenter
from backend.services.mm_service import MMService, Material
from backend.models.fi_models import FIApproval
from backend.models.mm_models import MMRequisition


@pytest.mark.asyncio
async def test_material_procurement_workflow(db: AsyncSession):
    """
    Tests the full material procurement workflow:
    1. Create a maintenance order with a component that is not in stock.
    2. Attempt to release the order, which should fail and trigger procurement.
    3. Check that a purchase requisition and a financial approval request have been created.
    4. Approve the financial approval request.
    5. Check that the stock level has been updated.
    6. Attempt to release the order again, which should now succeed.
    """
    # 1. Create data
    # Create material
    mm_service = MMService(db)
    material = await mm_service.create_material(
        material_id="MAT-999",
        description="Test Material",
        quantity=0,
        unit_of_measure="EA",
        reorder_level=10,
        storage_location="WH-01"
    )

    # Create cost center
    fi_service = FIService(db)
    cost_center = await fi_service.create_cost_center(
        cost_center_id="CC-TEST",
        name="Test Cost Center",
        budget_amount=Decimal("10000"),
        fiscal_year=2024,
        responsible_manager="testmgr"
    )

    # 2. Create a maintenance order with a component that is not in stock
    pm_workflow_service = PMWorkflowService(db)
    order = await pm_workflow_service.create_order(
        order_type=WorkflowOrderType.PREVENTIVE,
        equipment_id="EQ-001",
        functional_location="FL-001",
        priority=Priority.P3,
        planned_start_date=None,
        planned_end_date=None,
        breakdown_notification_id=None,
        created_by="testuser",
    )
    await pm_workflow_service.add_component(
        order_number=order.order_number,
        material_number=material.material_id,
        description="Test Material",
        quantity_required=Decimal("10"),
        unit_of_measure="EA",
        estimated_cost=Decimal("1000"),
    )
    operation = await pm_workflow_service.add_operation(
        order_number=order.order_number,
        operation_number="0010",
        work_center="WC-001",
        description="Test Operation",
        planned_hours=Decimal("2"),
    )
    await pm_workflow_service.calculate_cost_estimate(order.order_number)
    await pm_workflow_service.assign_technician(operation.operation_id, "tech-1", "testuser")
    order.status = "PLANNED"


    # 2. Attempt to release the order
    success, message, _ = await pm_workflow_service.release_order(
        order_number=order.order_number,
        released_by="testuser",
    )
    assert not success
    assert "material(s) not available" in message

    # 3. Check that a purchase requisition and a financial approval request have been created
    # Check for purchase requisition
    result = await db.execute(select(MMRequisition).where(MMRequisition.requested_by == "testuser"))
    requisition = result.scalar_one_or_none()
    assert requisition is not None
    assert requisition.material_id == material.material_id

    # Check for financial approval request
    result = await db.execute(select(FIApproval).where(FIApproval.requested_by == "testuser"))
    approval = result.scalar_one_or_none()
    assert approval is not None
    assert approval.ticket_id == requisition.ticket_id


    # 4. Approve the financial approval request
    await fi_service.approve_purchase_requisition(
        approval_id=approval.approval_id,
        decided_by="test_approver",
    )

    # 5. Check that the stock level has been updated
    material = await mm_service.get_material("MAT-999")
    assert material.quantity == 10

    # 6. Attempt to release the order again
    success, message, _ = await pm_workflow_service.release_order(
        order_number=order.order_number,
        released_by="testuser",
    )
    assert success

    # Clean up
    await db.delete(order)
    await db.delete(material)
    await db.delete(cost_center)
    await db.delete(requisition)
    await db.delete(approval)
    await db.commit()
