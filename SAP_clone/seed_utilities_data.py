"""
Seed Script for Utilities SAP Master Data (Power & Gas Networks)
Based on UK utilities like UKPN (UK Power Networks), SGN (Scotia Gas Networks)
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

def seed_utilities_data():
    """Seed SAP database with utilities master data"""
    print("🌱 Connecting to SAP database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("✅ Connected!")

    try:
        # ========================================
        # POWER NETWORK MATERIALS
        # ========================================
        print("\n⚡ Creating Power Network Materials...")

        materials = [
            # Cables & Conductors
            ("MAT-PWR-001", "11kV Underground Cable XLPE 3-Core 185mm² (per meter)", 5000, "M", 1000, "DEPOT-LONDON"),
            ("MAT-PWR-002", "33kV Underground Cable XLPE 3-Core 300mm² (per meter)", 3000, "M", 500, "DEPOT-LONDON"),
            ("MAT-PWR-003", "LV Underground Cable 4-Core 95mm² (per meter)", 8000, "M", 2000, "DEPOT-SOUTH"),
            ("MAT-PWR-004", "Overhead Line Conductor ACSR 175mm² (per meter)", 6000, "M", 1500, "DEPOT-EAST"),
            ("MAT-PWR-005", "Overhead Line Conductor AAC 50mm² (per meter)", 4000, "M", 1000, "DEPOT-NORTH"),

            # Transformers & Distribution
            ("MAT-PWR-006", "Distribution Transformer 500kVA 11kV/415V", 15, "EA", 3, "DEPOT-LONDON"),
            ("MAT-PWR-007", "Distribution Transformer 1000kVA 11kV/415V", 10, "EA", 2, "DEPOT-SOUTH"),
            ("MAT-PWR-008", "Pole Mounted Transformer 100kVA 11kV/415V", 25, "EA", 5, "DEPOT-EAST"),
            ("MAT-PWR-009", "Ring Main Unit (RMU) 11kV 630A", 12, "EA", 3, "DEPOT-LONDON"),
            ("MAT-PWR-010", "Circuit Breaker 11kV 630A SF6", 20, "EA", 5, "DEPOT-SOUTH"),

            # Switchgear & Protection
            ("MAT-PWR-011", "11kV Switchgear Panel 3-Phase", 8, "EA", 2, "DEPOT-LONDON"),
            ("MAT-PWR-012", "LV Distribution Board 400A TPN", 30, "EA", 8, "DEPOT-SOUTH"),
            ("MAT-PWR-013", "Current Transformer 11kV 200/5A", 50, "EA", 15, "DEPOT-EAST"),
            ("MAT-PWR-014", "Voltage Transformer 11kV/110V", 40, "EA", 10, "DEPOT-NORTH"),
            ("MAT-PWR-015", "Surge Arrester 11kV 10kA", 60, "EA", 15, "DEPOT-LONDON"),

            # Poles & Mounting
            ("MAT-PWR-016", "Wooden Utility Pole 10m Class 3", 100, "EA", 20, "DEPOT-EAST"),
            ("MAT-PWR-017", "Steel Pole 12m Galvanized", 50, "EA", 10, "DEPOT-NORTH"),
            ("MAT-PWR-018", "Concrete Pole 11m 600kg", 40, "EA", 10, "DEPOT-SOUTH"),
            ("MAT-PWR-019", "Cross Arm Assembly Steel", 150, "EA", 30, "DEPOT-EAST"),
            ("MAT-PWR-020", "Pole Mounted Hardware Kit", 200, "EA", 50, "DEPOT-NORTH"),

            # Meters & Monitoring
            ("MAT-PWR-021", "Smart Electricity Meter Single Phase SMETS2", 500, "EA", 100, "DEPOT-LONDON"),
            ("MAT-PWR-022", "Smart Electricity Meter Three Phase SMETS2", 200, "EA", 50, "DEPOT-SOUTH"),
            ("MAT-PWR-023", "CT Metering Unit 11kV", 30, "EA", 10, "DEPOT-LONDON"),
            ("MAT-PWR-024", "Data Logger RTU for Substations", 25, "EA", 5, "DEPOT-SOUTH"),

            # Earthing & Bonding
            ("MAT-PWR-025", "Earth Rod Copper Clad 1.2m x 16mm", 300, "EA", 75, "DEPOT-LONDON"),
            ("MAT-PWR-026", "Earth Conductor Bare Copper 50mm²", 2000, "M", 500, "DEPOT-SOUTH"),
            ("MAT-PWR-027", "Earthing Mat Copper Mesh 1m²", 100, "EA", 25, "DEPOT-EAST"),

            # GAS NETWORK MATERIALS
            # ======================
            # Pipes & Fittings
            ("MAT-GAS-001", "PE Pipe SDR11 180mm Gas Mains (per meter)", 4000, "M", 1000, "DEPOT-SCOTLAND"),
            ("MAT-GAS-002", "PE Pipe SDR11 125mm Gas Mains (per meter)", 6000, "M", 1500, "DEPOT-SCOTLAND"),
            ("MAT-GAS-003", "PE Pipe SDR11 63mm Gas Service (per meter)", 8000, "M", 2000, "DEPOT-SOUTH"),
            ("MAT-GAS-004", "Steel Pipe Schedule 40 300mm (per meter)", 2000, "M", 500, "DEPOT-SCOTLAND"),
            ("MAT-GAS-005", "PE Electrofusion Coupling 125mm", 200, "EA", 50, "DEPOT-SCOTLAND"),
            ("MAT-GAS-006", "PE Electrofusion Tee 180mm", 150, "EA", 40, "DEPOT-SCOTLAND"),
            ("MAT-GAS-007", "PE Butt Fusion Joint 63mm", 300, "EA", 75, "DEPOT-SOUTH"),

            # Valves & Regulators
            ("MAT-GAS-008", "Gate Valve PE 180mm", 30, "EA", 8, "DEPOT-SCOTLAND"),
            ("MAT-GAS-009", "Ball Valve PE 125mm", 50, "EA", 15, "DEPOT-SCOTLAND"),
            ("MAT-GAS-010", "Service Valve 25mm", 200, "EA", 50, "DEPOT-SOUTH"),
            ("MAT-GAS-011", "Pressure Regulator 2bar to 75mbar", 40, "EA", 10, "DEPOT-SCOTLAND"),
            ("MAT-GAS-012", "District Regulator 7bar to 2bar 500m³/h", 15, "EA", 3, "DEPOT-SCOTLAND"),
            ("MAT-GAS-013", "Emergency Control Valve (ECV) 25mm", 150, "EA", 40, "DEPOT-SOUTH"),

            # Meters & Monitoring
            ("MAT-GAS-014", "Smart Gas Meter Ultrasonic G4", 400, "EA", 100, "DEPOT-SCOTLAND"),
            ("MAT-GAS-015", "Smart Gas Meter Ultrasonic G6", 200, "EA", 50, "DEPOT-SOUTH"),
            ("MAT-GAS-016", "Industrial Gas Meter Turbine 160m³/h", 20, "EA", 5, "DEPOT-SCOTLAND"),
            ("MAT-GAS-017", "Gas Pressure Recorder Digital", 25, "EA", 8, "DEPOT-SCOTLAND"),
            ("MAT-GAS-018", "SCADA RTU for Gas Network", 30, "EA", 8, "DEPOT-SCOTLAND"),

            # Protection & Safety
            ("MAT-GAS-019", "Cathodic Protection Anode Magnesium", 100, "EA", 25, "DEPOT-SCOTLAND"),
            ("MAT-GAS-020", "Cathodic Protection Test Post", 80, "EA", 20, "DEPOT-SOUTH"),
            ("MAT-GAS-021", "Gas Leak Detector Portable", 40, "EA", 10, "DEPOT-SCOTLAND"),
            ("MAT-GAS-022", "Warning Marker Tape Gas Pipeline", 500, "RL", 100, "DEPOT-SCOTLAND"),
            ("MAT-GAS-023", "Slam Shut Valve 100mm", 15, "EA", 5, "DEPOT-SCOTLAND"),
            ("MAT-GAS-024", "Odorant Injection Pump", 10, "EA", 2, "DEPOT-SCOTLAND"),

            # Connection & Installation
            ("MAT-GAS-025", "Service Connection Kit 25mm", 100, "EA", 25, "DEPOT-SOUTH"),
            ("MAT-GAS-026", "Main Tapping Saddle 180mm/63mm", 60, "EA", 15, "DEPOT-SCOTLAND"),
            ("MAT-GAS-027", "PE Pipe Repair Clamp 125mm", 50, "EA", 15, "DEPOT-SCOTLAND"),
        ]

        for mat in materials:
            cur.execute("""
                INSERT INTO mm.materials
                (material_id, description, quantity, unit_of_measure, reorder_level, storage_location, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, mat)
            print(f"  ✓ {mat[0]}: {mat[1]} (Qty: {mat[2]})")

        # ========================================
        # NETWORK ASSETS (Substations, Gas Stations, etc.)
        # ========================================
        print("\n🏭 Creating Network Infrastructure Assets...")

        assets = [
            # POWER NETWORK - Primary Substations
            ("SUB-LONDON-001", "substation", "Primary Substation - London Central 132/11kV", "London, Westminster", date(2010, 3, 15), "operational", "132kV/11kV 90MVA primary substation serving central London"),
            ("SUB-LONDON-002", "substation", "Primary Substation - Canary Wharf 132/11kV", "London, Isle of Dogs", date(2015, 9, 20), "operational", "132kV/11kV 60MVA primary substation for financial district"),
            ("SUB-SOUTH-001", "substation", "Primary Substation - Brighton 132/33kV", "Brighton, East Sussex", date(2012, 6, 10), "operational", "132kV/33kV 45MVA primary substation"),
            ("SUB-EAST-001", "substation", "Primary Substation - Ipswich 132/11kV", "Ipswich, Suffolk", date(2008, 4, 25), "operational", "132kV/11kV 30MVA primary substation"),

            # POWER NETWORK - Secondary Substations
            ("SUB-LONDON-S001", "transformer", "Secondary Substation - Paddington 11kV/415V", "London, Paddington Station Area", date(2016, 11, 5), "operational", "11kV/415V 2x1000kVA secondary substation"),
            ("SUB-LONDON-S002", "transformer", "Secondary Substation - Kings Cross 11kV/415V", "London, Kings Cross", date(2017, 3, 12), "operational", "11kV/415V 2x500kVA secondary substation"),
            ("SUB-SOUTH-S001", "transformer", "Secondary Substation - Crawley 11kV/415V", "Crawley, West Sussex", date(2014, 8, 20), "operational", "11kV/415V 1x800kVA secondary substation"),
            ("SUB-EAST-S001", "transformer", "Secondary Substation - Colchester 11kV/415V", "Colchester, Essex", date(2013, 5, 18), "operational", "11kV/415V 1x500kVA secondary substation"),
            ("SUB-NORTH-S001", "transformer", "Secondary Substation - Luton 11kV/415V", "Luton, Bedfordshire", date(2015, 2, 8), "under_maintenance", "11kV/415V 2x630kVA secondary substation - scheduled maintenance"),

            # POWER NETWORK - Overhead Line Networks
            ("OHL-EAST-001", "feeder", "Overhead Line Network - Rural East Anglia", "Suffolk and Norfolk", date(2005, 7, 15), "operational", "11kV overhead network covering 45km rural area"),
            ("OHL-SOUTH-001", "feeder", "Overhead Line Network - Sussex Coast", "East Sussex", date(2007, 9, 22), "operational", "11kV overhead network coastal distribution"),

            # GAS NETWORK - Offtake Stations
            ("GAS-SCOT-001", "substation", "Gas Offtake Station - Edinburgh North", "Edinburgh, Granton", date(2011, 4, 10), "operational", "NTS offtake station 7bar pressure reduction to LDZ"),
            ("GAS-SCOT-002", "substation", "Gas Offtake Station - Glasgow West", "Glasgow, Yoker", date(2013, 8, 15), "operational", "NTS offtake station 7bar with odorization plant"),
            ("GAS-SOUTH-001", "substation", "Gas Offtake Station - Southampton", "Southampton, Fawley", date(2009, 6, 20), "operational", "NTS offtake station 7bar to LDZ 2bar system"),

            # GAS NETWORK - District Regulators
            ("GAS-SCOT-R001", "transformer", "District Governor - Edinburgh City Centre", "Edinburgh, Haymarket", date(2014, 3, 5), "operational", "District pressure reduction 2bar to 75mbar, capacity 8000m³/h"),
            ("GAS-SCOT-R002", "transformer", "District Governor - Glasgow South", "Glasgow, Giffnock", date(2015, 11, 12), "operational", "District pressure reduction 2bar to 75mbar, capacity 5000m³/h"),
            ("GAS-SOUTH-R001", "transformer", "District Governor - Guildford", "Guildford, Surrey", date(2012, 9, 8), "operational", "District pressure reduction 2bar to 75mbar, capacity 6000m³/h"),
            ("GAS-SOUTH-R002", "transformer", "District Governor - Portsmouth", "Portsmouth, Hampshire", date(2016, 5, 20), "operational", "District pressure reduction 2bar to 75mbar, capacity 7000m³/h"),

            # GAS NETWORK - Pipeline Networks
            ("GAS-SCOT-P001", "feeder", "Medium Pressure Pipeline Network - Edinburgh Ring", "Edinburgh Metropolitan Area", date(2010, 2, 15), "operational", "180mm PE pipeline 2bar ring main 28km"),
            ("GAS-SCOT-P002", "feeder", "Medium Pressure Pipeline Network - Glasgow Grid", "Glasgow Metropolitan Area", date(2011, 7, 22), "operational", "250mm PE pipeline 2bar grid system 42km"),
            ("GAS-SOUTH-P001", "feeder", "Medium Pressure Pipeline Network - Hampshire", "Hampshire Region", date(2008, 11, 10), "operational", "180mm PE pipeline 2bar network 35km"),

            # GAS NETWORK - Storage & Emergency
            ("GAS-SCOT-STR001", "substation", "Gas Storage Holder - Granton", "Edinburgh, Granton", date(1995, 5, 10), "operational", "LNG storage facility 50,000m³ for peak demand and emergencies"),
        ]

        for asset in assets:
            cur.execute("""
                INSERT INTO pm.assets
                (asset_id, asset_type, name, location, installation_date, status, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, asset)
            print(f"  ✓ {asset[0]}: {asset[2]}")

        # ========================================
        # COST CENTERS
        # ========================================
        print("\n💰 Creating Utilities Cost Centers...")

        cost_centers = [
            ("CC-UKPN-CAPEX", "UKPN Capital Expenditure", "Network infrastructure capital projects", 2026, 25000000.00, 5250000.00, "David Thompson"),
            ("CC-UKPN-MAINT", "UKPN Network Maintenance", "Routine maintenance and repairs", 2026, 8500000.00, 2100000.00, "Sarah Williams"),
            ("CC-UKPN-EMERG", "UKPN Emergency Response", "Emergency repairs and fault response", 2026, 3500000.00, 875000.00, "James Morrison"),
            ("CC-SGN-CAPEX", "SGN Capital Expenditure", "Gas network infrastructure projects", 2026, 18000000.00, 4200000.00, "Robert MacDonald"),
            ("CC-SGN-MAINT", "SGN Network Maintenance", "Gas pipeline maintenance and inspection", 2026, 6500000.00, 1625000.00, "Fiona Campbell"),
            ("CC-SGN-EMERG", "SGN Emergency Response", "Gas leak response and emergency repairs", 2026, 4000000.00, 950000.00, "Andrew Stewart"),
            ("CC-SMART-METER", "Smart Meter Rollout", "Smart meter installation program", 2026, 12000000.00, 3600000.00, "Emily Roberts"),
        ]

        for cc in cost_centers:
            cur.execute("""
                INSERT INTO fi.cost_centers
                (cost_center_id, name, description, fiscal_year, budget_allocated, budget_spent, responsible_manager, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, cc)
            print(f"  ✓ {cc[0]}: {cc[1]} (Budget: £{cc[4]:,.2f})")

        # ========================================
        # TECHNICIANS / ENGINEERS
        # ========================================
        print("\n👷 Creating Utilities Engineers/Technicians...")

        technicians = [
            # Power Network Engineers
            (201, "Michael Thompson", "HV Authorised Person, 11kV/33kV, NRSWA Supervisor", "Senior", "Available", "London", "+44-7700-900201", "m.thompson@ukpn.co.uk"),
            (202, "Sarah Mitchell", "HV Authorised Person, 11kV, Substation Maintenance", "Senior", "Available", "South East", "+44-7700-900202", "s.mitchell@ukpn.co.uk"),
            (203, "David Wilson", "LV Authorised, Cable Jointing, NRSWA", "Mid-Level", "Available", "East Anglia", "+44-7700-900203", "d.wilson@ukpn.co.uk"),
            (204, "Emma Johnson", "HV Authorised Person, Protection & Control, SCADA", "Senior", "Busy", "London", "+44-7700-900204", "e.johnson@ukpn.co.uk"),
            (205, "James Anderson", "HV/LV Authorised, Overhead Lines, Pole Mounting", "Mid-Level", "Available", "East Anglia", "+44-7700-900205", "j.anderson@ukpn.co.uk"),
            (206, "Rachel Brown", "Smart Meter Installation, SMETS2 Certified", "Junior", "Available", "South East", "+44-7700-900206", "r.brown@ukpn.co.uk"),

            # Gas Network Engineers
            (207, "Andrew MacDonald", "Gas Network Construction, PE Fusion, NRSWA", "Senior", "Available", "Scotland", "+44-7700-900207", "a.macdonald@sgn.co.uk"),
            (208, "Fiona Campbell", "Gas Emergency Engineer, Leak Detection, First Call", "Senior", "Available", "Scotland", "+44-7700-900208", "f.campbell@sgn.co.uk"),
            (209, "Robert Stewart", "Gas Network Maintenance, Pipeline Inspection, CP Testing", "Mid-Level", "Available", "Scotland", "+44-7700-900209", "r.stewart@sgn.co.uk"),
            (210, "Jennifer Murray", "Gas Service Engineer, Meter Installation, Appliance Safety", "Mid-Level", "Available", "South", "+44-7700-900210", "j.murray@sgn.co.uk"),
            (211, "Duncan Fraser", "Gas Pressure Regulation, District Governor Maintenance", "Senior", "On Leave", "Scotland", "+44-7700-900211", "d.fraser@sgn.co.uk"),
            (212, "Lisa Robertson", "Smart Gas Meter Installation, SMETS2 Certified", "Junior", "Available", "South", "+44-7700-900212", "l.robertson@sgn.co.uk"),

            # Specialist Engineers
            (213, "Peter Collins", "HV Protection Engineer, Relay Testing, Commissioning", "Senior", "Available", "London", "+44-7700-900213", "p.collins@ukpn.co.uk"),
            (214, "Helen Watson", "SCADA Systems Engineer, RTU Programming, Network Control", "Senior", "Available", "Scotland", "+44-7700-900214", "h.watson@sgn.co.uk"),
        ]

        for tech in technicians:
            cur.execute("""
                INSERT INTO core.technicians
                (technician_id, name, skills, certification_level, availability_status, assigned_territory, phone, email, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, tech)
            print(f"  ✓ {tech[0]}: {tech[1]} - {tech[2]}")

        conn.commit()

        print("\n" + "="*70)
        print("✅ Utilities Master Data Seeding Complete!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  • Materials (Power & Gas): {len(materials)}")
        print(f"  • Assets (Substations/Pipelines): {len(assets)}")
        print(f"  • Cost Centers: {len(cost_centers)}")
        print(f"  • Engineers/Technicians: {len(technicians)}")
        print(f"\n🎯 Utilities covered:")
        print(f"  ⚡ Power Network (UKPN-style):")
        print(f"     • Cables, transformers, switchgear")
        print(f"     • Primary & secondary substations")
        print(f"     • Overhead line networks")
        print(f"     • Smart electricity meters")
        print(f"  🔥 Gas Network (SGN-style):")
        print(f"     • PE pipes, valves, regulators")
        print(f"     • Offtake stations & district governors")
        print(f"     • Medium pressure pipelines")
        print(f"     • Smart gas meters & safety equipment")
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
    seed_utilities_data()
