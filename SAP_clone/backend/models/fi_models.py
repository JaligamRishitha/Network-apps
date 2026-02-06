"""
Finance (FI) module models.
Requirements: 4.1, 4.2, 4.3 - Cost centers, cost tracking, and financial approvals
"""
import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey, Text, Integer, Numeric, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.db.database import Base


class CostType(str, enum.Enum):
    """Cost types - Requirement 4.2"""
    CAPEX = "CAPEX"
    OPEX = "OPEX"


class ApprovalDecision(str, enum.Enum):
    """Approval decision status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CostCenter(Base):
    """
    Cost center model.
    Requirement 4.1 - Store cost_center_id, name, budget_amount, fiscal_year, responsible_manager
    """
    __tablename__ = "cost_centers"
    __table_args__ = {"schema": "fi"}

    cost_center_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    responsible_manager: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow
    )

    # Relationships
    cost_entries: Mapped[List["CostEntry"]] = relationship(
        "CostEntry",
        back_populates="cost_center",
        cascade="all, delete-orphan"
    )
    approvals: Mapped[List["FIApproval"]] = relationship(
        "FIApproval",
        back_populates="cost_center",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CostCenter(id={self.cost_center_id}, name={self.name})>"

    def to_dict(self) -> dict:
        """Convert cost center to dictionary for serialization."""
        return {
            "cost_center_id": self.cost_center_id,
            "name": self.name,
            "budget_amount": float(self.budget_amount) if self.budget_amount else 0.0,
            "fiscal_year": self.fiscal_year,
            "responsible_manager": self.responsible_manager,
            "description": self.description,
        }


class CostEntry(Base):
    """
    Cost entry model for tracking expenses.
    Requirement 4.2 - Track cost amount, cost_type (CAPEX, OPEX), and associated cost_center
    """
    __tablename__ = "cost_entries"
    __table_args__ = {"schema": "fi"}

    entry_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(30),
        ForeignKey("core.tickets.ticket_id", ondelete="SET NULL"),
        nullable=True
    )
    cost_center_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("fi.cost_centers.cost_center_id", ondelete="CASCADE"),
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cost_type: Mapped[CostType] = mapped_column(
        Enum(CostType, name="cost_type_enum", schema="fi", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    cost_center: Mapped["CostCenter"] = relationship("CostCenter", back_populates="cost_entries")

    def __repr__(self) -> str:
        return f"<CostEntry(id={self.entry_id}, amount={self.amount}, type={self.cost_type})>"

    def to_dict(self) -> dict:
        """Convert cost entry to dictionary for serialization."""
        return {
            "entry_id": self.entry_id,
            "ticket_id": self.ticket_id,
            "cost_center_id": self.cost_center_id,
            "amount": float(self.amount) if self.amount else 0.0,
            "cost_type": self.cost_type.value,
            "description": self.description,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "created_by": self.created_by,
        }


class FIApproval(Base):
    """
    Financial approval model.
    Requirement 4.3 - Create Finance_Approval ticket with amount, justification, approval_hierarchy
    """
    __tablename__ = "approvals"
    __table_args__ = {"schema": "fi"}

    approval_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(30),
        ForeignKey("core.tickets.ticket_id", ondelete="SET NULL"),
        nullable=True
    )
    cost_center_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("fi.cost_centers.cost_center_id", ondelete="CASCADE"),
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    approval_hierarchy: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision_enum", schema="fi", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ApprovalDecision.PENDING
    )
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    decided_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    cost_center: Mapped["CostCenter"] = relationship("CostCenter", back_populates="approvals")

    def __repr__(self) -> str:
        return f"<FIApproval(id={self.approval_id}, amount={self.amount}, decision={self.decision})>"
