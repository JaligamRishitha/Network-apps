"""
Plant Maintenance (PM) Service for asset and maintenance management.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5 - Asset CRUD, maintenance orders, incidents
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pm_models import (
    Asset, AssetType, AssetStatus,
    MaintenanceOrder, OrderType, OrderStatus,
    PMIncident, FaultType
)
from backend.models.ticket_models import Module, TicketType, Priority
from backend.services.ticket_service import TicketService
from backend.services.event_service import EventService, EventType


class PMServiceError(Exception):
    """Base exception for PM service errors"""
    pass


class AssetNotFoundError(PMServiceError):
    """Raised when an asset is not found"""
    pass


class PMService:
    """
    Service class for Plant Maintenance operations.
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
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
    
    # Asset CRUD Operations - Requirement 2.1
    
    async def create_asset(
        self,
        asset_type: AssetType,
        name: str,
        location: str,
        installation_date: date,
        status: AssetStatus = AssetStatus.OPERATIONAL,
        description: Optional[str] = None,
    ) -> Asset:
        """
        Create a new asset.
        Requirement 2.1 - Store asset master data
        """
        asset_id = f"AST-{uuid.uuid4().hex[:8].upper()}"
        
        asset = Asset(
            asset_id=asset_id,
            asset_type=asset_type,
            name=name,
            location=location,
            installation_date=installation_date,
            status=status,
            description=description,
        )
        
        self.session.add(asset)
        await self.session.flush()
        return asset

    
    async def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get an asset by ID."""
        result = await self.session.execute(
            select(Asset).where(Asset.asset_id == asset_id)
        )
        return result.scalar_one_or_none()
    
    async def get_asset_or_raise(self, asset_id: str) -> Asset:
        """Get an asset by ID or raise AssetNotFoundError."""
        asset = await self.get_asset(asset_id)
        if not asset:
            raise AssetNotFoundError(f"Asset not found: {asset_id}")
        return asset
    
    async def list_assets(
        self,
        asset_type: Optional[AssetType] = None,
        status: Optional[AssetStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Asset], int]:
        """List assets with optional filtering."""
        query = select(Asset)
        count_query = select(func.count(Asset.asset_id))
        
        if asset_type:
            query = query.where(Asset.asset_type == asset_type)
            count_query = count_query.where(Asset.asset_type == asset_type)
        if status:
            query = query.where(Asset.status == status)
            count_query = count_query.where(Asset.status == status)
        
        query = query.order_by(Asset.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        assets = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return assets, total
    
    async def update_asset_status(self, asset_id: str, status: AssetStatus) -> Asset:
        """Update asset status."""
        asset = await self.get_asset_or_raise(asset_id)
        asset.status = status
        asset.updated_at = datetime.utcnow()
        await self.session.flush()
        return asset
    
    # Maintenance Order Operations - Requirement 2.2
    
    async def create_maintenance_order(
        self,
        asset_id: str,
        order_type: OrderType,
        description: str,
        scheduled_date: datetime,
        created_by: str,
        priority: Priority = Priority.P3,
        correlation_id: Optional[str] = None,
    ) -> Tuple[MaintenanceOrder, "Ticket"]:
        """
        Create a maintenance order with associated ticket.
        Requirement 2.2 - Link order to asset, set order type, generate ticket
        """
        # Verify asset exists
        asset = await self.get_asset_or_raise(asset_id)
        
        # Create ticket for the maintenance order
        ticket = await self.ticket_service.create_ticket(
            module=Module.PM,
            ticket_type=TicketType.MAINTENANCE,
            priority=priority,
            title=f"Maintenance Order: {description[:50]}",
            created_by=created_by,
            description=description,
            correlation_id=correlation_id,
        )
        
        order_id = f"MO-{uuid.uuid4().hex[:8].upper()}"
        
        order = MaintenanceOrder(
            order_id=order_id,
            asset_id=asset_id,
            ticket_id=ticket.ticket_id,
            order_type=order_type,
            status=OrderStatus.PLANNED,
            description=description,
            scheduled_date=scheduled_date,
            created_by=created_by,
        )
        
        self.session.add(order)
        await self.session.flush()
        
        # Emit event - Requirement 2.4
        await self.event_service.emit_pm_ticket_event(
            ticket_id=ticket.ticket_id,
            ticket_type=TicketType.MAINTENANCE.value,
            asset_id=asset_id,
            fault_type=None,
            severity=priority.value,
            status=ticket.status.value,
            correlation_id=correlation_id,
        )
        
        return order, ticket
    
    async def get_maintenance_order(self, order_id: str) -> Optional[MaintenanceOrder]:
        """Get a maintenance order by ID."""
        result = await self.session.execute(
            select(MaintenanceOrder).where(MaintenanceOrder.order_id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def list_maintenance_orders(
        self,
        asset_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        order_type: Optional[OrderType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[MaintenanceOrder], int]:
        """List maintenance orders with optional filtering."""
        query = select(MaintenanceOrder)
        count_query = select(func.count(MaintenanceOrder.order_id))
        
        if asset_id:
            query = query.where(MaintenanceOrder.asset_id == asset_id)
            count_query = count_query.where(MaintenanceOrder.asset_id == asset_id)
        if status:
            query = query.where(MaintenanceOrder.status == status)
            count_query = count_query.where(MaintenanceOrder.status == status)
        if order_type:
            query = query.where(MaintenanceOrder.order_type == order_type)
            count_query = count_query.where(MaintenanceOrder.order_type == order_type)
        
        query = query.order_by(MaintenanceOrder.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        orders = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return orders, total

    
    async def complete_maintenance_order(
        self,
        order_id: str,
        completed_by: str,
        correlation_id: Optional[str] = None,
    ) -> MaintenanceOrder:
        """
        Complete a maintenance order and update asset history.
        Requirement 2.5 - Update asset maintenance history on completion
        """
        result = await self.session.execute(
            select(MaintenanceOrder).where(MaintenanceOrder.order_id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise PMServiceError(f"Maintenance order not found: {order_id}")
        
        order.status = OrderStatus.COMPLETED
        order.completed_date = datetime.utcnow()
        
        # Update ticket status if exists
        if order.ticket_id:
            await self.ticket_service.update_status(
                ticket_id=order.ticket_id,
                new_status=TicketStatus.CLOSED,
                changed_by=completed_by,
                comment="Maintenance order completed",
            )
        
        # Emit completion event
        self.event_service.create_event(event_type=EventType.PM_MAINTENANCE_ORDER_COMPLETED,
        payload={
            "order_id": order_id,
            "asset_id": order.asset_id,
            "completed_by": completed_by,
        },
        correlation_id=correlation_id,)
        
        await self.session.flush()
        return order
    
    # Incident Operations - Requirement 2.3
    
    async def create_incident(
        self,
        asset_id: str,
        fault_type: FaultType,
        description: str,
        reported_by: str,
        severity: Priority = Priority.P2,
        correlation_id: Optional[str] = None,
    ) -> Tuple[PMIncident, "Ticket"]:
        """
        Create an incident with associated ticket.
        Requirement 2.3 - Create incident with fault_type, affected_asset, severity
        """
        # Verify asset exists
        asset = await self.get_asset_or_raise(asset_id)
        
        # Create ticket for the incident
        ticket = await self.ticket_service.create_ticket(
            module=Module.PM,
            ticket_type=TicketType.INCIDENT,
            priority=severity,
            title=f"Incident: {fault_type.value} on {asset.name}",
            created_by=reported_by,
            description=description,
            correlation_id=correlation_id,
        )
        
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        
        incident = PMIncident(
            incident_id=incident_id,
            asset_id=asset_id,
            ticket_id=ticket.ticket_id,
            fault_type=fault_type,
            description=description,
            reported_by=reported_by,
        )
        
        self.session.add(incident)
        
        # Update asset status based on fault type
        if fault_type == FaultType.OUTAGE:
            asset.status = AssetStatus.OUT_OF_SERVICE
        elif fault_type in (FaultType.FAULT, FaultType.DEGRADATION):
            asset.status = AssetStatus.UNDER_MAINTENANCE
        
        await self.session.flush()
        
        # Emit event - Requirement 2.4
        await self.event_service.emit_pm_ticket_event(
            ticket_id=ticket.ticket_id,
            ticket_type=TicketType.INCIDENT.value,
            asset_id=asset_id,
            fault_type=fault_type.value,
            severity=severity.value,
            status=ticket.status.value,
            correlation_id=correlation_id,
        )
        
        return incident, ticket
    
    async def get_incident(self, incident_id: str) -> Optional[PMIncident]:
        """Get an incident by ID."""
        result = await self.session.execute(
            select(PMIncident).where(PMIncident.incident_id == incident_id)
        )
        return result.scalar_one_or_none()
    
    async def list_incidents(
        self,
        asset_id: Optional[str] = None,
        fault_type: Optional[FaultType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[PMIncident], int]:
        """List incidents with optional filtering."""
        query = select(PMIncident)
        count_query = select(func.count(PMIncident.incident_id))
        
        if asset_id:
            query = query.where(PMIncident.asset_id == asset_id)
            count_query = count_query.where(PMIncident.asset_id == asset_id)
        if fault_type:
            query = query.where(PMIncident.fault_type == fault_type)
            count_query = count_query.where(PMIncident.fault_type == fault_type)
        
        query = query.order_by(PMIncident.reported_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        incidents = list(result.scalars().all())
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        return incidents, total
    
    async def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        correlation_id: Optional[str] = None,
    ) -> PMIncident:
        """Resolve an incident and restore asset status."""
        result = await self.session.execute(
            select(PMIncident).where(PMIncident.incident_id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if not incident:
            raise PMServiceError(f"Incident not found: {incident_id}")
        
        incident.resolved_at = datetime.utcnow()
        
        # Restore asset status
        asset = await self.get_asset(incident.asset_id)
        if asset:
            asset.status = AssetStatus.OPERATIONAL
        
        # Update ticket status if exists
        if incident.ticket_id:
            await self.ticket_service.update_status(
                ticket_id=incident.ticket_id,
                new_status=TicketStatus.CLOSED,
                changed_by=resolved_by,
                comment="Incident resolved",
            )
        
        await self.session.flush()
        return incident


# Import for type hints
from backend.models.ticket_models import Ticket, TicketStatus
