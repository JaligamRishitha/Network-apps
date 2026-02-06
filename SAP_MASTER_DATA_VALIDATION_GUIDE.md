
# SAP Master Data for Appointment Validation

## Overview

SAP database has been populated with comprehensive master data that agents can use to validate appointment requests in real-time. This ensures appointments are only approved when resources, parts, skills, and budget are available.

---

## 📊 Master Data Seeded

### 1. **HVAC Materials (27 items)**

| Category | Examples | Quantity Range |
|----------|----------|----------------|
| **Air Filters** | Standard 20x25x1, HEPA, Carbon | 75-150 units |
| **Coolants** | R-410A, R-134A, Glycol | 25-60 units |
| **Thermostats** | Digital Programmable, Smart WiFi | 20-35 units |
| **Motors & Belts** | Condenser Fan, Blower Motor | 10-80 units |
| **Electrical** | Capacitors, Contactors | 30-50 units |
| **Coils** | Evaporator, Condenser | 6-8 units |
| **Ductwork** | Flexible Duct, Grilles | 50-100 units |
| **Tools** | Vacuum Oil, Leak Dye, Tape | 30-120 units |
| **Sensors** | Temperature, Pressure, CO2 | 18-60 units |

**Storage Locations:**
- `WH-CENTRAL` - Main warehouse (most items)
- `WH-NORTH` - North region warehouse
- `WH-SOUTH` - South region warehouse

---

### 2. **Building & HVAC Assets (11 items)**

#### Buildings:
- **Building A** - Main Office (5-story, 50,000 sq ft)
- **Building B** - R&D Center (3-story with labs)
- **Building C** - Warehouse (single-story)

#### HVAC Systems:
- **HVAC-A-001** - Building A Floors 1-2 (50-ton rooftop unit)
- **HVAC-A-002** - Building A Floors 3-5 (60-ton rooftop unit)
- **HVAC-A-003** - Building A Chiller (200-ton water-cooled)
- **HVAC-B-001** - Building B Floor 1 (40-ton VAV)
- **HVAC-B-002** - Building B Floors 2-3 (45-ton VAV) - *Under Maintenance*
- **HVAC-C-001** - Warehouse (30-ton makeup air)

#### Boilers:
- **BOILER-A-001** - Building A (2.5 MMBtu/hr)
- **BOILER-B-001** - Building B (1.8 MMBtu/hr condensing)

---

### 3. **Cost Centers (5 centers)**

| Cost Center ID | Name | Budget Allocated | Budget Spent | Available | Manager |
|----------------|------|------------------|--------------|-----------|---------|
| CC-FACILITY-001 | Facilities Maintenance | $500,000 | $125,000 | $375,000 | Sarah Johnson |
| CC-HVAC-001 | HVAC Operations | $350,000 | $87,500 | $262,500 | Michael Chen |
| CC-ENERGY-001 | Energy Management | $750,000 | $180,000 | $570,000 | Jennifer Martinez |
| CC-BLDGA-001 | Building A Operations | $250,000 | $60,000 | $190,000 | David Wilson |
| CC-BLDGB-001 | Building B Operations | $200,000 | $45,000 | $155,000 | Emily Brown |

---

### 4. **Technicians (8 technicians)**

| ID | Name | Certification | Skills | Territory | Status |
|----|------|---------------|--------|-----------|--------|
| 101 | John Smith | Senior | HVAC Certified, Electrical Safety, Refrigeration EPA 608 | North | Available |
| 102 | Maria Garcia | Senior | HVAC Certified, Boiler Operations, Building Automation | Central | Available |
| 103 | James Wilson | Mid-Level | HVAC Certified, Electrical Safety, Plumbing | South | Busy |
| 104 | Lisa Anderson | Senior | HVAC Certified, Energy Management, LEED AP | North | Available |
| 105 | Robert Taylor | Mid-Level | HVAC Certified, Refrigeration EPA 608, Controls Programming | Central | Available |
| 106 | Jennifer Lee | Junior | HVAC Certified, Electrical Safety, Fire Safety | South | Available |
| 107 | Michael Brown | Mid-Level | Boiler Operations, Plumbing, HVAC Basics | Central | On Leave |
| 108 | Sarah Martinez | Senior | HVAC Certified, Building Automation, Energy Auditing | North | Available |

---

## 🔌 Validation API Endpoints

All endpoints are available at `http://localhost:4772/api/appointments`

### 1. **Comprehensive Validation**

**Endpoint:** `POST /api/appointments/validate`

**Request Body:**
```json
{
  "required_parts": "Air filter, Coolant",
  "required_skills": "HVAC Certified, Electrical Safety",
  "location": "Building A, Floor 3",
  "cost_center_id": "CC-HVAC-001",
  "estimated_cost": 5000.00
}
```

