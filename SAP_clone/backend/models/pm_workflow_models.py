"""
6-Screen PM Workflow Models
Requirements: Complete maintenance lifecycle from planning to completion
"""
import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey, Text, Numeric, Boolean, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.db.database import Base


# Enums for the 6-screen workflow

class WorkflowOrderType(str, enum.Enum):
    """Order types for workflow - Requirement 1.1"""
    GENERAL = "general"
    BREAKDOWN = "breakdown"


class WorkflowOrderStatus(str, enum.Enum):
    """Order status states - Requirement 10.1"""
    CREATED = "created"
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    TECO = "teco"


class Priority(str, enum.Enum):
    """Order priority levels - Requirement 1.1"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class OperationStatus(str, enum.Enum):
    """Operation status - Requirement 1.3"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"


class POType(str, enum.Enum):
    """Purchase order types - Requirement 2.1, 2.2, 2.3"""
    MATERIAL = "material"
    SERVICE = "service"
    COMBINED = "combined"


class POStatus(str, enum.Enum):
    """Purchase order status - Requirement 2.4"""
    CREATED = "created"
    ORDERED = "ordered"
    PARTIALLY_DELIVERED = "partially_delivered"
    DELIVERED = "delivered"


class ConfirmationType(str, enum.Enum):
    """Confirmation types - Requirement 5.3, 5.4"""
    INTERNAL = "internal"
    EXTERNAL = "external"


class DocumentType(str, enum.Enum):
    """Document flow types - Requirement 9.1"""
    ORDER = "order"
    PO = "po"
    GR = "gr"
    GI = "gi"
    CONFIRMATION = "confirmation"
    SERVICE_ENTRY = "service_entry"
    TECO = "teco"


# Main Models

