"""
System Events Router - Captures system events and triggers automated ticket creation in ServiceNow.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import httpx
import uuid
import os

from app.database import get_db
from app.models import IntegrationLog
from app.config.event_mappings import (
    get_event_mapping,
    get_sla_definition,
    get_source_system_config,
    EventType,
    Priority,
)

router = APIRouter(prefix="/events", tags=["System Events"])

# ServiceNow backend URL - Use Docker container name for internal communication
SERVICENOW_URL = os.getenv("SERVICENOW_URL", "http://servicenow-backend:4780")


class EventStatus(str, Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SystemEventCreate(BaseModel):
    """Schema for incoming system events"""
    event_type: str = Field(..., description="Type of event (e.g., user_creation, password_reset)")
    source_system: str = Field(..., description="Source system (e.g., salesforce, sap)")
    title: str = Field(..., description="Short title/description of the event")
    description: Optional[str] = Field(None, description="Detailed description")
    affected_user: Optional[str] = Field(None, description="Email or ID of affected user")
    affected_ci: Optional[str] = Field(None, description="Affected configuration item")
    priority: Optional[str] = Field(None, description="Override default priority")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    callback_url: Optional[str] = Field(None, description="URL to call when ticket is created")


class SystemEventResponse(BaseModel):
    """Response schema for system events"""
    event_id: str
    status: EventStatus
    message: str
    ticket_number: Optional[str] = None
    created_at: str


class EventStatusResponse(BaseModel):
    """Response schema for event status check"""
    event_id: str
    status: EventStatus
    ticket_number: Optional[str] = None
    ticket_status: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


# In-memory event store (in production, use Redis or database)
event_store: Dict[str, Dict[str, Any]] = {}


async def create_servicenow_ticket(
    event_id: str,
    event_data: Dict[str, Any],
    mapping: Any,
    db: Session
) -> Optional[str]:
    """Create a ticket in ServiceNow with auto-categorization and assignment"""
    try:
        # Prepare ticket payload
        payload = {
            "event_type": event_data["event_type"],
            "source_system": event_data["source_system"],
            "title": event_data["title"],
            "description": event_data.get("description", ""),
            "category": mapping.category,
            "subcategory": mapping.subcategory,
            "priority": event_data.get("priority") or mapping.default_priority.value,
            "assignment_group": mapping.assignment_group,
            "ticket_type": mapping.ticket_type,
            "sla_hours": mapping.sla_hours,
            "affected_user": event_data.get("affected_user"),
            "affected_ci": event_data.get("affected_ci"),
            "metadata": event_data.get("metadata", {}),
            "requires_approval": mapping.requires_approval,
            "auto_assign": mapping.auto_assign,
            "event_id": event_id,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SERVICENOW_URL}/api/tickets/auto-create",
                json=payload
            )

            if response.status_code in [200, 201]:
                result = response.json()
                ticket_number = result.get("ticket_number")

                # Update event store
                event_store[event_id]["status"] = EventStatus.COMPLETED
                event_store[event_id]["ticket_number"] = ticket_number
                event_store[event_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"

                # Log success
                log = IntegrationLog(
                    integration_id=1,
                    level="INFO",
                    message=f"Created ServiceNow ticket {ticket_number} for event {event_id}"
                )
                db.add(log)
                db.commit()

                # Call callback URL if provided
                if event_data.get("callback_url"):
                    try:
                        await client.post(
                            event_data["callback_url"],
                            json={
                                "event_id": event_id,
                                "status": "completed",
                                "ticket_number": ticket_number,
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        )
                    except Exception as e:
                        print(f"Callback failed for event {event_id}: {e}")

                return ticket_number
            else:
                raise Exception(f"ServiceNow returned {response.status_code}: {response.text}")

    except Exception as e:
        event_store[event_id]["status"] = EventStatus.FAILED
        event_store[event_id]["error_message"] = str(e)
        event_store[event_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Log failure
        log = IntegrationLog(
            integration_id=1,
            level="ERROR",
            message=f"Failed to create ticket for event {event_id}: {str(e)}"
        )
        db.add(log)
        db.commit()

        return None


@router.post("/capture", response_model=SystemEventResponse)
async def capture_system_event(
    event: SystemEventCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_source_secret: Optional[str] = Header(None, alias="X-Source-Secret")
):
    """
    Capture a system event and initiate automated ticket creation.

    This endpoint:
    1. Validates the event source
    2. Looks up event-to-category mapping
    3. Creates a ticket in ServiceNow with auto-categorization
    4. Sets up SLA timers
    5. Assigns to appropriate group/agent
    """
    # Generate unique event ID
    event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Validate source system
    source_config = get_source_system_config(event.source_system)

    # Check webhook secret for trusted sources
    if source_config.get("webhook_secret"):
        if x_source_secret != source_config["webhook_secret"]:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid source secret for {event.source_system}"
            )

    # Get event mapping for categorization
    mapping = get_event_mapping(event.event_type)

    # Store event in memory
    event_data = {
        "event_id": event_id,
        "event_type": event.event_type,
        "source_system": event.source_system,
        "title": event.title,
        "description": event.description,
        "affected_user": event.affected_user,
        "affected_ci": event.affected_ci,
        "priority": event.priority,
        "metadata": event.metadata,
        "callback_url": event.callback_url,
        "status": EventStatus.PROCESSING,
        "ticket_number": None,
        "error_message": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "mapping": {
            "category": mapping.category,
            "subcategory": mapping.subcategory,
            "assignment_group": mapping.assignment_group,
            "sla_hours": mapping.sla_hours,
        }
    }
    event_store[event_id] = event_data

    # Log event capture
    log = IntegrationLog(
        integration_id=1,
        level="INFO",
        message=f"Captured event {event_id}: {event.event_type} from {event.source_system}"
    )
    db.add(log)
    db.commit()

    # Create ticket in background
    background_tasks.add_task(
        create_servicenow_ticket,
        event_id,
        event_data,
        mapping,
        db
    )

    return SystemEventResponse(
        event_id=event_id,
        status=EventStatus.PROCESSING,
        message=f"Event captured. Creating ticket with category '{mapping.category}/{mapping.subcategory}'",
        ticket_number=None,
        created_at=timestamp
    )


@router.get("/{event_id}/status", response_model=EventStatusResponse)
async def get_event_status(event_id: str):
    """
    Check the processing status of a captured event.

    Returns the current status and ticket information if available.
    """
    if event_id not in event_store:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    event = event_store[event_id]

    return EventStatusResponse(
        event_id=event_id,
        status=event["status"],
        ticket_number=event.get("ticket_number"),
        ticket_status=None,  # Could fetch from ServiceNow if needed
        error_message=event.get("error_message"),
        created_at=event["created_at"],
        updated_at=event["updated_at"]
    )


@router.get("/", response_model=List[EventStatusResponse])
async def list_recent_events(
    limit: int = 50,
    status: Optional[EventStatus] = None
):
    """
    List recent captured events.

    Optionally filter by status.
    """
    events = list(event_store.values())

    if status:
        events = [e for e in events if e["status"] == status]

    # Sort by created_at descending
    events.sort(key=lambda x: x["created_at"], reverse=True)

    return [
        EventStatusResponse(
            event_id=e["event_id"],
            status=e["status"],
            ticket_number=e.get("ticket_number"),
            ticket_status=None,
            error_message=e.get("error_message"),
            created_at=e["created_at"],
            updated_at=e["updated_at"]
        )
        for e in events[:limit]
    ]


@router.post("/batch", response_model=List[SystemEventResponse])
async def capture_batch_events(
    events: List[SystemEventCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Capture multiple system events in a single request.

    Useful for bulk imports or batch processing.
    """
    if len(events) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 events per batch"
        )

    responses = []
    timestamp = datetime.utcnow().isoformat() + "Z"

    for event in events:
        event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"
        mapping = get_event_mapping(event.event_type)

        event_data = {
            "event_id": event_id,
            "event_type": event.event_type,
            "source_system": event.source_system,
            "title": event.title,
            "description": event.description,
            "affected_user": event.affected_user,
            "affected_ci": event.affected_ci,
            "priority": event.priority,
            "metadata": event.metadata,
            "callback_url": event.callback_url,
            "status": EventStatus.PROCESSING,
            "ticket_number": None,
            "error_message": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        event_store[event_id] = event_data

        # Queue ticket creation
        background_tasks.add_task(
            create_servicenow_ticket,
            event_id,
            event_data,
            mapping,
            db
        )

        responses.append(SystemEventResponse(
            event_id=event_id,
            status=EventStatus.PROCESSING,
            message=f"Event queued for processing",
            ticket_number=None,
            created_at=timestamp
        ))

    return responses


@router.delete("/{event_id}")
async def cancel_event(event_id: str):
    """
    Cancel a pending event before ticket creation.

    Only works for events still in PENDING status.
    """
    if event_id not in event_store:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    event = event_store[event_id]

    if event["status"] != EventStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel event in {event['status']} status"
        )

    del event_store[event_id]

    return {"message": f"Event {event_id} cancelled", "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/mappings")
async def get_event_mappings():
    """
    Get all available event type mappings.

    Useful for understanding how events will be categorized.
    """
    from app.config.event_mappings import EVENT_MAPPINGS

    return {
        "mappings": [
            {
                "event_type": key.value if hasattr(key, 'value') else key,
                "category": mapping.category,
                "subcategory": mapping.subcategory,
                "default_priority": mapping.default_priority.value,
                "sla_hours": mapping.sla_hours,
                "assignment_group": mapping.assignment_group,
                "ticket_type": mapping.ticket_type,
                "requires_approval": mapping.requires_approval,
            }
            for key, mapping in EVENT_MAPPINGS.items()
        ]
    }


@router.get("/health")
async def events_health():
    """Health check for events endpoint"""
    return {
        "status": "healthy",
        "service": "system-events",
        "pending_events": len([e for e in event_store.values() if e["status"] == EventStatus.PENDING]),
        "processing_events": len([e for e in event_store.values() if e["status"] == EventStatus.PROCESSING]),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