**Response:**
```json
{
  "valid": true,
  "parts_validation": {
    "all_available": true,
    "parts_status": [
      {
        "part": "air filter",
        "available": true,
        "quantity": 150,
        "material_id": "MAT-HVAC-001",
        "storage_location": "WH-CENTRAL"
      },
      {
        "part": "coolant",
        "available": true,
        "quantity": 40,
        "material_id": "MAT-HVAC-004",
        "storage_location": "WH-CENTRAL"
      }
    ],
    "issues": [],
    "recommendations": []
  },
  "technician_validation": {
    "technicians_available": true,
    "matching_technicians": [...],
    "recommended_technician": {
      "technician_id": 101,
      "name": "John Smith",
      "skills": "HVAC Certified, Electrical Safety, Refrigeration EPA 608",
      "certification_level": "Senior",
      "assigned_territory": "North Region",
      "phone": "+1-555-0101",
      "email": "john.smith@company.com"
    }
  },
  "location_validation": {
    "location_found": true,
    "matching_assets": [...],
    "nearest_asset": {
      "asset_id": "HVAC-A-001",
      "name": "HVAC System - Building A Floor 1-2",
      "location": "Building A, Rooftop North",
      "status": "operational"
    }
  },
  "budget_validation": {
    "budget_sufficient": true,
    "cost_center": {
      "cost_center_id": "CC-HVAC-001",
      "name": "HVAC Operations",
      "budget_allocated": 350000.00,
      "budget_spent": 87500.00,
      "responsible_manager": "Michael Chen"
    },
    "available_budget": 262500.00,
    "budget_utilization": 25.00
  },
  "issues": [],
  "recommendations": []
}
```

---

### 2. **Search Parts**

**Endpoint:** `GET /api/appointments/parts/search?query=thermostat`

**Response:**
```json
{
  "query": "thermostat",
  "parts_found": [
    {
      "part": "thermostat",
      "available": true,
      "quantity": 35,
      "material_id": "MAT-HVAC-007",
      "storage_location": "WH-NORTH"
    }
  ]
}
```

---

### 3. **List Available Technicians**

**Endpoint:** `GET /api/appointments/technicians/available`

**Optional Filter:** `?skill=HVAC`

**Response:**
```json
{
  "count": 6,
  "technicians": [
    {
      "technician_id": 101,
      "name": "John Smith",
      "skills": "HVAC Certified, Electrical Safety, Refrigeration EPA 608",
      "certification_level": "Senior",
      "assigned_territory": "North Region",
      "phone": "+1-555-0101",
      "email": "john.smith@company.com"
    },
    ...
  ]
}
```

---

### 4. **Validate Technician Skills**

**Endpoint:** `GET /api/appointments/technicians/validate?required_skills=HVAC Certified,Electrical Safety`

**Response:**
```json
{
  "technicians_available": true,
  "matching_technicians": [...]  ,
  "recommended_technician": {...}
}
```

---

### 5. **Search Locations/Assets**

**Endpoint:** `GET /api/appointments/locations/search?location=Building A`

**Response:**
```json
{
  "location_found": true,
  "matching_assets": [...],
  "nearest_asset": {...}
}
```

---

### 6. **Check Budget**

**Endpoint:** `GET /api/appointments/budget/check?cost_center_id=CC-HVAC-001&estimated_cost=5000`

**Response:**
```json
{
  "budget_sufficient": true,
  "cost_center": {...},
  "available_budget": 262500.00,
  "budget_utilization": 25.00
}
```

---

### 7. **Get Material Recommendations**

**Endpoint:** `GET /api/appointments/materials/recommendations`

**Response:**
```json
{
  "count": 10,
  "materials": [...]
}
```

---

## 🧪 Testing

### Run Seed Script (Already Completed)
```bash
cd /home/pradeep1a/Network-apps/SAP_clone
python3 seed_sap_data.py
```

### Run Validation Tests
```bash
cd /home/pradeep1a/Network-apps
python3 test_appointment_validation.py
```

---

## 📝 Integration with Appointment Flow

### Updated Appointment Flow with Validation

```
User creates appointment in Salesforce
    ↓
Appointment Number: APT-20260205-XXXXXXXX (immediate)
    ↓
ServiceNow Ticket Created: INC0010123
    ↓
Status: PENDING_AGENT_REVIEW
    ↓
╔═══════════════════════════════════════╗
║  AGENT VALIDATION (New Step)         ║
║  ✓ Check parts availability in SAP   ║
║  ✓ Find qualified technician          ║
║  ✓ Verify location/asset exists       ║
║  ✓ Confirm budget availability        ║
╚═══════════════════════════════════════╝
    ↓
Agent Approval with validated data
    ↓
Create SAP Maintenance Order (automatic)
    ↓
Complete ✅
```

