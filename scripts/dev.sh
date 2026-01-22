#!/bin/bash
# Development server startup script
# Runs both backend (FastAPI) and frontend (Vite) servers

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load nvm for Node.js
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Resume Analysis Development Server ===${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your OpenAI API key${NC}"
fi

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}Starting Backend (FastAPI) on http://localhost:8001${NC}"
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend server
echo -e "${GREEN}Starting Frontend (Vite) on http://localhost:3003${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!

cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}=== Servers are running ===${NC}"
echo -e "Backend API:  ${YELLOW}http://localhost:8001${NC}"
echo -e "API Docs:     ${YELLOW}http://localhost:8001/docs${NC}"
echo -e "Frontend:     ${YELLOW}http://localhost:3003${NC}"
echo ""
echo -e "Press ${RED}Ctrl+C${NC} to stop all servers"
echo ""

# Wait for both processes
wait
