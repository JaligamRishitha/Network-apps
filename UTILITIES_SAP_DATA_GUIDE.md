# SAP Master Data for Utilities (Power & Gas Networks)

## Overview

SAP database populated with comprehensive master data for UK-style utilities operations, modeled after:
- **UKPN (UK Power Networks)** - Electricity distribution
- **SGN (Scotia Gas Networks)** - Gas distribution

---

## 📊 Master Data Summary

### ⚡ **Power Network Materials (27 items)**

| Category | Count | Examples |
|----------|-------|----------|
| **Cables & Conductors** | 5 | 11kV XLPE, 33kV XLPE, LV cables, Overhead conductors |
| **Transformers** | 4 | 500kVA, 1000kVA, Pole mounted |
| **Switchgear & Protection** | 5 | RMU, Circuit breakers, CTs, VTs, Surge arresters |
| **Poles & Mounting** | 5 | Wooden poles, Steel poles, Concrete poles, Hardware |
| **Meters & Monitoring** | 4 | SMETS2 smart meters, CT metering, SCADA RTU |
| **Earthing & Bonding** | 3 | Earth rods, Conductors, Earth mats |

**Storage Depots:**
- `DEPOT-LONDON` - Central London depot
- `DEPOT-SOUTH` - South East England
- `DEPOT-EAST` - East Anglia
- `DEPOT-NORTH` - North region

---

### 🔥 **Gas Network Materials (27 items)**

| Category | Count | Examples |
|----------|-------|----------|
| **Pipes & Fittings** | 7 | PE pipes (180mm, 125mm, 63mm), Steel pipes, Couplings, Tees |
| **Valves & Regulators** | 6 | Gate valves, Ball valves, Pressure regulators, ECVs |
| **Meters & Monitoring** | 5 | Smart gas meters G4/G6, Industrial meters, SCADA RTU |
| **Protection & Safety** | 6 | CP anodes, Leak detectors, Warning tape, Slam shut valves |
| **Connection & Installation** | 3 | Service kits, Tapping saddles, Repair clamps |

**Storage Depots:**
- `DEPOT-SCOTLAND` - Scottish gas network
- `DEPOT-SOUTH` - Southern England

---

### 🏭 **Network Infrastructure Assets (22 items)**

#### Power Network Assets (11):

**Primary Substations (132kV/11kV):**
- SUB-LONDON-001: London Central - 90MVA
- SUB-LONDON-002: Canary Wharf - 60MVA
- SUB-SOUTH-001: Brighton - 45MVA (132kV/33kV)
- SUB-EAST-001: Ipswich - 30MVA

**Secondary Substations (11kV/415V):**
- SUB-LONDON-S001: Paddington - 2x1000kVA
- SUB-LONDON-S002: Kings Cross - 2x500kVA
- SUB-SOUTH-S001: Crawley - 1x800kVA
- SUB-EAST-S001: Colchester - 1x500kVA
- SUB-NORTH-S001: Luton - 2x630kVA (Under Maintenance)

**Overhead Line Networks:**
- OHL-EAST-001: Rural East Anglia - 45km 11kV
- OHL-SOUTH-001: Sussex Coast - 11kV coastal

#### Gas Network Assets (11):

**Offtake Stations (NTS to LDZ):**
- GAS-SCOT-001: Edinburgh North - 7bar
- GAS-SCOT-002: Glasgow West - 7bar with odorization
- GAS-SOUTH-001: Southampton - 7bar to 2bar

**District Governors (Pressure Reduction):**
- GAS-SCOT-R001: Edinburgh City Centre - 8000m³/h
- GAS-SCOT-R002: Glasgow South - 5000m³/h
- GAS-SOUTH-R001: Guildford - 6000m³/h
- GAS-SOUTH-R002: Portsmouth - 7000m³/h

