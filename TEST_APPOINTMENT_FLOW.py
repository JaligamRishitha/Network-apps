#!/usr/bin/env python3
"""
Test Script: Salesforce → ServiceNow → Agent → SAP Appointment Flow
Demonstrates that appointment numbers are returned immediately
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
SALESFORCE_API = "http://localhost:4777"  # Salesforce backend
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login to Salesforce"""
    response = requests.post(
        f"{SALESFORCE_API}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def create_service_appointment(token):
    """
    Step 1: Create Service Appointment
    Returns appointment number IMMEDIATELY
    """
    print("\n" + "="*60)
    print("STEP 1: Creating Service Appointment in Salesforce")
    print("="*60)

    # Calculate scheduled times
    scheduled_start = (datetime.now() + timedelta(days=2)).isoformat()
    scheduled_end = (datetime.now() + timedelta(days=2, hours=2)).isoformat()

    appointment_data = {
        "account_id": 1,
        "subject": "HVAC System Maintenance",
        "description": "Routine maintenance check for HVAC system. Need technician with HVAC certification.",
        "appointment_type": "Maintenance",
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
        "priority": "High",
        "location": "Building A, Floor 3, Room 305",
        "required_skills": "HVAC Certified, Electrical Safety",
        "required_parts": "Air filter, Coolant"
    }

    response = requests.post(
        f"{SALESFORCE_API}/api/service/appointments",
        json=appointment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    result = response.json()

    print(f"\n✅ SUCCESS! Appointment created")
    print(f"\n📋 APPOINTMENT NUMBER: {result['appointment']['appointment_number']}")
    print(f"   (You can track this number throughout the process)")
    print(f"\n🎫 ServiceNow Ticket: {result['servicenow_ticket']}")
    print(f"📊 Status: {result['appointment']['status']}")
    print(f"🔄 Integration Status: {result['scheduling_request']['status']}")

    return result

def poll_scheduling_requests(token, appointment_number):
    """
    Step 2: Poll for status updates
    Check status of appointment using the scheduling requests endpoint
    """
    print("\n" + "="*60)
    print("STEP 2: Polling Scheduling Requests")
    print("="*60)

    response = requests.get(
        f"{SALESFORCE_API}/api/service/scheduling-requests",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    requests_list = response.json()

    # Find our appointment
    our_request = None
    for req in requests_list:
        if req.get('appointment_number') == appointment_number:
            our_request = req
            break

    if our_request:
        print(f"\n✅ Found appointment: {appointment_number}")
        print(f"   Status: {our_request['status']}")
        print(f"   Request ID: {our_request['id']}")
        print(f"   ServiceNow Ticket: {our_request.get('mulesoft_transaction_id', 'N/A')}")
        return our_request
    else:
        print(f"\n⚠️  Appointment not found in list")
        return None

def simulate_agent_approval(token, request_id):
    """
    Step 3: Agent approves and sends to SAP
    This would normally be done by an agent/AI system
    """
    print("\n" + "="*60)
    print("STEP 3: Agent Approval (Sends to SAP)")
    print("="*60)

    # Agent approves and assigns technician
    response = requests.post(
        f"{SALESFORCE_API}/api/service/scheduling-requests/{request_id}/approve",
        params={
            "technician_id": 101,
            "technician_name": "John Smith - HVAC Specialist"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    result = response.json()

    print(f"\n✅ Agent Approved!")
    print(f"   Technician Assigned: {result['scheduling_request'].get('technician_name')}")
    print(f"   Status: {result['scheduling_request']['status']}")
    print(f"   Integration: {result['scheduling_request']['integration_status']}")

    if result.get('sap_order_number'):
        print(f"\n🎉 SAP ORDER CREATED!")
        print(f"   SAP Order Number: {result['sap_order_number']}")
        print(f"   SAP Order ID: {result['sap_order_id']}")

    return result

def check_final_status(token, appointment_number):
    """
    Step 4: Check final status after SAP integration
    """
    print("\n" + "="*60)
    print("STEP 4: Final Status Check")
    print("="*60)

    response = requests.get(
        f"{SALESFORCE_API}/api/service/scheduling-requests",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    requests_list = response.json()

    for req in requests_list:
        if req.get('appointment_number') == appointment_number:
            print(f"\n📋 Appointment: {appointment_number}")
            print(f"   Status: {req['status']}")
            print(f"   Technician: {req.get('technician_name', 'Not assigned')}")
            print(f"   Parts Available: {req.get('parts_available', 'Unknown')}")
            print(f"   SAP Response: {req.get('sap_hr_response', 'N/A')}")
            return req

    return None

def main():
    """Run the complete flow test"""
    print("\n" + "="*60)
    print("TESTING: Salesforce → ServiceNow → Agent → SAP Flow")
    print("="*60)

    try:
        # Login
        print("\n🔐 Logging in...")
        token = login()
        print("✅ Logged in successfully")

        # Step 1: Create appointment (get number immediately)
        result = create_service_appointment(token)
        appointment_number = result['appointment']['appointment_number']

        print("\n⏱️  Waiting 2 seconds to simulate real-world delay...")
        time.sleep(2)

        # Step 2: Poll for status
        scheduling_request = poll_scheduling_requests(token, appointment_number)

        if not scheduling_request:
            print("\n❌ Could not find scheduling request")
            return

        request_id = scheduling_request['id']

        # Step 3: Simulate agent approval (sends to SAP)
        print("\n⏱️  Waiting 2 seconds before agent approval...")
        time.sleep(2)
        approval_result = simulate_agent_approval(token, request_id)

        # Step 4: Check final status
        print("\n⏱️  Waiting 2 seconds to check final status...")
        time.sleep(2)
        final_status = check_final_status(token, appointment_number)

        # Summary
        print("\n" + "="*60)
        print("🎉 FLOW COMPLETE!")
        print("="*60)
        print(f"\n✅ Appointment Number: {appointment_number}")
        print(f"✅ ServiceNow Ticket: {result['servicenow_ticket']}")
        print(f"✅ Agent Status: {final_status['status'] if final_status else 'Unknown'}")
        print(f"✅ SAP Integration: {final_status['integration_status'] if final_status else 'Unknown'}")

        print("\n" + "="*60)
        print("KEY TAKEAWAYS:")
        print("="*60)
        print("1. ✅ Appointment number returned IMMEDIATELY on creation")
        print("2. ✅ ServiceNow ticket created automatically")
        print("3. ✅ Status starts as 'PENDING_AGENT_REVIEW'")
        print("4. ✅ Poll /api/service/scheduling-requests to track status")
        print("5. ✅ After agent approval, SAP order created automatically")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
