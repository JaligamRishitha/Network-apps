"""
Plant Maintenance (PM) module models.
Requirements: 2.1, 2.2, 2.3 - Asset management, maintenance orders, and incidents
"""
import enum
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Date, Enum, ForeignKey, Text, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.db.database import Base


class AssetType(str, enum.Enum):
    """Asset types - Requirement 2.1"""
    SUBSTATION = "substation"
    TRANSFORMER = "transformer"
    FEEDER = "feeder"


class AssetStatus(str, enum.Enum):
    """Asset operational status"""
    OPERATIONAL = "operational"
    UNDER_MAINTENANCE = "under_maintenance"
    OUT_OF_SERVICE = "out_of_service"
    DECOMMISSIONED = "decommissioned"


class OrderType(str, enum.Enum):
    """Maintenance order types - Requirement 2.2"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"


class OrderStatus(str, enum.Enum):
    """Maintenance order status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FaultType(str, enum.Enum):
    """Incident fault types - Requirement 2.3"""
    FAULT = "fault"
    OUTAGE = "outage"
    DEGRADATION = "degradation"


class Asset(Base):
    """
    Asset master data model.
    Requirement 2.1 - Store asset_id, asset_type, location, installation_date, status
    """
    __tablename__ = "assets"
    __table_args__ = {"schema": "pm"}

    asset_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type_enum", schema="pm", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    installation_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status_enum", schema="pm", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AssetStatus.OPERATIONAL
    )
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
    maintenance_orders: Mapped[List["MaintenanceOrder"]] = relationship(
        "MaintenanceOrder",
        back_populates="asset",
        cascade="all, delete-orphan"
    )
    incidents: Mapped[List["PMIncident"]] = relationship(
        "PMIncident",
        back_populates="asset",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Asset(asset_id={self.asset_id}, type={self.asset_type}, status={self.status})>"

    def to_dict(self) -> dict:
        """Convert asset to dictionary for serialization."""
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type.value,
            "name": self.name,
            "location": self.location,
            "installation_date": self.installation_date.isoformat() if self.installation_date else None,
            "status": self.status.value,
            "description": self.description,
        }


class MaintenanceOrder(Base):
    """
    Maintenance order model.
    Requirement 2.2 - Link to asset, set order type (preventive, corrective, emergency)
    """
    __tablename__ = "maintenance_orders"
    __table_args__ = {"schema": "pm"}

    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    asset_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm.assets.asset_id", ondelete="CASCADE"),
        nullable=False
    )
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(30),
        ForeignKey("core.tickets.ticket_id", ondelete="SET NULL"),
        nullable=True
    )
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="order_type_enum", schema="pm", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum", schema="pm", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OrderStatus.PLANNED
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
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
    asset: Mapped["Asset"] = relationship("Asset", back_populates="maintenance_orders")

    def __repr__(self) -> str:
        return f"<MaintenanceOrder(order_id={self.order_id}, type={self.order_type}, status={self.status})>"


class PMIncident(Base):
    """
    PM Incident model.
    Requirement 2.3 - Create incident with fault_type, affected_asset, severity
    """
    __tablename__ = "incidents"
    __table_args__ = {"schema": "pm"}

    incident_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    asset_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("pm.assets.asset_id", ondelete="CASCADE"),
        nullable=False
    )
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(30),
        ForeignKey("core.tickets.ticket_id", ondelete="SET NULL"),
        nullable=True
    )
    fault_type: Mapped[FaultType] = mapped_column(
        Enum(FaultType, name="fault_type_enum", schema="pm", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reported_by: Mapped[str] = mapped_column(String(100), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="incidents")

    def __repr__(self) -> str:
        return f"<PMIncident(incident_id={self.incident_id}, fault_type={self.fault_type})>"
