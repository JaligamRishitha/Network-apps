#!/bin/bash
# Startup script for Salesforce Clone Application
# Starts both Backend API and MCP Server

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Salesforce Clone - Service Startup   ${NC}"
echo -e "${GREEN}========================================${NC}"

# Load environment variables if .env exists
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment from .env${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Default values
export API_BASE_URL=${API_BASE_URL:-"http://localhost:4799"}
export MCP_HOST=${MCP_HOST:-"0.0.0.0"}
export MCP_PORT=${MCP_PORT:-"8090"}
BACKEND_PORT=${BACKEND_PORT:-"4799"}

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Backend API Port: $BACKEND_PORT"
echo "  MCP Server Host: $MCP_HOST"
echo "  MCP Server Port: $MCP_PORT"
echo "  API Base URL (for MCP): $API_BASE_URL"
echo ""

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $MCP_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start Backend API
echo -e "${GREEN}Starting Backend API on port $BACKEND_PORT...${NC}"
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start MCP Server in HTTP mode
echo -e "${GREEN}Starting MCP Server on $MCP_HOST:$MCP_PORT...${NC}"
source mcp_venv/bin/activate 2>/dev/null || true
python mcp_server.py &
MCP_PID=$!

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Started Successfully!       ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Backend API:    http://0.0.0.0:$BACKEND_PORT"
echo -e "Backend Docs:   http://0.0.0.0:$BACKEND_PORT/docs"
echo -e "MCP Server:     http://$MCP_HOST:$MCP_PORT"
echo -e "MCP SSE Endpoint: http://$MCP_HOST:$MCP_PORT/sse"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $MCP_PID
