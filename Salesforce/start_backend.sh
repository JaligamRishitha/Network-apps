#!/bin/bash

# Start Backend Script
cd /home/pradeep1a/Network-apps/Salesforce/backend

# Kill existing process if running
lsof -ti:4799 | xargs kill -9 2>/dev/null

# Create logs directory if it doesn't exist
mkdir -p logs

# Start backend
echo "Starting Salesforce backend on port 4799..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 4799 --reload > logs/backend.log 2>&1 &

# Wait for startup
sleep 3

# Check if running
if curl -s http://localhost:4799/api/health | grep -q "healthy"; then
    echo "✅ Backend started successfully!"
    echo "   URL: http://localhost:4799"
    echo "   Logs: tail -f logs/backend.log"
else
    echo "❌ Backend failed to start"
    echo "   Check logs: tail -f logs/backend.log"
    exit 1
fi
