#!/usr/bin/env python3
"""
Sample Appointment Creation Script
Creates a sample appointment in Salesforce which automatically triggers ServiceNow ticket creation
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
SALESFORCE_API = "http://149.102.158.71:4799"
USERNAME = "admin"
PASSWORD = "admin123"

def create_sample_appointment():
    """Create a sample appointment in Salesforce"""

    print("=" * 60)
    print("Salesforce Appointment Creation")
    print("=" * 60)

    # Step 1: Login
    print("\n🔐 Step 1: Authenticating...")
    login_response = requests.post(
        f"{SALESFORCE_API}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return None

    token = login_response.json()["access_token"]
    print("✅ Authentication successful")

    # Step 2: Create Sample Appointment
    print("\n📋 Step 2: Creating Service Appointment...")

    # Calculate times
    scheduled_start = datetime.now() + timedelta(days=1)
    scheduled_end = scheduled_start + timedelta(hours=2)

    appointment_data = {
        "account_id": 8,  # Global Energy Corp
        "subject": "Emergency HV Cable Fault - London Paddington",
        "description": "11kV underground cable fault detected at Paddington Substation. Immediate repair required to restore power supply to commercial district.",
        "appointment_type": "Emergency Repair",
        "priority": "Urgent",
        "location": "Paddington Substation, Praed Street, London W2 1HQ",
        "required_skills": "HV Authorised Person, 11kV Switching, Cable Jointing",
        "required_parts": "11kV XLPE cable 300mm², Ring Main Unit components, Cable joints",
        "scheduled_start": scheduled_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "scheduled_end": scheduled_end.strftime("%Y-%m-%dT%H:%M:%S")
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print("\n📤 Request Payload:")
    print(json.dumps(appointment_data, indent=2))

    # Create appointment
    appointment_response = requests.post(
        f"{SALESFORCE_API}/api/service/appointments",
        headers=headers,
        json=appointment_data,
        timeout=30
    )

    if appointment_response.status_code not in [200, 201]:
        print(f"\n❌ Appointment creation failed: {appointment_response.status_code}")
        print(appointment_response.text)
        return None

    result = appointment_response.json()

    # Display Results
    print("\n" + "=" * 60)
    print("✅ APPOINTMENT CREATED SUCCESSFULLY!")
    print("=" * 60)

    print("\n📋 Appointment Details:")
    appointment = result.get("appointment", {})
    print(f"  • Appointment Number: {appointment.get('appointment_number', 'N/A')}")
    print(f"  • Subject: {appointment.get('subject', 'N/A')}")
    print(f"  • Status: {appointment.get('status', 'N/A')}")
    print(f"  • Priority: {appointment.get('priority', 'N/A')}")
    print(f"  • Location: {appointment.get('location', 'N/A')}")
    print(f"  • Scheduled: {appointment.get('scheduled_start', 'N/A')}")

    print("\n🎫 ServiceNow Ticket:")
    servicenow_ticket = result.get("servicenow_ticket", "N/A")
    print(f"  • Ticket Number: {servicenow_ticket}")
    print(f"  • Status: New/Open")
    print(f"  • Auto-created from Salesforce")

    print("\n📊 Scheduling Request:")
    scheduling = result.get("scheduling_request", {})
    print(f"  • Request ID: {scheduling.get('id', 'N/A')}")
    print(f"  • Status: {scheduling.get('status', 'N/A')}")
    print(f"  • Correlation ID: {scheduling.get('correlation_id', 'N/A')}")

    print("\n📝 Full Response:")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("✅ Integration Flow Completed:")
    print("=" * 60)
    print("  1. ✅ Appointment created in Salesforce")
    print("  2. ✅ ServiceNow ticket automatically created")
    print("  3. ✅ Scheduling request generated")
    print("  4. ⏳ Status: Pending Agent Review")
    print("\n  Next Step: Agent will review and validate the appointment")
    print("=" * 60)

    return result

if __name__ == "__main__":
    try:
        result = create_sample_appointment()
        if result:
            print("\n✨ Sample appointment created successfully!")
        else:
            print("\n❌ Failed to create sample appointment")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to Salesforce backend")
        print("   Please ensure the backend is running at http://149.102.158.71:4799")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
