"""
Work Order Flow Models - For receiving work orders from external CRM
and managing the PM → MM → FI workflow.
"""
import enum
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, DateTime, Enum, ForeignKey, Text, Integer, Numeric, Boolean, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.db.database import Base


class WorkOrderFlowStatus(str, enum.Enum):
    """Work order flow status through PM → MM → FI"""
    RECEIVED = "received"  # Received from CRM
    PENDING_MATERIAL_CHECK = "pending_material_check"  # Sent to MM for checking
    MATERIALS_AVAILABLE = "materials_available"  # All materials available
    MATERIALS_SHORTAGE = "materials_shortage"  # Some materials not available
    PURCHASE_REQUESTED = "purchase_requested"  # FI ticket raised for purchase
    PURCHASE_APPROVED = "purchase_approved"  # FI approved purchase
    PURCHASE_REJECTED = "purchase_rejected"  # FI rejected purchase
    READY_TO_PROCEED = "ready_to_proceed"  # Work order can proceed
    IN_PROGRESS = "in_progress"  # Work order in progress
    COMPLETED = "completed"  # Work order completed
    CANCELLED = "cancelled"  # Work order cancelled


class CRMWorkOrder(Base):
    """
    Work Order received from external CRM.
    Contains work order details and required materials for PM module.
    """
    __tablename__ = "crm_work_orders"
    __table_args__ = {"schema": "pm"}

    work_order_id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # CRM reference
    crm_reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Work order details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    site_location: Mapped[str] = mapped_column(String(500), nullable=False)

    # Priority
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    # Flow status
    flow_status: Mapped[WorkOrderFlowStatus] = mapped_column(
        Enum(WorkOrderFlowStatus, name="work_order_flow_status_enum", schema="pm",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=WorkOrderFlowStatus.RECEIVED
    )

    # Scheduling
    requested_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # PM module reference
    pm_maintenance_order_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pm_ticket_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # FI module reference for material purchase
    fi_approval_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fi_ticket_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Cost center for material procurement
    cost_center_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Estimated cost
    estimated_material_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # User tracking
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
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

    # Material check summary
    materials_check_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    materials: Mapped[List["WorkOrderMaterial"]] = relationship(
        "WorkOrderMaterial",
        back_populates="work_order",
        cascade="all, delete-orphan"
    )

    flow_history: Mapped[List["WorkOrderFlowHistory"]] = relationship(
        "WorkOrderFlowHistory",
        back_populates="work_order",
        cascade="all, delete-orphan",
        order_by="WorkOrderFlowHistory.created_at"
    )

    def __repr__(self) -> str:
        return f"<CRMWorkOrder(work_order_id={self.work_order_id}, status={self.flow_status})>"

    def to_dict(self) -> dict:
        """Convert work order to dictionary for serialization."""
        return {
            "work_order_id": self.work_order_id,
            "crm_reference_id": self.crm_reference_id,
            "title": self.title,
            "description": self.description,
            "customer_name": self.customer_name,
            "customer_contact": self.customer_contact,
            "site_location": self.site_location,
            "priority": self.priority,
            "flow_status": self.flow_status.value,
            "requested_date": self.requested_date.isoformat() if self.requested_date else None,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "pm_maintenance_order_id": self.pm_maintenance_order_id,
            "pm_ticket_id": self.pm_ticket_id,
            "fi_approval_id": self.fi_approval_id,
            "fi_ticket_id": self.fi_ticket_id,
            "cost_center_id": self.cost_center_id,
            "estimated_material_cost": float(self.estimated_material_cost) if self.estimated_material_cost else None,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "materials_check_summary": self.materials_check_summary,
            "materials": [m.to_dict() for m in self.materials] if self.materials else [],
        }


class WorkOrderMaterial(Base):
    """
    Materials required for a work order.
    Links CRM work order to MM materials.
    """
    __tablename__ = "work_order_materials"
    __table_args__ = {"schema": "pm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm.crm_work_orders.work_order_id", ondelete="CASCADE"),
        nullable=False
    )

    # Material reference (links to MM materials)
    material_id: Mapped[str] = mapped_column(String(50), nullable=False)
    material_description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Quantity
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)

    # Availability check results (set by MM)
    quantity_available: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    shortage_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # If material was ordered (links to MM requisition)
    requisition_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Unit price for cost estimation
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Timestamps
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    work_order: Mapped["CRMWorkOrder"] = relationship("CRMWorkOrder", back_populates="materials")

    def __repr__(self) -> str:
        return f"<WorkOrderMaterial(work_order_id={self.work_order_id}, material_id={self.material_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "work_order_id": self.work_order_id,
            "material_id": self.material_id,
            "material_description": self.material_description,
            "quantity_required": self.quantity_required,
            "unit_of_measure": self.unit_of_measure,
            "quantity_available": self.quantity_available,
            "is_available": self.is_available,
            "shortage_quantity": self.shortage_quantity,
            "requisition_id": self.requisition_id,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }


class WorkOrderFlowHistory(Base):
    """
    Tracks the flow history of a work order through PM → MM → FI.
    """
    __tablename__ = "work_order_flow_history"
    __table_args__ = {"schema": "pm"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm.crm_work_orders.work_order_id", ondelete="CASCADE"),
        nullable=False
    )

    # Status transition
    from_status: Mapped[WorkOrderFlowStatus] = mapped_column(
        Enum(WorkOrderFlowStatus, name="work_order_flow_status_enum", schema="pm",
             create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    to_status: Mapped[WorkOrderFlowStatus] = mapped_column(
        Enum(WorkOrderFlowStatus, name="work_order_flow_status_enum", schema="pm",
             create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Module that triggered the transition
    triggered_by_module: Mapped[str] = mapped_column(String(20), nullable=False)  # PM, MM, FI

    # User and notes
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    work_order: Mapped["CRMWorkOrder"] = relationship("CRMWorkOrder", back_populates="flow_history")

    def __repr__(self) -> str:
        return f"<WorkOrderFlowHistory(work_order_id={self.work_order_id}, {self.from_status} -> {self.to_status})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "work_order_id": self.work_order_id,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "triggered_by_module": self.triggered_by_module,
            "performed_by": self.performed_by,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
