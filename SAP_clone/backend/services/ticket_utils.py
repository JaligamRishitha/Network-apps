"""
Ticket utility functions for ID generation and SLA calculation.
Requirements: 1.1, 1.2, 1.3 - Ticket ID format, types, and SLA timers
"""
import re
from datetime import datetime, timedelta
from typing import Tuple
from backend.models.ticket_models import Module, Priority, TicketType, TicketStatus
from backend.config import get_settings


# SLA hours mapping based on priority - Requirement 1.3
SLA_HOURS = {
    Priority.P1: 4,   # P1: 4 hours
    Priority.P2: 8,   # P2: 8 hours
    Priority.P3: 24,  # P3: 24 hours
    Priority.P4: 72,  # P4: 72 hours
}

# Valid ticket types - Requirement 1.2
VALID_TICKET_TYPES = {
    TicketType.INCIDENT,
    TicketType.MAINTENANCE,
    TicketType.PROCUREMENT,
    TicketType.FINANCE_APPROVAL,
}

# Ticket ID pattern - Requirement 1.1
TICKET_ID_PATTERN = re.compile(r'^TKT-(PM|MM|FI)-(\d{8})-(\d{4})$')


def generate_ticket_id(module: Module, date: datetime, sequence: int) -> str:
    """
    Generate a ticket ID following the format TKT-{MODULE}-{YYYYMMDD}-{SEQUENCE}.
    Requirement 1.1
    
    Args:
        module: The module (PM, MM, FI)
        date: The date for the ticket
        sequence: The sequence number (1-9999)
    
    Returns:
        Formatted ticket ID string
    """
    date_str = date.strftime("%Y%m%d")
    sequence_str = f"{sequence:04d}"
    return f"TKT-{module.value}-{date_str}-{sequence_str}"


def validate_ticket_id(ticket_id: str) -> Tuple[bool, str]:
    """
    Validate that a ticket ID matches the expected format.
    Requirement 1.1
    
    Args:
        ticket_id: The ticket ID to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ticket_id:
        return False, "Ticket ID cannot be empty"
    
    match = TICKET_ID_PATTERN.match(ticket_id)
    if not match:
        return False, f"Ticket ID '{ticket_id}' does not match format TKT-{{MODULE}}-{{YYYYMMDD}}-{{SEQUENCE}}"
    
    module_str, date_str, sequence_str = match.groups()
    
    # Validate module
    if module_str not in [m.value for m in Module]:
        return False, f"Invalid module '{module_str}'"
    
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return False, f"Invalid date '{date_str}'"
    
    # Validate sequence
    sequence = int(sequence_str)
    if sequence < 1 or sequence > 9999:
        return False, f"Sequence {sequence} out of range (1-9999)"
    
    return True, ""


def parse_ticket_id(ticket_id: str) -> Tuple[Module, datetime, int]:
    """
    Parse a ticket ID into its components.
    
    Args:
        ticket_id: The ticket ID to parse
    
    Returns:
        Tuple of (module, date, sequence)
    
    Raises:
        ValueError: If the ticket ID is invalid
    """
    is_valid, error = validate_ticket_id(ticket_id)
    if not is_valid:
        raise ValueError(error)
    
    match = TICKET_ID_PATTERN.match(ticket_id)
    module_str, date_str, sequence_str = match.groups()
    
    module = Module(module_str)
    date = datetime.strptime(date_str, "%Y%m%d")
    sequence = int(sequence_str)
    
    return module, date, sequence


def calculate_sla_deadline(priority: Priority, created_at: datetime) -> datetime:
    """
    Calculate SLA deadline based on priority level.
    Requirement 1.3 - P1: 4h, P2: 8h, P3: 24h, P4: 72h
    
    Args:
        priority: The ticket priority
        created_at: The ticket creation timestamp
    
    Returns:
        The SLA deadline datetime
    """
    hours = SLA_HOURS.get(priority, 72)  # Default to P4 if unknown
    return created_at + timedelta(hours=hours)


def is_valid_ticket_type(ticket_type: TicketType) -> bool:
    """
    Check if a ticket type is valid.
    Requirement 1.2
    
    Args:
        ticket_type: The ticket type to validate
    
    Returns:
        True if valid, False otherwise
    """
    return ticket_type in VALID_TICKET_TYPES


def create_ticket_data(
    module: Module,
    ticket_type: TicketType,
    priority: Priority,
    title: str,
    created_by: str,
    sequence: int,
    created_at: datetime = None,
    description: str = None,
) -> dict:
    """
    Create a complete ticket data dictionary with generated ID and SLA.
    Requirements: 1.1, 1.2, 1.3
    
    Args:
        module: The module (PM, MM, FI)
        ticket_type: The type of ticket
        priority: The priority level
        title: Ticket title
        created_by: User who created the ticket
        sequence: Sequence number for ID generation
        created_at: Creation timestamp (defaults to now)
        description: Optional description
    
    Returns:
        Dictionary with all ticket fields
    """
    if created_at is None:
        created_at = datetime.utcnow()
    
    ticket_id = generate_ticket_id(module, created_at, sequence)
    sla_deadline = calculate_sla_deadline(priority, created_at)
    
    return {
        "ticket_id": ticket_id,
        "ticket_type": ticket_type,
        "module": module,
        "priority": priority,
        "status": TicketStatus.OPEN,
        "title": title,
        "description": description,
        "sla_deadline": sla_deadline,
        "created_at": created_at,
        "created_by": created_by,
    }
