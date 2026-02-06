#!/bin/bash
# Quick Start Script - Launch all services

echo "========================================="
echo "Starting Ticket System Services"
echo "========================================="

# Activate virtual environment
source /home/pradeep1a/Network-apps/mcp_venv/bin/activate

# Terminal 1: Ticket Orchestrator (Port 5001)
echo ""
echo "Starting Ticket Orchestrator on port 5001..."
python3 ticket_orchestrator.py &
ORCH_PID=$!
echo "✓ Ticket Orchestrator started (PID: $ORCH_PID)"

# Wait a bit
sleep 2

# Terminal 2: Salesforce-ServiceNow Integration (Port 8080)
echo ""
echo "Starting Salesforce-ServiceNow Integration on port 8080..."
python3 salesforce_servicenow_simple.py &
SF_PID=$!
echo "✓ Salesforce-ServiceNow Integration started (PID: $SF_PID)"

# Wait a bit
sleep 2

# Terminal 3: Mistral Agent API (Port 5000) - Optional
echo ""
echo "Starting Mistral Agent API on port 5000..."
python3 mistral_agent_api.py &
AGENT_PID=$!
echo "✓ Mistral Agent API started (PID: $AGENT_PID)"

sleep 3

echo ""
echo "========================================="
echo "All Services Running!"
echo "========================================="
echo ""
echo "API Endpoints:"
echo "  - Ticket Orchestrator: http://localhost:5001"
echo "  - Salesforce Integration: http://localhost:8080"
echo "  - Mistral Agent: http://localhost:5000"
echo ""
echo "Test endpoints:"
echo "  curl http://localhost:5001/api/stats"
echo "  curl http://localhost:5001/api/tickets"
echo "  curl http://localhost:8080/api/integration/status"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "kill $ORCH_PID $SF_PID $AGENT_PID; exit" INT
wait
