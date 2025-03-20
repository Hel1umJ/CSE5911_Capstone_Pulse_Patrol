#!/bin/bash

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Virtual environment setup
VENV_DIR="$PROJECT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if needed
if [ ! -f "$VENV_DIR/.dependencies_installed" ]; then
  echo "Installing dependencies..."
  # NORA.py dependencies
  pip install matplotlib pillow python-socketio requests tk
  # server.py dependencies
  pip install flask flask-cors flask-socketio
  # Mark dependencies as installed
  touch "$VENV_DIR/.dependencies_installed"
  echo "Dependencies installed successfully"
else
  echo "Dependencies already installed"
fi

if pgrep -f "server.py" > /dev/null; then
  echo "Web server is already running"
else
  echo "Starting Web Dashboard server..."
  cd "$PROJECT_DIR/Web_Vital_Dashboard"
  python server.py &
  SERVER_PID=$!
  echo "Server started with PID: $SERVER_PID"
  sleep 2
fi

if pgrep -f "NORA.py" > /dev/null; then
  echo "NORA GUI is already running"
else
  echo "Starting NORA GUI..."
  cd "$PROJECT_DIR/PI_Vital_Dashboard"
  python NORA.py &
  NORA_PID=$!
  echo "NORA GUI started with PID: $NORA_PID"
fi

echo "NORA system is now running!"
echo "Press Ctrl+C to stop all processes"

trap "echo 'Stopping all services...'; pkill -f 'server.py'; pkill -f 'NORA.py'; exit" INT TERM

while true; do
  sleep 1
done