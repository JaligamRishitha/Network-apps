"""
Production & Manufacturing Module API routes.
SAP ERP API - Production orders, BOM, and confirmations
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/production", tags=["Production & Manufacturing"])


# Request/Response Models

class BOMComponent(BaseModel):
    component_id: str
    material_id: str
    description: str
    quantity: float
    unit_of_measure: str


class RoutingOperation(BaseModel):
    operation_id: str
    operation_number: int
    work_center: str
    description: str
    setup_time: float
    run_time: float
    unit: str


class ProductionOrderResponse(BaseModel):
    order_id: str
    material_id: str
    material_description: str
    quantity: int
    unit_of_measure: str
    status: str
    planned_start: str
    planned_end: str
    actual_start: Optional[str]
    actual_end: Optional[str]
    work_center: str


class ProductionOrderListResponse(BaseModel):
    production_orders: List[ProductionOrderResponse]
    pagination: dict


class BOMResponse(BaseModel):
    bom_id: str
    material_id: str
    material_description: str
    base_quantity: int
    unit_of_measure: str
    components: List[BOMComponent]


class ConfirmationRequest(BaseModel):
    order_id: str
    operation_number: int
    quantity_confirmed: int
    yield_quantity: int
    scrap_quantity: int
    confirmed_by: str
    notes: Optional[str] = None


class ConfirmationResponse(BaseModel):
    confirmation_id: str
    order_id: str
    operation_number: int
    quantity_confirmed: int
    yield_quantity: int
    scrap_quantity: int
    confirmation_date: str
    confirmed_by: str


# Demo data
_production_orders = {
    "PRD-2024-00001": {
        "order_id": "PRD-2024-00001",
        "material_id": "FG-001",
        "material_description": "Finished Product A",
        "quantity": 100,
        "unit_of_measure": "EA",
        "status": "in_progress",
        "planned_start": "2024-01-15T08:00:00Z",
        "planned_end": "2024-01-20T17:00:00Z",
        "actual_start": "2024-01-15T08:30:00Z",
        "actual_end": None,
        "work_center": "WC-ASSEMBLY-01",
    },
    "PRD-2024-00002": {
        "order_id": "PRD-2024-00002",
        "material_id": "FG-002",
        "material_description": "Finished Product B",
        "quantity": 50,
        "unit_of_measure": "EA",
        "status": "planned",
        "planned_start": "2024-01-22T08:00:00Z",
        "planned_end": "2024-01-25T17:00:00Z",
        "actual_start": None,
        "actual_end": None,
        "work_center": "WC-ASSEMBLY-02",
    },
}

_boms = {
    "FG-001": {
        "bom_id": "BOM-FG-001",
        "material_id": "FG-001",
        "material_description": "Finished Product A",
        "base_quantity": 1,
        "unit_of_measure": "EA",
        "components": [
            {"component_id": "COMP-001", "material_id": "RAW-001", "description": "Raw Material 1", "quantity": 2.0, "unit_of_measure": "KG"},
            {"component_id": "COMP-002", "material_id": "RAW-002", "description": "Raw Material 2", "quantity": 1.5, "unit_of_measure": "KG"},
            {"component_id": "COMP-003", "material_id": "SEMI-001", "description": "Semi-finished Part", "quantity": 1.0, "unit_of_measure": "EA"},
        ],
    },
}

_confirmations = []
_confirmation_counter = 1


@router.get("/orders", response_model=ProductionOrderListResponse)
async def list_production_orders(
    status: Optional[str] = None,
    material_id: Optional[str] = None,
    work_center: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List production orders with filtering."""
    orders = list(_production_orders.values())
    
    if status:
        orders = [o for o in orders if o["status"] == status]
    if material_id:
        orders = [o for o in orders if o["material_id"] == material_id]
    if work_center:
        orders = [o for o in orders if o["work_center"] == work_center]
    
    total = len(orders)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    
    return ProductionOrderListResponse(
        production_orders=[ProductionOrderResponse(**o) for o in orders[start:end]],
        pagination={"page": page, "total_pages": total_pages, "total_records": total},
    )


@router.get("/orders/{order_id}", response_model=ProductionOrderResponse)
async def get_production_order(order_id: str):
    """Get production order details with BOM and routing."""
    if order_id not in _production_orders:
        raise HTTPException(status_code=404, detail=f"Production order not found: {order_id}")
    return ProductionOrderResponse(**_production_orders[order_id])


@router.get("/bom", response_model=BOMResponse)
async def get_bill_of_materials(material_id: str):
    """Get Bill of Materials for a material."""
    if material_id not in _boms:
        raise HTTPException(status_code=404, detail=f"BOM not found for material: {material_id}")
    
    bom = _boms[material_id]
    return BOMResponse(
        bom_id=bom["bom_id"],
        material_id=bom["material_id"],
        material_description=bom["material_description"],
        base_quantity=bom["base_quantity"],
        unit_of_measure=bom["unit_of_measure"],
        components=[BOMComponent(**c) for c in bom["components"]],
    )


@router.post("/confirmations", response_model=ConfirmationResponse)
async def confirm_production(request: ConfirmationRequest):
    """Confirm production order operations."""
    global _confirmation_counter
    
    if request.order_id not in _production_orders:
        raise HTTPException(status_code=404, detail=f"Production order not found: {request.order_id}")
    
    confirmation_id = f"CONF-2024-{_confirmation_counter:05d}"
    _confirmation_counter += 1
    
    confirmation = {
        "confirmation_id": confirmation_id,
        "order_id": request.order_id,
        "operation_number": request.operation_number,
        "quantity_confirmed": request.quantity_confirmed,
        "yield_quantity": request.yield_quantity,
        "scrap_quantity": request.scrap_quantity,
        "confirmation_date": datetime.now().isoformat(),
        "confirmed_by": request.confirmed_by,
    }
    _confirmations.append(confirmation)
    
    return ConfirmationResponse(**confirmation)
