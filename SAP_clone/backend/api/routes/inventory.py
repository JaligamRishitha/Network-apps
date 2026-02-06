"""
Inventory Module API routes.
SAP ERP API - Stock levels and movements
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/inventory", tags=["Inventory"])


# Request/Response Models

class StockItem(BaseModel):
    material_id: str
    material_description: str
    plant: str
    storage_location: str
    available_stock: int
    reserved_stock: int
    blocked_stock: int
    unit_of_measure: str
    last_updated: str


class StockListResponse(BaseModel):
    stock: List[StockItem]
    total: int


class StockMovementRequest(BaseModel):
    material_id: str
    quantity: int
    movement_type: str  # receipt, issue, transfer
    plant: str
    storage_location: str
    reference_doc: Optional[str] = None
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    movement_id: str
    material_id: str
    quantity: int
    movement_type: str
    plant: str
    storage_location: str
    movement_date: str
    reference_doc: Optional[str]


class StockMovementListResponse(BaseModel):
    movements: List[StockMovementResponse]
    total: int


# In-memory storage for demo - matches database seed data
_stock_levels = {
    "MAT-001": {
        "material_id": "MAT-001",
        "material_description": "Copper Wire 10mm",
        "plant": "1000",
        "storage_location": "Warehouse A, Shelf 1",
        "available_stock": 500,
        "reserved_stock": 50,
        "blocked_stock": 0,
        "unit_of_measure": "meters",
        "last_updated": "2026-01-15T10:30:00Z",
    },
    "MAT-002": {
        "material_id": "MAT-002",
        "material_description": "Circuit Breaker 100A",
        "plant": "1000",
        "storage_location": "Warehouse A, Shelf 2",
        "available_stock": 25,
        "reserved_stock": 5,
        "blocked_stock": 0,
        "unit_of_measure": "pieces",
        "last_updated": "2026-01-15T11:00:00Z",
    },
    "MAT-003": {
        "material_id": "MAT-003",
        "material_description": "Transformer Oil",
        "plant": "1000",
        "storage_location": "Warehouse B, Tank 1",
        "available_stock": 200,
        "reserved_stock": 30,
        "blocked_stock": 0,
        "unit_of_measure": "liters",
        "last_updated": "2026-01-15T12:00:00Z",
    },
    "MAT-004": {
        "material_id": "MAT-004",
        "material_description": "Insulation Tape",
        "plant": "1000",
        "storage_location": "Warehouse A, Shelf 3",
        "available_stock": 150,
        "reserved_stock": 20,
        "blocked_stock": 0,
        "unit_of_measure": "rolls",
        "last_updated": "2026-01-15T13:00:00Z",
    },
    "MAT-005": {
        "material_id": "MAT-005",
        "material_description": "Fuse 30A",
        "plant": "1000",
        "storage_location": "Warehouse A, Shelf 4",
        "available_stock": 80,
        "reserved_stock": 10,
        "blocked_stock": 0,
        "unit_of_measure": "pieces",
        "last_updated": "2026-01-15T14:00:00Z",
    },
}
_movements = []
_movement_counter = 1


@router.get("/stock", response_model=StockListResponse)
async def get_stock_levels(
    plant: Optional[str] = None,
    storage_location: Optional[str] = None,
    material_id: Optional[str] = None,
):
    """Get stock levels with optional filtering by plant and storage location."""
    stock = list(_stock_levels.values())
    
    if plant:
        stock = [s for s in stock if s["plant"] == plant]
    if storage_location:
        stock = [s for s in stock if s["storage_location"] == storage_location]
    if material_id:
        stock = [s for s in stock if s["material_id"] == material_id]
    
    return StockListResponse(
        stock=[StockItem(**s) for s in stock],
        total=len(stock),
    )


@router.get("/movements", response_model=StockMovementListResponse)
async def get_stock_movements(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    material_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get stock movements history with filtering."""
    movements = _movements.copy()
    
    if material_id:
        movements = [m for m in movements if m["material_id"] == material_id]
    if movement_type:
        movements = [m for m in movements if m["movement_type"] == movement_type]
    
    total = len(movements)
    start = (page - 1) * page_size
    end = start + page_size
    
    return StockMovementListResponse(
        movements=[StockMovementResponse(**m) for m in movements[start:end]],
        total=total,
    )


@router.post("/movements", response_model=StockMovementResponse)
async def post_goods_movement(request: StockMovementRequest):
    """Post goods movement (receipt, issue, transfer)."""
    global _movement_counter
    
    valid_types = ["receipt", "issue", "transfer"]
    if request.movement_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid movement type. Must be one of: {valid_types}")
    
    movement_id = f"MOV-{_movement_counter:06d}"
    _movement_counter += 1
    
    movement = {
        "movement_id": movement_id,
        "material_id": request.material_id,
        "quantity": request.quantity,
        "movement_type": request.movement_type,
        "plant": request.plant,
        "storage_location": request.storage_location,
        "movement_date": datetime.now().isoformat(),
        "reference_doc": request.reference_doc,
    }
    _movements.append(movement)
    
    # Update stock levels
    if request.material_id in _stock_levels:
        stock = _stock_levels[request.material_id]
        if request.movement_type == "receipt":
            stock["available_stock"] += request.quantity
        elif request.movement_type == "issue":
            stock["available_stock"] -= request.quantity
        stock["last_updated"] = datetime.now().isoformat()
    
    return StockMovementResponse(**movement)
