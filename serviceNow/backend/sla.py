"""
SLA Service - Timer creation, breach detection, and business hours calculation.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from enum import Enum

from models import (
    SLADefinition,
    TicketSLA,
    SLAStatus,
    Ticket,
    IncidentPriority,
)


# Business hours configuration
BUSINESS_HOURS = {
    "start_hour": 9,
    "end_hour": 17,
    "working_days": [0, 1, 2, 3, 4],  # Monday to Friday
    "timezone": "UTC",
}

# Default SLA definitions by priority
DEFAULT_SLA_DEFINITIONS = {
    "critical": {
        "name": "Critical SLA",
        "description": "SLA for critical priority tickets",
        "response_time_minutes": 30,
        "resolution_time_hours": 4,
        "business_hours_only": "false",  # 24/7 for critical
        "warning_threshold_percent": 80,
    },
    "high": {
        "name": "High SLA",
        "description": "SLA for high priority tickets",
        "response_time_minutes": 60,
        "resolution_time_hours": 8,
        "business_hours_only": "true",
        "warning_threshold_percent": 80,
    },
    "medium": {
        "name": "Medium SLA",
        "description": "SLA for medium priority tickets",
        "response_time_minutes": 240,
        "resolution_time_hours": 24,
        "business_hours_only": "true",
        "warning_threshold_percent": 80,
    },
    "low": {
        "name": "Low SLA",
        "description": "SLA for low priority tickets",
        "response_time_minutes": 480,
        "resolution_time_hours": 72,
        "business_hours_only": "true",
        "warning_threshold_percent": 80,
    },
}


def is_business_hours(dt: datetime) -> bool:
    """Check if datetime falls within business hours."""
    # Check if it's a working day
    if dt.weekday() not in BUSINESS_HOURS["working_days"]:
        return False

    # Check if it's within working hours
    hour = dt.hour
    return BUSINESS_HOURS["start_hour"] <= hour < BUSINESS_HOURS["end_hour"]


def next_business_hour(dt: datetime) -> datetime:
    """Get the next business hour from given datetime."""
    # If already in business hours, return as-is
    if is_business_hours(dt):
        return dt

    # If after business hours today, move to next business day start
    if dt.hour >= BUSINESS_HOURS["end_hour"]:
        dt = dt.replace(hour=BUSINESS_HOURS["start_hour"], minute=0, second=0, microsecond=0)
        dt += timedelta(days=1)
    elif dt.hour < BUSINESS_HOURS["start_hour"]:
        dt = dt.replace(hour=BUSINESS_HOURS["start_hour"], minute=0, second=0, microsecond=0)

    # Skip to next working day if needed
    while dt.weekday() not in BUSINESS_HOURS["working_days"]:
        dt += timedelta(days=1)

    return dt


def add_business_minutes(start: datetime, minutes: int) -> datetime:
    """Add business minutes to a datetime."""
    current = next_business_hour(start)
    remaining_minutes = minutes

    while remaining_minutes > 0:
        # Calculate minutes until end of current business day
        day_end = current.replace(hour=BUSINESS_HOURS["end_hour"], minute=0, second=0, microsecond=0)
        minutes_until_day_end = int((day_end - current).total_seconds() / 60)

        if minutes_until_day_end >= remaining_minutes:
            # Can complete within current business day
            return current + timedelta(minutes=remaining_minutes)
        else:
            # Move to next business day
            remaining_minutes -= minutes_until_day_end
            current = day_end + timedelta(days=1)
            current = current.replace(hour=BUSINESS_HOURS["start_hour"], minute=0, second=0, microsecond=0)

            # Skip weekends
            while current.weekday() not in BUSINESS_HOURS["working_days"]:
                current += timedelta(days=1)

    return current


def add_business_hours(start: datetime, hours: int) -> datetime:
    """Add business hours to a datetime."""
    return add_business_minutes(start, hours * 60)


def calculate_due_time(
    start_time: datetime,
    minutes: int,
    business_hours_only: bool = True
) -> datetime:
    """Calculate due time based on business hours setting."""
    if business_hours_only:
        return add_business_minutes(start_time, minutes)
    else:
        return start_time + timedelta(minutes=minutes)


def get_sla_definition(
    db: Session,
    priority: str,
    category: Optional[str] = None
) -> Optional[SLADefinition]:
    """
    Get SLA definition for a priority and optional category.

    Tries category-specific SLA first, then priority-only.
    """
    # Try category-specific SLA
    if category:
        sla = db.query(SLADefinition).filter(
            SLADefinition.priority == priority,
            SLADefinition.category == category,
            SLADefinition.is_active == "true"
        ).first()

        if sla:
            return sla

    # Fall back to priority-only SLA
    return db.query(SLADefinition).filter(
        SLADefinition.priority == priority,
        SLADefinition.category.is_(None),
        SLADefinition.is_active == "true"
    ).first()


def create_ticket_sla(
    db: Session,
    ticket_id: int,
    priority: str,
    category: Optional[str] = None,
    created_at: Optional[datetime] = None
) -> Optional[TicketSLA]:
    """
    Create SLA timer for a ticket.

    Args:
        db: Database session
        ticket_id: ID of the ticket
        priority: Ticket priority
        category: Ticket category (for category-specific SLAs)
        created_at: Ticket creation time (defaults to now)

    Returns:
        Created TicketSLA or None if no SLA definition found
    """
    # Get SLA definition
    sla_def = get_sla_definition(db, priority, category)

    if not sla_def:
        # Create default SLA definition if none exists
        sla_def = create_default_sla_definition(db, priority)

    start_time = created_at or datetime.utcnow()
    business_hours = sla_def.business_hours_only == "true"

    # Calculate due times
    response_due = calculate_due_time(
        start_time,
        sla_def.response_time_minutes,
        business_hours
    )

    resolution_due = calculate_due_time(
        start_time,
        sla_def.resolution_time_hours * 60,
        business_hours
    )

    # Create SLA timer
    ticket_sla = TicketSLA(
        ticket_id=ticket_id,
        sla_definition_id=sla_def.id,
        status=SLAStatus.active,
        response_due_at=response_due,
        resolution_due_at=resolution_due,
    )

    db.add(ticket_sla)
    db.commit()
    db.refresh(ticket_sla)

    return ticket_sla


def mark_response_met(db: Session, ticket_id: int) -> Optional[TicketSLA]:
    """Mark the response SLA as met for a ticket."""
    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id,
        TicketSLA.status == SLAStatus.active
    ).first()

    if not sla or sla.response_met_at:
        return sla

    sla.response_met_at = datetime.utcnow()

    # Check if response was within SLA
    if sla.response_met_at > sla.response_due_at:
        sla.response_breached = "true"

    db.commit()
    return sla


def mark_resolution_met(db: Session, ticket_id: int) -> Optional[TicketSLA]:
    """Mark the resolution SLA as met (ticket resolved)."""
    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id,
        TicketSLA.status == SLAStatus.active
    ).first()

    if not sla:
        return None

    sla.resolution_met_at = datetime.utcnow()

    # Check if resolution was within SLA
    if sla.resolution_met_at > sla.resolution_due_at:
        sla.resolution_breached = "true"
        sla.status = SLAStatus.breached
    else:
        sla.status = SLAStatus.achieved

    db.commit()
    return sla


def pause_sla(db: Session, ticket_id: int) -> Optional[TicketSLA]:
    """Pause SLA timer for a ticket (e.g., waiting for customer)."""
    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id,
        TicketSLA.status == SLAStatus.active
    ).first()

    if not sla:
        return None

    sla.status = SLAStatus.paused
    sla.pause_start_at = datetime.utcnow()

    db.commit()
    return sla


def resume_sla(db: Session, ticket_id: int) -> Optional[TicketSLA]:
    """Resume a paused SLA timer."""
    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id,
        TicketSLA.status == SLAStatus.paused
    ).first()

    if not sla or not sla.pause_start_at:
        return sla

    # Calculate pause duration
    pause_duration = datetime.utcnow() - sla.pause_start_at
    pause_minutes = int(pause_duration.total_seconds() / 60)

    # Update total pause time
    sla.total_pause_minutes += pause_minutes

    # Extend due times by pause duration
    sla.response_due_at += pause_duration
    sla.resolution_due_at += pause_duration

    # Resume SLA
    sla.status = SLAStatus.active
    sla.pause_start_at = None

    db.commit()
    return sla


def cancel_sla(db: Session, ticket_id: int) -> Optional[TicketSLA]:
    """Cancel SLA timer for a ticket (e.g., ticket cancelled)."""
    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id,
        TicketSLA.status.in_([SLAStatus.active, SLAStatus.paused])
    ).first()

    if not sla:
        return None

    sla.status = SLAStatus.cancelled
    db.commit()
    return sla


def check_sla_breaches(db: Session) -> List[Dict[str, Any]]:
    """
    Check all active SLAs for breaches.

    Returns list of breached SLAs with ticket details.
    """
    now = datetime.utcnow()
    breaches = []

    # Find active SLAs that are past due
    active_slas = db.query(TicketSLA).filter(
        TicketSLA.status == SLAStatus.active
    ).all()

    for sla in active_slas:
        ticket = db.query(Ticket).filter(Ticket.id == sla.ticket_id).first()
        if not ticket:
            continue

        breach_info = None

        # Check response breach
        if not sla.response_met_at and now > sla.response_due_at:
            minutes_overdue = int((now - sla.response_due_at).total_seconds() / 60)
            sla.response_breached = "true"
            breach_info = {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
                "sla_type": "response",
                "due_at": sla.response_due_at.isoformat(),
                "breached_at": now.isoformat(),
                "minutes_overdue": minutes_overdue,
                "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else None,
                "category": ticket.category,
            }

        # Check resolution breach
        if not sla.resolution_met_at and now > sla.resolution_due_at:
            minutes_overdue = int((now - sla.resolution_due_at).total_seconds() / 60)
            sla.resolution_breached = "true"
            sla.status = SLAStatus.breached
            breach_info = {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
                "sla_type": "resolution",
                "due_at": sla.resolution_due_at.isoformat(),
                "breached_at": now.isoformat(),
                "minutes_overdue": minutes_overdue,
                "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else None,
                "category": ticket.category,
            }

        if breach_info:
            breaches.append(breach_info)

    db.commit()
    return breaches


def get_slas_approaching_breach(
    db: Session,
    threshold_percent: int = 80
) -> List[Dict[str, Any]]:
    """
    Get SLAs that are approaching their breach threshold.

    Args:
        db: Database session
        threshold_percent: Percentage of SLA time elapsed to trigger warning

    Returns:
        List of SLAs approaching breach
    """
    now = datetime.utcnow()
    warnings = []

    active_slas = db.query(TicketSLA).filter(
        TicketSLA.status == SLAStatus.active,
        TicketSLA.warning_sent == "false"
    ).all()

    for sla in active_slas:
        ticket = db.query(Ticket).filter(Ticket.id == sla.ticket_id).first()
        if not ticket:
            continue

        warning_info = None

        # Check response SLA
        if not sla.response_met_at:
            total_time = (sla.response_due_at - sla.created_at).total_seconds()
            elapsed_time = (now - sla.created_at).total_seconds()
            percent_elapsed = (elapsed_time / total_time) * 100 if total_time > 0 else 0

            if percent_elapsed >= threshold_percent:
                warning_info = {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "title": ticket.title,
                    "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
                    "sla_type": "response",
                    "due_at": sla.response_due_at.isoformat(),
                    "percent_elapsed": round(percent_elapsed, 1),
                    "minutes_remaining": int((sla.response_due_at - now).total_seconds() / 60),
                    "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else None,
                }

        # Check resolution SLA
        if not sla.resolution_met_at:
            total_time = (sla.resolution_due_at - sla.created_at).total_seconds()
            elapsed_time = (now - sla.created_at).total_seconds()
            percent_elapsed = (elapsed_time / total_time) * 100 if total_time > 0 else 0

            if percent_elapsed >= threshold_percent:
                warning_info = {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "title": ticket.title,
                    "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
                    "sla_type": "resolution",
                    "due_at": sla.resolution_due_at.isoformat(),
                    "percent_elapsed": round(percent_elapsed, 1),
                    "minutes_remaining": int((sla.resolution_due_at - now).total_seconds() / 60),
                    "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else None,
                }

        if warning_info:
            warnings.append(warning_info)

    return warnings


def get_ticket_sla_status(db: Session, ticket_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed SLA status for a ticket."""
    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id
    ).first()

    if not sla:
        return None

    now = datetime.utcnow()
    sla_def = db.query(SLADefinition).filter(
        SLADefinition.id == sla.sla_definition_id
    ).first()

    return {
        "sla_id": sla.id,
        "status": sla.status.value,
        "sla_name": sla_def.name if sla_def else None,
        "response": {
            "due_at": sla.response_due_at.isoformat(),
            "met_at": sla.response_met_at.isoformat() if sla.response_met_at else None,
            "breached": sla.response_breached == "true",
            "minutes_remaining": max(0, int((sla.response_due_at - now).total_seconds() / 60)) if not sla.response_met_at else None,
        },
        "resolution": {
            "due_at": sla.resolution_due_at.isoformat(),
            "met_at": sla.resolution_met_at.isoformat() if sla.resolution_met_at else None,
            "breached": sla.resolution_breached == "true",
            "minutes_remaining": max(0, int((sla.resolution_due_at - now).total_seconds() / 60)) if not sla.resolution_met_at else None,
        },
        "paused_minutes": sla.total_pause_minutes,
        "warning_sent": sla.warning_sent == "true",
        "breach_notified": sla.breach_notified == "true",
    }


