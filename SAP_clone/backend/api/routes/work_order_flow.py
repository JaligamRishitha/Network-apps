"""
Work Order Flow API Routes.
Manages the PM → MM → FI workflow for work orders received from external CRM.

Flow:
1. POST /work-orders - Receive work order from CRM with materials
2. POST /work-orders/{id}/check-materials - Send to MM for material check
3. POST /work-orders/{id}/request-purchase - If shortage, raise FI ticket
4. POST /work-orders/{id}/approve-purchase - FI approves/rejects purchase
5. POST /work-orders/{id}/proceed - Proceed with work order
6. POST /work-orders/{id}/start - Start work order
7. POST /work-orders/{id}/complete - Complete work order
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.work_order_flow_models import WorkOrderFlowStatus
from backend.services.work_order_flow_service import (
    WorkOrderFlowService,
    WorkOrderNotFoundError,
    InvalidWorkOrderStateError,
    WorkOrderFlowError,
)


router = APIRouter(prefix="/work-order-flow", tags=["Work Order Flow (PM → MM → FI)"])


# =====================
# Request/Response Models
# =====================

class MaterialInput(BaseModel):
    material_id: str
    material_description: str
    quantity_required: int
    unit_of_measure: str = "EA"
    unit_price: Optional[float] = None


class WorkOrderCreateRequest(BaseModel):
    """Request to create a work order from CRM"""
    title: str
    description: str
    customer_name: str
    site_location: str
    requested_date: datetime
    cost_center_id: str
    created_by: str
    materials: List[MaterialInput]
    crm_reference_id: Optional[str] = None
    customer_contact: Optional[str] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None


class MaterialCheckResultResponse(BaseModel):
    material_id: str
    material_description: str
    quantity_required: int
    quantity_available: int
    is_available: bool
    shortage_quantity: int
    unit_price: Optional[float]


class WorkOrderMaterialResponse(BaseModel):
    id: int
    material_id: str
    material_description: str
    quantity_required: int
    unit_of_measure: str
    quantity_available: Optional[int]
    is_available: Optional[bool]
    shortage_quantity: Optional[int]
    requisition_id: Optional[str]
    unit_price: Optional[float]
    checked_at: Optional[str]


class WorkOrderFlowHistoryResponse(BaseModel):
    id: int
    from_status: str
    to_status: str
    triggered_by_module: str
    performed_by: str
    notes: Optional[str]
    created_at: str


class WorkOrderResponse(BaseModel):
    work_order_id: str
    crm_reference_id: Optional[str]
    title: str
    description: str
    customer_name: str
    customer_contact: Optional[str]
    site_location: str
    priority: str
    flow_status: str
    requested_date: str
    scheduled_date: Optional[str]
    completed_date: Optional[str]
    pm_maintenance_order_id: Optional[str]
    pm_ticket_id: Optional[str]
    fi_approval_id: Optional[str]
    fi_ticket_id: Optional[str]
    cost_center_id: str
    estimated_material_cost: Optional[float]
    created_by: str
    assigned_to: Optional[str]
    materials_check_summary: Optional[dict]
    materials: List[WorkOrderMaterialResponse]


class WorkOrderListResponse(BaseModel):
    work_orders: List[WorkOrderResponse]
    total: int


class MaterialCheckResponse(BaseModel):
    work_order_id: str
    flow_status: str
    all_materials_available: bool
    materials_check_summary: dict
    check_results: List[MaterialCheckResultResponse]


class PurchaseRequestResponse(BaseModel):
    work_order_id: str
    flow_status: str
    fi_approval_id: str
    fi_ticket_id: str
    estimated_material_cost: float


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    decided_by: str
    comment: Optional[str] = None


class PerformActionRequest(BaseModel):
    performed_by: str
    scheduled_date: Optional[datetime] = None


class JustificationRequest(BaseModel):
    performed_by: str
    justification: Optional[str] = None


# =====================
# Helper Functions
# =====================

def _work_order_to_response(work_order) -> WorkOrderResponse:
    """Convert work order model to response."""
    return WorkOrderResponse(
        work_order_id=work_order.work_order_id,
        crm_reference_id=work_order.crm_reference_id,
        title=work_order.title,
        description=work_order.description,
        customer_name=work_order.customer_name,
        customer_contact=work_order.customer_contact,
        site_location=work_order.site_location,
        priority=work_order.priority,
        flow_status=work_order.flow_status.value,
        requested_date=work_order.requested_date.isoformat() if work_order.requested_date else None,
        scheduled_date=work_order.scheduled_date.isoformat() if work_order.scheduled_date else None,
        completed_date=work_order.completed_date.isoformat() if work_order.completed_date else None,
        pm_maintenance_order_id=work_order.pm_maintenance_order_id,
        pm_ticket_id=work_order.pm_ticket_id,
        fi_approval_id=work_order.fi_approval_id,
        fi_ticket_id=work_order.fi_ticket_id,
        cost_center_id=work_order.cost_center_id,
        estimated_material_cost=float(work_order.estimated_material_cost) if work_order.estimated_material_cost else None,
        created_by=work_order.created_by,
        assigned_to=work_order.assigned_to,
        materials_check_summary=work_order.materials_check_summary,
        materials=[
            WorkOrderMaterialResponse(
                id=m.id,
                material_id=m.material_id,
                material_description=m.material_description,
                quantity_required=m.quantity_required,
                unit_of_measure=m.unit_of_measure,
                quantity_available=m.quantity_available,
                is_available=m.is_available,
                shortage_quantity=m.shortage_quantity,
                requisition_id=m.requisition_id,
                unit_price=float(m.unit_price) if m.unit_price else None,
                checked_at=m.checked_at.isoformat() if m.checked_at else None,
            )
            for m in work_order.materials
        ],
    )


# =====================
# API Routes
# =====================

@router.post("/work-orders", response_model=WorkOrderResponse)
async def create_work_order(
    request: WorkOrderCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1: Create a work order from CRM.
    This receives the work order with materials from external CRM system.
    """
    service = WorkOrderFlowService(db)

    materials = [
        {
            "material_id": m.material_id,
            "material_description": m.material_description,
            "quantity_required": m.quantity_required,
            "unit_of_measure": m.unit_of_measure,
            "unit_price": m.unit_price,
        }
        for m in request.materials
    ]

    work_order = await service.create_work_order_from_crm(
        title=request.title,
        description=request.description,
        customer_name=request.customer_name,
        site_location=request.site_location,
        requested_date=request.requested_date,
        cost_center_id=request.cost_center_id,
        created_by=request.created_by,
        materials=materials,
        crm_reference_id=request.crm_reference_id,
        customer_contact=request.customer_contact,
        priority=request.priority,
        assigned_to=request.assigned_to,
    )

    await db.commit()

    # Reload to get materials
    work_order = await service.get_work_order(work_order.work_order_id)
    return _work_order_to_response(work_order)


