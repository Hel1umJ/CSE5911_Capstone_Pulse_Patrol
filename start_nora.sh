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

# Check if running on a Raspberry Pi
IS_RASPBERRY_PI=false
if [[ $(uname -m) == arm* ]] || [[ $(uname -m) == aarch* ]]; then
  IS_RASPBERRY_PI=true
fi

# Install dependencies if needed
if [ ! -f "$VENV_DIR/.dependencies_installed" ]; then
  echo "Installing dependencies..."
  # NORA.py dependencies
  pip install matplotlib pillow python-socketio requests tk
  # server.py dependencies
  pip install flask flask-cors flask-socketio
  
  # Install pigpio if on Raspberry Pi
  if [ "$IS_RASPBERRY_PI" = true ]; then
    echo "Installing pigpio for Raspberry Pi..."
    sudo apt-get update -y
    sudo apt-get install -y pigpio python3-pigpio
    pip install pigpio
  fi
  
  # Mark dependencies as installed
  touch "$VENV_DIR/.dependencies_installed"
  echo "Dependencies installed successfully"
else
  echo "Dependencies already installed"
fi

# Start pigpio daemon if on Raspberry Pi
if [ "$IS_RASPBERRY_PI" = true ]; then
  if ! pgrep pigpiod > /dev/null; then
    echo "Starting pigpio daemon..."
    sudo pigpiod
    sleep 1
  else
    echo "pigpio daemon is already running"
  fi
fi

if pgrep -f "server.py" > /dev/null; then
  echo "Web server is already running"
else
  echo "Building React frontend..."
  cd "$PROJECT_DIR/Web_Vital_Dashboard"
  npm install
  npm run build
  
  echo "Starting Web Dashboard server..."
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

cleanup() {
  echo "Stopping all services..."
  pkill -f 'server.py'
  pkill -f 'NORA.py'
  
  # Let processes terminate properly
  sleep 1
  
  # Stop pigpio daemon if on Raspberry Pi
  if [ "$IS_RASPBERRY_PI" = true ]; then
    if pgrep pigpiod > /dev/null; then
      echo "Stopping pigpio daemon..."
      sudo killall pigpiod
    fi
  fi
  
  exit
}

trap cleanup INT TERM

while true; do
  sleep 1
done