---

## 🤖 Agent Integration Example

### Python Code for Agent Validation

```python
import requests

def validate_appointment(appointment_data):
    """
    Validate appointment request against SAP master data

    Args:
        appointment_data: Dict with appointment details

    Returns:
        Dict with validation result and recommendations
    """

    # Extract appointment details
    required_parts = appointment_data.get('required_parts')
    required_skills = appointment_data.get('required_skills')
    location = appointment_data.get('location')
    estimated_cost = 5000.00  # Could be calculated based on parts + labor

    # Call SAP validation API
    validation_request = {
        "required_parts": required_parts,
        "required_skills": required_skills,
        "location": location,
        "cost_center_id": "CC-HVAC-001",
        "estimated_cost": estimated_cost
    }

    response = requests.post(
        "http://localhost:4772/api/appointments/validate",
        json=validation_request
    )

    validation_result = response.json()

    # Decision logic
    if validation_result['valid']:
        # Get recommended technician
        recommended_tech = validation_result['technician_validation']['recommended_technician']

        return {
            "should_approve": True,
            "recommended_technician_id": recommended_tech['technician_id'],
            "recommended_technician_name": recommended_tech['name'],
            "validation_details": validation_result
        }
    else:
        # Cannot approve - missing resources
        return {
            "should_approve": False,
            "issues": validation_result['issues'],
            "validation_details": validation_result
        }


# Example usage
appointment = {
    "appointment_number": "APT-20260205-A7B3C9D2",
    "subject": "HVAC System Maintenance",
    "required_parts": "Air filter, Coolant",
    "required_skills": "HVAC Certified, Electrical Safety",
    "location": "Building A, Floor 3, Room 305"
}

result = validate_appointment(appointment)

if result['should_approve']:
    print(f"✅ Approve appointment")
    print(f"   Assign to: {result['recommended_technician_name']}")
else:
    print(f"❌ Cannot approve appointment")
    print(f"   Issues: {result['issues']}")
```

---

## 🎯 Validation Decision Matrix

| Validation Check | Pass | Fail | Action |
|------------------|------|------|--------|
| **Parts Available** | ✅ | ❌ | Reject if critical parts missing |
| **Technician Available** | ✅ | ❌ | Reject if no qualified tech |
| **Location Valid** | ✅ | ⚠️ | Warning only (manual override possible) |
| **Budget Sufficient** | ✅ | ❌ | Reject if over budget |

**Overall Approval Logic:**
- ✅ Approve: All critical checks pass
- ❌ Reject: Any critical check fails
- ⚠️ Manual Review: Non-critical warnings present

---

## 📂 Files Created

1. **`/home/pradeep1a/Network-apps/SAP_clone/seed_sap_data.py`**
   - Seeds SAP database with master data
   - 27 materials, 11 assets, 5 cost centers, 8 technicians

2. **`/home/pradeep1a/Network-apps/SAP_clone/backend/services/appointment_validation_service.py`**
   - Validation service with business logic
   - Methods for parts, technicians, locations, budget validation

3. **`/home/pradeep1a/Network-apps/SAP_clone/backend/api/routes/appointment_validation.py`**
   - REST API endpoints for validation
   - 7 endpoints for different validation scenarios

4. **`/home/pradeep1a/Network-apps/test_appointment_validation.py`**
   - Comprehensive test suite
   - 6 test scenarios demonstrating validation

5. **`/home/pradeep1a/Network-apps/SAP_MASTER_DATA_VALIDATION_GUIDE.md`** (this file)
   - Complete documentation

---

## 🚀 Next Steps

1. **Integrate with Salesforce Appointment Flow**
   - Add validation step before agent approval
   - Call SAP validation API from appointment approval endpoint

2. **Enhance Agent Logic**
   - Use validation results to make approval decisions
   - Provide detailed feedback on rejections

3. **Add Real-time Updates**
   - Update inventory after appointments
   - Mark technicians as busy during appointments
   - Track budget utilization

4. **Monitoring & Alerts**
   - Alert when parts fall below reorder level
   - Notify when budget utilization exceeds threshold
   - Track technician workload

---

## 📞 Support

- **API Base URL:** `http://localhost:4772/api/appointments`
- **Database:** PostgreSQL on port 4794
- **Validation Service:** `/home/pradeep1a/Network-apps/SAP_clone/backend/services/appointment_validation_service.py`
- **Test Script:** `/home/pradeep1a/Network-apps/test_appointment_validation.py`

---

**Last Updated:** 2026-02-05
**Version:** 1.0.0