**Pipeline Networks:**
- GAS-SCOT-P001: Edinburgh Ring - 180mm PE, 28km
- GAS-SCOT-P002: Glasgow Grid - 250mm PE, 42km
- GAS-SOUTH-P001: Hampshire - 180mm PE, 35km

**Storage:**
- GAS-SCOT-STR001: Granton LNG - 50,000m³

---

### 💰 **Cost Centers (7 centers)**

| Cost Center | Description | Budget (£) | Spent (£) | Available (£) | Manager |
|-------------|-------------|------------|-----------|---------------|---------|
| **CC-UKPN-CAPEX** | Capital projects | 25,000,000 | 5,250,000 | 19,750,000 | David Thompson |
| **CC-UKPN-MAINT** | Network maintenance | 8,500,000 | 2,100,000 | 6,400,000 | Sarah Williams |
| **CC-UKPN-EMERG** | Emergency response | 3,500,000 | 875,000 | 2,625,000 | James Morrison |
| **CC-SGN-CAPEX** | Gas infrastructure | 18,000,000 | 4,200,000 | 13,800,000 | Robert MacDonald |
| **CC-SGN-MAINT** | Gas maintenance | 6,500,000 | 1,625,000 | 4,875,000 | Fiona Campbell |
| **CC-SGN-EMERG** | Gas emergency | 4,000,000 | 950,000 | 3,050,000 | Andrew Stewart |
| **CC-SMART-METER** | Smart meter rollout | 12,000,000 | 3,600,000 | 8,400,000 | Emily Roberts |

---

### 👷 **Engineers/Technicians (14 people)**

#### Power Network Engineers (6):

| ID | Name | Skills | Level | Territory | Status |
|----|------|--------|-------|-----------|--------|
| 201 | Michael Thompson | HV AP, 11kV/33kV, NRSWA Supervisor | Senior | London | Available |
| 202 | Sarah Mitchell | HV AP, 11kV, Substation Maintenance | Senior | South East | Available |
| 203 | David Wilson | LV Authorised, Cable Jointing, NRSWA | Mid-Level | East Anglia | Available |
| 204 | Emma Johnson | HV AP, Protection & Control, SCADA | Senior | London | Busy |
| 205 | James Anderson | HV/LV Authorised, Overhead Lines | Mid-Level | East Anglia | Available |
| 206 | Rachel Brown | Smart Meter Installation, SMETS2 | Junior | South East | Available |

#### Gas Network Engineers (6):

| ID | Name | Skills | Level | Territory | Status |
|----|------|--------|-------|-----------|--------|
| 207 | Andrew MacDonald | Gas Network Construction, PE Fusion, NRSWA | Senior | Scotland | Available |
| 208 | Fiona Campbell | Gas Emergency Engineer, Leak Detection | Senior | Scotland | Available |
| 209 | Robert Stewart | Gas Maintenance, Pipeline Inspection, CP | Mid-Level | Scotland | Available |
| 210 | Jennifer Murray | Gas Service, Meter Installation, Safety | Mid-Level | South | Available |
| 211 | Duncan Fraser | Gas Pressure Regulation, District Governor | Senior | Scotland | On Leave |
| 212 | Lisa Robertson | Smart Gas Meter Installation, SMETS2 | Junior | South | Available |

#### Specialist Engineers (2):

| ID | Name | Skills | Level | Status |
|----|------|--------|-------|--------|
| 213 | Peter Collins | HV Protection, Relay Testing, Commissioning | Senior | Available |
| 214 | Helen Watson | SCADA Systems, RTU Programming, Network Control | Senior | Available |

---

## 🔌 Validation API Examples

### 1. Power Outage Response

**Scenario:** Power outage in London, need HV engineer with 11kV skills

```bash
curl -X POST http://localhost:4798/api/appointments/validate \
  -H "Content-Type: application/json" \
  -d '{
    "required_parts": "11kV cable, Ring Main Unit",
    "required_skills": "HV Authorised Person, 11kV",
    "location": "London",
    "cost_center_id": "CC-UKPN-EMERG",
    "estimated_cost": 25000.00
  }'
```

