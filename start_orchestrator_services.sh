#!/bin/bash
#
# Orchestrator Services Startup Script
# Starts both the Ticket Orchestrator and Auto-Forwarder services
#

echo "========================================================================"
echo " 🚀 Starting Orchestrator Services"
echo "========================================================================"

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f ticket_orchestrator.py 2>/dev/null
pkill -f servicenow_auto_forwarder_service.py 2>/dev/null
sleep 2

# Navigate to the correct directory
cd /home/pradeep1a/Network-apps

# Start Ticket Orchestrator
echo ""
echo "1️⃣  Starting Ticket Orchestrator..."
python3 ticket_orchestrator.py > ticket_orchestrator.log 2>&1 &
ORCH_PID=$!
sleep 5

# Verify orchestrator started
if ps -p $ORCH_PID > /dev/null; then
    echo "   ✅ Orchestrator started (PID: $ORCH_PID)"

    # Check health
    HEALTH=$(curl -s http://localhost:2486/api/health)
    if [ $? -eq 0 ]; then
        echo "   ✅ Orchestrator is healthy"
        echo "   📊 Status: $HEALTH"
    else
        echo "   ⚠️  Orchestrator may not be responding yet"
    fi
else
    echo "   ❌ Orchestrator failed to start"
    exit 1
fi

# Start Auto-Forwarder
echo ""
echo "2️⃣  Starting Auto-Forwarder Service..."
python3 servicenow_auto_forwarder_service.py > servicenow_autoforward.log 2>&1 &
FORWARD_PID=$!
sleep 3

# Verify auto-forwarder started
if ps -p $FORWARD_PID > /dev/null; then
    echo "   ✅ Auto-Forwarder started (PID: $FORWARD_PID)"
else
    echo "   ❌ Auto-Forwarder failed to start"
    echo "   📋 Check logs: tail -f servicenow_autoforward.log"
fi

# Summary
echo ""
echo "========================================================================"
echo " ✅ Services Started Successfully"
echo "========================================================================"
echo ""
echo "📡 Orchestrator:"
echo "   • URL: http://localhost:2486"
echo "   • Health: http://localhost:2486/api/health"
echo "   • Stats: http://localhost:2486/api/stats"
echo "   • Docs: http://localhost:2486/docs"
echo "   • PID: $ORCH_PID"
echo "   • Logs: tail -f ticket_orchestrator.log"
echo ""
echo "🔄 Auto-Forwarder:"
echo "   • ServiceNow: http://149.102.158.71:4780"
echo "   • Target: http://localhost:2486"
echo "   • PID: $FORWARD_PID"
echo "   • Logs: tail -f servicenow_autoforward.log"
echo ""
echo "========================================================================"
echo ""
echo "💡 Quick Commands:"
echo "   • Check status: ps aux | grep -E 'orchestrator|auto_forwarder'"
echo "   • View orchestrator logs: tail -f ticket_orchestrator.log"
echo "   • View forwarder logs: tail -f servicenow_autoforward.log"
echo "   • Stop services: pkill -f ticket_orchestrator.py; pkill -f servicenow_auto_forwarder"
echo ""
