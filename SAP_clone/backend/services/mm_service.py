"""
Materials Management (MM) Service for inventory and procurement management.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5 - Material CRUD, auto-reorder, requisitions
"""
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.mm_models import (
    Material, StockTransaction, TransactionType,
    MMRequisition, RequisitionStatus
)
from backend.models.ticket_models import Module, TicketType, Priority
from backend.services.ticket_service import TicketService
from backend.services.event_service import EventService, EventType


class MMServiceError(Exception):
    """Base exception for MM service errors"""
    pass


class MaterialNotFoundError(MMServiceError):
    """Raised when a material is not found"""
    pass


class InsufficientStockError(MMServiceError):
    """Raised when stock is insufficient for an operation"""
    pass


class MMService:
    """
    Service class for Materials Management operations.
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
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
    
    # Material CRUD Operations - Requirement 3.1
    
    async def create_material(
        self,
        description: str,
        quantity: int,
        unit_of_measure: str,
        reorder_level: int,
        storage_location: str,
        material_id: Optional[str] = None,
    ) -> Material:
        """
        Create a new material.
        Requirement 3.1 - Store material master data
        """
        if material_id is None:
            material_id = f"MAT-{uuid.uuid4().hex[:8].upper()}"
        
        material = Material(
            material_id=material_id,
            description=description,
            quantity=quantity,
            unit_of_measure=unit_of_measure,
            reorder_level=reorder_level,
            storage_location=storage_location,
        )
        
        self.session.add(material)
        await self.session.flush()
        return material

    
    async def get_material(self, material_id: str) -> Optional[Material]:
        """Get a material by ID."""
        result = await self.session.execute(
            select(Material).where(Material.material_id == material_id)
        )
        return result.scalar_one_or_none()
    
    async def get_material_or_raise(self, material_id: str) -> Material:
        """Get a material by ID or raise MaterialNotFoundError."""
        material = await self.get_material(material_id)
        if not material:
            raise MaterialNotFoundError(f"Material not found: {material_id}")
        return material
    
    async def list_materials(
        self,
        storage_location: Optional[str] = None,
        below_reorder: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Material], int]:
        """List materials with optional filtering."""
        query = select(Material)
        count_query = select(func.count(Material.material_id))
        
        if storage_location:
            query = query.where(Material.storage_location == storage_location)
            count_query = count_query.where(Material.storage_location == storage_location)
        if below_reorder:
            query = query.where(Material.quantity < Material.reorder_level)
            count_query = count_query.where(Material.quantity < Material.reorder_level)
        
        query = query.order_by(Material.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        materials = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return materials, total
    
    # Stock Transaction Operations - Requirement 3.4, 3.5
    
    async def process_stock_transaction(
        self,
        material_id: str,
        quantity_change: int,
        transaction_type: TransactionType,
        performed_by: str,
        reference_doc: Optional[str] = None,
        notes: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[StockTransaction, Optional["Ticket"]]:
        """
        Process a stock transaction and check for auto-reorder.
        Requirements: 3.2, 3.4, 3.5
        """
        material = await self.get_material_or_raise(material_id)
        
        # Validate stock for issue transactions
        if transaction_type == TransactionType.ISSUE:
            if material.quantity + quantity_change < 0:
                raise InsufficientStockError(
                    f"Insufficient stock for {material_id}. "
                    f"Available: {material.quantity}, Requested: {abs(quantity_change)}"
                )
        
        # Update material quantity
        old_quantity = material.quantity
        material.quantity += quantity_change
        material.updated_at = datetime.utcnow()
        
        # Create transaction record - Requirement 3.5
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        transaction = StockTransaction(
            transaction_id=transaction_id,
            material_id=material_id,
            quantity_change=quantity_change,
            transaction_type=transaction_type,
            performed_by=performed_by,
            reference_doc=reference_doc,
            notes=notes,
        )
        
        self.session.add(transaction)
        
        # Emit stock event - Requirement 3.4
        await self.event_service.emit_mm_stock_event(
            material_id=material_id,
            quantity_change=quantity_change,
            new_quantity=material.quantity,
            reorder_level=material.reorder_level,
            transaction_type=transaction_type.value,
            correlation_id=correlation_id,
        )
        
        # Check for auto-reorder - Requirement 3.2
        reorder_ticket = None
        if material.is_below_reorder_level() and old_quantity >= material.reorder_level:
            reorder_ticket = await self._create_reorder_ticket(
                material=material,
                performed_by=performed_by,
                correlation_id=correlation_id,
            )
        
        await self.session.flush()
        return transaction, reorder_ticket

    
    async def _create_reorder_ticket(
        self,
        material: Material,
        performed_by: str,
        correlation_id: Optional[str] = None,
    ) -> "Ticket":
        """
        Create auto-reorder ticket when stock falls below reorder level.
        Requirement 3.2 - Auto-generate procurement ticket
        """
        # Calculate suggested reorder quantity (reorder_level + buffer - current)
        buffer = material.reorder_level // 2  # 50% buffer
        suggested_quantity = material.reorder_level + buffer - material.quantity
        
        ticket = await self.ticket_service.create_ticket(
            module=Module.MM,
            ticket_type=TicketType.PROCUREMENT,
            priority=Priority.P3,
            title=f"Auto-Reorder: {material.description[:50]}",
            created_by="SYSTEM",
            description=(
                f"Stock for {material.material_id} ({material.description}) "
                f"has fallen below reorder level.\n"
                f"Current quantity: {material.quantity}\n"
                f"Reorder level: {material.reorder_level}\n"
                f"Suggested reorder quantity: {suggested_quantity}"
            ),
            correlation_id=correlation_id,
        )
        
        # Emit reorder event
        await self.event_service.emit_mm_stock_event(
            material_id=material.material_id,
            quantity_change=0,
            new_quantity=material.quantity,
            reorder_level=material.reorder_level,
            transaction_type="reorder",
            correlation_id=correlation_id,
            is_reorder=True,
        )
        
        return ticket
    
    async def get_transaction_history(
        self,
        material_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[StockTransaction], int]:
        """
        Get transaction history for a material.
        Requirement 3.5 - Maintain complete transaction history
        """
        query = (
            select(StockTransaction)
            .where(StockTransaction.material_id == material_id)
            .order_by(StockTransaction.transaction_date.desc())
            .limit(limit)
            .offset(offset)
        )
        
        count_query = (
            select(func.count(StockTransaction.transaction_id))
            .where(StockTransaction.material_id == material_id)
        )
        
        result = await self.session.execute(query)
        transactions = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return transactions, total
    
    # Purchase Requisition Operations - Requirement 3.3
    
    async def create_purchase_requisition(
        self,
        material_id: str,
        quantity: int,
        cost_center_id: str,
        justification: str,
        requested_by: str,
        correlation_id: Optional[str] = None,
    ) -> Tuple[MMRequisition, "Ticket"]:
        """
        Create a purchase requisition with associated ticket.
        Requirement 3.3 - Create procurement ticket linked to cost center
        """
        material = await self.get_material_or_raise(material_id)
        
        # Create ticket for the requisition
        ticket = await self.ticket_service.create_ticket(
            module=Module.MM,
            ticket_type=TicketType.PROCUREMENT,
            priority=Priority.P3,
            title=f"Purchase Requisition: {material.description[:50]}",
            created_by=requested_by,
            description=f"Quantity: {quantity} {material.unit_of_measure}\n{justification}",
            correlation_id=correlation_id,
        )
        
        requisition_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        
        requisition = MMRequisition(
            requisition_id=requisition_id,
            material_id=material_id,
            ticket_id=ticket.ticket_id,
            cost_center_id=cost_center_id,
            quantity=quantity,
            justification=justification,
            status=RequisitionStatus.PENDING,
            requested_by=requested_by,
        )
        
        self.session.add(requisition)
        
        # Emit requisition event
        self.event_service.create_event(event_type=EventType.MM_REQUISITION_CREATED,
        payload={
            "requisition_id": requisition_id,
            "material_id": material_id,
            "quantity": quantity,
            "cost_center_id": cost_center_id,
        },
        correlation_id=correlation_id,)
        
        await self.session.flush()
        return requisition, ticket
    
    async def get_requisition(self, requisition_id: str) -> Optional[MMRequisition]:
        """Get a requisition by ID."""
        result = await self.session.execute(
            select(MMRequisition).where(MMRequisition.requisition_id == requisition_id)
        )
        return result.scalar_one_or_none()
    
    async def list_requisitions(
        self,
        material_id: Optional[str] = None,
        status: Optional[RequisitionStatus] = None,
        cost_center_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[MMRequisition], int]:
        """List requisitions with optional filtering."""
        query = select(MMRequisition)
        count_query = select(func.count(MMRequisition.requisition_id))
        
        if material_id:
            query = query.where(MMRequisition.material_id == material_id)
            count_query = count_query.where(MMRequisition.material_id == material_id)
        if status:
            query = query.where(MMRequisition.status == status)
            count_query = count_query.where(MMRequisition.status == status)
        if cost_center_id:
            query = query.where(MMRequisition.cost_center_id == cost_center_id)
            count_query = count_query.where(MMRequisition.cost_center_id == cost_center_id)
        
        query = query.order_by(MMRequisition.requested_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        requisitions = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return requisitions, total
    
    async def approve_requisition(
        self,
        requisition_id: str,
        approved_by: str,
    ) -> MMRequisition:
        """Approve a purchase requisition."""
        result = await self.session.execute(
            select(MMRequisition).where(MMRequisition.requisition_id == requisition_id)
        )
        requisition = result.scalar_one_or_none()
        if not requisition:
            raise MMServiceError(f"Requisition not found: {requisition_id}")
        
        requisition.status = RequisitionStatus.APPROVED
        requisition.approved_by = approved_by
        requisition.approved_at = datetime.utcnow()
        
        await self.session.flush()
        return requisition


# Import for type hints
from backend.models.ticket_models import Ticket