**Expected Response:**
- ✅ Parts available: 11kV cable (5000m), RMU (12 units)
- ✅ Engineer available: Michael Thompson (HV AP, London)
- ✅ Location: SUB-LONDON-001 or SUB-LONDON-002
- ✅ Budget: £2,625,000 available in emergency fund

---

### 2. Gas Leak Emergency

**Scenario:** Gas leak reported in Scotland, need emergency engineer

```bash
curl -X POST http://localhost:4798/api/appointments/validate \
  -H "Content-Type: application/json" \
  -d '{
    "required_parts": "PE Pipe, Service Valve, Repair Clamp",
    "required_skills": "Gas Emergency Engineer, Leak Detection",
    "location": "Edinburgh",
    "cost_center_id": "CC-SGN-EMERG",
    "estimated_cost": 15000.00
  }'
```

**Expected Response:**
- ✅ Parts available: PE pipe (4000m), Service valves (200), Clamps (50)
- ✅ Engineer available: Fiona Campbell (Gas Emergency, Scotland)
- ✅ Location: GAS-SCOT-001 or GAS-SCOT-R001
- ✅ Budget: £3,050,000 available

---

### 3. Smart Meter Installation

**Scenario:** Smart meter installation program

```bash
curl -X POST http://localhost:4798/api/appointments/validate \
  -H "Content-Type: application/json" \
  -d '{
    "required_parts": "Smart Electricity Meter, Smart Gas Meter",
    "required_skills": "Smart Meter Installation, SMETS2 Certified",
    "location": "South East",
    "cost_center_id": "CC-SMART-METER",
    "estimated_cost": 500.00
  }'
```

**Expected Response:**
- ✅ Parts available: Electric meters (500), Gas meters (400)
- ✅ Engineers available: Rachel Brown or Lisa Robertson
- ✅ Budget: £8,400,000 available in smart meter program

---

### 4. Substation Maintenance

**Scenario:** Scheduled maintenance on secondary substation

```bash
curl -X POST http://localhost:4798/api/appointments/validate \
  -H "Content-Type: application/json" \
  -d '{
    "required_parts": "Transformer, Circuit Breaker, Current Transformer",
    "required_skills": "HV Authorised Person, Substation Maintenance",
    "location": "Paddington",
    "cost_center_id": "CC-UKPN-MAINT",
    "estimated_cost": 50000.00
  }'
```

**Expected Response:**
- ✅ Parts available: Transformers (15), Circuit breakers (20), CTs (50)
- ✅ Engineer available: Sarah Mitchell (HV AP, Substation Maint)
- ✅ Location: SUB-LONDON-S001 (Paddington)
- ✅ Budget: £6,400,000 available

---

### 5. Gas Pipeline Installation

**Scenario:** New gas pipeline connection

```bash
curl -X POST http://localhost:4798/api/appointments/validate \
  -H "Content-Type: application/json" \
  -d '{
    "required_parts": "PE Pipe 125mm, Electrofusion Coupling, Tapping Saddle",
    "required_skills": "Gas Network Construction, PE Fusion, NRSWA",
    "location": "Glasgow",
    "cost_center_id": "CC-SGN-CAPEX",
    "estimated_cost": 75000.00
  }'
```

**Expected Response:**
- ✅ Parts available: PE pipe (6000m), Couplings (200), Saddles (60)
- ✅ Engineer available: Andrew MacDonald (Gas Construction, Scotland)
- ✅ Location: GAS-SCOT-P002 (Glasgow Grid)
- ✅ Budget: £13,800,000 available

---

## 🎯 Common Work Order Types

### Power Network:

1. **Emergency Response**
   - Power outage restoration
   - Fault location and repair
   - Cable strikes/damage