def create_default_sla_definition(db: Session, priority: str) -> SLADefinition:
    """Create a default SLA definition for a priority if none exists."""
    defaults = DEFAULT_SLA_DEFINITIONS.get(priority, DEFAULT_SLA_DEFINITIONS["medium"])

    sla_def = SLADefinition(
        name=defaults["name"],
        description=defaults["description"],
        priority=priority,
        response_time_minutes=defaults["response_time_minutes"],
        resolution_time_hours=defaults["resolution_time_hours"],
        business_hours_only=defaults["business_hours_only"],
        warning_threshold_percent=defaults["warning_threshold_percent"],
    )

    db.add(sla_def)
    db.commit()
    db.refresh(sla_def)

    return sla_def


def create_all_default_sla_definitions(db: Session) -> List[SLADefinition]:
    """Create default SLA definitions for all priority levels."""
    created = []

    for priority, defaults in DEFAULT_SLA_DEFINITIONS.items():
        existing = db.query(SLADefinition).filter(
            SLADefinition.priority == priority,
            SLADefinition.category.is_(None)
        ).first()

        if not existing:
            sla_def = SLADefinition(
                name=defaults["name"],
                description=defaults["description"],
                priority=priority,
                response_time_minutes=defaults["response_time_minutes"],
                resolution_time_hours=defaults["resolution_time_hours"],
                business_hours_only=defaults["business_hours_only"],
                warning_threshold_percent=defaults["warning_threshold_percent"],
            )
            db.add(sla_def)
            created.append(sla_def)

    db.commit()
    return created
