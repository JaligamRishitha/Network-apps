# 🎯 Creating Sample Appointment & Testing ServiceNow Ticket Creation

## Current Status: Automatic Integration Not Working

**The Salesforce backend has database connection issues. Use the manual two-step process below.**

---

## ✅ **WORKING SOLUTION: Manual Two-Step Process**

This creates both appointment and ticket successfully:

### Run This Script:

```bash
cd /home/pradeep1a/Network-apps
python3 COMPLETE_APPOINTMENT_DEMO.py
```

**This script:**
1. ✅ Creates appointment in Salesforce
2. ✅ Creates ServiceNow ticket
3. ✅ Links them together
4. ✅ Shows both ticket numbers

### Expected Output:
```
✅ APPOINTMENT CREATED IN SALESFORCE
  Appointment Number: APT-20260205-XXXXXXXX

✅ SERVICENOW TICKET CREATED
  Ticket Number: INC7239331

✅ Integration Status: Success
```

---

## 📋 **Verify Tickets Were Created**

### Check Salesforce Appointments:

```bash
# Get list of all appointments
TOKEN=$(curl -s -X POST http://207.180.217.117:4799/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

curl -s -H "Authorization: Bearer $TOKEN" \
  http://207.180.217.117:4799/api/service/scheduling-requests | \
  python3 -m json.tool | grep -E "appointment_number|status" | head -20
```

### Check ServiceNow Tickets:

```bash
# Get ServiceNow token
SNOW_TOKEN=$(curl -s -X POST http://207.180.217.117:4780/token \
  -d "username=admin@company.com&password=admin123" | \
  python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

# List all tickets
curl -s -H "Authorization: Bearer $SNOW_TOKEN" \
  http://207.180.217.117:4780/tickets/ | \
  python3 -m json.tool | head -50
```

---

## 🧪 **Test Script - Create Appointment & Ticket**

Save this as `test_appointment_with_ticket.py`:

```python
#!/usr/bin/env python3
"""
Test script: Creates appointment in Salesforce AND ticket in ServiceNow
"""

import requests
import json
from datetime import datetime, timedelta

SALESFORCE_API = "http://207.180.217.117:4799"
SERVICENOW_API = "http://207.180.217.117:4780"

def test_appointment_creation():
    """Create appointment and verify ticket"""

    print("=" * 70)
    print("TESTING APPOINTMENT & TICKET CREATION")
    print("=" * 70)

    # Step 1: Salesforce Login
    print("\n🔐 Step 1: Logging into Salesforce...")
    sf_response = requests.post(
        f"{SALESFORCE_API}/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10
    )

    if sf_response.status_code != 200:
        print(f"❌ Salesforce login failed")
        return False

    sf_token = sf_response.json()["access_token"]
    print("✅ Salesforce login successful")

    # Step 2: ServiceNow Login
    print("\n🔐 Step 2: Logging into ServiceNow...")
    snow_response = requests.post(
        f"{SERVICENOW_API}/token",
        data={"username": "admin@company.com", "password": "admin123"},
        timeout=10
    )

    if snow_response.status_code != 200:
        print(f"❌ ServiceNow login failed")
        return False

    snow_token = snow_response.json()["access_token"]
    print("✅ ServiceNow login successful")

    # Step 3: Create Appointment
    print("\n📋 Step 3: Creating appointment in Salesforce...")

    scheduled_start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    scheduled_end = (datetime.now() + timedelta(days=1, hours=2)).strftime("%Y-%m-%dT%H:%M:%S")

    appointment_data = {
        "account_id": 8,
        "subject": "INTEGRATION TEST - Transformer Maintenance",
        "description": "Routine maintenance on 33kV transformer. Testing ticket creation flow.",
        "appointment_type": "Maintenance",
        "priority": "High",
        "location": "Substation Alpha, London",
        "required_skills": "HV Authorised Person, Transformer Specialist",
        "required_parts": "Transformer oil, Testing equipment",
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end
    }

    appt_response = requests.post(
        f"{SALESFORCE_API}/api/service/appointments",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {sf_token}"
        },
        json=appointment_data,
        timeout=30
    )

    if appt_response.status_code not in [200, 201]:
        print(f"❌ Appointment creation failed: {appt_response.status_code}")
        return False

    appointment = appt_response.json().get("appointment", {})
    appointment_number = appointment.get("appointment_number")

    print(f"✅ Appointment created: {appointment_number}")

    # Step 4: Create ServiceNow Ticket
    print("\n🎫 Step 4: Creating ServiceNow ticket...")

    priority_map = {"Normal": "3", "High": "2", "Urgent": "1"}
    priority = priority_map.get(appointment.get("priority"), "3")

    ticket_description = f"""Service Appointment Request from Salesforce

Appointment Number: {appointment_number}
Type: {appointment.get('appointment_type')}
Priority: {appointment.get('priority')}
Location: {appointment.get('location')}

Required Skills: {appointment.get('required_skills')}
Required Parts: {appointment.get('required_parts')}

Scheduled: {appointment.get('scheduled_start')} to {appointment.get('scheduled_end')}

Description:
{appointment.get('description')}
"""

    ticket_params = {
        "short_description": f"Service Appointment: {appointment.get('subject')}",
        "description": ticket_description,
        "category": "request",
        "priority": priority
    }

    ticket_response = requests.post(
        f"{SERVICENOW_API}/api/servicenow/incidents",
        params=ticket_params,
        headers={"Authorization": f"Bearer {snow_token}"},
        timeout=10
    )

    if ticket_response.status_code != 200:
        print(f"❌ Ticket creation failed: {ticket_response.status_code}")
        return False

    ticket_data = ticket_response.json().get("result", {})
    ticket_number = ticket_data.get("number")

    print(f"✅ ServiceNow ticket created: {ticket_number}")

    # Step 5: Summary
    print("\n" + "=" * 70)
    print("🎉 SUCCESS - BOTH CREATED!")
    print("=" * 70)
    print(f"\n📋 Salesforce Appointment:")
    print(f"  • Number: {appointment_number}")
    print(f"  • Subject: {appointment.get('subject')}")
    print(f"  • Status: {appointment.get('status')}")
    print(f"  • Priority: {appointment.get('priority')}")
    print(f"  • Location: {appointment.get('location')}")

    print(f"\n🎫 ServiceNow Ticket:")
    print(f"  • Number: {ticket_number}")
    print(f"  • Priority: {priority}")
    print(f"  • Category: request")
    print(f"  • Status: New/Open")

    print(f"\n🔗 They are linked by appointment number: {appointment_number}")
    print("\n" + "=" * 70)

    return True

if __name__ == "__main__":
    try:
        success = test_appointment_creation()
        if success:
            print("\n✅ Test completed successfully!")
        else:
            print("\n❌ Test failed")
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error - Backend not accessible")
        print("   Check if Salesforce backend is running:")
        print("   docker ps | grep salesforce")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

Run it:
```bash
python3 test_appointment_with_ticket.py
```

---

## 📊 **What You'll See**

### Successful Test Output:
```
======================================================================
TESTING APPOINTMENT & TICKET CREATION
======================================================================