@router.get("/work-orders", response_model=WorkOrderListResponse)
async def list_work_orders(
    flow_status: Optional[str] = None,
    customer_name: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List work orders with optional filtering."""
    service = WorkOrderFlowService(db)

    status_enum = WorkOrderFlowStatus(flow_status) if flow_status else None

    work_orders, total = await service.list_work_orders(
        flow_status=status_enum,
        customer_name=customer_name,
        limit=limit,
        offset=offset,
    )

    return WorkOrderListResponse(
        work_orders=[_work_order_to_response(wo) for wo in work_orders],
        total=total,
    )


@router.get("/work-orders/pending-purchase", response_model=WorkOrderListResponse)
async def get_pending_purchase_orders(db: AsyncSession = Depends(get_db)):
    """Get work orders pending purchase request (for MM Purchase Orders view)."""
    service = WorkOrderFlowService(db)
    work_orders, total = await service.list_work_orders(
        flow_status=WorkOrderFlowStatus.MATERIALS_SHORTAGE,
        limit=100
    )
    return WorkOrderListResponse(
        work_orders=[_work_order_to_response(wo) for wo in work_orders],
        total=total
    )


@router.get("/work-orders/pending-approval", response_model=WorkOrderListResponse)
async def get_pending_approval_orders(db: AsyncSession = Depends(get_db)):
    """Get work orders pending FI approval (for FI Approvals Inbox)."""
    service = WorkOrderFlowService(db)
    work_orders, total = await service.list_work_orders(
        flow_status=WorkOrderFlowStatus.PURCHASE_REQUESTED,
        limit=100
    )
    return WorkOrderListResponse(
        work_orders=[_work_order_to_response(wo) for wo in work_orders],
        total=total
    )


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a work order by ID."""
    service = WorkOrderFlowService(db)

    try:
        work_order = await service.get_work_order_or_raise(work_order_id)
        return _work_order_to_response(work_order)
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")


@router.patch("/work-orders/{work_order_id}/materials-status")
async def update_materials_status(
    work_order_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update work order materials check summary and flow status from agent validation."""
    from sqlalchemy import select
    from backend.models.work_order_flow_models import CRMWorkOrder

    stmt = select(CRMWorkOrder).where(CRMWorkOrder.work_order_id == work_order_id)
    result = await db.execute(stmt)
    work_order = result.scalars().first()

    if not work_order:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")

    all_available = request.get("all_available", True)
    materials_summary = {
        "all_available": all_available,
        "shortage_count": request.get("shortage_count", 0),
        "checked_by": request.get("checked_by", "agent"),
        "checked_at": datetime.now().isoformat(),
        "details": request.get("details", "Validated by AI agent")
    }
    work_order.materials_check_summary = materials_summary

    new_status = WorkOrderFlowStatus.MATERIALS_AVAILABLE if all_available else WorkOrderFlowStatus.MATERIALS_SHORTAGE
    work_order.flow_status = new_status

    await db.commit()

    return {
        "work_order_id": work_order_id,
        "flow_status": new_status.value,
        "materials_check_summary": materials_summary
    }


@router.post("/work-orders/{work_order_id}/check-materials", response_model=MaterialCheckResponse)
async def check_materials(
    work_order_id: str,
    request: PerformActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2: Send work order to MM for material availability check.
    This checks if all required materials are available in inventory.
    """
    service = WorkOrderFlowService(db)

    try:
        work_order, check_results = await service.send_to_mm_for_material_check(
            work_order_id=work_order_id,
            performed_by=request.performed_by,
        )
        await db.commit()

        return MaterialCheckResponse(
            work_order_id=work_order.work_order_id,
            flow_status=work_order.flow_status.value,
            all_materials_available=work_order.materials_check_summary.get("all_available", False),
            materials_check_summary=work_order.materials_check_summary,
            check_results=[
                MaterialCheckResultResponse(
                    material_id=r.material_id,
                    material_description=r.material_description,
                    quantity_required=r.quantity_required,
                    quantity_available=r.quantity_available,
                    is_available=r.is_available,
                    shortage_quantity=r.shortage_quantity,
                    unit_price=float(r.unit_price) if r.unit_price else None,
                )
                for r in check_results
            ],
        )
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")
    except InvalidWorkOrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/work-orders/{work_order_id}/request-purchase", response_model=PurchaseRequestResponse)
async def request_purchase(
    work_order_id: str,
    request: JustificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 3: MM raises a ticket to FI for purchasing materials that are not available.
    This is only called when materials are in shortage.
    """
    service = WorkOrderFlowService(db)

    try:
        work_order, fi_approval_id, fi_ticket_id = await service.raise_fi_ticket_for_purchase(
            work_order_id=work_order_id,
            performed_by=request.performed_by,
            justification=request.justification,
        )
        await db.commit()

        return PurchaseRequestResponse(
            work_order_id=work_order.work_order_id,
            flow_status=work_order.flow_status.value,
            fi_approval_id=fi_approval_id,
            fi_ticket_id=fi_ticket_id,
            estimated_material_cost=float(work_order.estimated_material_cost) if work_order.estimated_material_cost else 0,
        )
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")
    except InvalidWorkOrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except WorkOrderFlowError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/work-orders/{work_order_id}/approve-purchase", response_model=WorkOrderResponse)
async def handle_purchase_approval(
    work_order_id: str,
    request: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 4: FI approves or rejects the purchase request.
    If approved, purchase requisitions are created in MM.
    """
    service = WorkOrderFlowService(db)

    try:
        work_order = await service.handle_fi_approval_decision(
            work_order_id=work_order_id,
            approved=request.approved,
            decided_by=request.decided_by,
            comment=request.comment,
        )
        await db.commit()

        # Reload to get updated materials
        work_order = await service.get_work_order(work_order_id)
        return _work_order_to_response(work_order)
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")
    except InvalidWorkOrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/work-orders/{work_order_id}/proceed", response_model=WorkOrderResponse)
async def proceed_work_order(
    work_order_id: str,
    request: PerformActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 5: Proceed with work order after materials are confirmed available.
    """
    service = WorkOrderFlowService(db)

    try:
        work_order = await service.proceed_with_work_order(
            work_order_id=work_order_id,
            performed_by=request.performed_by,
        )
        await db.commit()

        work_order = await service.get_work_order(work_order_id)
        return _work_order_to_response(work_order)
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")
    except InvalidWorkOrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/work-orders/{work_order_id}/start", response_model=WorkOrderResponse)
async def start_work_order(
    work_order_id: str,
    request: PerformActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 6: Start working on the work order.
    """
    service = WorkOrderFlowService(db)

    try:
        work_order = await service.start_work_order(
            work_order_id=work_order_id,
            performed_by=request.performed_by,
            scheduled_date=request.scheduled_date,
        )
        await db.commit()

        work_order = await service.get_work_order(work_order_id)
        return _work_order_to_response(work_order)
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")
    except InvalidWorkOrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/work-orders/{work_order_id}/complete", response_model=WorkOrderResponse)
async def complete_work_order(
    work_order_id: str,
    request: PerformActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 7: Complete the work order.
    """
    service = WorkOrderFlowService(db)

    try:
        work_order = await service.complete_work_order(
            work_order_id=work_order_id,
            performed_by=request.performed_by,
        )
        await db.commit()

        work_order = await service.get_work_order(work_order_id)
        return _work_order_to_response(work_order)
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")
    except InvalidWorkOrderStateError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/work-orders/{work_order_id}/history", response_model=List[WorkOrderFlowHistoryResponse])
async def get_work_order_history(
    work_order_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the flow history for a work order."""
    service = WorkOrderFlowService(db)

    try:
        await service.get_work_order_or_raise(work_order_id)
        history = await service.get_flow_history(work_order_id)

        return [
            WorkOrderFlowHistoryResponse(
                id=h.id,
                from_status=h.from_status.value,
                to_status=h.to_status.value,
                triggered_by_module=h.triggered_by_module,
                performed_by=h.performed_by,
                notes=h.notes,
                created_at=h.created_at.isoformat() if h.created_at else None,
            )
            for h in history
        ]
    except WorkOrderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work order not found: {work_order_id}")


@router.post("/seed-data")
async def seed_test_data(db: AsyncSession = Depends(get_db)):
    """Seed test work orders with materials for demo."""
    service = WorkOrderFlowService(db)
    
    test_orders = [
        {
            "title": "Transformer Maintenance - Available Materials",
            "description": "Routine maintenance on transformer T-001",
            "customer_name": "City Power Grid",
            "site_location": "Substation A",
            "requested_date": datetime.now(),
            "cost_center_id": "CC-MAINT-001",
            "created_by": "crm_system",
            "materials": [{"material_id": "MAT-001", "material_description": "Transformer Oil 20L", "quantity_required": 2, "unit_of_measure": "EA", "unit_price": 150.0}],
            "priority": "high"
        },
        {
            "title": "Bushing Replacement - Material Shortage",
            "description": "Replace damaged copper bushing",
            "customer_name": "Industrial Complex",
            "site_location": "Factory B",
            "requested_date": datetime.now(),
            "cost_center_id": "CC-MAINT-001",
            "created_by": "crm_system",
            "materials": [{"material_id": "MAT-002", "material_description": "Copper Bushing", "quantity_required": 5, "unit_of_measure": "EA", "unit_price": 200.0}],
            "priority": "medium"
        },
        {
            "title": "Cable Installation - Purchase Required",
            "description": "Install new 11KV cable line",
            "customer_name": "Metro Transit",
            "site_location": "Station C",
            "requested_date": datetime.now(),
            "cost_center_id": "CC-MAINT-001",
            "created_by": "crm_system",
            "materials": [{"material_id": "MAT-003", "material_description": "11KV Cable 100m", "quantity_required": 150, "unit_of_measure": "M", "unit_price": 50.0}],
            "priority": "low"
        }
    ]
    
    created = []
    for order_data in test_orders:
        wo = await service.create_work_order_from_crm(**order_data)
        created.append(wo.work_order_id)
    
    await db.commit()
    return {"message": "Test data seeded", "work_order_ids": created}
