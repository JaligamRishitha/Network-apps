"""
Assignment Rules Engine - CMDB-based assignment logic with round-robin agent selection.
"""

from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from models import (
    AssignmentGroup,
    AssignmentGroupMember,
    CategoryAssignmentMapping,
    User,
    Ticket,
)


def get_assignment_group_by_name(db: Session, group_name: str) -> Optional[AssignmentGroup]:
    """Get assignment group by name (case-insensitive)."""
    return db.query(AssignmentGroup).filter(
        func.lower(AssignmentGroup.name) == group_name.lower(),
        AssignmentGroup.is_active == "true"
    ).first()


def get_assignment_group_for_category(
    db: Session,
    category: str,
    subcategory: Optional[str] = None
) -> Optional[AssignmentGroup]:
    """
    Get the assignment group for a ticket category.

    Looks up CategoryAssignmentMapping to find the appropriate group.
    Tries exact match first, then category-only match.
    """
    # Try exact match with subcategory
    if subcategory:
        mapping = db.query(CategoryAssignmentMapping).filter(
            CategoryAssignmentMapping.category == category,
            CategoryAssignmentMapping.subcategory == subcategory
        ).first()

        if mapping:
            return db.query(AssignmentGroup).filter(
                AssignmentGroup.id == mapping.group_id,
                AssignmentGroup.is_active == "true"
            ).first()

    # Try category-only match
    mapping = db.query(CategoryAssignmentMapping).filter(
        CategoryAssignmentMapping.category == category,
        CategoryAssignmentMapping.subcategory.is_(None)
    ).first()

    if mapping:
        return db.query(AssignmentGroup).filter(
            AssignmentGroup.id == mapping.group_id,
            AssignmentGroup.is_active == "true"
        ).first()

    return None


def get_next_agent_round_robin(
    db: Session,
    group_id: int
) -> Optional[Tuple[int, str]]:
    """
    Get the next agent in the group using round-robin assignment.

    Selects the member with the lowest assignment count who hasn't been
    assigned most recently.

    Returns:
        Tuple of (user_id, user_name) or None if no agents available
    """
    # Get all active members of the group, ordered by assignment count and last assigned
    members = db.query(AssignmentGroupMember).filter(
        AssignmentGroupMember.group_id == group_id,
        AssignmentGroupMember.is_active == "true"
    ).order_by(
        AssignmentGroupMember.assignment_count.asc(),
        AssignmentGroupMember.last_assigned_at.asc().nullsfirst()
    ).all()

    if not members:
        return None

    # Get the first member (lowest assignment count, least recently assigned)
    next_member = members[0]

    # Get user details
    user = db.query(User).filter(User.id == next_member.user_id).first()

    if not user:
        return None

    return user.id, user.full_name


def assign_ticket_to_group(
    db: Session,
    ticket_id: int,
    group_name: str,
    auto_assign_agent: bool = True
) -> Dict[str, Any]:
    """
    Assign a ticket to a group and optionally to an agent.

    Args:
        db: Database session
        ticket_id: ID of the ticket to assign
        group_name: Name of the assignment group
        auto_assign_agent: Whether to automatically assign to an agent

    Returns:
        Dict with assignment details
    """
    result = {
        "success": False,
        "group_id": None,
        "group_name": None,
        "assigned_to_id": None,
        "assigned_to_name": None,
        "message": ""
    }

    # Find the ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        result["message"] = f"Ticket {ticket_id} not found"
        return result

    # Find the assignment group
    group = get_assignment_group_by_name(db, group_name)
    if not group:
        result["message"] = f"Assignment group '{group_name}' not found"
        return result

    result["group_id"] = group.id
    result["group_name"] = group.name

    # Auto-assign to agent if requested
    if auto_assign_agent:
        agent = get_next_agent_round_robin(db, group.id)
        if agent:
            user_id, user_name = agent
            ticket.assigned_to_id = user_id
            result["assigned_to_id"] = user_id
            result["assigned_to_name"] = user_name

            # Update the member's assignment count
            member = db.query(AssignmentGroupMember).filter(
                AssignmentGroupMember.group_id == group.id,
                AssignmentGroupMember.user_id == user_id
            ).first()

            if member:
                member.assignment_count += 1
                member.last_assigned_at = datetime.utcnow()

    db.commit()

    result["success"] = True
    result["message"] = f"Ticket assigned to {result['group_name']}"
    if result["assigned_to_name"]:
        result["message"] += f" / {result['assigned_to_name']}"

    return result


