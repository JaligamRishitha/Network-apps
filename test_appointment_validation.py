#!/usr/bin/env python3
"""
Test Script: Agent Validation of Appointment Requests against SAP Master Data
Demonstrates how agents validate parts, technicians, locations, and budget
"""

import requests
import json
from typing import Dict

# API URLs
SAP_API = "http://localhost:4772"  # SAP backend

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_validation_result(result: Dict):
    """Pretty print validation results"""
    print(f"\n{'='*80}")
    print(f"Validation Status: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
    print(f"{'='*80}")

    # Parts Validation
    if result.get('parts_validation'):
        parts = result['parts_validation']
        print(f"\n📦 PARTS VALIDATION:")
        print(f"   All Available: {'✅ Yes' if parts.get('all_available') else '❌ No'}")
        if parts.get('parts_status'):
            for part_status in parts['parts_status']:
                status_icon = "✅" if part_status['available'] else "❌"
                print(f"   {status_icon} {part_status['part']}: Qty {part_status.get('quantity', 0)}")
                if part_status.get('storage_location'):
                    print(f"      Location: {part_status['storage_location']}")
        if parts.get('issues'):
            print(f"\n   ⚠️  Issues:")
            for issue in parts['issues']:
                print(f"      • {issue}")

    # Technician Validation
    if result.get('technician_validation'):
        tech = result['technician_validation']
        print(f"\n👨‍🔧 TECHNICIAN VALIDATION:")
        print(f"   Available: {'✅ Yes' if tech.get('technicians_available') else '❌ No'}")
        if tech.get('recommended_technician'):
            recommended = tech['recommended_technician']
            print(f"\n   ✅ Recommended Technician:")
            print(f"      Name: {recommended['name']}")
            print(f"      ID: {recommended['technician_id']}")
            print(f"      Level: {recommended['certification_level']}")
            print(f"      Skills: {recommended['skills']}")
            print(f"      Territory: {recommended['assigned_territory']}")
            print(f"      Contact: {recommended['phone']}")
        if tech.get('matching_technicians'):
            print(f"\n   Available Technicians: {len(tech['matching_technicians'])}")

    # Location Validation
    if result.get('location_validation'):
        loc = result['location_validation']
        print(f"\n📍 LOCATION VALIDATION:")
        print(f"   Found: {'✅ Yes' if loc.get('location_found') else '❌ No'}")
        if loc.get('nearest_asset'):
            asset = loc['nearest_asset']
            print(f"\n   ✅ Nearest Asset:")
            print(f"      Asset ID: {asset['asset_id']}")
            print(f"      Name: {asset['name']}")
            print(f"      Location: {asset['location']}")
            print(f"      Status: {asset['status']}")

    # Budget Validation
    if result.get('budget_validation'):
        budget = result['budget_validation']
        print(f"\n💰 BUDGET VALIDATION:")
        print(f"   Sufficient: {'✅ Yes' if budget.get('budget_sufficient') else '❌ No'}")
        if budget.get('cost_center'):
            cc = budget['cost_center']
            print(f"\n   Cost Center: {cc['cost_center_id']} - {cc['name']}")
            print(f"   Allocated: ${cc['budget_allocated']:,.2f}")
            print(f"   Spent: ${cc['budget_spent']:,.2f}")
            print(f"   Available: ${budget['available_budget']:,.2f}")
            print(f"   Utilization: {budget['budget_utilization']}%")
            print(f"   Manager: {cc['responsible_manager']}")

    # Issues & Recommendations
    if result.get('issues'):
        print(f"\n❌ ISSUES:")
        for issue in result['issues']:
            print(f"   • {issue}")

    if result.get('recommendations'):
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in result['recommendations']:
            print(f"   • {rec}")

    print("="*80)


def test_scenario_1_valid_request():
    """Test Scenario 1: Valid appointment with all requirements met"""
    print_section("SCENARIO 1: Valid HVAC Appointment Request")

    appointment_request = {
        "required_parts": "Air filter, Coolant",
        "required_skills": "HVAC Certified, Electrical Safety",
        "location": "Building A, Floor 3",
        "cost_center_id": "CC-HVAC-001",
        "estimated_cost": 5000.00
    }

    print("\n📋 Appointment Request:")
    print(f"   Parts Needed: {appointment_request['required_parts']}")
    print(f"   Skills Required: {appointment_request['required_skills']}")
    print(f"   Location: {appointment_request['location']}")
    print(f"   Cost Center: {appointment_request['cost_center_id']}")
    print(f"   Estimated Cost: ${appointment_request['estimated_cost']:,.2f}")

    print("\n🔍 Validating against SAP master data...")

    try:
        response = requests.post(
            f"{SAP_API}/api/appointments/validate",
            json=appointment_request,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()

        print_validation_result(result)

    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_scenario_2_missing_parts():
    """Test Scenario 2: Appointment with unavailable parts"""
    print_section("SCENARIO 2: Appointment with Unavailable Parts")

    appointment_request = {
        "required_parts": "Flux Capacitor, Dilithium Crystals",
        "required_skills": "HVAC Certified",
        "location": "Building B",
        "cost_center_id": "CC-HVAC-001",
        "estimated_cost": 3000.00
    }

    print("\n📋 Appointment Request:")
    print(f"   Parts Needed: {appointment_request['required_parts']}")
    print(f"   Skills Required: {appointment_request['required_skills']}")
    print(f"   Location: {appointment_request['location']}")

    print("\n🔍 Validating against SAP master data...")

    try:
        response = requests.post(
            f"{SAP_API}/api/appointments/validate",
            json=appointment_request
        )
        response.raise_for_status()
        result = response.json()

        print_validation_result(result)

    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_scenario_3_no_qualified_technician():
    """Test Scenario 3: Appointment requiring unavailable skills"""
    print_section("SCENARIO 3: Appointment Requiring Unavailable Skills")

    appointment_request = {
        "required_parts": "Air filter",
        "required_skills": "Nuclear Engineering, Rocket Science",
        "location": "Building A",
        "cost_center_id": "CC-HVAC-001",
        "estimated_cost": 2000.00
    }

    print("\n📋 Appointment Request:")
    print(f"   Parts Needed: {appointment_request['required_parts']}")
    print(f"   Skills Required: {appointment_request['required_skills']}")

    print("\n🔍 Validating against SAP master data...")

    try:
        response = requests.post(
            f"{SAP_API}/api/appointments/validate",
            json=appointment_request
        )
        response.raise_for_status()
        result = response.json()

        print_validation_result(result)

    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_scenario_4_insufficient_budget():
    """Test Scenario 4: Appointment exceeding budget"""
    print_section("SCENARIO 4: Appointment Exceeding Available Budget")

    appointment_request = {
        "required_parts": "Air filter, Coolant",
        "required_skills": "HVAC Certified",
        "location": "Building A",
        "cost_center_id": "CC-BLDGB-001",
        "estimated_cost": 500000.00  # Way over budget
    }

    print("\n📋 Appointment Request:")
    print(f"   Cost Center: {appointment_request['cost_center_id']}")
    print(f"   Estimated Cost: ${appointment_request['estimated_cost']:,.2f}")

    print("\n🔍 Validating against SAP master data...")

    try:
        response = requests.post(
            f"{SAP_API}/api/appointments/validate",
            json=appointment_request
        )
        response.raise_for_status()
        result = response.json()

        print_validation_result(result)

    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_scenario_5_search_parts():
    """Test Scenario 5: Search for available parts"""
    print_section("SCENARIO 5: Search for Available HVAC Parts")

    search_query = "thermostat"

    print(f"\n🔍 Searching for: '{search_query}'")

    try:
        response = requests.get(
            f"{SAP_API}/api/appointments/parts/search",
            params={"query": search_query}
        )
        response.raise_for_status()
        result = response.json()

        print(f"\n📦 Found {len(result['parts_found'])} matching parts:\n")
        for part in result['parts_found']:
            if part['available']:
                print(f"   ✅ {part['part']}")
                print(f"      Material ID: {part['material_id']}")
                print(f"      Quantity: {part['quantity']}")
                print(f"      Location: {part['storage_location']}")
                print()

    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_scenario_6_list_technicians():
    """Test Scenario 6: List available technicians"""
    print_section("SCENARIO 6: List Available Technicians")

    try:
        response = requests.get(f"{SAP_API}/api/appointments/technicians/available")
        response.raise_for_status()
        result = response.json()

        print(f"\n👨‍🔧 Found {result['count']} available technicians:\n")
        for tech in result['technicians']:
            print(f"   ✅ {tech['name']} (ID: {tech['technician_id']})")
            print(f"      Level: {tech['certification_level']}")
            print(f"      Skills: {tech['skills']}")
            print(f"      Territory: {tech['assigned_territory']}")
            print(f"      Contact: {tech['phone']}")
            print()

    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("  APPOINTMENT VALIDATION TEST SUITE")
    print("  Validating Appointment Requests against SAP Master Data")
    print("="*80)

    # Run test scenarios
    test_scenario_1_valid_request()
    input("\n\nPress Enter to continue to next scenario...")

    test_scenario_2_missing_parts()
    input("\n\nPress Enter to continue to next scenario...")

    test_scenario_3_no_qualified_technician()
    input("\n\nPress Enter to continue to next scenario...")

    test_scenario_4_insufficient_budget()
    input("\n\nPress Enter to continue to next scenario...")

    test_scenario_5_search_parts()
    input("\n\nPress Enter to continue to next scenario...")

    test_scenario_6_list_technicians()

    print("\n" + "="*80)
    print("  ✅ ALL TEST SCENARIOS COMPLETE")
    print("="*80)
    print("\n🎯 Key Takeaways:")
    print("  • Agents can validate parts availability in real-time")
    print("  • Agents can find qualified technicians with required skills")
    print("  • Agents can verify location/asset existence")
    print("  • Agents can check budget constraints")
    print("  • All validation happens against SAP master data")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
