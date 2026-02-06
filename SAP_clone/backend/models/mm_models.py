"""
Materials Management (MM) module models.
Requirements: 3.1, 3.5 - Inventory management and transaction history
"""
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey, Text, Integer, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.db.database import Base


class TransactionType(str, enum.Enum):
    """Stock transaction types - Requirement 3.4"""
    RECEIPT = "receipt"
    ISSUE = "issue"
    ADJUSTMENT = "adjustment"


class RequisitionStatus(str, enum.Enum):
    """Purchase requisition status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    RECEIVED = "received"


class Material(Base):
    """
    Material master data model.
    Requirement 3.1 - Store material_id, description, quantity, unit_of_measure,
    reorder_level, storage_location
    """
    __tablename__ = "materials"
    __table_args__ = {"schema": "mm"}

    material_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_location: Mapped[str] = mapped_column(String(100), nullable=False)
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
    transactions: Mapped[List["StockTransaction"]] = relationship(
        "StockTransaction",
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="StockTransaction.transaction_date"
    )
    requisitions: Mapped[List["MMRequisition"]] = relationship(
        "MMRequisition",
        back_populates="material",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Material(material_id={self.material_id}, qty={self.quantity})>"

    def to_dict(self) -> dict:
        """Convert material to dictionary for serialization."""
        return {
            "material_id": self.material_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_of_measure": self.unit_of_measure,
            "reorder_level": self.reorder_level,
            "storage_location": self.storage_location,
        }

    def is_below_reorder_level(self) -> bool:
        """Check if stock is below reorder level - Requirement 3.2"""
        return self.quantity < self.reorder_level


class StockTransaction(Base):
    """
    Stock transaction model for tracking inventory changes.
    Requirement 3.5 - Maintain complete transaction history with timestamps and user attribution
    """
    __tablename__ = "stock_transactions"
    __table_args__ = {"schema": "mm"}

    transaction_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    material_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("mm.materials.material_id", ondelete="CASCADE"),
        nullable=False
    )
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type_enum", schema="mm", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_doc: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<StockTransaction(id={self.transaction_id}, type={self.transaction_type}, qty={self.quantity_change})>"

    def to_dict(self) -> dict:
        """Convert transaction to dictionary for serialization."""
        return {
            "transaction_id": self.transaction_id,
            "material_id": self.material_id,
            "quantity_change": self.quantity_change,
            "transaction_type": self.transaction_type.value,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "performed_by": self.performed_by,
            "reference_doc": self.reference_doc,
            "notes": self.notes,
        }


class MMRequisition(Base):
    """
    Purchase requisition model.
    Requirement 3.3 - Create procurement ticket linked to requesting cost center
    """
    __tablename__ = "requisitions"
    __table_args__ = {"schema": "mm"}

    requisition_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    material_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("mm.materials.material_id", ondelete="CASCADE"),
        nullable=False
    )
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(30),
        ForeignKey("core.tickets.ticket_id", ondelete="SET NULL"),
        nullable=True
    )
    cost_center_id: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequisitionStatus] = mapped_column(
        Enum(RequisitionStatus, name="requisition_status_enum", schema="mm", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RequisitionStatus.PENDING
    )
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="requisitions")

    def __repr__(self) -> str:
        return f"<MMRequisition(id={self.requisition_id}, material={self.material_id}, status={self.status})>"
