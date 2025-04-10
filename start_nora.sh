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

# Install dependencies every time
echo "Installing dependencies..."
# NORA.py dependencies
pip install matplotlib pillow python-socketio requests tk
# server.py dependencies
pip install flask flask-cors flask-socketio

# Install GPIO libraries for Raspberry Pi
if [ "$IS_RASPBERRY_PI" = true ]; then
  echo "Installing GPIO libraries..."
  sudo apt-get update -y
  sudo apt-get install -y python3-gpiozero
  pip install gpiozero
fi

echo "Dependencies installed successfully"


if [ "$IS_RASPBERRY_PI" = true ]; then
  # Enable SPI communication on RPI:
  echo "Enabling SPI communication on RPI..."
  sudo raspi-config nonint do_spi 0 
  
  # Check if SPI is enabled correctly
  if [ -e /dev/spidev0.0 ] || [ -e /dev/spidev0.1 ]; then
    echo "SPI interface is enabled and ready"
  else
    echo "WARNING: SPI interface not detected. Please reboot and try again."
  fi
fi

# Check GPIO access 
if [ "$IS_RASPBERRY_PI" = true ]; then
  echo "Checking GPIO access..."
  if timeout 5 python3 -c "from gpiozero import Device; from gpiozero.pins.mock import MockFactory; from importlib import import_module; print('Testing pin factories:'); factories = ['lgpio', 'rpigpio', 'pigpio', 'native']; available = []; for f in factories: try: import_module(f); available.append(f); print(f'- {f}: AVAILABLE'); except ImportError: print(f'- {f}: NOT FOUND'); print('OK')" 2>/dev/null | grep -q "OK"; then
    echo "GPIO access test successful"
  else
    echo "WARNING: GPIO access test failed - ensure you're running with sudo"
    echo "Adding current user to gpio group for better permissions..."
    sudo usermod -a -G gpio $USER
    echo "You may need to log out and back in for this to take effect"
  fi
fi

if pgrep -f "server.py" > /dev/null; then
  echo "Web server is already running"
else
  echo "Building React frontend..."
  # Install npm if not present
  command -v npm >/dev/null || sudo apt-get install -y nodejs npm
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
  
  # GPIO cleanup is automatic
  
  exit
}

trap cleanup INT TERM

while true; do
  sleep 1
done