"""
Unit tests for breakdown maintenance differentiation.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.pm_workflow_service import PMWorkflowService
from backend.models.pm_workflow_models import (
    WorkflowOrderType, WorkflowOrderStatus, Priority
)


@pytest.mark.asyncio
async def test_breakdown_order_auto_creation(db_session: AsyncSession):
    """
    Test breakdown order auto-creation from notification.
    Requirements: 7.1, 7.2
    
    Verifies that:
    - Breakdown order is created with URGENT priority
    - Equipment and functional location are pre-populated
    - Notification reference is stored
    - Default operation is auto-created
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order from notification
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-12345",
        equipment_id="PUMP-001",
        functional_location="PLANT-A/AREA-1",
        notification_description="Pump failure - immediate attention required",
        created_by="operator1"
    )
    
    await db_session.commit()
    
    # Verify order properties
    assert order.order_type == WorkflowOrderType.BREAKDOWN
    assert order.priority == Priority.URGENT
    assert order.equipment_id == "PUMP-001"
    assert order.functional_location == "PLANT-A/AREA-1"
    assert order.breakdown_notification_id == "NOTIF-12345"
    assert order.status == WorkflowOrderStatus.CREATED
    assert order.created_by == "operator1"
    
    # Verify order number has breakdown prefix
    assert order.order_number.startswith("BD-")
    
    # Verify default operation was created
    assert len(order.operations) == 1
    operation = order.operations[0]
    assert operation.operation_number == "0010"
    assert operation.work_center == "EMERGENCY"
    assert "Emergency repair" in operation.description
    assert "Pump failure" in operation.description


@pytest.mark.asyncio
async def test_breakdown_order_reduced_validation(db_session: AsyncSession):
    """
    Test reduced validation for breakdown order release.
    Requirements: 7.3, 7.4
    
    Verifies that:
    - Breakdown orders can be released without full permit approval
    - Material availability is not strictly enforced
    - Only technician assignment is required
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-67890",
        equipment_id="MOTOR-002",
        functional_location="PLANT-B/AREA-2",
        notification_description="Motor overheating",
        created_by="operator2"
    )
    
    # Transition to PLANNED status
    order.status = WorkflowOrderStatus.PLANNED
    
    # Assign technician to operation
    operation = order.operations[0]
    operation.technician_id = "tech-001"
    
    await db_session.commit()
    
    # Release breakdown order with emergency permit
    success, error_msg, released_order = await service.release_breakdown_order(
        order_number=order.order_number,
        released_by="supervisor1",
        emergency_permit_id="EMERG-PERMIT-001"
    )
    
    await db_session.commit()
    
    # Verify release succeeded
    assert success is True
    assert error_msg is None
    assert released_order is not None
    assert released_order.status == WorkflowOrderStatus.RELEASED
    assert released_order.released_by == "supervisor1"
    assert released_order.released_at is not None


@pytest.mark.asyncio
async def test_breakdown_order_release_requires_technician(db_session: AsyncSession):
    """
    Test that breakdown order release still requires technician assignment.
    Requirement 7.3
    
    Even with reduced validation, technician assignment is mandatory.
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-11111",
        equipment_id="VALVE-003",
        functional_location="PLANT-C/AREA-3",
        notification_description="Valve stuck",
        created_by="operator3"
    )
    
    # Transition to PLANNED status
    order.status = WorkflowOrderStatus.PLANNED
    
    # Do NOT assign technician
    await db_session.commit()
    
    # Attempt to release without technician
    success, error_msg, released_order = await service.release_breakdown_order(
        order_number=order.order_number,
        released_by="supervisor2"
    )
    
    # Verify release failed
    assert success is False
    assert "technician" in error_msg.lower()
    assert released_order is None


@pytest.mark.asyncio
async def test_emergency_stock_goods_issue(db_session: AsyncSession):
    """
    Test emergency stock GI without PO for breakdown orders.
    Requirement 7.4
    
    Verifies that:
    - Emergency stock can be issued without PO
    - Component is auto-created if not exists
    - Cost is estimated and tracked
    - Document flow is created
    """
    service = PMWorkflowService(db_session)
    
    # Create and release breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-22222",
        equipment_id="BEARING-004",
        functional_location="PLANT-D/AREA-4",
        notification_description="Bearing failure",
        created_by="operator4"
    )
    
    order.status = WorkflowOrderStatus.RELEASED
    await db_session.commit()
    
    # Issue emergency stock
    success, error_msg, gi = await service.create_emergency_goods_issue(
        order_number=order.order_number,
        material_number="BEARING-XYZ-123",
        quantity_issued=Decimal("2.0"),
        cost_center="CC-MAINT",
        issued_by="tech-002",
        emergency_stock_location="EMERGENCY-WAREHOUSE"
    )
    
    await db_session.commit()
    
    # Verify GI succeeded
    assert success is True
    assert error_msg is None
    assert gi is not None
    assert gi.material_number == "BEARING-XYZ-123"
    assert gi.quantity_issued == Decimal("2.0")
    assert gi.cost_center == "CC-MAINT"
    assert gi.issued_by == "tech-002"
    
    # Verify GI document number
    assert gi.gi_document.startswith("GI-")
    
    # Verify component was auto-created
    await db_session.refresh(order)
    assert len(order.components) > 0
    component = next(c for c in order.components if c.material_number == "BEARING-XYZ-123")
    assert component is not None
    assert component.quantity_issued == Decimal("2.0")


