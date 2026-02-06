"""
Finance (FI) API routes.
Requirements: 4.1, 4.2, 4.3, 4.5 - Cost center, cost entry, and approval management
"""
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.fi_models import CostType, ApprovalDecision
from backend.services.fi_service import (
    FIService, CostCenterNotFoundError, ApprovalNotFoundError, FIServiceError
)


router = APIRouter(prefix="/fi", tags=["Finance"])


# Request/Response Models

class CostCenterCreateRequest(BaseModel):
    name: str
    budget_amount: float
    fiscal_year: int
    responsible_manager: str
    cost_center_id: Optional[str] = None
    description: Optional[str] = None


class CostCenterResponse(BaseModel):
    cost_center_id: str
    name: str
    budget_amount: float
    fiscal_year: int
    responsible_manager: str
    description: Optional[str]


class CostCenterListResponse(BaseModel):
    cost_centers: List[CostCenterResponse]
    total: int


class CostEntryCreateRequest(BaseModel):
    cost_center_id: str
    amount: float
    cost_type: str
    created_by: str
    ticket_id: Optional[str] = None
    description: Optional[str] = None


class CostEntryResponse(BaseModel):
    entry_id: str
    ticket_id: Optional[str]
    cost_center_id: str
    amount: float
    cost_type: str
    description: Optional[str]
    entry_date: str
    created_by: str


class ApprovalCreateRequest(BaseModel):
    cost_center_id: str
    amount: float
    justification: str
    requested_by: str
    approval_hierarchy: Optional[List[str]] = None


class ApprovalResponse(BaseModel):
    approval_id: str
    ticket_id: Optional[str]
    cost_center_id: str
    amount: float
    justification: str
    decision: str
    requested_by: str
    requested_at: str
    decided_by: Optional[str]
    decided_at: Optional[str]


class ApprovalDecisionRequest(BaseModel):
    decided_by: str
    comment: Optional[str] = None


# Cost Center Routes

