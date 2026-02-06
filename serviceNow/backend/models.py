from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"
    user = "user"

class IncidentPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class TicketType(str, enum.Enum):
    incident = "incident"
    service_request = "service_request"
    change_request = "change_request"
    problem = "problem"

class TicketStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"
    cancelled = "cancelled"

class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.user)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    reported_incidents = relationship("Incident", back_populates="reporter", foreign_keys="Incident.reporter_id")
    assigned_incidents = relationship("Incident", back_populates="assigned_to", foreign_keys="Incident.assigned_to_id")
    submitted_tickets = relationship("Ticket", back_populates="requester", foreign_keys="Ticket.requester_id")
    assigned_tickets = relationship("Ticket", back_populates="assigned_to", foreign_keys="Ticket.assigned_to_id")
    pending_approvals = relationship("Approval", back_populates="approver", foreign_keys="Approval.approver_id")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    priority = Column(Enum(IncidentPriority), default=IncidentPriority.medium)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.new)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reporter = relationship("User", back_populates="reported_incidents", foreign_keys=[reporter_id])
    assigned_to = relationship("User", back_populates="assigned_incidents", foreign_keys=[assigned_to_id])

class ServiceCatalogItem(Base):
    __tablename__ = "service_catalog_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    summary = Column(Text)
    category = Column(String, index=True)
    tags = Column(String)  # Comma-separated tags
    author_id = Column(Integer, ForeignKey("users.id"))
    views = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", foreign_keys=[author_id])

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    ticket_type = Column(Enum(TicketType), default=TicketType.service_request)
    status = Column(Enum(TicketStatus), default=TicketStatus.submitted)
    priority = Column(Enum(IncidentPriority), default=IncidentPriority.medium)
    category = Column(String)
    subcategory = Column(String)
    requester_id = Column(Integer, ForeignKey("users.id"))
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    contact_number = Column(String, nullable=True)
    preferred_contact = Column(String, default="email")
    urgency = Column(String, default="medium")
    business_justification = Column(Text, nullable=True)
    estimated_cost = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    # ServiceNow integration fields
    servicenow_sys_id = Column(String, nullable=True, index=True)
    servicenow_number = Column(String, nullable=True, index=True)
    # Salesforce integration fields
    correlation_id = Column(String, nullable=True, index=True)
    source_system = Column(String, nullable=True)  # e.g., "Salesforce"
    source_request_id = Column(String, nullable=True)  # e.g., "1" from Salesforce
    source_request_type = Column(String, nullable=True)  # e.g., "Service Appointment"

    requester = relationship("User", back_populates="submitted_tickets", foreign_keys=[requester_id])
    assigned_to = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_to_id])
    approvals = relationship("Approval", back_populates="ticket")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.pending)
    comments = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="approvals")
    approver = relationship("User", back_populates="pending_approvals", foreign_keys=[approver_id])


# ============================================================================
# ASSIGNMENT GROUP MODELS
# ============================================================================

class AssignmentGroup(Base):
    """Groups that handle specific ticket categories"""
    __tablename__ = "assignment_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(String, default="true")  # Using String for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    manager = relationship("User", foreign_keys=[manager_id])
    members = relationship("AssignmentGroupMember", back_populates="group")
    category_mappings = relationship("CategoryAssignmentMapping", back_populates="group")


class AssignmentGroupMember(Base):
    """Users belonging to assignment groups"""
    __tablename__ = "assignment_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("assignment_groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(String, default="true")
    assignment_count = Column(Integer, default=0)  # For round-robin tracking
    last_assigned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("AssignmentGroup", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])


class CategoryAssignmentMapping(Base):
    """Maps ticket categories to assignment groups"""
    __tablename__ = "category_assignment_mappings"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    subcategory = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("assignment_groups.id"))
    priority_override = Column(String, nullable=True)  # Override default priority for this category
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("AssignmentGroup", back_populates="category_mappings")


# ============================================================================
# SLA MODELS
# ============================================================================

class SLAStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    breached = "breached"
    achieved = "achieved"
    cancelled = "cancelled"


class SLADefinition(Base):
    """SLA rules per priority and category"""
    __tablename__ = "sla_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    priority = Column(String, index=True)  # critical, high, medium, low
    category = Column(String, nullable=True)  # Optional category-specific SLA
    response_time_minutes = Column(Integer, default=60)
    resolution_time_hours = Column(Integer, default=24)
    business_hours_only = Column(String, default="true")  # String for SQLite compatibility
    warning_threshold_percent = Column(Integer, default=80)  # Send warning at 80% elapsed
    is_active = Column(String, default="true")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TicketSLA(Base):
    """Active SLA timer for each ticket"""
    __tablename__ = "ticket_slas"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), index=True)
    sla_definition_id = Column(Integer, ForeignKey("sla_definitions.id"))
    status = Column(Enum(SLAStatus), default=SLAStatus.active)

    # Response SLA
    response_due_at = Column(DateTime)
    response_met_at = Column(DateTime, nullable=True)
    response_breached = Column(String, default="false")

    # Resolution SLA
    resolution_due_at = Column(DateTime)
    resolution_met_at = Column(DateTime, nullable=True)
    resolution_breached = Column(String, default="false")

    # Tracking
    pause_start_at = Column(DateTime, nullable=True)
    total_pause_minutes = Column(Integer, default=0)
    warning_sent = Column(String, default="false")
    breach_notified = Column(String, default="false")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ticket = relationship("Ticket", foreign_keys=[ticket_id])
    sla_definition = relationship("SLADefinition", foreign_keys=[sla_definition_id])


# ============================================================================
# NOTIFICATION MODELS
# ============================================================================

class NotificationType(str, enum.Enum):
    sla_warning = "sla_warning"
    sla_breach = "sla_breach"
    ticket_assigned = "ticket_assigned"
    ticket_updated = "ticket_updated"
    ticket_resolved = "ticket_resolved"
    approval_required = "approval_required"
    approval_completed = "approval_completed"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class Notification(Base):
    """Notification log and queue"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(Enum(NotificationType))
    status = Column(Enum(NotificationStatus), default=NotificationStatus.pending)

    # Target
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipient_email = Column(String, nullable=True)
    recipient_group_id = Column(Integer, ForeignKey("assignment_groups.id"), nullable=True)

    # Content
    subject = Column(String)
    message = Column(Text)

    # Reference
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    sla_id = Column(Integer, ForeignKey("ticket_slas.id"), nullable=True)

    # Webhook callback (for MuleSoft)
    webhook_url = Column(String, nullable=True)
    webhook_payload = Column(Text, nullable=True)
    webhook_response = Column(Text, nullable=True)

    # Tracking
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recipient = relationship("User", foreign_keys=[recipient_id])
    recipient_group = relationship("AssignmentGroup", foreign_keys=[recipient_group_id])
    ticket = relationship("Ticket", foreign_keys=[ticket_id])
    sla = relationship("TicketSLA", foreign_keys=[sla_id])