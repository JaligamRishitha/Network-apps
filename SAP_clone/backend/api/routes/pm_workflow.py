"""
PM Workflow API Routes - Screen 1: Order Planning & Initiation
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.services.pm_workflow_service import PMWorkflowService
from backend.models.pm_workflow_models import (
    WorkflowOrderType, WorkflowOrderStatus, Priority,
    OperationStatus, POType, POStatus
)


router = APIRouter(prefix="/pm-workflow", tags=["PM Workflow"])


# Request/Response Models for Screen 1

class OperationRequest(BaseModel):
    """Operation data for order creation - Requirement 1.3"""
    operation_number: str
    work_center: str
    description: str
    planned_hours: float
    technician_id: Optional[str] = None


class ComponentRequest(BaseModel):
    """Component data for order creation - Requirement 1.4"""
    material_number: Optional[str] = None
    description: str
    quantity_required: float
    unit_of_measure: str
    estimated_cost: float
    has_master_data: bool = True


class PermitRequest(BaseModel):
    """Permit request data - Requirement 1.6"""
    permit_type: str
    approver: str
    required: bool = True


class OrderCreateRequest(BaseModel):
    """Create maintenance order - Requirements 1.1, 1.7"""
    order_type: str = Field(..., description="general or breakdown")
    equipment_id: Optional[str] = None
    functional_location: Optional[str] = None
    priority: str = "normal"
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    breakdown_notification_id: Optional[str] = None
    created_by: str
    operations: List[OperationRequest] = []
    components: List[ComponentRequest] = []
    permits: List[PermitRequest] = []
    
    class Config:
        use_enum_values = True


class OperationResponse(BaseModel):
    """Operation response"""
    operation_id: str
    operation_number: str
    work_center: str
    description: str
    planned_hours: float
    actual_hours: Optional[float]
    status: str
    technician_id: Optional[str]


class ComponentResponse(BaseModel):
    """Component response"""
    component_id: str
    material_number: Optional[str]
    description: str
    quantity_required: float
    quantity_issued: float
    unit_of_measure: str
    estimated_cost: float
    actual_cost: Optional[float]
    has_master_data: bool


class CostSummaryResponse(BaseModel):
    """Cost summary response - Requirement 1.5"""
    estimated_material_cost: float
    estimated_labor_cost: float
    estimated_external_cost: float
    estimated_total_cost: float


class OrderResponse(BaseModel):
    """Maintenance order response"""
    order_number: str
    order_type: str
    status: str
    equipment_id: Optional[str]
    functional_location: Optional[str]
    priority: str
    planned_start_date: Optional[str]
    planned_end_date: Optional[str]
    breakdown_notification_id: Optional[str]
    created_by: str
    created_at: str
    operations: List[OperationResponse]
    components: List[ComponentResponse]
    cost_summary: Optional[CostSummaryResponse]


# Screen 1: Order Planning & Initiation Routes

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new maintenance order (general or breakdown).
    Requirements: 1.1, 1.2, 1.7
    """
    service = PMWorkflowService(db)
    
    try:
        order_type = WorkflowOrderType(request.order_type.lower())
        priority = Priority(request.priority.lower())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    
    # Validate required fields
    if not request.equipment_id and not request.functional_location:
        raise HTTPException(
            status_code=400,
            detail="Either equipment_id or functional_location is required"
        )
    
    # Create order
    order = await service.create_order(
        order_type=order_type,
        equipment_id=request.equipment_id,
        functional_location=request.functional_location,
        priority=priority,
        planned_start_date=request.planned_start_date,
        planned_end_date=request.planned_end_date,
        breakdown_notification_id=request.breakdown_notification_id,
        created_by=request.created_by
    )
    
    # Add operations
    for op_req in request.operations:
        await service.add_operation(
            order_number=order.order_number,
            operation_number=op_req.operation_number,
            work_center=op_req.work_center,
            description=op_req.description,
            planned_hours=Decimal(str(op_req.planned_hours)),
            technician_id=op_req.technician_id
        )
    
    # Add components
    for comp_req in request.components:
        await service.add_component(
            order_number=order.order_number,
            material_number=comp_req.material_number,
            description=comp_req.description,
            quantity_required=Decimal(str(comp_req.quantity_required)),
            unit_of_measure=comp_req.unit_of_measure,
            estimated_cost=Decimal(str(comp_req.estimated_cost)),
            has_master_data=comp_req.has_master_data
        )
    
    # Calculate cost estimate (skip if no components/operations)
    if request.components or request.operations:
        await service.calculate_cost_estimate(order.order_number)
    
    await db.commit()
    
    # Reload order with relationships
    order = await service.get_order(order.order_number)
    
    # Build response
    return await _build_order_response(order)