@router.post("/cost-centers", response_model=CostCenterResponse)
async def create_cost_center(
    request: CostCenterCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new cost center. Requirement 4.1"""
    service = FIService(db)
    
    cost_center = await service.create_cost_center(
        name=request.name,
        budget_amount=Decimal(str(request.budget_amount)),
        fiscal_year=request.fiscal_year,
        responsible_manager=request.responsible_manager,
        cost_center_id=request.cost_center_id,
        description=request.description,
    )
    await db.commit()
    
    return CostCenterResponse(
        cost_center_id=cost_center.cost_center_id,
        name=cost_center.name,
        budget_amount=float(cost_center.budget_amount),
        fiscal_year=cost_center.fiscal_year,
        responsible_manager=cost_center.responsible_manager,
        description=cost_center.description,
    )


@router.get("/cost-centers", response_model=CostCenterListResponse)
async def list_cost_centers(
    fiscal_year: Optional[int] = None,
    responsible_manager: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List cost centers with optional filtering."""
    service = FIService(db)
    
    cost_centers, total = await service.list_cost_centers(
        fiscal_year=fiscal_year,
        responsible_manager=responsible_manager,
        limit=limit,
        offset=offset,
    )
    
    return CostCenterListResponse(
        cost_centers=[
            CostCenterResponse(
                cost_center_id=cc.cost_center_id,
                name=cc.name,
                budget_amount=float(cc.budget_amount),
                fiscal_year=cc.fiscal_year,
                responsible_manager=cc.responsible_manager,
                description=cc.description,
            )
            for cc in cost_centers
        ],
        total=total,
    )


@router.get("/cost-centers/{cost_center_id}", response_model=CostCenterResponse)
async def get_cost_center(
    cost_center_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a cost center by ID."""
    service = FIService(db)
    
    try:
        cost_center = await service.get_cost_center_or_raise(cost_center_id)
        return CostCenterResponse(
            cost_center_id=cost_center.cost_center_id,
            name=cost_center.name,
            budget_amount=float(cost_center.budget_amount),
            fiscal_year=cost_center.fiscal_year,
            responsible_manager=cost_center.responsible_manager,
            description=cost_center.description,
        )
    except CostCenterNotFoundError:
        raise HTTPException(status_code=404, detail=f"Cost center not found: {cost_center_id}")


# Cost Entry Routes

@router.post("/cost-entries", response_model=CostEntryResponse)
async def create_cost_entry(
    request: CostEntryCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a cost entry. Requirement 4.2"""
    service = FIService(db)
    
    try:
        cost_type = CostType(request.cost_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cost type: {request.cost_type}")
    
    try:
        entry = await service.create_cost_entry(
            cost_center_id=request.cost_center_id,
            amount=Decimal(str(request.amount)),
            cost_type=cost_type,
            created_by=request.created_by,
            ticket_id=request.ticket_id,
            description=request.description,
        )
        await db.commit()
        
        return CostEntryResponse(
            entry_id=entry.entry_id,
            ticket_id=entry.ticket_id,
            cost_center_id=entry.cost_center_id,
            amount=float(entry.amount),
            cost_type=entry.cost_type.value,
            description=entry.description,
            entry_date=entry.entry_date.isoformat(),
            created_by=entry.created_by,
        )
    except CostCenterNotFoundError:
        raise HTTPException(status_code=404, detail=f"Cost center not found: {request.cost_center_id}")
    except FIServiceError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/cost-entries", response_model=List[CostEntryResponse])
async def list_cost_entries(
    cost_center_id: Optional[str] = None,
    ticket_id: Optional[str] = None,
    cost_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List cost entries with optional filtering."""
    service = FIService(db)
    
    type_enum = CostType(cost_type) if cost_type else None
    
    entries, total = await service.get_cost_entries(
        cost_center_id=cost_center_id,
        ticket_id=ticket_id,
        cost_type=type_enum,
        limit=limit,
        offset=offset,
    )
    
    return [
        CostEntryResponse(
            entry_id=e.entry_id,
            ticket_id=e.ticket_id,
            cost_center_id=e.cost_center_id,
            amount=float(e.amount),
            cost_type=e.cost_type.value,
            description=e.description,
            entry_date=e.entry_date.isoformat(),
            created_by=e.created_by,
        )
        for e in entries
    ]


# Approval Routes

@router.post("/approval-requests", response_model=ApprovalResponse)
async def create_approval_request(
    request: ApprovalCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create an approval request. Requirement 4.3"""
    service = FIService(db)
    
    try:
        approval, ticket = await service.create_approval_request(
            cost_center_id=request.cost_center_id,
            amount=Decimal(str(request.amount)),
            justification=request.justification,
            requested_by=request.requested_by,
            approval_hierarchy=request.approval_hierarchy,
        )
        await db.commit()
        
        return ApprovalResponse(
            approval_id=approval.approval_id,
            ticket_id=approval.ticket_id,
            cost_center_id=approval.cost_center_id,
            amount=float(approval.amount),
            justification=approval.justification,
            decision=approval.decision.value,
            requested_by=approval.requested_by,
            requested_at=approval.requested_at.isoformat(),
            decided_by=approval.decided_by,
            decided_at=approval.decided_at.isoformat() if approval.decided_at else None,
        )
    except CostCenterNotFoundError:
        raise HTTPException(status_code=404, detail=f"Cost center not found: {request.cost_center_id}")


@router.get("/approval-requests", response_model=List[ApprovalResponse])
async def list_approval_requests(
    cost_center_id: Optional[str] = None,
    decision: Optional[str] = None,
    requested_by: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List approval requests with optional filtering."""
    service = FIService(db)
    
    decision_enum = ApprovalDecision(decision) if decision else None
    
    approvals, total = await service.list_approvals(
        cost_center_id=cost_center_id,
        decision=decision_enum,
        requested_by=requested_by,
        limit=limit,
        offset=offset,
    )
    
    return [
        ApprovalResponse(
            approval_id=a.approval_id,
            ticket_id=a.ticket_id,
            cost_center_id=a.cost_center_id,
            amount=float(a.amount),
            justification=a.justification,
            decision=a.decision.value,
            requested_by=a.requested_by,
            requested_at=a.requested_at.isoformat(),
            decided_by=a.decided_by,
            decided_at=a.decided_at.isoformat() if a.decided_at else None,
        )
        for a in approvals
    ]


@router.post("/approval-requests/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_request(
    approval_id: str,
    request: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve a request. Requirement 4.5"""
    service = FIService(db)
    
    try:
        approval = await service.approve_request(
            approval_id=approval_id,
            decided_by=request.decided_by,
            comment=request.comment,
        )
        await db.commit()
        
        return ApprovalResponse(
            approval_id=approval.approval_id,
            ticket_id=approval.ticket_id,
            cost_center_id=approval.cost_center_id,
            amount=float(approval.amount),
            justification=approval.justification,
            decision=approval.decision.value,
            requested_by=approval.requested_by,
            requested_at=approval.requested_at.isoformat(),
            decided_by=approval.decided_by,
            decided_at=approval.decided_at.isoformat() if approval.decided_at else None,
        )
    except ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail=f"Approval not found: {approval_id}")
    except FIServiceError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/approval-requests/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_request(
    approval_id: str,
    request: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reject a request. Requirement 4.5"""
    service = FIService(db)
    
    try:
        approval = await service.reject_request(
            approval_id=approval_id,
            decided_by=request.decided_by,
            comment=request.comment,
        )
        await db.commit()
        
        return ApprovalResponse(
            approval_id=approval.approval_id,
            ticket_id=approval.ticket_id,
            cost_center_id=approval.cost_center_id,
            amount=float(approval.amount),
            justification=approval.justification,
            decision=approval.decision.value,
            requested_by=approval.requested_by,
            requested_at=approval.requested_at.isoformat(),
            decided_by=approval.decided_by,
            decided_at=approval.decided_at.isoformat() if approval.decided_at else None,
        )
    except ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail=f"Approval not found: {approval_id}")
    except FIServiceError as e:
        raise HTTPException(status_code=422, detail=str(e))