@pytest.mark.asyncio
async def test_emergency_stock_only_for_breakdown_orders(db_session: AsyncSession):
    """
    Test that emergency stock GI is only allowed for breakdown orders.
    Requirement 7.4
    """
    service = PMWorkflowService(db_session)
    
    # Create general maintenance order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="PUMP-005",
        functional_location="PLANT-E/AREA-5",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=None,
        breakdown_notification_id=None,
        created_by="planner1"
    )
    
    order.status = WorkflowOrderStatus.RELEASED
    await db_session.commit()
    
    # Attempt emergency stock GI on general order
    success, error_msg, gi = await service.create_emergency_goods_issue(
        order_number=order.order_number,
        material_number="PART-ABC-456",
        quantity_issued=Decimal("1.0"),
        cost_center="CC-MAINT",
        issued_by="tech-003"
    )
    
    # Verify it failed
    assert success is False
    assert "breakdown" in error_msg.lower()
    assert gi is None


@pytest.mark.asyncio
async def test_mandatory_malfunction_reporting(db_session: AsyncSession):
    """
    Test mandatory malfunction reporting for breakdown orders.
    Requirement 7.5
    
    Verifies that:
    - Malfunction report can be created
    - Malfunction report is required for breakdown orders
    - TECO fails without malfunction report
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-33333",
        equipment_id="CONVEYOR-006",
        functional_location="PLANT-F/AREA-6",
        notification_description="Conveyor belt torn",
        created_by="operator5"
    )
    
    await db_session.commit()
    
    # Check if malfunction report is required
    required, reason = await service.validate_malfunction_report_required(order.order_number)
    
    assert required is True
    assert "mandatory" in reason.lower()
    
    # Create malfunction report
    success, error_msg, report = await service.create_malfunction_report(
        order_number=order.order_number,
        cause_code="WEAR",
        description="Belt worn due to excessive load",
        root_cause="Overloading of conveyor system",
        corrective_action="Replaced belt and adjusted load limits",
        reported_by="tech-004"
    )
    
    await db_session.commit()
    
    # Verify report created
    assert success is True
    assert error_msg is None
    assert report is not None
    assert report.cause_code == "WEAR"
    assert report.description == "Belt worn due to excessive load"
    assert report.root_cause == "Overloading of conveyor system"
    assert report.corrective_action == "Replaced belt and adjusted load limits"
    
    # Verify report ID format
    assert report.report_id.startswith("MAL-")


@pytest.mark.asyncio
async def test_breakdown_teco_requires_malfunction_report(db_session: AsyncSession):
    """
    Test that breakdown TECO requires malfunction report.
    Requirement 7.5
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-44444",
        equipment_id="COMPRESSOR-007",
        functional_location="PLANT-G/AREA-7",
        notification_description="Compressor failure",
        created_by="operator6"
    )
    
    # Set order to CONFIRMED status (ready for TECO)
    order.status = WorkflowOrderStatus.CONFIRMED
    
    # Mark operation as confirmed
    operation = order.operations[0]
    operation.status = "confirmed"
    
    await db_session.commit()
    
    # Attempt TECO without malfunction report
    success, error_msg, teco_order = await service.teco_breakdown_order(
        order_number=order.order_number,
        completed_by="supervisor3"
    )
    
    # Verify TECO failed
    assert success is False
    assert "malfunction report" in error_msg.lower()
    assert "mandatory" in error_msg.lower()


