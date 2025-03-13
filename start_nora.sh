#!/bin/bash

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

if pgrep -f "server.py" > /dev/null; then
  echo "Web server is already running"
else
  echo "Starting Web Dashboard server..."
  cd "$PROJECT_DIR/Web_Vital_Dashboard"
  python3 server.py &
  SERVER_PID=$!
  echo "Server started with PID: $SERVER_PID"
  sleep 2
fi

if pgrep -f "NORA.py" > /dev/null; then
  echo "NORA GUI is already running"
else
  echo "Starting NORA GUI..."
  cd "$PROJECT_DIR/PI_Vital_Dashboard"
  python3 NORA.py &
  NORA_PID=$!
  echo "NORA GUI started with PID: $NORA_PID"
fi

echo "NORA system is now running!"
echo "Press Ctrl+C to stop all processes"

trap "echo 'Stopping all services...'; pkill -f 'server.py'; pkill -f 'NORA.py'; exit" INT TERM

while true; do
  sleep 1
done