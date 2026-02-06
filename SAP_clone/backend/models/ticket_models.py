"""
Ticket models and enums for the unified ticketing system.
Requirements: 1.1, 1.2, 1.4 - Unified ticketing with ID format, types, and audit trail
"""
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey, Text, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.db.database import Base


class TicketType(str, enum.Enum):
    """Ticket types across all modules - Requirement 1.2"""
    INCIDENT = "Incident"
    MAINTENANCE = "Maintenance"
    PROCUREMENT = "Procurement"
    FINANCE_APPROVAL = "Finance_Approval"


class TicketStatus(str, enum.Enum):
    """Valid ticket statuses - Requirement 1.5"""
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In_Progress"
    CLOSED = "Closed"


class Priority(str, enum.Enum):
    """Priority levels with SLA timers - Requirement 1.3"""
    P1 = "P1"  # 4 hours
    P2 = "P2"  # 8 hours
    P3 = "P3"  # 24 hours
    P4 = "P4"  # 72 hours


class Module(str, enum.Enum):
    """Module identifiers for ticket ID generation"""
    PM = "PM"
    MM = "MM"
    FI = "FI"


class Ticket(Base):
    """
    Unified ticket model for all modules.
    Requirements: 1.1, 1.2, 1.3, 1.4
    
    Ticket ID format: TKT-{MODULE}-{YYYYMMDD}-{SEQUENCE}
    """
    __tablename__ = "tickets"
    __table_args__ = {"schema": "core"}

    ticket_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    ticket_type: Mapped[TicketType] = mapped_column(
        Enum(TicketType, name="ticket_type_enum", schema="core", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    module: Mapped[Module] = mapped_column(
        Enum(Module, name="module_enum", schema="core", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum", schema="core", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status_enum", schema="core", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TicketStatus.OPEN
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    audit_entries: Mapped[List["AuditEntry"]] = relationship(
        "AuditEntry",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="AuditEntry.changed_at"
    )

    def __repr__(self) -> str:
        return f"<Ticket(ticket_id={self.ticket_id}, status={self.status})>"


class AuditEntry(Base):
    """
    Audit trail for ticket status changes.
    Requirement 1.4 - Record audit trail with timestamp, user, previous/new status
    """
    __tablename__ = "audit_entries"
    __table_args__ = {"schema": "core"}

    entry_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("core.tickets.ticket_id", ondelete="CASCADE"),
        nullable=False
    )
    previous_status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status_enum", schema="core", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    new_status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status_enum", schema="core", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="audit_entries")

    def __repr__(self) -> str:
        return f"<AuditEntry(ticket_id={self.ticket_id}, {self.previous_status} -> {self.new_status})>"
