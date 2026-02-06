"""
Seed Master Data for Appointment Request Validation
Creates realistic SAP master data for agents to validate against:
- Materials (HVAC parts, tools, consumables)
- Plants/Warehouses
- Assets (Buildings, HVAC systems, Equipment)
- Technicians with skills
- Cost Centers
"""
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

import sys
sys.path.append('/home/pradeep1a/Network-apps/SAP_clone')

from backend.config import get_settings
from backend.models.pm_models import Asset, AssetType, AssetStatus
from backend.models.mm_models import Material
from backend.models.fi_models import CostCenter
from backend.db.database import Base


async def seed_master_data():
    """Seed SAP with master data for appointment validation"""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🌱 Seeding SAP Master Data for Appointment Validation...")

        # ========================================
        # HVAC MATERIALS (For appointment parts validation)
        # ========================================
        print("\n📦 Creating HVAC Materials...")
        materials = [
            # Air Filters
            Material(
                material_id="MAT-HVAC-001",
                description="HVAC Air Filter - Standard 20x25x1",
                quantity=150,
                unit_of_measure="EA",
                reorder_level=30,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-002",
                description="HVAC Air Filter - HEPA 20x25x4",
                quantity=75,
                unit_of_measure="EA",
                reorder_level=15,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-003",
                description="HVAC Air Filter - Carbon 16x20x1",
                quantity=100,
                unit_of_measure="EA",
                reorder_level=20,
                storage_location="WH-NORTH"
            ),

            # Coolants & Refrigerants
            Material(
                material_id="MAT-HVAC-004",
                description="R-410A Refrigerant Coolant (25lb cylinder)",
                quantity=40,
                unit_of_measure="CYL",
                reorder_level=10,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-005",
                description="R-134A Refrigerant Coolant (30lb cylinder)",
                quantity=25,
                unit_of_measure="CYL",
                reorder_level=8,
                storage_location="WH-SOUTH"
            ),
            Material(
                material_id="MAT-HVAC-006",
                description="Glycol Coolant Solution (5 gallon)",
                quantity=60,
                unit_of_measure="GAL",
                reorder_level=15,
                storage_location="WH-CENTRAL"
            ),

            # Thermostats & Controls
            Material(
                material_id="MAT-HVAC-007",
                description="Digital Programmable Thermostat",
                quantity=35,
                unit_of_measure="EA",
                reorder_level=10,
                storage_location="WH-NORTH"
            ),
            Material(
                material_id="MAT-HVAC-008",
                description="Smart WiFi Thermostat",
                quantity=20,
                unit_of_measure="EA",
                reorder_level=5,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-009",
                description="HVAC Control Board Module",
                quantity=15,
                unit_of_measure="EA",
                reorder_level=5,
                storage_location="WH-CENTRAL"
            ),

            # Belts & Motors
            Material(
                material_id="MAT-HVAC-010",
                description="HVAC Blower Motor Belt - Standard",
                quantity=80,
                unit_of_measure="EA",
                reorder_level=20,
                storage_location="WH-NORTH"
            ),
            Material(
                material_id="MAT-HVAC-011",
                description="Condenser Fan Motor 1/3 HP",
                quantity=12,
                unit_of_measure="EA",
                reorder_level=3,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-012",
                description="Blower Fan Motor 1/2 HP",
                quantity=10,
                unit_of_measure="EA",
                reorder_level=3,
                storage_location="WH-SOUTH"
            ),

            # Capacitors & Electrical
            Material(
                material_id="MAT-HVAC-013",
                description="Run Capacitor 35/5 MFD",
                quantity=50,
                unit_of_measure="EA",
                reorder_level=15,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-014",
                description="Start Capacitor 88-108 MFD",
                quantity=40,
                unit_of_measure="EA",
                reorder_level=10,
                storage_location="WH-NORTH"
            ),
            Material(
                material_id="MAT-HVAC-015",
                description="Contactor 30 Amp 240V",
                quantity=30,
                unit_of_measure="EA",
                reorder_level=8,
                storage_location="WH-CENTRAL"
            ),

            # Coils & Heat Exchangers
            Material(
                material_id="MAT-HVAC-016",
                description="Evaporator Coil Assembly 3-Ton",
                quantity=8,
                unit_of_measure="EA",
                reorder_level=2,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-017",
                description="Condenser Coil 4-Ton",
                quantity=6,
                unit_of_measure="EA",
                reorder_level=2,
                storage_location="WH-SOUTH"
            ),

            # Ductwork & Vents
            Material(
                material_id="MAT-HVAC-018",
                description="Flexible Duct 6-inch x 25ft",
                quantity=100,
                unit_of_measure="EA",
                reorder_level=25,
                storage_location="WH-NORTH"
            ),
            Material(
                material_id="MAT-HVAC-019",
                description="Supply Air Grille 14x6",
                quantity=75,
                unit_of_measure="EA",
                reorder_level=20,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-020",
                description="Return Air Grille 20x20",
                quantity=50,
                unit_of_measure="EA",
                reorder_level=15,
                storage_location="WH-NORTH"
            ),

            # Tools & Consumables
            Material(
                material_id="MAT-HVAC-021",
                description="HVAC Vacuum Pump Oil (1 quart)",
                quantity=40,
                unit_of_measure="QT",
                reorder_level=10,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-022",
                description="Leak Detection Dye (8 oz)",
                quantity=30,
                unit_of_measure="EA",
                reorder_level=10,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-023",
                description="HVAC Foil Tape 3-inch x 50yd",
                quantity=120,
                unit_of_measure="RL",
                reorder_level=30,
                storage_location="WH-NORTH"
            ),
            Material(
                material_id="MAT-HVAC-024",
                description="HVAC Sealant Mastic (1 gallon)",
                quantity=45,
                unit_of_measure="GAL",
                reorder_level=15,
                storage_location="WH-SOUTH"
            ),

            # Sensors & Safety
            Material(
                material_id="MAT-HVAC-025",
                description="Temperature Sensor Probe",
                quantity=60,
                unit_of_measure="EA",
                reorder_level=15,
                storage_location="WH-CENTRAL"
            ),
            Material(
                material_id="MAT-HVAC-026",
                description="Pressure Switch 50-300 PSI",
                quantity=25,
                unit_of_measure="EA",
                reorder_level=8,
                storage_location="WH-NORTH"
            ),
            Material(
                material_id="MAT-HVAC-027",
                description="CO2 Sensor Module",
                quantity=18,
                unit_of_measure="EA",
                reorder_level=5,
                storage_location="WH-CENTRAL"
            ),
        ]

        for material in materials:
            session.add(material)
            print(f"  ✓ {material.material_id}: {material.description} (Qty: {material.quantity})")

        # ========================================
        # BUILDING ASSETS (For appointment location validation)
        # ========================================
        print("\n🏢 Creating Building & HVAC Assets...")
        assets = [
            # Buildings
            Asset(
                asset_id="BLD-A",
                asset_type=AssetType.SUBSTATION,  # Using existing enum
                name="Building A - Main Office",
                location="1000 Enterprise Blvd, Suite 100",
                installation_date=date(2015, 3, 1),
                status=AssetStatus.OPERATIONAL,
                description="5-story office building with 50,000 sq ft"
            ),
            Asset(
                asset_id="BLD-B",
                asset_type=AssetType.SUBSTATION,
                name="Building B - R&D Center",
                location="1000 Enterprise Blvd, Suite 200",
                installation_date=date(2018, 6, 15),
                status=AssetStatus.OPERATIONAL,
                description="3-story research facility with labs"
            ),
            Asset(
                asset_id="BLD-C",
                asset_type=AssetType.SUBSTATION,
                name="Building C - Warehouse",
                location="1000 Enterprise Blvd, Suite 300",
                installation_date=date(2012, 9, 10),
                status=AssetStatus.OPERATIONAL,
                description="Single-story warehouse and distribution center"
            ),

            # HVAC Systems - Building A
            Asset(
                asset_id="HVAC-A-001",
                asset_type=AssetType.TRANSFORMER,  # Using existing enum
                name="HVAC System - Building A Floor 1-2",
                location="Building A, Rooftop North",
                installation_date=date(2015, 3, 1),
                status=AssetStatus.OPERATIONAL,
                description="50-ton package rooftop unit serving floors 1-2"
            ),
            Asset(
                asset_id="HVAC-A-002",
                asset_type=AssetType.TRANSFORMER,
                name="HVAC System - Building A Floor 3-5",
                location="Building A, Rooftop South",
                installation_date=date(2015, 3, 1),
                status=AssetStatus.OPERATIONAL,
                description="60-ton package rooftop unit serving floors 3-5"
            ),
            Asset(
                asset_id="HVAC-A-003",
                asset_type=AssetType.TRANSFORMER,
                name="HVAC Chiller - Building A",
                location="Building A, Mechanical Room",
                installation_date=date(2015, 3, 1),
                status=AssetStatus.OPERATIONAL,
                description="200-ton water-cooled chiller with cooling tower"
            ),

            # HVAC Systems - Building B
            Asset(
                asset_id="HVAC-B-001",
                asset_type=AssetType.TRANSFORMER,
                name="HVAC System - Building B Floor 1",
                location="Building B, Rooftop East",
                installation_date=date(2018, 6, 15),
                status=AssetStatus.OPERATIONAL,
                description="40-ton VAV system with energy recovery"
            ),
            Asset(
                asset_id="HVAC-B-002",
                asset_type=AssetType.TRANSFORMER,
                name="HVAC System - Building B Floor 2-3",
                location="Building B, Rooftop West",
                installation_date=date(2018, 6, 15),
                status=AssetStatus.UNDER_MAINTENANCE,
                description="45-ton VAV system with lab exhaust"
            ),

            # HVAC Systems - Building C
            Asset(
                asset_id="HVAC-C-001",
                asset_type=AssetType.TRANSFORMER,
                name="HVAC System - Warehouse",
                location="Building C, Rooftop",
                installation_date=date(2012, 9, 10),
                status=AssetStatus.OPERATIONAL,
                description="30-ton warehouse makeup air unit"
            ),

            # Boilers & Heating
            Asset(
                asset_id="BOILER-A-001",
                asset_type=AssetType.FEEDER,
                name="Boiler System - Building A",
                location="Building A, Basement Mechanical Room",
                installation_date=date(2015, 3, 1),
                status=AssetStatus.OPERATIONAL,
                description="Natural gas boiler 2.5 MMBtu/hr"
            ),
            Asset(
                asset_id="BOILER-B-001",
                asset_type=AssetType.FEEDER,
                name="Boiler System - Building B",
                location="Building B, Mechanical Room",
                installation_date=date(2018, 6, 15),
                status=AssetStatus.OPERATIONAL,
                description="High-efficiency condensing boiler 1.8 MMBtu/hr"
            ),
        ]

        for asset in assets:
            session.add(asset)
            print(f"  ✓ {asset.asset_id}: {asset.name}")

        # ========================================
        # COST CENTERS (For budget validation)
        # ========================================
        print("\n💰 Creating Cost Centers...")
        cost_centers = [
            CostCenter(
                cost_center_id="CC-FACILITY-001",
                name="Facilities Maintenance",
                description="Building maintenance and operations",
                fiscal_year=2026,
                budget_allocated=Decimal("500000.00"),
                budget_spent=Decimal("125000.00"),
                responsible_manager="Sarah Johnson"
            ),
            CostCenter(
                cost_center_id="CC-HVAC-001",
                name="HVAC Operations",
                description="HVAC maintenance and repairs",
                fiscal_year=2026,
                budget_allocated=Decimal("350000.00"),
                budget_spent=Decimal("87500.00"),
                responsible_manager="Michael Chen"
            ),
            CostCenter(
                cost_center_id="CC-ENERGY-001",
                name="Energy Management",
                description="Utilities and energy efficiency",
                fiscal_year=2026,
                budget_allocated=Decimal("750000.00"),
                budget_spent=Decimal("180000.00"),
                responsible_manager="Jennifer Martinez"
            ),
            CostCenter(
                cost_center_id="CC-BLDGA-001",
                name="Building A Operations",
                description="Building A specific operations",
                fiscal_year=2026,
                budget_allocated=Decimal("250000.00"),
                budget_spent=Decimal("60000.00"),
                responsible_manager="David Wilson"
            ),
            CostCenter(
                cost_center_id="CC-BLDGB-001",
                name="Building B Operations",
                description="Building B specific operations",
                fiscal_year=2026,
                budget_allocated=Decimal("200000.00"),
                budget_spent=Decimal("45000.00"),
                responsible_manager="Emily Brown"
            ),
        ]

        for cc in cost_centers:
            session.add(cc)
            print(f"  ✓ {cc.cost_center_id}: {cc.name} (Budget: ${cc.budget_allocated})")

        # ========================================
        # TECHNICIANS (Store in a custom table for validation)
        # ========================================
        print("\n👨‍🔧 Creating Technician Skills Data...")

        # Create technicians table if not exists
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS core.technicians (
                technician_id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                skills TEXT NOT NULL,
                certification_level VARCHAR(50) NOT NULL,
                availability_status VARCHAR(50) NOT NULL,
                assigned_territory VARCHAR(100),
                phone VARCHAR(50),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        technicians_data = [
            (101, "John Smith", "HVAC Certified, Electrical Safety, Refrigeration EPA 608", "Senior", "Available", "North Region", "+1-555-0101", "john.smith@company.com"),
            (102, "Maria Garcia", "HVAC Certified, Boiler Operations, Building Automation", "Senior", "Available", "Central Region", "+1-555-0102", "maria.garcia@company.com"),
            (103, "James Wilson", "HVAC Certified, Electrical Safety, Plumbing", "Mid-Level", "Busy", "South Region", "+1-555-0103", "james.wilson@company.com"),
            (104, "Lisa Anderson", "HVAC Certified, Energy Management, LEED AP", "Senior", "Available", "North Region", "+1-555-0104", "lisa.anderson@company.com"),
            (105, "Robert Taylor", "HVAC Certified, Refrigeration EPA 608, Controls Programming", "Mid-Level", "Available", "Central Region", "+1-555-0105", "robert.taylor@company.com"),
            (106, "Jennifer Lee", "HVAC Certified, Electrical Safety, Fire Safety", "Junior", "Available", "South Region", "+1-555-0106", "jennifer.lee@company.com"),
            (107, "Michael Brown", "Boiler Operations, Plumbing, HVAC Basics", "Mid-Level", "On Leave", "Central Region", "+1-555-0107", "michael.brown@company.com"),
            (108, "Sarah Martinez", "HVAC Certified, Building Automation, Energy Auditing", "Senior", "Available", "North Region", "+1-555-0108", "sarah.martinez@company.com"),
        ]

        for tech in technicians_data:
            await session.execute(text("""
                INSERT INTO core.technicians
                (technician_id, name, skills, certification_level, availability_status, assigned_territory, phone, email)
                VALUES (:id, :name, :skills, :cert, :status, :territory, :phone, :email)
                ON CONFLICT (technician_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    skills = EXCLUDED.skills,
                    certification_level = EXCLUDED.certification_level,
                    availability_status = EXCLUDED.availability_status,
                    assigned_territory = EXCLUDED.assigned_territory,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email
            """), {
                "id": tech[0],
                "name": tech[1],
                "skills": tech[2],
                "cert": tech[3],
                "status": tech[4],
                "territory": tech[5],
                "phone": tech[6],
                "email": tech[7]
            })
            print(f"  ✓ {tech[0]}: {tech[1]} - {tech[2]}")

        await session.commit()

        print("\n" + "="*70)
        print("✅ Master Data Seeding Complete!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  • Materials (HVAC Parts): {len(materials)}")
        print(f"  • Assets (Buildings/HVAC): {len(assets)}")
        print(f"  • Cost Centers: {len(cost_centers)}")
        print(f"  • Technicians: {len(technicians_data)}")
        print(f"\n🎯 Agents can now validate:")
        print(f"  ✓ Required parts availability")
        print(f"  ✓ Technician skills & availability")
        print(f"  ✓ Asset location & status")
        print(f"  ✓ Budget allocation")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(seed_master_data())