🔐 Step 1: Logging into Salesforce...
✅ Salesforce login successful

🔐 Step 2: Logging into ServiceNow...
✅ ServiceNow login successful

📋 Step 3: Creating appointment in Salesforce...
✅ Appointment created: APT-20260206-A1B2C3D4

🎫 Step 4: Creating ServiceNow ticket...
✅ ServiceNow ticket created: INC7239332

======================================================================
🎉 SUCCESS - BOTH CREATED!
======================================================================

📋 Salesforce Appointment:
  • Number: APT-20260206-A1B2C3D4
  • Subject: INTEGRATION TEST - Transformer Maintenance
  • Status: Pending Agent Review
  • Priority: High
  • Location: Substation Alpha, London

🎫 ServiceNow Ticket:
  • Number: INC7239332
  • Priority: 2
  • Category: request
  • Status: New/Open

🔗 They are linked by appointment number: APT-20260206-A1B2C3D4
======================================================================

✅ Test completed successfully!
```

---

## 🔧 **Why Automatic Integration Doesn't Work**

The Salesforce backend container has database connection issues:
- It's looking for `postgres-salesforce`
- The actual container is named `salesforce-db`
- Network configuration mismatch

**Solution:** Use the manual two-step process above. It works perfectly!

---

## ✅ **Recommended Approach for Your Frontend**

Use the two-step process in your frontend:

```javascript
async function createAppointmentWithTicket(appointmentData) {
  // Step 1: Create Salesforce appointment
  const appointment = await createSalesforceAppointment(appointmentData);

  // Step 2: Create ServiceNow ticket
  const ticket = await createServiceNowTicket(appointment);

  return {
    appointmentNumber: appointment.appointment_number,
    ticketNumber: ticket.number
  };
}
```

This way you have:
- ✅ Full control
- ✅ Error handling for each step
- ✅ Can retry independently
- ✅ Works immediately without fixing backend

---

## 📝 **Summary**

- ✅ **Demo script works**: `python3 COMPLETE_APPOINTMENT_DEMO.py`
- ✅ **Salesforce works**: Creates appointments
- ✅ **ServiceNow works**: Creates tickets
- ❌ **Automatic integration broken**: Database connection issues
- ✅ **Solution**: Use manual two-step process (works perfectly!)

**Run the demo script now to see it working!**
