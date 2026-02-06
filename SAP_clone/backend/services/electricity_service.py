"""
Electricity Load Request Service
Handles electricity load enhancement requests from MuleSoft integration
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ticket_models import Module, TicketType, Priority
from backend.services.ticket_service import TicketService
from backend.services.event_service import EventService


class ElectricityLoadRequest:
    """Data model for electricity load enhancement request"""
    
    def __init__(
        self,
        request_id: str,
        customer_id: str,
        current_load: float,
        requested_load: float,
        connection_type: str,
        city: str,
        pin_code: str,
    ):
        self.request_id = request_id
        self.customer_id = customer_id
        self.current_load = current_load
        self.requested_load = requested_load
        self.connection_type = connection_type
        self.city = city
        self.pin_code = pin_code
        self.load_increase = requested_load - current_load
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "customer_id": self.customer_id,
            "current_load": self.current_load,
            "requested_load": self.requested_load,
            "load_increase": self.load_increase,
            "connection_type": self.connection_type,
            "city": self.city,
            "pin_code": self.pin_code,
        }


class ElectricityService:
    """Service for processing electricity load requests"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.ticket_service = TicketService(session)
        self.event_service = EventService(session)
    
    def _determine_priority(self, load_increase: float) -> Priority:
        """Determine priority based on load increase amount"""
        if load_increase >= 20:  # Major load increase
            return Priority.P1
        elif load_increase >= 10:
            return Priority.P2
        elif load_increase >= 5:
            return Priority.P3
        else:
            return Priority.P4
    
    def _calculate_estimated_cost(self, load_increase: float, connection_type: str) -> float:
        """Calculate estimated cost for load enhancement"""
        base_rate = 5000.0  # Base processing fee
        per_kw_rate = 2500.0 if connection_type == "RESIDENTIAL" else 3500.0
        return base_rate + (load_increase * per_kw_rate)
    
    def _requires_equipment_upgrade(self, requested_load: float) -> bool:
        """Check if equipment upgrade is required"""
        return requested_load > 15  # Loads above 15 kW need equipment upgrade
    
    async def process_load_request(
        self,
        load_request: ElectricityLoadRequest,
        created_by: str = "mulesoft_integration",
    ) -> Dict[str, Any]:
        """
        Process electricity load enhancement request.
        Creates tickets and triggers workflows across modules.
        """
        priority = self._determine_priority(load_request.load_increase)
        estimated_cost = self._calculate_estimated_cost(
            load_request.load_increase,
            load_request.connection_type
        )
        requires_equipment = self._requires_equipment_upgrade(load_request.requested_load)
        
        # Create main PM ticket for load enhancement work order
        pm_ticket = await self.ticket_service.create_ticket(
            module=Module.PM,
            ticket_type=TicketType.MAINTENANCE,
            priority=priority,
            title=f"Load Enhancement: {load_request.customer_id} - {load_request.current_load}kW to {load_request.requested_load}kW",
            description=f"""
Electricity Load Enhancement Request
Request ID: {load_request.request_id}
Customer: {load_request.customer_id}
Location: {load_request.city}, {load_request.pin_code}
Connection Type: {load_request.connection_type}
Current Load: {load_request.current_load} kW
Requested Load: {load_request.requested_load} kW
Load Increase: {load_request.load_increase} kW
Estimated Cost: ₹{estimated_cost:,.2f}
Equipment Upgrade Required: {'Yes' if requires_equipment else 'No'}
            """.strip(),
            created_by=created_by,
            correlation_id=load_request.request_id,
        )
        
        # Create FI ticket for cost approval if cost is significant
        fi_ticket = None
        if estimated_cost > 10000:
            fi_ticket = await self.ticket_service.create_ticket(
                module=Module.FI,
                ticket_type=TicketType.FINANCE_APPROVAL,
                priority=priority,
                title=f"Cost Approval: Load Enhancement {load_request.customer_id}",
                description=f"""
Financial approval required for load enhancement.
Customer: {load_request.customer_id}
Estimated Cost: ₹{estimated_cost:,.2f}
Load Increase: {load_request.load_increase} kW
Related PM Ticket: {pm_ticket.ticket_id}
                """.strip(),
                created_by=created_by,
                correlation_id=load_request.request_id,
            )
        
        # Create MM ticket for equipment procurement if needed
        mm_ticket = None
        if requires_equipment:
            mm_ticket = await self.ticket_service.create_ticket(
                module=Module.MM,
                ticket_type=TicketType.PROCUREMENT,
                priority=priority,
                title=f"Equipment Procurement: Load Enhancement {load_request.customer_id}",
                description=f"""
Equipment procurement required for load enhancement.
Customer: {load_request.customer_id}
Requested Load: {load_request.requested_load} kW
Required Equipment: High-capacity meter, cables, circuit breaker
Location: {load_request.city}, {load_request.pin_code}
Related PM Ticket: {pm_ticket.ticket_id}
                """.strip(),
                created_by=created_by,
                correlation_id=load_request.request_id,
            )
        
        # Log event (optional - can be removed if EventService doesn't support it)
        # await self.event_service.log_event(
        #     event_type="electricity_load_request_received",
        #     module="integration",
        #     entity_id=load_request.request_id,
        #     user_id=created_by,
        #     details={
        #         "customer_id": load_request.customer_id,
        #         "load_increase": load_request.load_increase,
        #         "pm_ticket": pm_ticket.ticket_id,
        #         "fi_ticket": fi_ticket.ticket_id if fi_ticket else None,
        #         "mm_ticket": mm_ticket.ticket_id if mm_ticket else None,
        #         "estimated_cost": estimated_cost,
        #     }
        # )
        
        await self.session.commit()
        
        return {
            "status": "accepted",
            "request_id": load_request.request_id,
            "customer_id": load_request.customer_id,
            "estimated_cost": estimated_cost,
            "priority": priority.value,
            "tickets_created": {
                "pm_ticket": pm_ticket.ticket_id,
                "fi_ticket": fi_ticket.ticket_id if fi_ticket else None,
                "mm_ticket": mm_ticket.ticket_id if mm_ticket else None,
            },
            "workflow_status": "initiated",
            "next_steps": [
                "Technical feasibility assessment" if requires_equipment else "Site survey scheduled",
                "Financial approval pending" if fi_ticket else "Cost approved",
                "Equipment procurement initiated" if mm_ticket else "No equipment needed",
            ],
        }
