"""
Finance (FI) Service for cost center and approval management.
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5 - Cost centers, cost tracking, approvals
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.fi_models import (
    CostCenter, CostEntry, CostType,
    FIApproval, ApprovalDecision
)
from backend.models.ticket_models import Module, TicketType, Priority
from backend.services.ticket_service import TicketService
from backend.services.event_service import EventService, EventType


class FIServiceError(Exception):
    """Base exception for FI service errors"""
    pass


class CostCenterNotFoundError(FIServiceError):
    """Raised when a cost center is not found"""
    pass


class ApprovalNotFoundError(FIServiceError):
    """Raised when an approval is not found"""
    pass


class FIService:
    """
    Service class for Finance operations.
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def __init__(
        self,
        session: AsyncSession,
        ticket_service: Optional[TicketService] = None,
        event_service: Optional[EventService] = None,
    ):
        self.session = session
        self.ticket_service = ticket_service or TicketService(session)
        self.event_service = event_service or EventService()
    
    # Cost Center CRUD Operations - Requirement 4.1
    
    async def create_cost_center(
        self,
        name: str,
        budget_amount: Decimal,
        fiscal_year: int,
        responsible_manager: str,
        cost_center_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CostCenter:
        """
        Create a new cost center.
        Requirement 4.1 - Store cost center master data
        """
        if cost_center_id is None:
            cost_center_id = f"CC-{uuid.uuid4().hex[:8].upper()}"
        
        cost_center = CostCenter(
            cost_center_id=cost_center_id,
            name=name,
            budget_amount=budget_amount,
            fiscal_year=fiscal_year,
            responsible_manager=responsible_manager,
            description=description,
        )
        
        self.session.add(cost_center)
        await self.session.flush()
        return cost_center

    
    async def get_cost_center(self, cost_center_id: str) -> Optional[CostCenter]:
        """Get a cost center by ID."""
        result = await self.session.execute(
            select(CostCenter).where(CostCenter.cost_center_id == cost_center_id)
        )
        return result.scalar_one_or_none()
    
    async def get_cost_center_or_raise(self, cost_center_id: str) -> CostCenter:
        """Get a cost center by ID or raise CostCenterNotFoundError."""
        cost_center = await self.get_cost_center(cost_center_id)
        if not cost_center:
            raise CostCenterNotFoundError(f"Cost center not found: {cost_center_id}")
        return cost_center
    
    async def list_cost_centers(
        self,
        fiscal_year: Optional[int] = None,
        responsible_manager: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[CostCenter], int]:
        """List cost centers with optional filtering."""
        query = select(CostCenter)
        count_query = select(func.count(CostCenter.cost_center_id))
        
        if fiscal_year:
            query = query.where(CostCenter.fiscal_year == fiscal_year)
            count_query = count_query.where(CostCenter.fiscal_year == fiscal_year)
        if responsible_manager:
            query = query.where(CostCenter.responsible_manager == responsible_manager)
            count_query = count_query.where(CostCenter.responsible_manager == responsible_manager)
        
        query = query.order_by(CostCenter.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        cost_centers = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return cost_centers, total
    
    # Cost Entry Operations - Requirement 4.2
    
    async def create_cost_entry(
        self,
        cost_center_id: str,
        amount: Decimal,
        cost_type: CostType,
        created_by: str,
        ticket_id: Optional[str] = None,
        description: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> CostEntry:
        """
        Create a cost entry.
        Requirement 4.2 - Track cost amount, cost_type, and associated cost_center
        """
        # Verify cost center exists
        await self.get_cost_center_or_raise(cost_center_id)
        
        if amount <= 0:
            raise FIServiceError("Cost entry amount must be positive")
        
        entry_id = f"CE-{uuid.uuid4().hex[:8].upper()}"
        
        entry = CostEntry(
            entry_id=entry_id,
            ticket_id=ticket_id,
            cost_center_id=cost_center_id,
            amount=amount,
            cost_type=cost_type,
            description=description,
            created_by=created_by,
        )
        
        self.session.add(entry)
        
        # Emit cost entry event
        self.event_service.create_event(event_type=EventType.FI_COST_ENTRY_CREATED,
        payload={
            "entry_id": entry_id,
            "cost_center_id": cost_center_id,
            "amount": float(amount),
            "cost_type": cost_type.value,
            "ticket_id": ticket_id,
        },
        correlation_id=correlation_id,)
        
        await self.session.flush()
        return entry
    
    async def get_cost_entries(
        self,
        cost_center_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        cost_type: Optional[CostType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[CostEntry], int]:
        """List cost entries with optional filtering."""
        query = select(CostEntry)
        count_query = select(func.count(CostEntry.entry_id))
        
        if cost_center_id:
            query = query.where(CostEntry.cost_center_id == cost_center_id)
            count_query = count_query.where(CostEntry.cost_center_id == cost_center_id)
        if ticket_id:
            query = query.where(CostEntry.ticket_id == ticket_id)
            count_query = count_query.where(CostEntry.ticket_id == ticket_id)
        if cost_type:
            query = query.where(CostEntry.cost_type == cost_type)
            count_query = count_query.where(CostEntry.cost_type == cost_type)
        
        query = query.order_by(CostEntry.entry_date.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        entries = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return entries, total

    
    # Approval Workflow Operations - Requirement 4.3, 4.5
    
    async def create_approval_request(
        self,
        cost_center_id: str,
        amount: Decimal,
        justification: str,
        requested_by: str,
        approval_hierarchy: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[FIApproval, "Ticket"]:
        """
        Create a financial approval request with associated ticket.
        Requirement 4.3 - Create Finance_Approval ticket with amount, justification, hierarchy
        """
        # Verify cost center exists
        cost_center = await self.get_cost_center_or_raise(cost_center_id)
        
        # Determine priority based on amount
        if amount >= Decimal("100000"):
            priority = Priority.P1
        elif amount >= Decimal("50000"):
            priority = Priority.P2
        elif amount >= Decimal("10000"):
            priority = Priority.P3
        else:
            priority = Priority.P4
        
        # Create ticket for the approval
        ticket = await self.ticket_service.create_ticket(
            module=Module.FI,
            ticket_type=TicketType.FINANCE_APPROVAL,
            priority=priority,
            title=f"Approval Request: {amount:,.2f} for {cost_center.name}",
            created_by=requested_by,
            description=justification,
            correlation_id=correlation_id,
        )
        
        approval_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
        
        approval = FIApproval(
            approval_id=approval_id,
            ticket_id=ticket.ticket_id,
            cost_center_id=cost_center_id,
            amount=amount,
            justification=justification,
            approval_hierarchy=approval_hierarchy,
            decision=ApprovalDecision.PENDING,
            requested_by=requested_by,
        )
        
        self.session.add(approval)
        
        # Emit approval request event - Requirement 4.5
        await self.event_service.emit_fi_approval_event(
            ticket_id=ticket.ticket_id,
            approval_id=approval_id,
            amount=float(amount),
            cost_type="PENDING",
            decision=None,
            correlation_id=correlation_id,
        )
        
        await self.session.flush()
        return approval, ticket
    
    async def get_approval(self, approval_id: str) -> Optional[FIApproval]:
        """Get an approval by ID."""
        result = await self.session.execute(
            select(FIApproval).where(FIApproval.approval_id == approval_id)
        )
        return result.scalar_one_or_none()
    
    async def get_approval_or_raise(self, approval_id: str) -> FIApproval:
        """Get an approval by ID or raise ApprovalNotFoundError."""
        approval = await self.get_approval(approval_id)
        if not approval:
            raise ApprovalNotFoundError(f"Approval not found: {approval_id}")
        return approval
    
    async def list_approvals(
        self,
        cost_center_id: Optional[str] = None,
        decision: Optional[ApprovalDecision] = None,
        requested_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[FIApproval], int]:
        """List approvals with optional filtering."""
        query = select(FIApproval)
        count_query = select(func.count(FIApproval.approval_id))
        
        if cost_center_id:
            query = query.where(FIApproval.cost_center_id == cost_center_id)
            count_query = count_query.where(FIApproval.cost_center_id == cost_center_id)
        if decision:
            query = query.where(FIApproval.decision == decision)
            count_query = count_query.where(FIApproval.decision == decision)
        if requested_by:
            query = query.where(FIApproval.requested_by == requested_by)
            count_query = count_query.where(FIApproval.requested_by == requested_by)
        
        query = query.order_by(FIApproval.requested_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        approvals = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return approvals, total
    
    async def approve_request(
        self,
        approval_id: str,
        decided_by: str,
        comment: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> FIApproval:
        """
        Approve a financial request.
        Requirement 4.5 - Emit approval event when approved
        """
        approval = await self.get_approval_or_raise(approval_id)
        
        if approval.decision != ApprovalDecision.PENDING:
            raise FIServiceError(f"Approval {approval_id} has already been decided")
        
        approval.decision = ApprovalDecision.APPROVED
        approval.decided_by = decided_by
        approval.decided_at = datetime.utcnow()
        approval.decision_comment = comment
        
        # Update ticket status if exists
        if approval.ticket_id:
            await self.ticket_service.update_status(
                ticket_id=approval.ticket_id,
                new_status=TicketStatus.CLOSED,
                changed_by=decided_by,
                comment=f"Approved: {comment}" if comment else "Approved",
            )
        
        # Emit approval event - Requirement 4.5
        await self.event_service.emit_fi_approval_event(
            ticket_id=approval.ticket_id or "",
            approval_id=approval_id,
            amount=float(approval.amount),
            cost_type="APPROVED",
            decision="approved",
            correlation_id=correlation_id,
        )
        
        await self.session.flush()
        return approval
    
    async def reject_request(
        self,
        approval_id: str,
        decided_by: str,
        comment: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> FIApproval:
        """
        Reject a financial request.
        Requirement 4.5 - Emit approval event when rejected
        """
        approval = await self.get_approval_or_raise(approval_id)
        
        if approval.decision != ApprovalDecision.PENDING:
            raise FIServiceError(f"Approval {approval_id} has already been decided")
        
        approval.decision = ApprovalDecision.REJECTED
        approval.decided_by = decided_by
        approval.decided_at = datetime.utcnow()
        approval.decision_comment = comment
        
        # Update ticket status if exists
        if approval.ticket_id:
            await self.ticket_service.update_status(
                ticket_id=approval.ticket_id,
                new_status=TicketStatus.CLOSED,
                changed_by=decided_by,
                comment=f"Rejected: {comment}" if comment else "Rejected",
            )
        
        # Emit rejection event - Requirement 4.5
        await self.event_service.emit_fi_approval_event(
            ticket_id=approval.ticket_id or "",
            approval_id=approval_id,
            amount=float(approval.amount),
            cost_type="REJECTED",
            decision="rejected",
            correlation_id=correlation_id,
        )
        
        await self.session.flush()
        return approval
    
    # Cross-module Event Handling - Requirement 4.4
    
    async def handle_pm_event(
        self,
        ticket_id: str,
        cost_center_id: str,
        amount: Decimal,
        cost_type: CostType,
        created_by: str,
        correlation_id: Optional[str] = None,
    ) -> CostEntry:
        """
        Handle PM module event to create cost entry.
        Requirement 4.4 - Process PM events to create cost entries
        """
        return await self.create_cost_entry(
            cost_center_id=cost_center_id,
            amount=amount,
            cost_type=cost_type,
            created_by=created_by,
            ticket_id=ticket_id,
            description=f"Cost from PM ticket {ticket_id}",
            correlation_id=correlation_id,
        )
    
    async def handle_mm_event(
        self,
        ticket_id: str,
        cost_center_id: str,
        amount: Decimal,
        cost_type: CostType,
        created_by: str,
        correlation_id: Optional[str] = None,
    ) -> CostEntry:
        """
        Handle MM module event to create cost entry.
        Requirement 4.4 - Process MM events to create cost entries
        """
        return await self.create_cost_entry(
            cost_center_id=cost_center_id,
            amount=amount,
            cost_type=cost_type,
            created_by=created_by,
            ticket_id=ticket_id,
            description=f"Cost from MM ticket {ticket_id}",
            correlation_id=correlation_id,
        )


# Import for type hints
from backend.models.ticket_models import Ticket, TicketStatus
