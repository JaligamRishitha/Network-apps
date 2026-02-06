#!/bin/bash
# Electricity Load Request API - cURL Examples
# Make this file executable: chmod +x curl_examples.sh

BASE_URL="http://localhost:8000/api/integration"

echo "=========================================="
echo "Electricity Load Request API - Test Suite"
echo "=========================================="
echo ""

# Test 1: Small residential load (PM only)
echo "Test 1: Small Residential Load (3kW → 5kW)"
echo "Expected: PM ticket only, Cost: ₹10,000"
echo "------------------------------------------"
curl -X POST "$BASE_URL/mulesoft/load-request" \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-10001",
    "CustomerID": "CUST-10001",
    "CurrentLoad": 3,
    "RequestedLoad": 5,
    "ConnectionType": "RESIDENTIAL",
    "City": "Mumbai",
    "PinCode": "400001"
  }' | jq '.'
echo ""
echo ""

# Test 2: Medium residential load (PM + FI)
echo "Test 2: Medium Residential Load (5kW → 10kW)"
echo "Expected: PM + FI tickets, Cost: ₹17,500"
echo "------------------------------------------"
curl -X POST "$BASE_URL/mulesoft/load-request" \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-10002",
    "CustomerID": "CUST-10002",
    "CurrentLoad": 5,
    "RequestedLoad": 10,
    "ConnectionType": "RESIDENTIAL",
    "City": "Delhi",
    "PinCode": "110001"
  }' | jq '.'
echo ""
echo ""

# Test 3: Large commercial load (PM + FI + MM)
echo "Test 3: Large Commercial Load (10kW → 30kW)"
echo "Expected: PM + FI + MM tickets, Cost: ₹75,000"
echo "------------------------------------------"
curl -X POST "$BASE_URL/mulesoft/load-request" \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "SF-REQ-10003",
    "CustomerID": "CUST-10003",
    "CurrentLoad": 10,
    "RequestedLoad": 30,
    "ConnectionType": "COMMERCIAL",
    "City": "Bangalore",
    "PinCode": "560001"
  }' | jq '.'
echo ""
echo ""

# Test 4: XML format - Residential
echo "Test 4: XML Format - Residential (5kW → 15kW)"
echo "Expected: PM + FI tickets, Cost: ₹30,000"
echo "------------------------------------------"
curl -X POST "$BASE_URL/mulesoft/load-request/xml" \
  -H "Content-Type: application/xml" \
  -d '<ElectricityLoadRequest>
    <RequestID>SF-REQ-10004</RequestID>
    <CustomerID>CUST-10004</CustomerID>
    <CurrentLoad>5</CurrentLoad>
    <RequestedLoad>15</RequestedLoad>
    <ConnectionType>RESIDENTIAL</ConnectionType>
    <City>Chennai</City>
    <PinCode>600001</PinCode>
</ElectricityLoadRequest>' | jq '.'
echo ""
echo ""

# Test 5: XML format - Large commercial
echo "Test 5: XML Format - Large Commercial (15kW → 40kW)"
echo "Expected: PM + FI + MM tickets, Cost: ₹92,500"
echo "------------------------------------------"
curl -X POST "$BASE_URL/mulesoft/load-request/xml" \
  -H "Content-Type: application/xml" \
  -d '<ElectricityLoadRequest>
    <RequestID>SF-REQ-10005</RequestID>
    <CustomerID>CUST-10005</CustomerID>
    <CurrentLoad>15</CurrentLoad>
    <RequestedLoad>40</RequestedLoad>
    <ConnectionType>COMMERCIAL</ConnectionType>
    <City>Hyderabad</City>
    <PinCode>500081</PinCode>
</ElectricityLoadRequest>' | jq '.'
echo ""
echo ""

# Verify tickets created
echo "=========================================="
echo "Verifying Tickets Created"
echo "=========================================="
echo ""

echo "PM Tickets:"
echo "-----------"
curl -s "http://localhost:8000/api/v1/pm/tickets" | jq '.tickets[] | {ticket_id, title, status, priority}'
echo ""

echo "FI Tickets:"
echo "-----------"
curl -s "http://localhost:8000/api/v1/fi/tickets" | jq '.tickets[] | {ticket_id, title, status, priority}'
echo ""

echo "MM Tickets:"
echo "-----------"
curl -s "http://localhost:8000/api/v1/mm/tickets" | jq '.tickets[] | {ticket_id, title, status, priority}'
echo ""

echo "=========================================="
echo "Test Suite Complete!"
echo "=========================================="