class WorkflowMaintenanceOrder(Base):
    """
    Maintenance Order for 6-screen workflow.
    Requirements: 1.1, 1.2, 1.7, 10.1
    """
    __tablename__ = "workflow_maintenance_orders"
    __table_args__ = {"schema": "pm_workflow"}

    order_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_type: Mapped[WorkflowOrderType] = mapped_column(
        Enum(WorkflowOrderType, name="workflow_order_type_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status: Mapped[WorkflowOrderStatus] = mapped_column(
        Enum(WorkflowOrderStatus, name="workflow_order_status_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=WorkflowOrderStatus.CREATED
    )
    equipment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    functional_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Priority.NORMAL
    )
    planned_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    breakdown_notification_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    released_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    operations: Mapped[List["WorkflowOperation"]] = relationship(
        "WorkflowOperation",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    components: Mapped[List["WorkflowComponent"]] = relationship(
        "WorkflowComponent",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    purchase_orders: Mapped[List["WorkflowPurchaseOrder"]] = relationship(
        "WorkflowPurchaseOrder",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    goods_receipts: Mapped[List["WorkflowGoodsReceipt"]] = relationship(
        "WorkflowGoodsReceipt",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    goods_issues: Mapped[List["WorkflowGoodsIssue"]] = relationship(
        "WorkflowGoodsIssue",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    confirmations: Mapped[List["WorkflowConfirmation"]] = relationship(
        "WorkflowConfirmation",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    malfunction_reports: Mapped[List["WorkflowMalfunctionReport"]] = relationship(
        "WorkflowMalfunctionReport",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    document_flow: Mapped[List["WorkflowDocumentFlow"]] = relationship(
        "WorkflowDocumentFlow",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    cost_summary: Mapped[Optional["WorkflowCostSummary"]] = relationship(
        "WorkflowCostSummary",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WorkflowMaintenanceOrder(order_number={self.order_number}, type={self.order_type}, status={self.status})>"


class WorkflowOperation(Base):
    """
    Operation within a maintenance order.
    Requirements: 1.3
    """
    __tablename__ = "workflow_operations"
    __table_args__ = {"schema": "pm_workflow"}

    operation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    operation_number: Mapped[str] = mapped_column(String(10), nullable=False)
    work_center: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    planned_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[OperationStatus] = mapped_column(
        Enum(OperationStatus, name="operation_status_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OperationStatus.PLANNED
    )
    technician_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confirmation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="operations")

    def __repr__(self) -> str:
        return f"<WorkflowOperation(operation_id={self.operation_id}, order={self.order_number}, status={self.status})>"


class WorkflowComponent(Base):
    """
    Component (material) required for maintenance order.
    Requirements: 1.4
    """
    __tablename__ = "workflow_components"
    __table_args__ = {"schema": "pm_workflow"}

    component_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    material_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_required: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    quantity_issued: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    unit_of_measure: Mapped[str] = mapped_column(String(10), nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    actual_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    has_master_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reservation_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="components")

    def __repr__(self) -> str:
        return f"<WorkflowComponent(component_id={self.component_id}, material={self.material_number})>"


class WorkflowPurchaseOrder(Base):
    """
    Purchase Order for materials or services.
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    __tablename__ = "workflow_purchase_orders"
    __table_args__ = {"schema": "pm_workflow"}

    po_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    po_type: Mapped[POType] = mapped_column(
        Enum(POType, name="po_type_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, name="po_status_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=POStatus.CREATED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="purchase_orders")

    def __repr__(self) -> str:
        return f"<WorkflowPurchaseOrder(po_number={self.po_number}, type={self.po_type}, status={self.status})>"


class WorkflowGoodsReceipt(Base):
    """
    Goods Receipt for delivered materials.
    Requirements: 4.1, 4.2
    """
    __tablename__ = "workflow_goods_receipts"
    __table_args__ = {"schema": "pm_workflow"}

    gr_document: Mapped[str] = mapped_column(String(50), primary_key=True)
    po_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_purchase_orders.po_number", ondelete="CASCADE"),
        nullable=False
    )
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    material_number: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    receipt_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    storage_location: Mapped[str] = mapped_column(String(100), nullable=False)
    received_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="goods_receipts")

    def __repr__(self) -> str:
        return f"<WorkflowGoodsReceipt(gr_document={self.gr_document}, material={self.material_number})>"


class WorkflowGoodsIssue(Base):
    """
    Goods Issue for material consumption.
    Requirements: 5.1, 5.2
    """
    __tablename__ = "workflow_goods_issues"
    __table_args__ = {"schema": "pm_workflow"}

    gi_document: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    component_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_components.component_id", ondelete="CASCADE"),
        nullable=False
    )
    material_number: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_issued: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cost_center: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="goods_issues")

    def __repr__(self) -> str:
        return f"<WorkflowGoodsIssue(gi_document={self.gi_document}, material={self.material_number})>"


class WorkflowConfirmation(Base):
    """
    Work confirmation (internal or external).
    Requirements: 5.3, 5.4, 5.6
    """
    __tablename__ = "workflow_confirmations"
    __table_args__ = {"schema": "pm_workflow"}

    confirmation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    operation_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_operations.operation_id", ondelete="CASCADE"),
        nullable=False
    )
    confirmation_type: Mapped[ConfirmationType] = mapped_column(
        Enum(ConfirmationType, name="confirmation_type_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    actual_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    confirmation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    technician_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vendor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="confirmations")

    def __repr__(self) -> str:
        return f"<WorkflowConfirmation(confirmation_id={self.confirmation_id}, type={self.confirmation_type})>"


class WorkflowMalfunctionReport(Base):
    """
    Malfunction report for breakdown maintenance.
    Requirements: 5.5, 7.5
    """
    __tablename__ = "workflow_malfunction_reports"
    __table_args__ = {"schema": "pm_workflow"}

    report_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    cause_code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str] = mapped_column(String(100), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="malfunction_reports")

    def __repr__(self) -> str:
        return f"<WorkflowMalfunctionReport(report_id={self.report_id}, cause={self.cause_code})>"


class WorkflowDocumentFlow(Base):
    """
    Document flow tracking for audit trail.
    Requirements: 9.1, 9.2, 9.3
    """
    __tablename__ = "workflow_document_flow"
    __table_args__ = {"schema": "pm_workflow"}

    flow_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        nullable=False
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type_enum", schema="pm_workflow", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    related_document: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="document_flow")

    def __repr__(self) -> str:
        return f"<WorkflowDocumentFlow(flow_id={self.flow_id}, type={self.document_type})>"


class WorkflowCostSummary(Base):
    """
    Cost summary for maintenance order.
    Requirements: 1.5, 6.4, 6.5, 6.6
    """
    __tablename__ = "workflow_cost_summaries"
    __table_args__ = {"schema": "pm_workflow"}

    order_number: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm_workflow.workflow_maintenance_orders.order_number", ondelete="CASCADE"),
        primary_key=True
    )
    estimated_material_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    estimated_labor_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    estimated_external_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    estimated_total_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    actual_material_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    actual_labor_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    actual_external_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    actual_total_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    material_variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    labor_variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    external_variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_variance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    variance_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    # Relationships
    order: Mapped["WorkflowMaintenanceOrder"] = relationship("WorkflowMaintenanceOrder", back_populates="cost_summary")

    def __repr__(self) -> str:
        return f"<WorkflowCostSummary(order_number={self.order_number}, total_actual={self.actual_total_cost})>"
