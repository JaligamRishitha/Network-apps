"""
Seed Data Script
Requirement 9.4 - Load predefined demo data
"""
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.config import get_settings
from backend.models.pm_models import Asset, AssetType, AssetStatus
from backend.models.mm_models import Material
from backend.models.fi_models import CostCenter
from backend.models.ticket_models import Ticket, TicketType, TicketStatus, Priority, Module
from backend.db.database import Base


async def seed_database():
    """Seed the database with demo data."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Seed Assets
        assets = [
            Asset(
                asset_id="AST-SUB-001",
                asset_type=AssetType.SUBSTATION,
                name="Main Substation Alpha",
                location="Building A, Floor 1",
                installation_date=date(2020, 1, 15),
                status=AssetStatus.OPERATIONAL,
                description="Primary power distribution substation"
            ),
            Asset(
                asset_id="AST-TRF-001",
                asset_type=AssetType.TRANSFORMER,
                name="Transformer T1-500kVA",
                location="Building A, Basement",
                installation_date=date(2019, 6, 20),
                status=AssetStatus.OPERATIONAL,
                description="500kVA step-down transformer"
            ),
            Asset(
                asset_id="AST-TRF-002",
                asset_type=AssetType.TRANSFORMER,
                name="Transformer T2-250kVA",
                location="Building B, Basement",
                installation_date=date(2021, 3, 10),
                status=AssetStatus.UNDER_MAINTENANCE,
                description="250kVA distribution transformer"
            ),
            Asset(
                asset_id="AST-FDR-001",
                asset_type=AssetType.FEEDER,
                name="Feeder Line F1",
                location="North Campus",
                installation_date=date(2018, 9, 5),
                status=AssetStatus.OPERATIONAL,
                description="11kV overhead feeder line"
            ),
            Asset(
                asset_id="AST-FDR-002",
                asset_type=AssetType.FEEDER,
                name="Feeder Line F2",
                location="South Campus",
                installation_date=date(2022, 1, 20),
                status=AssetStatus.OPERATIONAL,
                description="Underground cable feeder"
            ),
        ]
        
        # Seed Materials
        materials = [
            Material(
                material_id="MAT-CBL-001",
                description="11kV XLPE Cable (per meter)",
                quantity=500,
                unit_of_measure="M",
                reorder_level=100,
                storage_location="WH-01"
            ),
            Material(
                material_id="MAT-TRF-OIL",
                description="Transformer Oil (per liter)",
                quantity=200,
                unit_of_measure="L",
                reorder_level=50,
                storage_location="WH-02"
            ),
            Material(
                material_id="MAT-FSE-001",
                description="HRC Fuse 100A",
                quantity=25,
                unit_of_measure="EA",
                reorder_level=10,
                storage_location="WH-01"
            ),
            Material(
                material_id="MAT-INS-001",
                description="Porcelain Insulator",
                quantity=8,
                unit_of_measure="EA",
                reorder_level=15,
                storage_location="WH-01"
            ),
            Material(
                material_id="MAT-CON-001",
                description="Cable Connector Kit",
                quantity=30,
                unit_of_measure="SET",
                reorder_level=10,
                storage_location="WH-01"
            ),
        ]
        
        # Seed Cost Centers
        cost_centers = [
            CostCenter(
                cost_center_id="CC-PM-001",
                name="Plant Maintenance Operations",
                budget_amount=Decimal("500000.00"),
                fiscal_year=2024,
                responsible_manager="John Smith",
                description="Budget for PM operations"
            ),
            CostCenter(
                cost_center_id="CC-MM-001",
                name="Materials Procurement",
                budget_amount=Decimal("300000.00"),
                fiscal_year=2024,
                responsible_manager="Jane Doe",
                description="Budget for material purchases"
            ),
            CostCenter(
                cost_center_id="CC-EM-001",
                name="Emergency Repairs",
                budget_amount=Decimal("100000.00"),
                fiscal_year=2024,
                responsible_manager="Bob Wilson",
                description="Emergency repair fund"
            ),
        ]
        
        # Seed Tickets
        now = datetime.utcnow()
        tickets = [
            Ticket(
                ticket_id="TKT-PM-20240115-0001",
                ticket_type=TicketType.INCIDENT,
                module=Module.PM,
                priority=Priority.P2,
                status=TicketStatus.OPEN,
                title="Transformer T2 overheating alarm",
                description="Temperature sensor triggered high temp alarm",
                sla_deadline=now + timedelta(hours=8),
                created_at=now - timedelta(hours=2),
                created_by="engineer"
            ),
            Ticket(
                ticket_id="TKT-PM-20240115-0002",
                ticket_type=TicketType.MAINTENANCE,
                module=Module.PM,
                priority=Priority.P3,
                status=TicketStatus.ASSIGNED,
                title="Scheduled maintenance for Substation Alpha",
                description="Annual preventive maintenance",
                sla_deadline=now + timedelta(hours=24),
                created_at=now - timedelta(days=1),
                created_by="engineer",
                assigned_to="tech_team"
            ),
            Ticket(
                ticket_id="TKT-MM-20240115-0001",
                ticket_type=TicketType.PROCUREMENT,
                module=Module.MM,
                priority=Priority.P3,
                status=TicketStatus.OPEN,
                title="Auto-Reorder: Porcelain Insulator",
                description="Stock below reorder level",
                sla_deadline=now + timedelta(hours=24),
                created_at=now - timedelta(hours=4),
                created_by="SYSTEM"
            ),
            Ticket(
                ticket_id="TKT-FI-20240115-0001",
                ticket_type=TicketType.FINANCE_APPROVAL,
                module=Module.FI,
                priority=Priority.P2,
                status=TicketStatus.OPEN,
                title="Approval: Emergency transformer replacement",
                description="Budget approval for T2 replacement",
                sla_deadline=now + timedelta(hours=8),
                created_at=now - timedelta(hours=1),
                created_by="finance"
            ),
        ]
        
        # Add all to session
        for asset in assets:
            session.add(asset)
        for material in materials:
            session.add(material)
        for cc in cost_centers:
            session.add(cc)
        for ticket in tickets:
            session.add(ticket)
        
        await session.commit()
        print("Seed data loaded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