@router.get("/orders/{order_number}", response_model=OrderResponse)
async def get_order(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get maintenance order by number"""
    service = PMWorkflowService(db)
    order = await service.get_order(order_number)
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_number}")
    
    return await _build_order_response(order)


@router.get("/orders/recent", response_model=List[dict])
async def get_recent_orders(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent maintenance orders for dashboard/list views.
    Returns simplified order data without full relationships.
    """
    from sqlalchemy import desc
    
    result = await db.execute(
        select(WorkflowMaintenanceOrder)
        .order_by(desc(WorkflowMaintenanceOrder.created_at))
        .limit(limit)
    )
    orders = result.scalars().all()
    
    return [
        {
            "order_number": order.order_number,
            "order_type": order.order_type.value,
            "status": order.status.value,
            "priority": order.priority.value,
            "equipment_id": order.equipment_id,
            "functional_location": order.functional_location,
            "created_at": order.created_at.isoformat(),
            "created_by": order.created_by,
            "planned_start_date": order.planned_start_date.isoformat() if order.planned_start_date else None,
            "planned_end_date": order.planned_end_date.isoformat() if order.planned_end_date else None,
        }
        for order in orders
    ]


@router.post("/orders/{order_number}/operations", response_model=OperationResponse)
async def add_operation(
    order_number: str,
    request: OperationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Add operation to maintenance order.
    Requirement 1.3
    """
    service = PMWorkflowService(db)
    
    operation = await service.add_operation(
        order_number=order_number,
        operation_number=request.operation_number,
        work_center=request.work_center,
        description=request.description,
        planned_hours=Decimal(str(request.planned_hours)),
        technician_id=request.technician_id
    )
    
    await db.commit()
    
    return OperationResponse(
        operation_id=operation.operation_id,
        operation_number=operation.operation_number,
        work_center=operation.work_center,
        description=operation.description,
        planned_hours=float(operation.planned_hours),
        actual_hours=float(operation.actual_hours) if operation.actual_hours else None,
        status=operation.status.value,
        technician_id=operation.technician_id
    )


@router.put("/orders/{order_number}/operations/{operation_id}")
async def update_operation(
    order_number: str,
    operation_id: str,
    request: OperationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update operation - Requirement 1.3"""
    service = PMWorkflowService(db)
    
    operation = await service.update_operation(
        operation_id=operation_id,
        work_center=request.work_center,
        description=request.description,
        planned_hours=Decimal(str(request.planned_hours)),
        technician_id=request.technician_id
    )
    
    if not operation:
        raise HTTPException(status_code=404, detail=f"Operation not found: {operation_id}")
    
    await db.commit()
    
    return {"message": "Operation updated successfully"}


@router.delete("/orders/{order_number}/operations/{operation_id}")
async def delete_operation(
    order_number: str,
    operation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete operation - Requirement 1.3"""
    service = PMWorkflowService(db)
    
    success = await service.delete_operation(operation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Operation not found: {operation_id}")
    
    await db.commit()
    
    return {"message": "Operation deleted successfully"}


@router.post("/orders/{order_number}/components", response_model=ComponentResponse)
async def add_component(
    order_number: str,
    request: ComponentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Add component to maintenance order.
    Requirement 1.4
    """
    service = PMWorkflowService(db)
    
    component = await service.add_component(
        order_number=order_number,
        material_number=request.material_number,
        description=request.description,
        quantity_required=Decimal(str(request.quantity_required)),
        unit_of_measure=request.unit_of_measure,
        estimated_cost=Decimal(str(request.estimated_cost)),
        has_master_data=request.has_master_data
    )
    
    await db.commit()
    
    return ComponentResponse(
        component_id=component.component_id,
        material_number=component.material_number,
        description=component.description,
        quantity_required=float(component.quantity_required),
        quantity_issued=float(component.quantity_issued),
        unit_of_measure=component.unit_of_measure,
        estimated_cost=float(component.estimated_cost),
        actual_cost=float(component.actual_cost) if component.actual_cost else None,
        has_master_data=component.has_master_data
    )


@router.put("/orders/{order_number}/components/{component_id}")
async def update_component(
    order_number: str,
    component_id: str,
    request: ComponentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update component - Requirement 1.4"""
    service = PMWorkflowService(db)
    
    component = await service.update_component(
        component_id=component_id,
        material_number=request.material_number,
        description=request.description,
        quantity_required=Decimal(str(request.quantity_required)),
        unit_of_measure=request.unit_of_measure,
        estimated_cost=Decimal(str(request.estimated_cost)),
        has_master_data=request.has_master_data
    )
    
    if not component:
        raise HTTPException(status_code=404, detail=f"Component not found: {component_id}")
    
    await db.commit()
    
    return {"message": "Component updated successfully"}


@router.delete("/orders/{order_number}/components/{component_id}")
async def delete_component(
    order_number: str,
    component_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete component - Requirement 1.4"""
    service = PMWorkflowService(db)
    
    success = await service.delete_component(component_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Component not found: {component_id}")
    
    await db.commit()
    
    return {"message": "Component deleted successfully"}


@router.post("/orders/{order_number}/calculate-costs", response_model=CostSummaryResponse)
async def calculate_costs(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate cost estimate for order.
    Requirement 1.5
    """
    service = PMWorkflowService(db)
    
    cost_summary = await service.calculate_cost_estimate(order_number)
    
    if not cost_summary:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_number}")
    
    await db.commit()
    
    return CostSummaryResponse(
        estimated_material_cost=float(cost_summary.estimated_material_cost),
        estimated_labor_cost=float(cost_summary.estimated_labor_cost),
        estimated_external_cost=float(cost_summary.estimated_external_cost),
        estimated_total_cost=float(cost_summary.estimated_total_cost)
    )


# Helper function to build order response
async def _build_order_response(order) -> OrderResponse:
    """Build order response from order model"""
    operations = [
        OperationResponse(
            operation_id=op.operation_id,
            operation_number=op.operation_number,
            work_center=op.work_center,
            description=op.description,
            planned_hours=float(op.planned_hours),
            actual_hours=float(op.actual_hours) if op.actual_hours else None,
            status=op.status.value,
            technician_id=op.technician_id
        )
        for op in order.operations
    ]
    
    components = [
        ComponentResponse(
            component_id=comp.component_id,
            material_number=comp.material_number,
            description=comp.description,
            quantity_required=float(comp.quantity_required),
            quantity_issued=float(comp.quantity_issued),
            unit_of_measure=comp.unit_of_measure,
            estimated_cost=float(comp.estimated_cost),
            actual_cost=float(comp.actual_cost) if comp.actual_cost else None,
            has_master_data=comp.has_master_data
        )
        for comp in order.components
    ]
    
    cost_summary = None
    if order.cost_summary:
        cost_summary = CostSummaryResponse(
            estimated_material_cost=float(order.cost_summary.estimated_material_cost),
            estimated_labor_cost=float(order.cost_summary.estimated_labor_cost),
            estimated_external_cost=float(order.cost_summary.estimated_external_cost),
            estimated_total_cost=float(order.cost_summary.estimated_total_cost)
        )
    
    return OrderResponse(
        order_number=order.order_number,
        order_type=order.order_type.value,
        status=order.status.value,
        equipment_id=order.equipment_id,
        functional_location=order.functional_location,
        priority=order.priority.value,
        planned_start_date=order.planned_start_date.isoformat() if order.planned_start_date else None,
        planned_end_date=order.planned_end_date.isoformat() if order.planned_end_date else None,
        breakdown_notification_id=order.breakdown_notification_id,
        created_by=order.created_by,
        created_at=order.created_at.isoformat(),
        operations=operations,
        components=components,
        cost_summary=cost_summary
    )


# Screen 2: Procurement & Material Planning Routes

class PurchaseOrderCreateRequest(BaseModel):
    """Create purchase order - Requirements 2.1, 2.2, 2.3"""
    order_number: str
    po_type: str = Field(..., description="material, service, or combined")
    vendor_id: str
    total_value: float
    delivery_date: datetime
    created_by: str


class PurchaseOrderResponse(BaseModel):
    """Purchase order response"""
    po_number: str
    order_number: str
    po_type: str
    vendor_id: str
    total_value: float
    delivery_date: str
    status: str
    created_at: str


class PurchaseOrderStatusUpdateRequest(BaseModel):
    """Update PO status - Requirement 2.5"""
    status: str = Field(..., description="created, ordered, partially_delivered, or delivered")
    updated_by: str


class DocumentFlowEntryResponse(BaseModel):
    """Document flow entry response"""
    flow_id: str
    document_type: str
    document_number: str
    transaction_date: str
    user_id: str
    status: str
    related_document: Optional[str]


@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    request: PurchaseOrderCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create purchase order for materials or services.
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    service = PMWorkflowService(db)
    
    try:
        po_type = POType(request.po_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid PO type: {request.po_type}")
    
    try:
        po = await service.create_purchase_order(
            order_number=request.order_number,
            po_type=po_type,
            vendor_id=request.vendor_id,
            total_value=Decimal(str(request.total_value)),
            delivery_date=request.delivery_date,
            created_by=request.created_by
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    await db.commit()
    
    return PurchaseOrderResponse(
        po_number=po.po_number,
        order_number=po.order_number,
        po_type=po.po_type.value,
        vendor_id=po.vendor_id,
        total_value=float(po.total_value),
        delivery_date=po.delivery_date.isoformat(),
        status=po.status.value,
        created_at=po.created_at.isoformat()
    )


@router.get("/purchase-orders/{po_number}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get purchase order by number"""
    service = PMWorkflowService(db)
    po = await service.get_purchase_order(po_number)
    
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order not found: {po_number}")
    
    return PurchaseOrderResponse(
        po_number=po.po_number,
        order_number=po.order_number,
        po_type=po.po_type.value,
        vendor_id=po.vendor_id,
        total_value=float(po.total_value),
        delivery_date=po.delivery_date.isoformat(),
        status=po.status.value,
        created_at=po.created_at.isoformat()
    )


@router.get("/orders/{order_number}/purchase-orders", response_model=List[PurchaseOrderResponse])
async def get_order_purchase_orders(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all purchase orders for a maintenance order.
    Requirement 2.5
    """
    service = PMWorkflowService(db)
    pos = await service.get_order_purchase_orders(order_number)
    
    return [
        PurchaseOrderResponse(
            po_number=po.po_number,
            order_number=po.order_number,
            po_type=po.po_type.value,
            vendor_id=po.vendor_id,
            total_value=float(po.total_value),
            delivery_date=po.delivery_date.isoformat(),
            status=po.status.value,
            created_at=po.created_at.isoformat()
        )
        for po in pos
    ]


@router.put("/purchase-orders/{po_number}/status", response_model=PurchaseOrderResponse)
async def update_po_status(
    po_number: str,
    request: PurchaseOrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update purchase order status.
    Requirement 2.5
    """
    service = PMWorkflowService(db)
    
    try:
        status = POStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
    
    po = await service.update_po_status(
        po_number=po_number,
        status=status,
        updated_by=request.updated_by
    )
    
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order not found: {po_number}")
    
    await db.commit()
    
    return PurchaseOrderResponse(
        po_number=po.po_number,
        order_number=po.order_number,
        po_type=po.po_type.value,
        vendor_id=po.vendor_id,
        total_value=float(po.total_value),
        delivery_date=po.delivery_date.isoformat(),
        status=po.status.value,
        created_at=po.created_at.isoformat()
    )


@router.get("/orders/{order_number}/procurement-flow", response_model=List[DocumentFlowEntryResponse])
async def get_procurement_document_flow(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get procurement-related document flow for order.
    Requirement 2.6
    """
    service = PMWorkflowService(db)
    flow_entries = await service.get_procurement_document_flow(order_number)
    
    return [
        DocumentFlowEntryResponse(
            flow_id=entry.flow_id,
            document_type=entry.document_type.value,
            document_number=entry.document_number,
            transaction_date=entry.transaction_date.isoformat(),
            user_id=entry.user_id,
            status=entry.status,
            related_document=entry.related_document
        )
        for entry in flow_entries
    ]


# Screen 3: Order Release & Execution Readiness Routes

class OrderReleaseRequest(BaseModel):
    """Release order request - Requirements 3.1, 3.2, 3.3"""
    released_by: str
    override_blocks: bool = False
    override_reason: Optional[str] = None


class ReadinessChecklistResponse(BaseModel):
    """Readiness checklist response - Requirement 3.4"""
    order_number: str
    order_type: str
    current_status: str
    can_release: bool
    blocking_reasons: List[str]
    checklist: dict


class TechnicianAssignmentRequest(BaseModel):
    """Assign technician to operation - Requirement 3.3"""
    technician_id: str
    assigned_by: str


@router.post("/orders/{order_number}/release")
async def release_order(
    order_number: str,
    request: OrderReleaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Release order for execution.
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    service = PMWorkflowService(db)
    
    success, error_message, order = await service.release_order(
        order_number=order_number,
        released_by=request.released_by,
        override_blocks=request.override_blocks,
        override_reason=request.override_reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return {
        "message": "Order released successfully",
        "order_number": order.order_number,
        "status": order.status.value,
        "released_by": order.released_by,
        "released_at": order.released_at.isoformat()
    }


@router.get("/orders/{order_number}/readiness-checklist", response_model=ReadinessChecklistResponse)
async def get_readiness_checklist(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get readiness checklist for order release.
    Requirement 3.4
    """
    service = PMWorkflowService(db)
    checklist = await service.get_readiness_checklist(order_number)
    
    if "error" in checklist:
        raise HTTPException(status_code=404, detail=checklist["error"])
    
    return ReadinessChecklistResponse(**checklist)


@router.put("/operations/{operation_id}/assign-technician")
async def assign_technician(
    operation_id: str,
    request: TechnicianAssignmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Assign technician to operation.
    Requirement 3.3
    """
    service = PMWorkflowService(db)
    
    operation = await service.assign_technician(
        operation_id=operation_id,
        technician_id=request.technician_id,
        assigned_by=request.assigned_by
    )
    
    if not operation:
        raise HTTPException(status_code=404, detail=f"Operation not found: {operation_id}")
    
    await db.commit()
    
    return {
        "message": "Technician assigned successfully",
        "operation_id": operation.operation_id,
        "technician_id": operation.technician_id
    }


# Screen 4: Material Receipt & Service Entry Routes

class GoodsReceiptCreateRequest(BaseModel):
    """Create goods receipt - Requirements 4.1, 4.2"""
    po_number: str
    material_number: str
    quantity_received: float
    storage_location: str
    received_by: str
    quality_passed: bool = True
    quality_notes: Optional[str] = None


class GoodsReceiptResponse(BaseModel):
    """Goods receipt response"""
    gr_document: str
    po_number: str
    order_number: str
    material_number: str
    quantity_received: float
    receipt_date: str
    storage_location: str
    received_by: str


class ServiceEntryCreateRequest(BaseModel):
    """Create service entry - Requirements 4.3, 4.4"""
    po_number: str
    service_description: str
    hours_or_units: float
    acceptance_date: datetime
    acceptor: str
    service_quality: str = "acceptable"


class ServiceEntryResponse(BaseModel):
    """Service entry response"""
    service_entry_document: str
    po_number: str
    order_number: str
    service_description: str
    hours_or_units: float
    acceptance_date: str
    acceptor: str
    service_quality: str


@router.post("/goods-receipts", response_model=GoodsReceiptResponse)
async def create_goods_receipt(
    request: GoodsReceiptCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create goods receipt for delivered materials.
    Requirements: 4.1, 4.2
    """
    service = PMWorkflowService(db)
    
    success, error_message, gr = await service.create_goods_receipt(
        po_number=request.po_number,
        material_number=request.material_number,
        quantity_received=Decimal(str(request.quantity_received)),
        storage_location=request.storage_location,
        received_by=request.received_by,
        quality_passed=request.quality_passed,
        quality_notes=request.quality_notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return GoodsReceiptResponse(
        gr_document=gr.gr_document,
        po_number=gr.po_number,
        order_number=gr.order_number,
        material_number=gr.material_number,
        quantity_received=float(gr.quantity_received),
        receipt_date=gr.receipt_date.isoformat(),
        storage_location=gr.storage_location,
        received_by=gr.received_by
    )


@router.post("/service-entries", response_model=ServiceEntryResponse)
async def create_service_entry(
    request: ServiceEntryCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create service entry for external work performed.
    Requirements: 4.3, 4.4
    """
    service = PMWorkflowService(db)
    
    success, error_message, service_entry_doc = await service.create_service_entry(
        po_number=request.po_number,
        service_description=request.service_description,
        hours_or_units=Decimal(str(request.hours_or_units)),
        acceptance_date=request.acceptance_date,
        acceptor=request.acceptor,
        service_quality=request.service_quality
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Get PO to retrieve order_number
    po = await service.get_purchase_order(request.po_number)
    
    await db.commit()
    
    return ServiceEntryResponse(
        service_entry_document=service_entry_doc,
        po_number=request.po_number,
        order_number=po.order_number,
        service_description=request.service_description,
        hours_or_units=float(request.hours_or_units),
        acceptance_date=request.acceptance_date.isoformat(),
        acceptor=request.acceptor,
        service_quality=request.service_quality
    )


@router.get("/orders/{order_number}/goods-receipts", response_model=List[GoodsReceiptResponse])
async def get_order_goods_receipts(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all goods receipts for an order.
    Requirement 4.2
    """
    service = PMWorkflowService(db)
    grs = await service.get_goods_receipts_for_order(order_number)
    
    return [
        GoodsReceiptResponse(
            gr_document=gr.gr_document,
            po_number=gr.po_number,
            order_number=gr.order_number,
            material_number=gr.material_number,
            quantity_received=float(gr.quantity_received),
            receipt_date=gr.receipt_date.isoformat(),
            storage_location=gr.storage_location,
            received_by=gr.received_by
        )
        for gr in grs
    ]


@router.get("/orders/{order_number}/service-entries", response_model=List[DocumentFlowEntryResponse])
async def get_order_service_entries(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all service entries for an order.
    Requirement 4.3
    """
    service = PMWorkflowService(db)
    entries = await service.get_service_entries_for_order(order_number)
    
    return [
        DocumentFlowEntryResponse(
            flow_id=entry.flow_id,
            document_type=entry.document_type.value,
            document_number=entry.document_number,
            transaction_date=entry.transaction_date.isoformat(),
            user_id=entry.user_id,
            status=entry.status,
            related_document=entry.related_document
        )
        for entry in entries
    ]


# Screen 6: Completion & Cost Settlement Routes

class TECORequest(BaseModel):
    """TECO request - Requirements 6.1, 6.2, 6.3"""
    completed_by: str


class CompletionChecklistResponse(BaseModel):
    """Completion checklist response - Requirements 6.1, 6.2, 6.3"""
    order_number: str
    order_type: str
    current_status: str
    can_teco: bool
    blocking_reasons: List[str]
    checklist: dict


class CostAnalysisResponse(BaseModel):
    """Cost analysis response - Requirements 6.4, 6.5, 6.6"""
    order_number: str
    estimated_costs: dict
    actual_costs: dict
    variances: dict


class CostSettlementRequest(BaseModel):
    """Cost settlement request - Requirement 6.7"""
    cost_center: str
    settled_by: str


@router.post("/orders/{order_number}/teco")
async def teco_order(
    order_number: str,
    request: TECORequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Technically complete order (TECO).
    Requirements: 6.1, 6.2, 6.3
    """
    service = PMWorkflowService(db)
    
    success, error_message, order = await service.teco_order(
        order_number=order_number,
        completed_by=request.completed_by
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return {
        "message": "Order technically completed successfully",
        "order_number": order.order_number,
        "status": order.status.value,
        "completed_by": order.completed_by,
        "completed_at": order.completed_at.isoformat()
    }


@router.get("/orders/{order_number}/completion-checklist", response_model=CompletionChecklistResponse)
async def get_completion_checklist(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get completion checklist for TECO validation.
    Requirements: 6.1, 6.2, 6.3
    """
    service = PMWorkflowService(db)
    checklist = await service.get_completion_checklist(order_number)
    
    if "error" in checklist:
        raise HTTPException(status_code=404, detail=checklist["error"])
    
    return CompletionChecklistResponse(**checklist)


@router.get("/orders/{order_number}/cost-analysis", response_model=CostAnalysisResponse)
async def get_cost_analysis(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get cost analysis with variance details.
    Requirements: 6.4, 6.5, 6.6
    """
    service = PMWorkflowService(db)
    analysis = await service.get_cost_analysis(order_number)
    
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    
    return CostAnalysisResponse(**analysis)


@router.post("/orders/{order_number}/settle-costs")
async def settle_costs(
    order_number: str,
    request: CostSettlementRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Settle costs to cost center.
    Requirement 6.7
    """
    service = PMWorkflowService(db)
    
    success, error_message = await service.settle_costs(
        order_number=order_number,
        cost_center=request.cost_center,
        settled_by=request.settled_by
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return {
        "message": "Costs settled successfully",
        "order_number": order_number,
        "cost_center": request.cost_center
    }


# Document Flow Tracking Routes (Task 9)

@router.get("/orders/{order_number}/document-flow", response_model=List[DocumentFlowEntryResponse])
async def get_order_document_flow(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete document flow for an order.
    Requirements: 9.1, 9.2, 9.4, 9.5
    
    Returns all document flow entries in chronological order,
    providing a complete audit trail of all transactions.
    """
    service = PMWorkflowService(db)
    flow_entries = await service.get_document_flow(order_number)
    
    if not flow_entries:
        # Check if order exists
        order = await service.get_order(order_number)
        if not order:
            raise HTTPException(status_code=404, detail=f"Order not found: {order_number}")
    
    return [
        DocumentFlowEntryResponse(
            flow_id=entry.flow_id,
            document_type=entry.document_type.value,
            document_number=entry.document_number,
            transaction_date=entry.transaction_date.isoformat(),
            user_id=entry.user_id,
            status=entry.status,
            related_document=entry.related_document
        )
        for entry in flow_entries
    ]


@router.get("/orders/{order_number}/document-flow/{document_type}", response_model=List[DocumentFlowEntryResponse])
async def get_order_document_flow_by_type(
    order_number: str,
    document_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document flow entries filtered by document type.
    Requirement 9.4
    
    Allows filtering the audit trail by specific transaction types
    (e.g., only POs, only GIs, etc.)
    """
    service = PMWorkflowService(db)
    
    try:
        doc_type_enum = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {document_type}. Valid types: {[t.value for t in DocumentType]}"
        )
    
    flow_entries = await service.get_document_flow_by_type(order_number, doc_type_enum)
    
    return [
        DocumentFlowEntryResponse(
            flow_id=entry.flow_id,
            document_type=entry.document_type.value,
            document_number=entry.document_number,
            transaction_date=entry.transaction_date.isoformat(),
            user_id=entry.user_id,
            status=entry.status,
            related_document=entry.related_document
        )
        for entry in flow_entries
    ]


# Task 11: Breakdown Maintenance Differentiation Routes

class BreakdownOrderCreateRequest(BaseModel):
    """Create breakdown order from notification - Requirements 7.1, 7.2"""
    notification_id: str
    equipment_id: str
    functional_location: str
    notification_description: str
    created_by: str


class BreakdownOrderReleaseRequest(BaseModel):
    """Release breakdown order - Requirements 7.3, 7.4"""
    released_by: str
    emergency_permit_id: Optional[str] = None


class EmergencyGoodsIssueRequest(BaseModel):
    """Emergency goods issue request - Requirement 7.4"""
    material_number: str
    quantity_issued: float
    cost_center: str
    issued_by: str
    emergency_stock_location: str = "EMERGENCY"


class EmergencyGoodsIssueResponse(BaseModel):
    """Emergency goods issue response"""
    gi_document: str
    order_number: str
    material_number: str
    quantity_issued: float
    issue_date: str
    cost_center: str
    issued_by: str
    emergency_stock_location: str


class MalfunctionReportRequest(BaseModel):
    """Malfunction report request - Requirements 5.5, 7.5"""
    cause_code: str
    description: str
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    reported_by: str


class MalfunctionReportResponse(BaseModel):
    """Malfunction report response"""
    report_id: str
    order_number: str
    cause_code: str
    description: str
    root_cause: Optional[str]
    corrective_action: Optional[str]
    reported_by: str
    reported_at: str


class BreakdownTECORequest(BaseModel):
    """Breakdown TECO request - Requirement 7.6"""
    completed_by: str
    post_review_required: bool = True


class BreakdownOrderSummaryResponse(BaseModel):
    """Breakdown order summary for post-completion review - Requirement 7.6"""
    order_number: str
    order_type: str
    status: str
    priority: str
    breakdown_notification_id: Optional[str]
    equipment_id: Optional[str]
    functional_location: Optional[str]
    created_at: str
    released_at: Optional[str]
    completed_at: Optional[str]
    response_time_hours: Optional[float]
    completion_time_hours: Optional[float]
    malfunction_reports: List[dict]
    cost_analysis: dict
    document_flow_count: int
    post_review_required: bool


@router.post("/breakdown-orders/from-notification", response_model=OrderResponse)
async def create_breakdown_order_from_notification(
    request: BreakdownOrderCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-create breakdown order from notification.
    Requirements: 7.1, 7.2
    
    Breakdown orders are automatically created with:
    - Highest priority (URGENT)
    - Pre-populated equipment and functional location
    - Reference to breakdown notification
    - Default emergency operation
    """
    service = PMWorkflowService(db)
    
    order = await service.create_breakdown_order_from_notification(
        notification_id=request.notification_id,
        equipment_id=request.equipment_id,
        functional_location=request.functional_location,
        notification_description=request.notification_description,
        created_by=request.created_by
    )
    
    await db.commit()
    await db.refresh(order)
    
    return await _build_order_response(order)


@router.post("/breakdown-orders/{order_number}/release")
async def release_breakdown_order(
    order_number: str,
    request: BreakdownOrderReleaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Release breakdown order with reduced validation.
    Requirements: 7.3, 7.4
    
    Breakdown orders have reduced validation:
    - Emergency permits accepted instead of full permits
    - Material availability not strictly enforced
    - Can proceed with emergency stock
    """
    service = PMWorkflowService(db)
    
    success, error_message, order = await service.release_breakdown_order(
        order_number=order_number,
        released_by=request.released_by,
        emergency_permit_id=request.emergency_permit_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return {
        "message": "Breakdown order released successfully with reduced validation",
        "order_number": order.order_number,
        "status": order.status.value,
        "released_by": order.released_by,
        "released_at": order.released_at.isoformat(),
        "emergency_permit_id": request.emergency_permit_id
    }


@router.post("/breakdown-orders/{order_number}/emergency-goods-issue", response_model=EmergencyGoodsIssueResponse)
async def create_emergency_goods_issue(
    order_number: str,
    request: EmergencyGoodsIssueRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create goods issue from emergency stock without PO.
    Requirement 7.4
    
    For breakdown orders, materials can be issued from emergency stock
    without going through the full procurement cycle.
    """
    service = PMWorkflowService(db)
    
    success, error_message, gi = await service.create_emergency_goods_issue(
        order_number=order_number,
        material_number=request.material_number,
        quantity_issued=Decimal(str(request.quantity_issued)),
        cost_center=request.cost_center,
        issued_by=request.issued_by,
        emergency_stock_location=request.emergency_stock_location
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return EmergencyGoodsIssueResponse(
        gi_document=gi.gi_document,
        order_number=gi.order_number,
        material_number=gi.material_number,
        quantity_issued=float(gi.quantity_issued),
        issue_date=gi.issue_date.isoformat(),
        cost_center=gi.cost_center,
        issued_by=gi.issued_by,
        emergency_stock_location=request.emergency_stock_location
    )


@router.post("/orders/{order_number}/malfunction-report", response_model=MalfunctionReportResponse)
async def create_malfunction_report(
    order_number: str,
    request: MalfunctionReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create malfunction report.
    Requirements: 5.5, 7.5
    
    For breakdown orders, this is mandatory before TECO.
    """
    service = PMWorkflowService(db)
    
    success, error_message, report = await service.create_malfunction_report(
        order_number=order_number,
        cause_code=request.cause_code,
        description=request.description,
        root_cause=request.root_cause,
        corrective_action=request.corrective_action,
        reported_by=request.reported_by
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return MalfunctionReportResponse(
        report_id=report.report_id,
        order_number=report.order_number,
        cause_code=report.cause_code,
        description=report.description,
        root_cause=report.root_cause,
        corrective_action=report.corrective_action,
        reported_by=report.reported_by,
        reported_at=report.reported_at.isoformat()
    )


@router.get("/orders/{order_number}/malfunction-report-required")
async def check_malfunction_report_required(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if malfunction report is required for order.
    Requirement 7.5
    """
    service = PMWorkflowService(db)
    
    required, reason = await service.validate_malfunction_report_required(order_number)
    
    return {
        "order_number": order_number,
        "malfunction_report_required": required,
        "reason": reason
    }


@router.post("/breakdown-orders/{order_number}/teco")
async def teco_breakdown_order(
    order_number: str,
    request: BreakdownTECORequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Technically complete breakdown order with mandatory post-review.
    Requirement 7.6
    
    Breakdown orders require:
    - Mandatory malfunction report
    - Post-completion review flag
    - Root cause analysis
    """
    service = PMWorkflowService(db)
    
    success, error_message, order = await service.teco_breakdown_order(
        order_number=order_number,
        completed_by=request.completed_by,
        post_review_required=request.post_review_required
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    await db.commit()
    
    return {
        "message": "Breakdown order technically completed successfully",
        "order_number": order.order_number,
        "status": order.status.value,
        "completed_by": order.completed_by,
        "completed_at": order.completed_at.isoformat(),
        "post_review_required": request.post_review_required
    }


@router.get("/breakdown-orders/{order_number}/summary", response_model=BreakdownOrderSummaryResponse)
async def get_breakdown_order_summary(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of breakdown order for post-completion review.
    Requirement 7.6
    
    Provides comprehensive breakdown order data including:
    - Response and completion times
    - Malfunction reports
    - Cost analysis
    - Document flow
    """
    service = PMWorkflowService(db)
    
    summary = await service.get_breakdown_order_summary(order_number)
    
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    
    return BreakdownOrderSummaryResponse(**summary)


# Cost Management Endpoints (Task 12)

class CostVarianceResponse(BaseModel):
    """Cost variance analysis response - Requirements 6.5, 6.6"""
    order_number: str
    estimated_costs: dict
    actual_costs: dict
    variances: dict
    variance_status: str
    requires_explanation: bool


class CostElementBreakdownResponse(BaseModel):
    """Cost element breakdown response - Requirements 1.5, 6.4"""
    order_number: str
    summary: dict
    material_costs: dict
    labor_costs: dict
    external_costs: dict


class CostSettlementRequest(BaseModel):
    """Cost settlement request - Requirement 6.7"""
    cost_center: str
    wbs_element: Optional[str] = None
    equipment_number: Optional[str] = None
    settlement_notes: Optional[str] = None


class CostSettlementResponse(BaseModel):
    """Cost settlement response"""
    success: bool
    settlement_document: Optional[str]
    message: Optional[str]


@router.post("/orders/{order_number}/accumulate-costs", response_model=CostSummaryResponse)
async def accumulate_actual_costs(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Accumulate actual costs from all postings (GI, confirmations, service entries).
    Requirement 6.4
    """
    from backend.services.pm_workflow_cost_service import CostManagementService
    
    cost_service = CostManagementService(db)
    cost_summary = await cost_service.accumulate_actual_costs(order_number)
    
    if not cost_summary:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_number}")
    
    await db.commit()
    
    return CostSummaryResponse(
        estimated_material_cost=float(cost_summary.estimated_material_cost),
        estimated_labor_cost=float(cost_summary.estimated_labor_cost),
        estimated_external_cost=float(cost_summary.estimated_external_cost),
        estimated_total_cost=float(cost_summary.estimated_total_cost)
    )


@router.get("/orders/{order_number}/cost-variance", response_model=CostVarianceResponse)
async def get_cost_variance(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get cost variance analysis with detailed breakdown by element.
    Requirements: 6.5, 6.6
    """
    from backend.services.pm_workflow_cost_service import CostManagementService
    
    cost_service = CostManagementService(db)
    variance_analysis = await cost_service.calculate_cost_variance(order_number)
    
    if not variance_analysis:
        raise HTTPException(status_code=404, detail=f"Cost summary not found for order: {order_number}")
    
    return CostVarianceResponse(**variance_analysis)


@router.get("/orders/{order_number}/cost-breakdown", response_model=CostElementBreakdownResponse)
async def get_cost_element_breakdown(
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed cost element breakdown with line items.
    Requirements: 1.5, 6.4
    """
    from backend.services.pm_workflow_cost_service import CostManagementService
    
    cost_service = CostManagementService(db)
    breakdown = await cost_service.get_cost_element_breakdown(order_number)
    
    if not breakdown:
        raise HTTPException(status_code=404, detail=f"Cost summary not found for order: {order_number}")
    
    return CostElementBreakdownResponse(**breakdown)


@router.post("/orders/{order_number}/settle-costs", response_model=CostSettlementResponse)
async def settle_costs_to_fi(
    order_number: str,
    request: CostSettlementRequest,
    settled_by: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Settle costs to FI (Financial Accounting).
    Requirement 6.7
    
    Posts final costs to cost center, WBS element, or equipment.
    """
    from backend.services.pm_workflow_cost_service import CostManagementService
    
    cost_service = CostManagementService(db)
    success, error_msg, settlement_doc = await cost_service.settle_costs_to_fi(
        order_number=order_number,
        cost_center=request.cost_center,
        wbs_element=request.wbs_element,
        equipment_number=request.equipment_number,
        settled_by=settled_by,
        settlement_notes=request.settlement_notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_msg)
    
    await db.commit()
    
    return CostSettlementResponse(
        success=True,
        settlement_document=settlement_doc,
        message=f"Costs settled to {request.cost_center}"
    )
