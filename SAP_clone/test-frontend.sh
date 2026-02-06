#!/bin/bash

# SAP ERP Frontend & API Integration Test Script
# Tests all endpoints and simulates frontend behavior

echo "============================================================"
echo "  SAP ERP Frontend & API Integration Test"
echo "============================================================"
echo ""

FRONTEND_URL="http://localhost:2003"
API_URL="http://localhost:2004"
PASSED=0
FAILED=0
TOKEN=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

info() {
    echo -e "ℹ️  $1"
}

# Test 1: Frontend is accessible
echo ""
echo "=== Test 1: Frontend Accessibility ==="
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL/)
if [ "$FRONTEND_STATUS" = "200" ]; then
    pass "Frontend is accessible (HTTP $FRONTEND_STATUS)"
else
    fail "Frontend not accessible (HTTP $FRONTEND_STATUS)"
fi

# Test 2: Frontend serves React app
echo ""
echo "=== Test 2: Frontend Content ==="
FRONTEND_CONTENT=$(curl -s $FRONTEND_URL/)
if echo "$FRONTEND_CONTENT" | grep -q "SAP ERP"; then
    pass "Frontend serves SAP ERP Demo app"
else
    warn "SAP ERP title not found in response"
fi

if echo "$FRONTEND_CONTENT" | grep -q "react"; then
    pass "React app detected"
else
    warn "React not detected in response"
fi

# Test 3: Backend Health
echo ""
echo "=== Test 3: Backend Health ==="
HEALTH=$(curl -s $API_URL/health)
if echo "$HEALTH" | grep -q "healthy"; then
    pass "Backend is healthy"
    echo "   Response: $HEALTH"
else
    fail "Backend health check failed"
fi

# Test 4: Authentication
echo ""
echo "=== Test 4: Authentication (Login) ==="
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    pass "Login successful"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    info "Token obtained: ${TOKEN:0:30}..."
else
    fail "Login failed"
    echo "   Response: $LOGIN_RESPONSE"
fi

# Test 5: Tickets API (Used by PM, FI, AllTickets pages)
echo ""
echo "=== Test 5: Tickets API ==="
TICKETS=$(curl -s "$API_URL/api/v1/tickets?limit=5" -H "Authorization: Bearer $TOKEN")
TICKET_COUNT=$(echo "$TICKETS" | grep -o '"ticket_id"' | wc -l)
if [ "$TICKET_COUNT" -gt 0 ]; then
    pass "Tickets API returns data ($TICKET_COUNT tickets)"
else
    fail "Tickets API returned no data"
fi

# Test PM module filter
PM_TICKETS=$(curl -s "$API_URL/api/v1/tickets?module=PM&limit=5" -H "Authorization: Bearer $TOKEN")
if echo "$PM_TICKETS" | grep -q "PM"; then
    pass "Tickets API PM filter works"
else
    warn "PM tickets filter may not be working"
fi

# Test 6: PM Assets API
echo ""
echo "=== Test 6: PM (Plant Maintenance) APIs ==="
ASSETS=$(curl -s "$API_URL/api/v1/pm/assets?limit=5" -H "Authorization: Bearer $TOKEN")
ASSET_COUNT=$(echo "$ASSETS" | grep -o '"asset_id"' | wc -l)
if [ "$ASSET_COUNT" -gt 0 ]; then
    pass "PM Assets API returns data ($ASSET_COUNT assets)"
else
    fail "PM Assets API returned no data"
fi

# Test Maintenance Orders
ORDERS=$(curl -s "$API_URL/api/v1/pm/maintenance-orders?limit=5" -H "Authorization: Bearer $TOKEN")
if echo "$ORDERS" | grep -q "order_id\|MO-"; then
    pass "PM Maintenance Orders API works"
else
    warn "PM Maintenance Orders may be empty"
fi

# Test 7: MM Materials API
echo ""
echo "=== Test 7: MM (Materials Management) APIs ==="
MATERIALS=$(curl -s "$API_URL/api/v1/mm/materials?limit=5" -H "Authorization: Bearer $TOKEN")
MATERIAL_COUNT=$(echo "$MATERIALS" | grep -o '"material_id"' | wc -l)
if [ "$MATERIAL_COUNT" -gt 0 ]; then
    pass "MM Materials API returns data ($MATERIAL_COUNT materials)"
else
    fail "MM Materials API returned no data"
fi

# Test Requisitions
REQUISITIONS=$(curl -s "$API_URL/api/v1/mm/purchase-requisitions?limit=5" -H "Authorization: Bearer $TOKEN")
if echo "$REQUISITIONS" | grep -q "requisition_id\|REQ-\|\[\]"; then
    pass "MM Purchase Requisitions API works"
else
    warn "MM Purchase Requisitions may have issues"
fi

# Test 8: FI APIs
echo ""
echo "=== Test 8: FI (Finance) APIs ==="
COST_CENTERS=$(curl -s "$API_URL/api/v1/fi/cost-centers?limit=5" -H "Authorization: Bearer $TOKEN")
CC_COUNT=$(echo "$COST_CENTERS" | grep -o '"cost_center_id"' | wc -l)
if [ "$CC_COUNT" -gt 0 ]; then
    pass "FI Cost Centers API returns data ($CC_COUNT cost centers)"
else
    fail "FI Cost Centers API returned no data"
fi

# Test Approvals
APPROVALS=$(curl -s "$API_URL/api/v1/fi/approval-requests?limit=5" -H "Authorization: Bearer $TOKEN")
APPROVAL_COUNT=$(echo "$APPROVALS" | grep -o '"approval_id"' | wc -l)
if [ "$APPROVAL_COUNT" -gt 0 ]; then
    pass "FI Approval Requests API returns data ($APPROVAL_COUNT approvals)"
