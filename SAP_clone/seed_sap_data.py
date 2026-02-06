"""
Simple Seed Script for SAP Master Data
Uses direct PostgreSQL connection
"""
import psycopg2
from datetime import date, datetime

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 4794,
    "database": "sap_erp",
    "user": "sap",
    "password": "sap_secret"
}

def seed_data():
    """Seed SAP database with master data"""
    print("🌱 Connecting to SAP database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("✅ Connected!")

    try:
        # ========================================
        # HVAC MATERIALS
        # ========================================
        print("\n📦 Creating HVAC Materials...")

        materials = [
            ("MAT-HVAC-001", "HVAC Air Filter - Standard 20x25x1", 150, "EA", 30, "WH-CENTRAL"),
            ("MAT-HVAC-002", "HVAC Air Filter - HEPA 20x25x4", 75, "EA", 15, "WH-CENTRAL"),
            ("MAT-HVAC-003", "HVAC Air Filter - Carbon 16x20x1", 100, "EA", 20, "WH-NORTH"),
            ("MAT-HVAC-004", "R-410A Refrigerant Coolant (25lb cylinder)", 40, "CYL", 10, "WH-CENTRAL"),
            ("MAT-HVAC-005", "R-134A Refrigerant Coolant (30lb cylinder)", 25, "CYL", 8, "WH-SOUTH"),
            ("MAT-HVAC-006", "Glycol Coolant Solution (5 gallon)", 60, "GAL", 15, "WH-CENTRAL"),
            ("MAT-HVAC-007", "Digital Programmable Thermostat", 35, "EA", 10, "WH-NORTH"),
            ("MAT-HVAC-008", "Smart WiFi Thermostat", 20, "EA", 5, "WH-CENTRAL"),
            ("MAT-HVAC-009", "HVAC Control Board Module", 15, "EA", 5, "WH-CENTRAL"),
            ("MAT-HVAC-010", "HVAC Blower Motor Belt - Standard", 80, "EA", 20, "WH-NORTH"),
            ("MAT-HVAC-011", "Condenser Fan Motor 1/3 HP", 12, "EA", 3, "WH-CENTRAL"),
            ("MAT-HVAC-012", "Blower Fan Motor 1/2 HP", 10, "EA", 3, "WH-SOUTH"),
            ("MAT-HVAC-013", "Run Capacitor 35/5 MFD", 50, "EA", 15, "WH-CENTRAL"),
            ("MAT-HVAC-014", "Start Capacitor 88-108 MFD", 40, "EA", 10, "WH-NORTH"),
            ("MAT-HVAC-015", "Contactor 30 Amp 240V", 30, "EA", 8, "WH-CENTRAL"),
            ("MAT-HVAC-016", "Evaporator Coil Assembly 3-Ton", 8, "EA", 2, "WH-CENTRAL"),
            ("MAT-HVAC-017", "Condenser Coil 4-Ton", 6, "EA", 2, "WH-SOUTH"),
            ("MAT-HVAC-018", "Flexible Duct 6-inch x 25ft", 100, "EA", 25, "WH-NORTH"),
            ("MAT-HVAC-019", "Supply Air Grille 14x6", 75, "EA", 20, "WH-CENTRAL"),
            ("MAT-HVAC-020", "Return Air Grille 20x20", 50, "EA", 15, "WH-NORTH"),
            ("MAT-HVAC-021", "HVAC Vacuum Pump Oil (1 quart)", 40, "QT", 10, "WH-CENTRAL"),
            ("MAT-HVAC-022", "Leak Detection Dye (8 oz)", 30, "EA", 10, "WH-CENTRAL"),
            ("MAT-HVAC-023", "HVAC Foil Tape 3-inch x 50yd", 120, "RL", 30, "WH-NORTH"),
            ("MAT-HVAC-024", "HVAC Sealant Mastic (1 gallon)", 45, "GAL", 15, "WH-SOUTH"),
            ("MAT-HVAC-025", "Temperature Sensor Probe", 60, "EA", 15, "WH-CENTRAL"),
            ("MAT-HVAC-026", "Pressure Switch 50-300 PSI", 25, "EA", 8, "WH-NORTH"),
            ("MAT-HVAC-027", "CO2 Sensor Module", 18, "EA", 5, "WH-CENTRAL"),
        ]

        for mat in materials:
            cur.execute("""
                INSERT INTO mm.materials
                (material_id, description, quantity, unit_of_measure, reorder_level, storage_location, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (material_id) DO UPDATE SET
                    description = EXCLUDED.description,
                    quantity = EXCLUDED.quantity,
                    unit_of_measure = EXCLUDED.unit_of_measure,
                    reorder_level = EXCLUDED.reorder_level,
                    storage_location = EXCLUDED.storage_location,
                    updated_at = NOW()
            """, mat)
            print(f"  ✓ {mat[0]}: {mat[1]} (Qty: {mat[2]})")

        # ========================================
        # BUILDING ASSETS
        # ========================================
        print("\n🏢 Creating Building & HVAC Assets...")

        assets = [
            ("BLD-A", "substation", "Building A - Main Office", "1000 Enterprise Blvd, Suite 100", date(2015, 3, 1), "operational", "5-story office building with 50,000 sq ft"),
            ("BLD-B", "substation", "Building B - R&D Center", "1000 Enterprise Blvd, Suite 200", date(2018, 6, 15), "operational", "3-story research facility with labs"),
            ("BLD-C", "substation", "Building C - Warehouse", "1000 Enterprise Blvd, Suite 300", date(2012, 9, 10), "operational", "Single-story warehouse and distribution center"),
            ("HVAC-A-001", "transformer", "HVAC System - Building A Floor 1-2", "Building A, Rooftop North", date(2015, 3, 1), "operational", "50-ton package rooftop unit serving floors 1-2"),
            ("HVAC-A-002", "transformer", "HVAC System - Building A Floor 3-5", "Building A, Rooftop South", date(2015, 3, 1), "operational", "60-ton package rooftop unit serving floors 3-5"),
            ("HVAC-A-003", "transformer", "HVAC Chiller - Building A", "Building A, Mechanical Room", date(2015, 3, 1), "operational", "200-ton water-cooled chiller with cooling tower"),
            ("HVAC-B-001", "transformer", "HVAC System - Building B Floor 1", "Building B, Rooftop East", date(2018, 6, 15), "operational", "40-ton VAV system with energy recovery"),
            ("HVAC-B-002", "transformer", "HVAC System - Building B Floor 2-3", "Building B, Rooftop West", date(2018, 6, 15), "under_maintenance", "45-ton VAV system with lab exhaust"),
            ("HVAC-C-001", "transformer", "HVAC System - Warehouse", "Building C, Rooftop", date(2012, 9, 10), "operational", "30-ton warehouse makeup air unit"),
            ("BOILER-A-001", "feeder", "Boiler System - Building A", "Building A, Basement Mechanical Room", date(2015, 3, 1), "operational", "Natural gas boiler 2.5 MMBtu/hr"),
            ("BOILER-B-001", "feeder", "Boiler System - Building B", "Building B, Mechanical Room", date(2018, 6, 15), "operational", "High-efficiency condensing boiler 1.8 MMBtu/hr"),
        ]

        for asset in assets:
            cur.execute("""
                INSERT INTO pm.assets
                (asset_id, asset_type, name, location, installation_date, status, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (asset_id) DO UPDATE SET
                    asset_type = EXCLUDED.asset_type,
                    name = EXCLUDED.name,
                    location = EXCLUDED.location,
                    installation_date = EXCLUDED.installation_date,
                    status = EXCLUDED.status,
                    description = EXCLUDED.description,
                    updated_at = NOW()
            """, asset)
            print(f"  ✓ {asset[0]}: {asset[2]}")

        # ========================================
        # COST CENTERS
        # ========================================
        print("\n💰 Creating Cost Centers...")

        cost_centers = [
            ("CC-FACILITY-001", "Facilities Maintenance", "Building maintenance and operations", 2026, 500000.00, 125000.00, "Sarah Johnson"),
            ("CC-HVAC-001", "HVAC Operations", "HVAC maintenance and repairs", 2026, 350000.00, 87500.00, "Michael Chen"),
            ("CC-ENERGY-001", "Energy Management", "Utilities and energy efficiency", 2026, 750000.00, 180000.00, "Jennifer Martinez"),
            ("CC-BLDGA-001", "Building A Operations", "Building A specific operations", 2026, 250000.00, 60000.00, "David Wilson"),
            ("CC-BLDGB-001", "Building B Operations", "Building B specific operations", 2026, 200000.00, 45000.00, "Emily Brown"),
        ]

        for cc in cost_centers:
            cur.execute("""
                INSERT INTO fi.cost_centers
                (cost_center_id, name, description, fiscal_year, budget_allocated, budget_spent, responsible_manager, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (cost_center_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    fiscal_year = EXCLUDED.fiscal_year,
                    budget_allocated = EXCLUDED.budget_allocated,
                    budget_spent = EXCLUDED.budget_spent,
                    responsible_manager = EXCLUDED.responsible_manager,
                    updated_at = NOW()
            """, cc)
            print(f"  ✓ {cc[0]}: {cc[1]} (Budget: ${cc[4]:,.2f})")

        # ========================================
        # TECHNICIANS
        # ========================================
        print("\n👨‍🔧 Creating Technician Skills Data...")

        # Create table if not exists
        cur.execute("""
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
        """)

        technicians = [
            (101, "John Smith", "HVAC Certified, Electrical Safety, Refrigeration EPA 608", "Senior", "Available", "North Region", "+1-555-0101", "john.smith@company.com"),
            (102, "Maria Garcia", "HVAC Certified, Boiler Operations, Building Automation", "Senior", "Available", "Central Region", "+1-555-0102", "maria.garcia@company.com"),
            (103, "James Wilson", "HVAC Certified, Electrical Safety, Plumbing", "Mid-Level", "Busy", "South Region", "+1-555-0103", "james.wilson@company.com"),
            (104, "Lisa Anderson", "HVAC Certified, Energy Management, LEED AP", "Senior", "Available", "North Region", "+1-555-0104", "lisa.anderson@company.com"),
            (105, "Robert Taylor", "HVAC Certified, Refrigeration EPA 608, Controls Programming", "Mid-Level", "Available", "Central Region", "+1-555-0105", "robert.taylor@company.com"),
            (106, "Jennifer Lee", "HVAC Certified, Electrical Safety, Fire Safety", "Junior", "Available", "South Region", "+1-555-0106", "jennifer.lee@company.com"),
            (107, "Michael Brown", "Boiler Operations, Plumbing, HVAC Basics", "Mid-Level", "On Leave", "Central Region", "+1-555-0107", "michael.brown@company.com"),
            (108, "Sarah Martinez", "HVAC Certified, Building Automation, Energy Auditing", "Senior", "Available", "North Region", "+1-555-0108", "sarah.martinez@company.com"),
        ]

        for tech in technicians:
            cur.execute("""
                INSERT INTO core.technicians
                (technician_id, name, skills, certification_level, availability_status, assigned_territory, phone, email, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (technician_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    skills = EXCLUDED.skills,
                    certification_level = EXCLUDED.certification_level,
                    availability_status = EXCLUDED.availability_status,
                    assigned_territory = EXCLUDED.assigned_territory,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email
            """, tech)
            print(f"  ✓ {tech[0]}: {tech[1]} - {tech[2]}")

        conn.commit()

        print("\n" + "="*70)
        print("✅ Master Data Seeding Complete!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  • Materials (HVAC Parts): {len(materials)}")
        print(f"  • Assets (Buildings/HVAC): {len(assets)}")
        print(f"  • Cost Centers: {len(cost_centers)}")
        print(f"  • Technicians: {len(technicians)}")
        print(f"\n🎯 Agents can now validate:")
        print(f"  ✓ Required parts availability")
        print(f"  ✓ Technician skills & availability")
        print(f"  ✓ Asset location & status")
        print(f"  ✓ Budget allocation")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    seed_data()
