#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "Stopping VitalLink Complete System..."
echo ""

# Function to stop a service
stop_service() {
  local name=$1
  local pidfile="logs/${name}.pid"

  if [ -f "$pidfile" ]; then
    PID=$(cat "$pidfile")
    if kill -0 $PID 2>/dev/null; then
      kill $PID 2>/dev/null
      echo "✓ Stopped $name (PID: $PID)"
    else
      echo "  $name already stopped"
    fi
    rm -f "$pidfile"
  fi
}

# Stop all services
stop_service "backend"
stop_service "wristbands"
stop_service "dashboard"
stop_service "kiosk"

# Cleanup
rm -f logs/all_pids.txt

echo ""
echo "✓ VitalLink system stopped"