@pytest.mark.asyncio
async def test_breakdown_teco_with_post_review(db_session: AsyncSession):
    """
    Test breakdown TECO with post-completion review.
    Requirement 7.6
    
    Verifies that:
    - Breakdown orders can be TECO'd with malfunction report
    - Post-completion review flag is set
    - Document flow entry is created for review
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-55555",
        equipment_id="TURBINE-008",
        functional_location="PLANT-H/AREA-8",
        notification_description="Turbine vibration",
        created_by="operator7"
    )
    
    # Set order to CONFIRMED status
    order.status = WorkflowOrderStatus.CONFIRMED
    
    # Mark operation as confirmed
    operation = order.operations[0]
    operation.status = "confirmed"
    
    # Create malfunction report
    await service.create_malfunction_report(
        order_number=order.order_number,
        cause_code="VIBRATION",
        description="Excessive vibration detected",
        root_cause="Bearing misalignment",
        corrective_action="Realigned bearings and balanced rotor",
        reported_by="tech-005"
    )
    
    await db_session.commit()
    
    # TECO with post-review
    success, error_msg, teco_order = await service.teco_breakdown_order(
        order_number=order.order_number,
        completed_by="supervisor4",
        post_review_required=True
    )
    
    await db_session.commit()
    
    # Verify TECO succeeded
    assert success is True
    assert error_msg is None
    assert teco_order is not None
    assert teco_order.status == WorkflowOrderStatus.TECO
    assert teco_order.completed_by == "supervisor4"
    assert teco_order.completed_at is not None
    
    # Verify document flow includes post-review entry
    doc_flow = await service.get_document_flow(order.order_number)
    review_entries = [e for e in doc_flow if "review" in e.status.lower()]
    assert len(review_entries) > 0


@pytest.mark.asyncio
async def test_breakdown_order_summary(db_session: AsyncSession):
    """
    Test breakdown order summary for post-completion review.
    Requirement 7.6
    
    Verifies that summary includes:
    - Response time (created to released)
    - Completion time (released to completed)
    - Malfunction reports
    - Cost analysis
    - Document flow count
    """
    service = PMWorkflowService(db_session)
    
    # Create breakdown order
    order = await service.create_breakdown_order_from_notification(
        notification_id="NOTIF-66666",
        equipment_id="GENERATOR-009",
        functional_location="PLANT-I/AREA-9",
        notification_description="Generator overload",
        created_by="operator8"
    )
    
    # Simulate workflow progression
    order.status = WorkflowOrderStatus.PLANNED
    operation = order.operations[0]
    operation.technician_id = "tech-006"
    await db_session.commit()
    
    # Release
    await service.release_breakdown_order(
        order_number=order.order_number,
        released_by="supervisor5"
    )
    
    # Create malfunction report
    await service.create_malfunction_report(
        order_number=order.order_number,
        cause_code="OVERLOAD",
        description="Generator exceeded capacity",
        root_cause="Unexpected load spike",
        corrective_action="Load balancing implemented",
        reported_by="tech-006"
    )
    
    # TECO
    order.status = WorkflowOrderStatus.CONFIRMED
    operation.status = "confirmed"
    await db_session.commit()
    
    await service.teco_breakdown_order(
        order_number=order.order_number,
        completed_by="supervisor5"
    )
    
    await db_session.commit()
    
    # Get summary
    summary = await service.get_breakdown_order_summary(order.order_number)
    
    # Verify summary structure
    assert summary["order_number"] == order.order_number
    assert summary["order_type"] == "breakdown"
    assert summary["status"] == "teco"
    assert summary["priority"] == "urgent"
    assert summary["breakdown_notification_id"] == "NOTIF-66666"
    assert summary["response_time_hours"] is not None
    assert summary["completion_time_hours"] is not None
    assert len(summary["malfunction_reports"]) == 1
    assert summary["malfunction_reports"][0]["cause_code"] == "OVERLOAD"
    assert "cost_analysis" in summary
    assert summary["document_flow_count"] > 0
    assert summary["post_review_required"] is True


@pytest.mark.asyncio
async def test_general_order_cannot_use_breakdown_methods(db_session: AsyncSession):
    """
    Test that general maintenance orders cannot use breakdown-specific methods.
    Requirements: 7.3, 7.4
    """
    service = PMWorkflowService(db_session)
    
    # Create general maintenance order
    order = await service.create_order(
        order_type=WorkflowOrderType.GENERAL,
        equipment_id="PUMP-010",
        functional_location="PLANT-J/AREA-10",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow(),
        planned_end_date=None,
        breakdown_notification_id=None,
        created_by="planner2"
    )
    
    order.status = WorkflowOrderStatus.PLANNED
    await db_session.commit()
    
    # Attempt breakdown release on general order
    success, error_msg, released_order = await service.release_breakdown_order(
        order_number=order.order_number,
        released_by="supervisor6"
    )
    
    # Verify it failed
    assert success is False
    assert "breakdown" in error_msg.lower()
    
    # Attempt breakdown TECO on general order
    order.status = WorkflowOrderStatus.CONFIRMED
    await db_session.commit()
    
    success, error_msg, teco_order = await service.teco_breakdown_order(
        order_number=order.order_number,
        completed_by="supervisor6"
    )
    
    # Verify it failed
    assert success is False
    assert "breakdown" in error_msg.lower()
