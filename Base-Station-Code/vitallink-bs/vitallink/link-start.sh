#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat <<"EOF"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║  ██╗   ██╗██╗████████╗ █████╗ ██╗     ██╗     ██╗███╗   ██╗██╗  ██╗      ║
║  ██║   ██║██║╚══██╔══╝██╔══██╗██║     ██║     ██║████╗  ██║██║ ██╔╝      ║
║  ██║   ██║██║   ██║   ███████║██║     ██║     ██║██╔██╗ ██║█████╔╝       ║
║  ╚██╗ ██╔╝██║   ██║   ██╔══██║██║     ██║     ██║██║╚██╗██║██╔═██╗       ║
║   ╚████╔╝ ██║   ██║   ██║  ██║███████╗███████╗██║██║ ╚████║██║  ██╗      ║
║    ╚═══╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝      ║
║                                                                          ║
║                     Complete System Startup                              ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}Starting VitalLink Complete System...${NC}\n"

# Create logs directory
mkdir -p logs

# Activate Python virtual environment
echo -e "${BLUE}[1/5]${NC} Activating Python environment..."
source .venv/bin/activate

# Start Backend
echo -e "${BLUE}[2/5]${NC} Starting Backend API..."
python backend/server.py >logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID >logs/backend.pid
echo -e "      ${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
sleep 3

# Start Wristband System
echo -e "${BLUE}[3/5]${NC} Starting Wristband Management System..."
python simulator/main_runner.py >logs/wristbands.log 2>&1 &
WRISTBAND_PID=$!
echo $WRISTBAND_PID >logs/wristbands.pid
echo -e "      ${GREEN}✓${NC} Wristband system started (PID: $WRISTBAND_PID)"
sleep 2

# Start Dashboard Frontend
echo -e "${BLUE}[4/5]${NC} Starting Staff Dashboard..."
cd frontend/dashboard
npm run dev >../../logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID >../../logs/dashboard.pid
cd ../..
echo -e "      ${GREEN}✓${NC} Dashboard started (PID: $DASHBOARD_PID)"
sleep 2

# Start Kiosk Frontend
echo -e "${BLUE}[5/5]${NC} Starting Check-in Kiosk..."
cd frontend/kiosk
npm run dev >../../logs/kiosk.log 2>&1 &
KIOSK_PID=$!
echo $KIOSK_PID >../../logs/kiosk.pid
cd ../..
echo -e "      ${GREEN}✓${NC} Kiosk started (PID: $KIOSK_PID)"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    ✅ VitalLink System Running!                       ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📊 Access Points:${NC}"
echo -e "  ${BLUE}•${NC} Backend API:        http://localhost:8000"
echo -e "  ${BLUE}•${NC} API Documentation:  http://localhost:8000/docs"
echo -e "  ${BLUE}•${NC} Staff Dashboard:    http://localhost:5173"
echo -e "  ${BLUE}•${NC} Check-in Kiosk:     http://localhost:5174"
echo ""
echo -e "${YELLOW}📝 View Logs:${NC}"
echo -e "  ${BLUE}•${NC} Backend:     tail -f logs/backend.log"
echo -e "  ${BLUE}•${NC} Wristbands:  tail -f logs/wristbands.log"
echo -e "  ${BLUE}•${NC} Dashboard:   tail -f logs/dashboard.log"
echo -e "  ${BLUE}•${NC} Kiosk:       tail -f logs/kiosk.log"
echo ""
echo -e "${YELLOW}🔧 System Features:${NC}"
echo -e "  ${GREEN}✓${NC} Auto-assigns wristbands when patients check in"
echo -e "  ${GREEN}✓${NC} Prefers real wristbands over simulated"
echo -e "  ${GREEN}✓${NC} Creates emergency simulated bands if needed"
echo -e "  ${GREEN}✓${NC} Real-time monitoring and updates"
echo ""
echo -e "${YELLOW}🛑 Stop System:${NC}"
echo -e "  ${BLUE}•${NC} Run: ./stop_everything.sh"
echo -e "  ${BLUE}•${NC} Or press Ctrl+C (will stop all services)"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Save all PIDs for easy cleanup
cat >logs/all_pids.txt <<PIDSEOF
$BACKEND_PID
$WRISTBAND_PID
$DASHBOARD_PID
$KIOSK_PID
PIDSEOF

echo -e "${BLUE}Tip:${NC} Open http://localhost:5174 to check in a patient and watch it appear on http://localhost:5173"
echo ""

# Optional: Wait for user interrupt
# read -p "Press Enter to stop all services..."
# ./stop_everything.sh