2. **Planned Maintenance**
   - Transformer servicing
   - Switchgear maintenance
   - Protection relay testing

3. **Capital Projects**
   - New substation construction
   - Cable replacement programs
   - Network reinforcement

4. **Smart Meter Rollout**
   - SMETS2 meter installations
   - Communications hub setup

### Gas Network:

1. **Emergency Response**
   - Gas leak response
   - Pipeline damage repair
   - Emergency valve operations

2. **Planned Maintenance**
   - Pipeline inspection
   - Cathodic protection testing
   - Regulator servicing

3. **Capital Projects**
   - New pipeline installation
   - Offtake station upgrades
   - Pressure system reinforcement

4. **Customer Connections**
   - New service connections
   - Meter installations
   - Appliance safety checks

---

## 📋 Materials Quick Reference

### Power Network Common Materials:

| Material ID | Description | Typical Use |
|-------------|-------------|-------------|
| MAT-PWR-001 | 11kV Cable XLPE | Underground distribution |
| MAT-PWR-006 | Transformer 500kVA | Secondary substation |
| MAT-PWR-009 | Ring Main Unit | Network switching |
| MAT-PWR-021 | Smart Meter SMETS2 | Customer metering |
| MAT-PWR-025 | Earth Rod | Substation earthing |

### Gas Network Common Materials:

| Material ID | Description | Typical Use |
|-------------|-------------|-------------|
| MAT-GAS-001 | PE Pipe 180mm | Main distribution |
| MAT-GAS-003 | PE Pipe 63mm | Service connections |
| MAT-GAS-011 | Pressure Regulator | District regulation |
| MAT-GAS-014 | Smart Gas Meter G4 | Domestic metering |
| MAT-GAS-021 | Leak Detector | Safety equipment |

---

## 🔧 Skills & Certifications

### Power Network Skills:
- **HV Authorised Person** - Authorized for high voltage work (11kV, 33kV)
- **LV Authorised** - Low voltage authorized
- **NRSWA** - New Roads and Street Works Act certified
- **Cable Jointing** - HV/LV cable jointing qualified
- **Protection & Control** - Relay testing and commissioning
- **SCADA** - Supervisory control systems

### Gas Network Skills:
- **Gas Network Construction** - Pipeline construction qualified
- **PE Fusion** - Polyethylene pipe fusion welding
- **Leak Detection** - Gas leak location and repair
- **First Call Operative** - Emergency response authorized
- **CP Testing** - Cathodic protection testing
- **Appliance Safety** - Gas appliance safety checks
- **NRSWA** - Street works certified

---

## 📞 Support & Integration

**API Base URL:** `http://localhost:4798/api/appointments`

**Key Endpoints:**
- `POST /validate` - Comprehensive validation
- `GET /parts/search?query=<term>` - Search materials
- `GET /technicians/available` - List available engineers
- `GET /locations/search?location=<location>` - Find assets

**Database:** PostgreSQL on port 4794
**Seed Script:** `/home/pradeep1a/Network-apps/SAP_clone/seed_utilities_data.py`

---

## 🚀 Integration with Appointment Flow

The utilities data integrates with your existing appointment flow:

```
Salesforce Request → APT-XXXXXXXX (immediate)
    ↓
ServiceNow Ticket → INC0010123
    ↓
Agent Validation against SAP:
  ✓ Check materials (cables, pipes, meters, etc.)
  ✓ Find qualified engineer (HV AP, Gas Emergency, etc.)
  ✓ Verify asset location (substation, pipeline, etc.)
  ✓ Confirm budget (CAPEX, maintenance, emergency)
    ↓
Agent Approval → Assign Engineer
    ↓
Create SAP Work Order → Maintenance/Service Order
    ↓
Complete ✅
```

---

**Last Updated:** 2026-02-05
**Version:** 1.0.0
**Utilities:** UKPN (Power) | SGN (Gas)