else
    warn "FI Approval Requests may be empty"
fi

# Test 9: Work Order Flow APIs
echo ""
echo "=== Test 9: Work Order Flow APIs (PM → MM → FI) ==="
WORK_ORDERS=$(curl -s "$API_URL/api/v1/work-order-flow/work-orders?limit=5" -H "Authorization: Bearer $TOKEN")
WO_COUNT=$(echo "$WORK_ORDERS" | grep -o '"work_order_id"' | wc -l)
if [ "$WO_COUNT" -gt 0 ]; then
    pass "Work Orders API returns data ($WO_COUNT work orders)"
else
    fail "Work Orders API returned no data"
fi

# Test Pending Purchase
PENDING_PURCHASE=$(curl -s "$API_URL/api/v1/work-order-flow/work-orders/pending-purchase" -H "Authorization: Bearer $TOKEN")
if echo "$PENDING_PURCHASE" | grep -q "work_orders\|total"; then
    pass "Pending Purchase API works"
else
    fail "Pending Purchase API failed"
fi

# Test Pending Approval
PENDING_APPROVAL=$(curl -s "$API_URL/api/v1/work-order-flow/work-orders/pending-approval" -H "Authorization: Bearer $TOKEN")
if echo "$PENDING_APPROVAL" | grep -q "work_orders\|total"; then
    pass "Pending Approval API works"
else
    fail "Pending Approval API failed"
fi

# Test 10: CRM Integration APIs
echo ""
echo "=== Test 10: CRM Integration APIs ==="
CRM_HEALTH=$(curl -s "$API_URL/api/v1/crm-integration/health" -H "Authorization: Bearer $TOKEN")
if echo "$CRM_HEALTH" | grep -q "healthy"; then
    pass "CRM Integration health check works"
else
    fail "CRM Integration health check failed"
fi

# Test 11: Users API
echo ""
echo "=== Test 11: Users API ==="
USERS=$(curl -s "$API_URL/api/v1/users" -H "Authorization: Bearer $TOKEN")
if echo "$USERS" | grep -q "username\|admin"; then
    pass "Users API works"
else
    warn "Users API may have issues"
fi

# Test 12: Sales API (Frontend uses /api prefix)
echo ""
echo "=== Test 12: Sales API ==="
SALES=$(curl -s "$API_URL/api/sales/orders?limit=3")
if echo "$SALES" | grep -q "order_id\|orders"; then
    pass "Sales Orders API works"
else
    warn "Sales Orders API may have issues"
fi

# Test 13: Create Operations (Simulating button clicks)
echo ""
echo "=== Test 13: Create Operations (Button Simulations) ==="

# Simulate "Create Asset" button
info "Simulating 'Create Asset' button click..."
CREATE_ASSET=$(curl -s -X POST "$API_URL/api/v1/pm/assets" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"asset_type": "transformer", "name": "Browser Test Asset", "location": "Test Lab", "installation_date": "2026-02-01", "status": "operational"}')
if echo "$CREATE_ASSET" | grep -q "asset_id"; then
    pass "Create Asset button works"
else
    fail "Create Asset failed"
fi

# Simulate "Create Material" button
info "Simulating 'Create Material' button click..."
CREATE_MATERIAL=$(curl -s -X POST "$API_URL/api/v1/mm/materials" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description": "Browser Test Material", "quantity": 100, "unit_of_measure": "EA", "reorder_level": 10, "storage_location": "Test Warehouse"}')
if echo "$CREATE_MATERIAL" | grep -q "material_id"; then
    pass "Create Material button works"
else
    fail "Create Material failed"
fi

# Simulate "Create Cost Center" button
info "Simulating 'Create Cost Center' button click..."
CREATE_CC=$(curl -s -X POST "$API_URL/api/v1/fi/cost-centers" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Browser Test CC", "budget_amount": 10000, "fiscal_year": 2026, "responsible_manager": "test_user"}')
if echo "$CREATE_CC" | grep -q "cost_center_id"; then
    pass "Create Cost Center button works"
else
    fail "Create Cost Center failed"
fi

# Test 14: Status Update Operations
echo ""
echo "=== Test 14: Status Update Operations ==="

# Get a ticket to update
TICKET_ID=$(echo "$TICKETS" | grep -o '"ticket_id":"[^"]*' | head -1 | cut -d'"' -f4)
if [ -n "$TICKET_ID" ]; then
    info "Testing status update on ticket: $TICKET_ID"
    UPDATE_STATUS=$(curl -s -X PATCH "$API_URL/api/v1/tickets/$TICKET_ID/status" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"new_status": "In Progress", "changed_by": "browser_test", "comment": "Testing status update"}')
    if echo "$UPDATE_STATUS" | grep -q "ticket_id\|status"; then
        pass "Ticket status update works"
    else
        warn "Ticket status update may have issues"
    fi
else
    warn "No ticket available for status update test"
fi

# Print Summary
echo ""
echo "============================================================"
echo "  TEST RESULTS SUMMARY"
echo "============================================================"
echo ""
echo -e "${GREEN}✅ PASSED: $PASSED${NC}"
echo -e "${RED}❌ FAILED: $FAILED${NC}"
echo ""
TOTAL=$((PASSED + FAILED))
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo "Pass Rate: $PASS_RATE% ($PASSED/$TOTAL)"
else
    echo "No tests executed"
fi
echo ""
echo "============================================================"

# Exit with appropriate code
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
