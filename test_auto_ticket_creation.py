#!/usr/bin/env python3
"""
Complete End-to-End Test for Automatic ServiceNow Ticket Creation
"""
import requests
import json
from datetime import datetime, timedelta

print("\n" + "="*80)
print(" AUTOMATIC SERVICENOW TICKET CREATION - COMPLETE TEST")
print("="*80)

SALESFORCE_BASE = "http://207.180.217.117:4799"
SERVICENOW_BASE = "http://207.180.217.117:4780"

# Step 1: Check backend health
print("\n[1/5] Checking Backend Health...")
try:
    sf_health = requests.get(f"{SALESFORCE_BASE}/api/health", timeout=5)
    snow_health = requests.get(f"{SERVICENOW_BASE}/health", timeout=5)

    print(f"  ✅ Salesforce Backend: {sf_health.json()}")
    print(f"  ✅ ServiceNow Backend: {snow_health.json()}")
except Exception as e:
    print(f"  ❌ Error checking health: {e}")
    exit(1)

# Step 2: Register/Login to Salesforce
print("\n[2/5] Authenticating with Salesforce...")

# Try to register a test user (will fail if exists, which is okay)
register_data = {
    "username": "automation_test",
    "email": "automation@test.com",
    "password": "testpass123",
    "full_name": "Automation Test User"
}

requests.post(f"{SALESFORCE_BASE}/api/auth/register", json=register_data)

# Login with JSON data
login_payload = {
    "username": "automation_test",
    "password": "testpass123"
}

login_response = requests.post(
    f"{SALESFORCE_BASE}/api/auth/login",
    json=login_payload
)

if login_response.status_code != 200:
    print(f"  ❌ Login failed: {login_response.status_code}")
    print(f"  Response: {login_response.text}")
    exit(1)

token_data = login_response.json()
sf_token = token_data.get("access_token")
print(f"  ✅ Logged in successfully")
print(f"  Token: {sf_token[:30]}...")

# Step 3: Create Service Appointment (which should auto-create ServiceNow ticket)
print("\n[3/5] Creating Service Appointment...")

tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00")
appointment_data = {
    "subject": "🚨 URGENT: Production Server Down",
    "description": "Critical production server experiencing downtime. Immediate attention required.",
    "appointment_type": "Emergency Repair",
    "scheduled_start": tomorrow,
    "priority": "Urgent",
    "location": "Data Center Building A, Server Room 3",
    "required_skills": "Linux Administration, Network Troubleshooting",
    "required_parts": "Replacement drives, network cables"
}

headers = {
    "Authorization": f"Bearer {sf_token}",
    "Content-Type": "application/json"
}

appt_response = requests.post(
    f"{SALESFORCE_BASE}/api/service/appointments",
    json=appointment_data,
    headers=headers
)

if appt_response.status_code not in [200, 201]:
    print(f"  ❌ Failed to create appointment: {appt_response.status_code}")
    print(f"  Response: {appt_response.text}")
    exit(1)

appt_result = appt_response.json()
print(f"  ✅ Service Appointment Created!")
print(f"     Appointment ID: {appt_result.get('appointment', {}).get('id')}")
print(f"     Appointment Number: {appt_result.get('appointment', {}).get('appointment_number')}")
print(f"     Subject: {appt_result.get('appointment', {}).get('subject')}")
print(f"     Priority: {appt_result.get('appointment', {}).get('priority')}")

# Step 4: Check if ServiceNow ticket was created
servicenow_ticket_number = appt_result.get('servicenow_ticket')
print(f"\n[4/5] Checking ServiceNow Ticket Creation...")

if servicenow_ticket_number:
    print(f"  ✅ ServiceNow Ticket Number: {servicenow_ticket_number}")
    print(f"  🎉 AUTOMATIC TICKET CREATION SUCCESSFUL!")
else:
    print(f"  ⚠️  No ServiceNow ticket number in response")
    print(f"  This might indicate the webhook failed or returned an error")

# Step 5: Display full result
print(f"\n[5/5] Complete Result:")
print("="*80)
print(json.dumps(appt_result, indent=2))
print("="*80)

# Summary
print(f"\n" + "="*80)
print(" TEST SUMMARY")
print("="*80)
print(f"✅ Salesforce Backend: Healthy")
print(f"✅ ServiceNow Backend: Healthy")
print(f"✅ Authentication: Successful")
print(f"✅ Appointment Created: {appt_result.get('appointment', {}).get('appointment_number')}")

if servicenow_ticket_number:
    print(f"✅ ServiceNow Ticket: {servicenow_ticket_number}")
    print(f"\n🎉 SUCCESS! AUTOMATIC SERVICENOW TICKET CREATION IS WORKING! 🎉")
else:
    print(f"⚠️  ServiceNow Ticket: Not created (check backend logs)")
    print(f"\n⚠️  Integration needs debugging - ticket creation may have failed")

print("="*80 + "\n")
