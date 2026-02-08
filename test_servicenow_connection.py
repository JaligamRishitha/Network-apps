#!/usr/bin/env python3
"""
Test ServiceNow Connection and Create Sample Ticket
"""

import requests
import json

SERVICENOW_API = "http://207.180.217.117:4780"
SERVICENOW_USER = "admin@company.com"
SERVICENOW_PASSWORD = "admin123"

def get_servicenow_token():
    """Get ServiceNow access token"""
    try:
        response = requests.post(
            f"{SERVICENOW_API}/token",
            data={"username": SERVICENOW_USER, "password": SERVICENOW_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_servicenow_health():
    """Test ServiceNow backend health"""
    try:
        response = requests.get(f"{SERVICENOW_API}/health", timeout=10)
        print(f"✅ ServiceNow Health: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ ServiceNow Health Check Failed: {e}")
        return False

def create_test_ticket(token):
    """Create a test ServiceNow ticket directly"""
    try:
        ticket_params = {
            "short_description": "Test Service Appointment from Salesforce",
            "description": "Testing ServiceNow ticket creation API\n\nAppointment Number: APT-TEST-001\nType: Maintenance\nLocation: Test Location",
            "category": "request",
            "priority": "2"
        }

        print("\n📤 Creating ServiceNow Ticket...")
        print("Request Parameters:")
        print(json.dumps(ticket_params, indent=2))

        response = requests.post(
            f"{SERVICENOW_API}/api/servicenow/incidents",
            params=ticket_params,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )

        print(f"\n📥 Response Status: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"\n✅ Ticket Created Successfully!")
            print(f"   Incident ID: {result.get('incident_id')}")
            print(f"   Number: {result.get('number', result.get('incident_number'))}")
            return True
        else:
            print(f"\n❌ Ticket Creation Failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ServiceNow Connection Test")
    print("=" * 60)

    print("\n1. Testing ServiceNow Backend Health...")
    health_ok = test_servicenow_health()

    if health_ok:
        print("\n2. Authenticating with ServiceNow...")
        token = get_servicenow_token()

        if token:
            print("\n3. Testing Ticket Creation...")
            create_test_ticket(token)
        else:
            print("\n❌ Cannot proceed - Authentication failed")
    else:
        print("\n❌ Cannot proceed - ServiceNow backend is not accessible")
