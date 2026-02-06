"""
Materials Management (MM) API routes.
Requirements: 3.1, 3.3, 3.4 - Material, stock transaction, and requisition management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.mm_models import TransactionType, RequisitionStatus
from backend.services.mm_service import MMService, MaterialNotFoundError, InsufficientStockError


router = APIRouter(prefix="/mm", tags=["Materials Management"])


# Request/Response Models

class MaterialCreateRequest(BaseModel):
    description: str
    quantity: int
    unit_of_measure: str
    reorder_level: int
    storage_location: str
    material_id: Optional[str] = None


class MaterialResponse(BaseModel):
    material_id: str
    description: str
    quantity: int
    unit_of_measure: str
    reorder_level: int
    storage_location: str
    is_below_reorder: bool


class MaterialListResponse(BaseModel):
    materials: List[MaterialResponse]
    total: int


class StockTransactionRequest(BaseModel):
    material_id: str
    quantity_change: int
    transaction_type: str
    performed_by: str
    reference_doc: Optional[str] = None
    notes: Optional[str] = None


class StockTransactionResponse(BaseModel):
    transaction_id: str
    material_id: str
    quantity_change: int
    transaction_type: str
    transaction_date: str
    performed_by: str
    new_quantity: int
    reorder_ticket_id: Optional[str] = None


class RequisitionCreateRequest(BaseModel):
    material_id: str
    quantity: int
    cost_center_id: str
    justification: str
    requested_by: str


class RequisitionResponse(BaseModel):
    requisition_id: str
    material_id: str
    ticket_id: Optional[str]
    cost_center_id: str
    quantity: int
    justification: str
    status: str
    requested_by: str
    requested_at: str


# Material Routes

@router.post("/materials", response_model=MaterialResponse)
async def create_material(
    request: MaterialCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new material. Requirement 3.1"""
    service = MMService(db)
    
    material = await service.create_material(
        description=request.description,
        quantity=request.quantity,
        unit_of_measure=request.unit_of_measure,
        reorder_level=request.reorder_level,
        storage_location=request.storage_location,
        material_id=request.material_id,
    )
    await db.commit()
    
    return MaterialResponse(
        material_id=material.material_id,
        description=material.description,
        quantity=material.quantity,
        unit_of_measure=material.unit_of_measure,
        reorder_level=material.reorder_level,
        storage_location=material.storage_location,
        is_below_reorder=material.is_below_reorder_level(),
    )


@router.get("/materials", response_model=MaterialListResponse)
async def list_materials(
    storage_location: Optional[str] = None,
    below_reorder: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List materials with optional filtering."""
    service = MMService(db)
    
    materials, total = await service.list_materials(
        storage_location=storage_location,
        below_reorder=below_reorder,
        limit=limit,
        offset=offset,
    )
    
    return MaterialListResponse(
        materials=[
            MaterialResponse(
                material_id=m.material_id,
                description=m.description,
                quantity=m.quantity,
                unit_of_measure=m.unit_of_measure,
                reorder_level=m.reorder_level,
                storage_location=m.storage_location,
                is_below_reorder=m.is_below_reorder_level(),
            )
            for m in materials
        ],
        total=total,
    )


@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a material by ID."""
    service = MMService(db)
    
    try:
        material = await service.get_material_or_raise(material_id)
        return MaterialResponse(
            material_id=material.material_id,
            description=material.description,
            quantity=material.quantity,
            unit_of_measure=material.unit_of_measure,
            reorder_level=material.reorder_level,
            storage_location=material.storage_location,
            is_below_reorder=material.is_below_reorder_level(),
        )
    except MaterialNotFoundError:
        raise HTTPException(status_code=404, detail=f"Material not found: {material_id}")


# Stock Transaction Routes

@router.post("/stock-transactions", response_model=StockTransactionResponse)
async def create_stock_transaction(
    request: StockTransactionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process a stock transaction. Requirements 3.2, 3.4"""
    service = MMService(db)
    
    try:
        transaction_type = TransactionType(request.transaction_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid transaction type: {request.transaction_type}")
    
    try:
        transaction, reorder_ticket = await service.process_stock_transaction(
            material_id=request.material_id,
            quantity_change=request.quantity_change,
            transaction_type=transaction_type,
            performed_by=request.performed_by,
            reference_doc=request.reference_doc,
            notes=request.notes,
        )
        
        # Get updated material quantity
        material = await service.get_material(request.material_id)
        await db.commit()
        
        return StockTransactionResponse(
            transaction_id=transaction.transaction_id,
            material_id=transaction.material_id,
            quantity_change=transaction.quantity_change,
            transaction_type=transaction.transaction_type.value,
            transaction_date=transaction.transaction_date.isoformat(),
            performed_by=transaction.performed_by,
            new_quantity=material.quantity if material else 0,
            reorder_ticket_id=reorder_ticket.ticket_id if reorder_ticket else None,
        )
    except MaterialNotFoundError:
        raise HTTPException(status_code=404, detail=f"Material not found: {request.material_id}")
    except InsufficientStockError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/materials/{material_id}/transactions")
async def get_transaction_history(
    material_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get transaction history for a material. Requirement 3.5"""
    service = MMService(db)
    
    transactions, total = await service.get_transaction_history(
        material_id=material_id,
        limit=limit,
        offset=offset,
    )
    
    return {
        "transactions": [t.to_dict() for t in transactions],
        "total": total,
    }


# Purchase Requisition Routes

@router.post("/purchase-requisitions", response_model=RequisitionResponse)
async def create_purchase_requisition(
    request: RequisitionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a purchase requisition. Requirement 3.3"""
    service = MMService(db)
    
    try:
        requisition, ticket = await service.create_purchase_requisition(
            material_id=request.material_id,
            quantity=request.quantity,
            cost_center_id=request.cost_center_id,
            justification=request.justification,
            requested_by=request.requested_by,
        )
        await db.commit()
        
        return RequisitionResponse(
            requisition_id=requisition.requisition_id,
            material_id=requisition.material_id,
            ticket_id=requisition.ticket_id,
            cost_center_id=requisition.cost_center_id,
            quantity=requisition.quantity,
            justification=requisition.justification,
            status=requisition.status.value,
            requested_by=requisition.requested_by,
            requested_at=requisition.requested_at.isoformat(),
        )
    except MaterialNotFoundError:
        raise HTTPException(status_code=404, detail=f"Material not found: {request.material_id}")


@router.get("/purchase-requisitions", response_model=List[RequisitionResponse])
async def list_purchase_requisitions(
    material_id: Optional[str] = None,
    status: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List purchase requisitions."""
    service = MMService(db)
    
    status_enum = RequisitionStatus(status) if status else None
    
    requisitions, total = await service.list_requisitions(
        material_id=material_id,
        status=status_enum,
        cost_center_id=cost_center_id,
        limit=limit,
        offset=offset,
    )
    
    return [
        RequisitionResponse(
            requisition_id=r.requisition_id,
            material_id=r.material_id,
            ticket_id=r.ticket_id,
            cost_center_id=r.cost_center_id,
            quantity=r.quantity,
            justification=r.justification,
            status=r.status.value,
            requested_by=r.requested_by,
            requested_at=r.requested_at.isoformat(),
        )
        for r in requisitions
    ]
