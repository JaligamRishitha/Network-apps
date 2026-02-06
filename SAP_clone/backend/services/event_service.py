"""
Event Service for publishing events to the integration layer.
Requirements: 2.4, 3.4, 4.5, 5.2, 6.3 - Event emission with correlation IDs
"""
import uuid
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from backend.config import get_settings


class EventType(str, Enum):
    """Event types with module prefixes - Requirements 2.4, 3.4, 4.5"""
    # PM Events
    PM_TICKET_CREATED = "PM_TICKET_CREATED"
    PM_TICKET_UPDATED = "PM_TICKET_UPDATED"
    PM_INCIDENT_CREATED = "PM_INCIDENT_CREATED"
    PM_MAINTENANCE_ORDER_CREATED = "PM_MAINTENANCE_ORDER_CREATED"
    PM_MAINTENANCE_ORDER_COMPLETED = "PM_MAINTENANCE_ORDER_COMPLETED"
    
    # MM Events
    MM_STOCK_CHANGED = "MM_STOCK_CHANGED"
    MM_REORDER_TRIGGERED = "MM_REORDER_TRIGGERED"
    MM_REQUISITION_CREATED = "MM_REQUISITION_CREATED"
    
    # FI Events
    FI_APPROVAL_REQUESTED = "FI_APPROVAL_REQUESTED"
    FI_APPROVAL_COMPLETED = "FI_APPROVAL_COMPLETED"
    FI_COST_ENTRY_CREATED = "FI_COST_ENTRY_CREATED"

    # USER Events
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"


class Event:
    """
    Event data structure for integration layer.
    Requirements: 5.2, 6.3 - Event with correlation_id
    """
    
    def __init__(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.payload = payload
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "payload": self.payload,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        event = cls(
            event_type=EventType(data["event_type"]),
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
        )
        event.event_id = data.get("event_id", event.event_id)
        if "timestamp" in data:
            event.timestamp = datetime.fromisoformat(data["timestamp"].rstrip("Z"))
        return event



def validate_event_type_prefix(event_type: EventType) -> bool:
    """
    Validate that event type has correct module prefix.
    Requirements: 2.4, 3.4, 4.5
    """
    valid_prefixes = {"PM_", "MM_", "FI_", "USER_"}
    return any(event_type.value.startswith(prefix) for prefix in valid_prefixes)


def get_event_module(event_type: EventType) -> str:
    """Get the module from event type prefix."""
    if event_type.value.startswith("PM_"):
        return "PM"
    elif event_type.value.startswith("MM_"):
        return "MM"
    elif event_type.value.startswith("FI_"):
        return "FI"
    elif event_type.value.startswith("USER_"):
        return "USER"
    return "UNKNOWN"


class EventService:
    """
    Service for creating and publishing events to the integration layer.
    Requirements: 2.4, 3.4, 4.5, 5.2
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        settings = get_settings()
        self.webhook_url = webhook_url or settings.camel_webhook_url
        self._published_events: list[Event] = []  # For testing
    
    def create_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Create a new event with correlation_id.
        Requirement 6.3 - Assign correlation_id that propagates through operations
        """
        if not validate_event_type_prefix(event_type):
            raise ValueError(f"Invalid event type prefix: {event_type}")
        
        return Event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
        )
    
    async def publish_event(self, event: Event) -> bool:
        """
        Publish event to Apache Camel via REST webhook.
        Requirement 5.2 - Publish event with correlation_id
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=event.to_dict(),
                    headers={
                        "Content-Type": "application/json",
                        "X-Correlation-ID": event.correlation_id,
                    },
                )
                response.raise_for_status()
                self._published_events.append(event)
                return True
        except httpx.HTTPError:
            # Log error but don't fail the operation
            return False
    
    async def emit_pm_ticket_event(
        self,
        ticket_id: str,
        ticket_type: str,
        asset_id: Optional[str],
        fault_type: Optional[str],
        severity: str,
        status: str,
        correlation_id: Optional[str] = None,
        is_update: bool = False,
    ) -> Event:
        """
        Emit PM ticket event.
        Requirement 2.4 - Emit event containing ticket_id, event_type, timestamp, payload
        """
        event_type = EventType.PM_TICKET_UPDATED if is_update else EventType.PM_TICKET_CREATED
        
        event = self.create_event(
            event_type=event_type,
            payload={
                "ticket_id": ticket_id,
                "ticket_type": ticket_type,
                "asset_id": asset_id,
                "fault_type": fault_type,
                "severity": severity,
                "status": status,
            },
            correlation_id=correlation_id,
        )
        
        await self.publish_event(event)
        return event
    
    async def emit_mm_stock_event(
        self,
        material_id: str,
        quantity_change: int,
        new_quantity: int,
        reorder_level: int,
        transaction_type: str,
        correlation_id: Optional[str] = None,
        is_reorder: bool = False,
    ) -> Event:
        """
        Emit MM stock event.
        Requirement 3.4 - Emit inventory event with material_id, quantity_change, transaction_type
        """
        event_type = EventType.MM_REORDER_TRIGGERED if is_reorder else EventType.MM_STOCK_CHANGED
        
        event = self.create_event(
            event_type=event_type,
            payload={
                "material_id": material_id,
                "quantity_change": quantity_change,
                "new_quantity": new_quantity,
                "reorder_level": reorder_level,
                "transaction_type": transaction_type,
            },
            correlation_id=correlation_id,
        )
        
        await self.publish_event(event)
        return event
    
    async def emit_fi_approval_event(
        self,
        ticket_id: str,
        approval_id: str,
        amount: float,
        cost_type: str,
        decision: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Emit FI approval event.
        Requirement 4.5 - Emit approval event when approved or rejected
        """
        event_type = EventType.FI_APPROVAL_COMPLETED if decision else EventType.FI_APPROVAL_REQUESTED
        
        event = self.create_event(
            event_type=event_type,
            payload={
                "ticket_id": ticket_id,
                "approval_id": approval_id,
                "amount": amount,
                "cost_type": cost_type,
                "decision": decision,
            },
            correlation_id=correlation_id,
        )
        
        await self.publish_event(event)
        return event

    async def emit_user_event(
        self,
        username: str,
        roles: list[str],
        created_at: str,
        event_type: EventType = EventType.USER_CREATED,
        correlation_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Emit USER event for user lifecycle operations."""
        payload = {
            "username": username,
            "roles": roles,
            "created_at": created_at,
            "event_type": event_type.value,
        }
        if additional_data:
            payload.update(additional_data)

        event = self.create_event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
        )
        await self.publish_event(event)
        return event

    def get_published_events(self) -> list[Event]:
        """Get list of published events (for testing)."""
        return self._published_events.copy()
    
    def clear_published_events(self) -> None:
        """Clear published events (for testing)."""
        self._published_events.clear()
