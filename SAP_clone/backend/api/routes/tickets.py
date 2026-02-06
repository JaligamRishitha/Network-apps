"""
Ticket API routes.
Requirements: 1.4, 1.5 - Ticket status management and state transitions
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.ticket_models import Module, TicketStatus, Priority, TicketType
from backend.services.ticket_service import (
    TicketService, TicketNotFoundError, InvalidStateTransitionError
)


router = APIRouter(prefix="/tickets", tags=["Tickets"])


class TicketResponse(BaseModel):
    """Ticket response model"""
    ticket_id: str
    ticket_type: str
    module: str
    priority: str
    status: str
    title: str
    description: Optional[str]
    sla_deadline: str
    created_at: str
    created_by: str
    assigned_to: Optional[str]

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Paginated ticket list response"""
    tickets: List[TicketResponse]
    total: int
    page: int
    limit: int


class CreateTicketRequest(BaseModel):
    """Create ticket request"""
    module: str
    ticket_type: str
    priority: str
    title: str
    description: Optional[str] = None
    created_by: str


class StatusUpdateRequest(BaseModel):
    """Status update request"""
    new_status: str
    comment: Optional[str] = None
    changed_by: str


class AuditEntryResponse(BaseModel):
    """Audit entry response"""
    entry_id: int
    ticket_id: str
    previous_status: str
    new_status: str
    changed_by: str
    changed_at: str
    comment: Optional[str]


@router.post("", response_model=TicketResponse)
async def create_ticket(
    request: CreateTicketRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new ticket.
    """
    service = TicketService(db)
    
    try:
        module_enum = Module(request.module)
        ticket_type_enum = TicketType(request.ticket_type)
        priority_enum = Priority(request.priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    ticket = await service.create_ticket(
        module=module_enum,
        ticket_type=ticket_type_enum,
        priority=priority_enum,
        title=request.title,
        description=request.description,
        created_by=request.created_by,
    )
    await db.commit()
    
    return TicketResponse(
        ticket_id=ticket.ticket_id,
        ticket_type=ticket.ticket_type.value,
        module=ticket.module.value,
        priority=ticket.priority.value,
        status=ticket.status.value,
        title=ticket.title,
        description=ticket.description,
        sla_deadline=ticket.sla_deadline.isoformat(),
        created_at=ticket.created_at.isoformat(),
        created_by=ticket.created_by,
        assigned_to=ticket.assigned_to,
    )


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    module: Optional[str] = Query(None, description="Filter by module (PM, MM, FI)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List tickets with optional filtering.
    """
    service = TicketService(db)
    
    # Convert string filters to enums
    module_enum = Module(module) if module else None
    status_enum = TicketStatus(status) if status else None
    priority_enum = Priority(priority) if priority else None
    
    offset = (page - 1) * limit
    tickets, total = await service.list_tickets(
        module=module_enum,
        status=status_enum,
        priority=priority_enum,
        limit=limit,
        offset=offset,
    )
    
    return TicketListResponse(
        tickets=[
            TicketResponse(
                ticket_id=t.ticket_id,
                ticket_type=t.ticket_type.value,
                module=t.module.value,
                priority=t.priority.value,
                status=t.status.value,
                title=t.title,
                description=t.description,
                sla_deadline=t.sla_deadline.isoformat(),
                created_at=t.created_at.isoformat(),
                created_by=t.created_by,
                assigned_to=t.assigned_to,
            )
            for t in tickets
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a ticket by ID.
    """
    service = TicketService(db)
    
    try:
        ticket = await service.get_ticket_or_raise(ticket_id)
        return TicketResponse(
            ticket_id=ticket.ticket_id,
            ticket_type=ticket.ticket_type.value,
            module=ticket.module.value,
            priority=ticket.priority.value,
            status=ticket.status.value,
            title=ticket.title,
            description=ticket.description,
            sla_deadline=ticket.sla_deadline.isoformat(),
            created_at=ticket.created_at.isoformat(),
            created_by=ticket.created_by,
            assigned_to=ticket.assigned_to,
        )
    except TicketNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}")


@router.patch("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update ticket status with state machine validation.
    Requirements: 1.4, 1.5 - Enforce valid state transitions and create audit trail
    """
    service = TicketService(db)
    
    try:
        new_status = TicketStatus(request.new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.new_status}")
    
    try:
        ticket, audit_entry = await service.update_status(
            ticket_id=ticket_id,
            new_status=new_status,
            changed_by=request.changed_by,
            comment=request.comment,
        )
        await db.commit()
        
        return {
            "ticket_id": ticket.ticket_id,
            "status": ticket.status.value,
            "audit_entry": AuditEntryResponse(
                entry_id=audit_entry.entry_id,
                ticket_id=audit_entry.ticket_id,
                previous_status=audit_entry.previous_status.value,
                new_status=audit_entry.new_status.value,
                changed_by=audit_entry.changed_by,
                changed_at=audit_entry.changed_at.isoformat(),
                comment=audit_entry.comment,
            ),
        }
    except TicketNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{ticket_id}/audit", response_model=List[AuditEntryResponse])
async def get_ticket_audit_trail(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get audit trail for a ticket.
    Requirement 1.4 - Record audit trail with timestamp, user, previous/new status
    """
    service = TicketService(db)
    
    entries = await service.get_audit_trail(ticket_id)
    
    return [
        AuditEntryResponse(
            entry_id=e.entry_id,
            ticket_id=e.ticket_id,
            previous_status=e.previous_status.value,
            new_status=e.new_status.value,
            changed_by=e.changed_by,
            changed_at=e.changed_at.isoformat(),
            comment=e.comment,
        )
        for e in entries
    ]