def assign_by_category(
    db: Session,
    ticket_id: int,
    category: str,
    subcategory: Optional[str] = None,
    fallback_group: str = "IT Service Desk",
    auto_assign_agent: bool = True
) -> Dict[str, Any]:
    """
    Assign a ticket based on its category.

    Args:
        db: Database session
        ticket_id: ID of the ticket
        category: Ticket category
        subcategory: Ticket subcategory
        fallback_group: Group to use if no mapping found
        auto_assign_agent: Whether to auto-assign to agent

    Returns:
        Dict with assignment details
    """
    # Find group for category
    group = get_assignment_group_for_category(db, category, subcategory)

    if group:
        return assign_ticket_to_group(
            db=db,
            ticket_id=ticket_id,
            group_name=group.name,
            auto_assign_agent=auto_assign_agent
        )

    # Use fallback group
    return assign_ticket_to_group(
        db=db,
        ticket_id=ticket_id,
        group_name=fallback_group,
        auto_assign_agent=auto_assign_agent
    )


def reassign_ticket(
    db: Session,
    ticket_id: int,
    new_group_name: Optional[str] = None,
    new_agent_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Reassign a ticket to a different group or agent.

    Args:
        db: Database session
        ticket_id: ID of the ticket
        new_group_name: New assignment group (optional)
        new_agent_id: New agent ID (optional)

    Returns:
        Dict with reassignment details
    """
    result = {
        "success": False,
        "previous_group": None,
        "previous_agent": None,
        "new_group": None,
        "new_agent": None,
        "message": ""
    }

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        result["message"] = f"Ticket {ticket_id} not found"
        return result

    # Store previous assignment
    if ticket.assigned_to:
        result["previous_agent"] = ticket.assigned_to.full_name

    # Reassign to new group
    if new_group_name:
        group = get_assignment_group_by_name(db, new_group_name)
        if not group:
            result["message"] = f"Group '{new_group_name}' not found"
            return result

        result["new_group"] = group.name

        # If no specific agent specified, use round-robin
        if not new_agent_id:
            agent = get_next_agent_round_robin(db, group.id)
            if agent:
                new_agent_id = agent[0]
                result["new_agent"] = agent[1]

    # Assign to new agent
    if new_agent_id:
        user = db.query(User).filter(User.id == new_agent_id).first()
        if not user:
            result["message"] = f"User {new_agent_id} not found"
            return result

        ticket.assigned_to_id = new_agent_id
        result["new_agent"] = user.full_name

        # Update assignment count if in a group
        if new_group_name:
            member = db.query(AssignmentGroupMember).filter(
                AssignmentGroupMember.user_id == new_agent_id
            ).first()
            if member:
                member.assignment_count += 1
                member.last_assigned_at = datetime.utcnow()

    db.commit()

    result["success"] = True
    result["message"] = "Ticket reassigned successfully"
    return result


def get_group_workload(db: Session, group_id: int) -> Dict[str, Any]:
    """
    Get workload statistics for an assignment group.

    Returns:
        Dict with workload statistics
    """
    group = db.query(AssignmentGroup).filter(AssignmentGroup.id == group_id).first()
    if not group:
        return {"error": "Group not found"}

    members = db.query(AssignmentGroupMember).filter(
        AssignmentGroupMember.group_id == group_id,
        AssignmentGroupMember.is_active == "true"
    ).all()

    member_stats = []
    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            # Count open tickets for this user
            open_tickets = db.query(Ticket).filter(
                Ticket.assigned_to_id == member.user_id,
                Ticket.status.in_(["submitted", "pending_approval", "approved", "in_progress"])
            ).count()

            member_stats.append({
                "user_id": member.user_id,
                "user_name": user.full_name,
                "total_assignments": member.assignment_count,
                "open_tickets": open_tickets,
                "last_assigned_at": member.last_assigned_at.isoformat() if member.last_assigned_at else None
            })

    return {
        "group_id": group.id,
        "group_name": group.name,
        "total_members": len(members),
        "members": member_stats,
        "total_open_tickets": sum(m["open_tickets"] for m in member_stats)
    }


def list_available_groups(db: Session) -> List[Dict[str, Any]]:
    """List all active assignment groups with member counts."""
    groups = db.query(AssignmentGroup).filter(
        AssignmentGroup.is_active == "true"
    ).all()

    result = []
    for group in groups:
        member_count = db.query(AssignmentGroupMember).filter(
            AssignmentGroupMember.group_id == group.id,
            AssignmentGroupMember.is_active == "true"
        ).count()

        result.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "email": group.email,
            "member_count": member_count
        })

    return result


def create_default_groups(db: Session) -> List[AssignmentGroup]:
    """Create default assignment groups if they don't exist."""
    default_groups = [
        {
            "name": "IT Service Desk",
            "description": "First-line IT support for general issues",
            "email": "servicedesk@company.com"
        },
        {
            "name": "Identity Management",
            "description": "User account and identity services",
            "email": "identity@company.com"
        },
        {
            "name": "Access Management",
            "description": "Access control and permissions",
            "email": "access@company.com"
        },
        {
            "name": "Infrastructure",
            "description": "Server and infrastructure support",
            "email": "infrastructure@company.com"
        },
        {
            "name": "Network Operations",
            "description": "Network and connectivity support",
            "email": "network@company.com"
        },
        {
            "name": "Security Operations",
            "description": "Security incident response",
            "email": "security@company.com"
        },
        {
            "name": "Desktop Support",
            "description": "Desktop and software support",
            "email": "desktop@company.com"
        },
        {
            "name": "IT Assets",
            "description": "Hardware and asset management",
            "email": "assets@company.com"
        },
        {
            "name": "Operations",
            "description": "General operations and work orders",
            "email": "operations@company.com"
        },
        {
            "name": "SAP User Management",
            "description": "SAP system user administration and password resets",
            "email": "sap-admin@company.com"
        },
    ]

    created_groups = []
    for group_data in default_groups:
        existing = db.query(AssignmentGroup).filter(
            AssignmentGroup.name == group_data["name"]
        ).first()

        if not existing:
            group = AssignmentGroup(**group_data)
            db.add(group)
            created_groups.append(group)

    db.commit()
    return created_groups


def create_default_category_mappings(db: Session) -> List[CategoryAssignmentMapping]:
    """Create default category to group mappings."""
    mappings = [
        {"category": "User Account", "subcategory": None, "group_name": "Identity Management"},
        {"category": "User Account", "subcategory": "Account Creation", "group_name": "Identity Management"},
        {"category": "User Account", "subcategory": "Password Reset", "group_name": "SAP User Management"},
        {"category": "Access", "subcategory": None, "group_name": "Access Management"},
        {"category": "Access", "subcategory": "Access Request", "group_name": "Access Management"},
        {"category": "Hardware", "subcategory": None, "group_name": "IT Assets"},
        {"category": "Hardware", "subcategory": "Hardware Request", "group_name": "IT Assets"},
        {"category": "Hardware", "subcategory": "Hardware Repair", "group_name": "Desktop Support"},
        {"category": "Software", "subcategory": None, "group_name": "Desktop Support"},
        {"category": "Software", "subcategory": "Software Installation", "group_name": "Desktop Support"},
        {"category": "Network", "subcategory": None, "group_name": "Network Operations"},
        {"category": "Network", "subcategory": "Connectivity", "group_name": "Network Operations"},
        {"category": "Network", "subcategory": "VPN", "group_name": "Network Operations"},
        {"category": "Security", "subcategory": None, "group_name": "Security Operations"},
        {"category": "Security", "subcategory": "Security Incident", "group_name": "Security Operations"},
        {"category": "System", "subcategory": None, "group_name": "Infrastructure"},
        {"category": "System", "subcategory": "Alert", "group_name": "Infrastructure"},
        {"category": "Work Order", "subcategory": None, "group_name": "Operations"},
        {"category": "General", "subcategory": None, "group_name": "IT Service Desk"},
    ]

    created_mappings = []
    for mapping_data in mappings:
        # Get group ID
        group = db.query(AssignmentGroup).filter(
            AssignmentGroup.name == mapping_data["group_name"]
        ).first()

        if not group:
            continue

        # Check if mapping exists
        existing = db.query(CategoryAssignmentMapping).filter(
            CategoryAssignmentMapping.category == mapping_data["category"],
            CategoryAssignmentMapping.subcategory == mapping_data["subcategory"]
        ).first()

        if not existing:
            mapping = CategoryAssignmentMapping(
                category=mapping_data["category"],
                subcategory=mapping_data["subcategory"],
                group_id=group.id
            )
            db.add(mapping)
            created_mappings.append(mapping)

    db.commit()
    return created_mappings
