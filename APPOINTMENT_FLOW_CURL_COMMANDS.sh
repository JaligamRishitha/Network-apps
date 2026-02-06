#!/bin/bash
#
# Quick Test: Salesforce → ServiceNow → Agent → SAP Flow
# Curl commands for testing appointment flow
#

SALESFORCE_API="http://localhost:4777"
USERNAME="admin"
PASSWORD="admin123"

echo "=========================================="
echo "Appointment Flow Test with Curl"
echo "=========================================="

# Step 1: Login
echo ""
echo "Step 1: Login to Salesforce..."
LOGIN_RESPONSE=$(curl -s -X POST "${SALESFORCE_API}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  exit 1
fi

echo "✅ Logged in successfully"
echo "Token: ${TOKEN:0:20}..."

# Step 2: Create Service Appointment
echo ""
echo "=========================================="
echo "Step 2: Create Service Appointment"
echo "=========================================="

APPOINTMENT_RESPONSE=$(curl -s -X POST "${SALESFORCE_API}/api/service/appointments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "account_id": 1,
    "subject": "HVAC System Maintenance",
    "description": "Routine maintenance check for HVAC system. Need certified technician.",
    "appointment_type": "Maintenance",
    "scheduled_start": "2026-02-07T09:00:00",
    "scheduled_end": "2026-02-07T11:00:00",
    "priority": "High",
    "location": "Building A, Floor 3, Room 305",
    "required_skills": "HVAC Certified, Electrical Safety",
    "required_parts": "Air filter, Coolant"
  }')

echo ""
echo "Response:"
echo $APPOINTMENT_RESPONSE | python3 -m json.tool

# Extract appointment number
APPOINTMENT_NUMBER=$(echo $APPOINTMENT_RESPONSE | grep -o '"appointment_number":"[^"]*' | sed 's/"appointment_number":"//')
SERVICENOW_TICKET=$(echo $APPOINTMENT_RESPONSE | grep -o '"servicenow_ticket":"[^"]*' | sed 's/"servicenow_ticket":"//')

echo ""
echo "=========================================="
echo "✅ Appointment Created!"
echo "=========================================="
echo "📋 Appointment Number: ${APPOINTMENT_NUMBER}"
echo "🎫 ServiceNow Ticket: ${SERVICENOW_TICKET}"
echo "📊 Status: Pending Agent Review"

# Step 3: Poll Scheduling Requests
echo ""
echo "=========================================="
echo "Step 3: Poll Scheduling Requests"
echo "=========================================="
echo ""
echo "Waiting 3 seconds..."
sleep 3

SCHEDULING_REQUESTS=$(curl -s -X GET "${SALESFORCE_API}/api/service/scheduling-requests" \
  -H "Authorization: Bearer ${TOKEN}")

echo "All Scheduling Requests:"
echo $SCHEDULING_REQUESTS | python3 -m json.tool

# Extract request ID for our appointment
REQUEST_ID=$(echo $SCHEDULING_REQUESTS | python3 -c "
import sys, json
requests = json.load(sys.stdin)
for req in requests:
    if req.get('appointment_number') == '${APPOINTMENT_NUMBER}':
        print(req.get('id'))
        break
")

if [ -z "$REQUEST_ID" ]; then
  echo "❌ Could not find scheduling request"
  exit 1
fi

echo ""
echo "✅ Found Scheduling Request: ID=${REQUEST_ID}"

# Step 4: Agent Approval (Sends to SAP)
echo ""
echo "=========================================="
echo "Step 4: Agent Approval (Sends to SAP)"
echo "=========================================="
echo ""
echo "Simulating agent approval with technician assignment..."

APPROVAL_RESPONSE=$(curl -s -X POST \
  "${SALESFORCE_API}/api/service/scheduling-requests/${REQUEST_ID}/approve?technician_id=101&technician_name=John%20Smith%20-%20HVAC%20Specialist" \
  -H "Authorization: Bearer ${TOKEN}")

echo ""
echo "Approval Response:"
echo $APPROVAL_RESPONSE | python3 -m json.tool

SAP_ORDER=$(echo $APPROVAL_RESPONSE | grep -o '"sap_order_number":"[^"]*' | sed 's/"sap_order_number":"//')

echo ""
echo "=========================================="
echo "✅ Agent Approved!"
echo "=========================================="
echo "👨‍🔧 Technician: John Smith - HVAC Specialist"
echo "📦 SAP Order: ${SAP_ORDER}"

# Step 5: Check Final Status
echo ""
echo "=========================================="
echo "Step 5: Final Status Check"
echo "=========================================="
echo ""
echo "Waiting 2 seconds..."
sleep 2

FINAL_STATUS=$(curl -s -X GET "${SALESFORCE_API}/api/service/scheduling-requests" \
  -H "Authorization: Bearer ${TOKEN}")

echo "Final Status (All Requests):"
echo $FINAL_STATUS | python3 -m json.tool | grep -A 20 "${APPOINTMENT_NUMBER}"

# Summary
echo ""
echo "=========================================="
echo "🎉 FLOW COMPLETE!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  📋 Appointment Number: ${APPOINTMENT_NUMBER}"
echo "  🎫 ServiceNow Ticket:  ${SERVICENOW_TICKET}"
echo "  📦 SAP Order Number:   ${SAP_ORDER}"
echo ""
echo "Key Points:"
echo "  ✅ Appointment number returned IMMEDIATELY"
echo "  ✅ ServiceNow ticket created automatically"
echo "  ✅ Status: Pending Agent Review → Agent Approved"
echo "  ✅ SAP order created after agent approval"
echo ""
echo "=========================================="

# Individual curl command examples
echo ""
echo "=========================================="
echo "📚 Individual Command Examples"
echo "=========================================="
echo ""
echo "# 1. Login"
echo "curl -X POST ${SALESFORCE_API}/api/auth/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
echo ""
echo "# 2. Create Appointment (Returns number immediately)"
echo "curl -X POST ${SALESFORCE_API}/api/service/appointments \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "  -d '{\"account_id\":1,\"subject\":\"Test\",\"appointment_type\":\"Maintenance\",\"priority\":\"High\",\"scheduled_start\":\"2026-02-07T09:00:00\",\"scheduled_end\":\"2026-02-07T11:00:00\",\"location\":\"Test Location\"}'"
echo ""
echo "# 3. Poll Scheduling Requests"
echo "curl -X GET ${SALESFORCE_API}/api/service/scheduling-requests \\"
echo "  -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "# 4. Agent Approval (Creates SAP order)"
echo "curl -X POST '${SALESFORCE_API}/api/service/scheduling-requests/1/approve?technician_id=101&technician_name=John%20Smith' \\"
echo "  -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "# 5. Filter by Status"
echo "curl -X GET '${SALESFORCE_API}/api/service/scheduling-requests?status=PENDING_AGENT_REVIEW' \\"
echo "  -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "=========================================="
