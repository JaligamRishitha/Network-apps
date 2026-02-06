#!/bin/bash

# Test script to verify MuleSoft events API integration

echo "Testing MuleSoft Events API Integration"
echo "========================================"
echo ""

# Test 1: Check if MuleSoft events API is running
echo "1. Checking MuleSoft events API at localhost:3001/events..."
curl -X POST http://localhost:3001/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "message": "Testing connection"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo "2. To test the full flow:"
echo "   a. Create a Load Enhancement Request in the UI"
echo "   b. Go to FI module and approve/reject the ticket"
echo "   c. Check MuleSoft events API for the event"
echo ""
echo "3. Expected event payload at localhost:3001/events:"
echo '{
  "event_type": "ticket_status_update",
  "ticket_id": "TKT-FI-20260121-0001",
  "correlation_id": "SF-REQ-10021",
  "module": "FI",
  "status": "Approved",
  "updated_by": "admin",
  "timestamp": "2026-01-21T12:00:00",
  "comment": "Approved by admin"
}'
echo ""
echo "4. Monitor Camel logs:"
echo "   docker logs sap-erp-camel --tail 20 -f"
