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
# Install apt packages for Tkinter and PIL integration
sudo apt-get install -y python3-tk python3-pil python3-pil.imagetk

# NORA.py dependencies - install with sudo to ensure system-wide availability
sudo pip3 install --break-system-packages matplotlib pillow python-socketio requests tk
# server.py dependencies - also install with sudo for consistency
sudo pip3 install --break-system-packages flask flask-cors flask-socketio

# Install GPIO libraries and other required dependencies for Raspberry Pi
if [ "$IS_RASPBERRY_PI" = true ]; then
  echo "Installing GPIO libraries and dependencies..."
  sudo apt-get update -y
  # Install system packages - make sure we have everything needed for GPIO
  sudo apt-get install -y python3-gpiozero libopenblas0 python3-pigpio python3-rpi.gpio i2c-tools
  
  # Enable SPI and I2C interfaces if not already enabled
  sudo raspi-config nonint do_spi 0
  sudo raspi-config nonint do_i2c 0
  
  # Make sure gpio group exists and add current user to it
  if ! grep -q "^gpio:" /etc/group; then
    echo "Creating gpio group..."
    sudo groupadd gpio
  fi
  echo "Adding user to gpio group..."
  sudo usermod -a -G gpio $USER
  
  # Set permissions for GPIO, SPI, and I2C devices
  echo "Setting hardware device permissions..."
  sudo chmod a+rw /dev/gpiomem 2>/dev/null || true
  sudo chmod a+rw /dev/i2c-* 2>/dev/null || true
  sudo chmod a+rw /dev/spidev* 2>/dev/null || true
  
  # Stop and restart pigpio daemon to ensure it's running properly
  echo "Ensuring pigpio daemon is running correctly..."
  sudo systemctl stop pigpiod
  sudo systemctl enable pigpiod
  sudo systemctl start pigpiod
  # Wait a moment for the daemon to be fully started
  sleep 2
  
  # Install Python packages
  echo "Installing Python packages for GPIO access..."
  # Install Python packages using pip directly
  echo "Installing Python packages directly..."
  sudo pip3 install --break-system-packages gpiozero pigpio
  sudo pip3 install --break-system-packages adafruit-circuitpython-ads1x15
  
  # Force gpiozero to use pigpio pin factory
  echo "Setting GPIOZERO_PIN_FACTORY=pigpio"
  export GPIOZERO_PIN_FACTORY=pigpio
fi

echo "Dependencies installed successfully"


if [ "$IS_RASPBERRY_PI" = true ]; then
  # Enable SPI and I2C communication on RPI:
  echo "Enabling SPI and I2C communication on RPI..."
  sudo raspi-config nonint do_spi 0
  sudo raspi-config nonint do_i2c 0
  
  # Check if SPI is enabled correctly
  if [ -e /dev/spidev0.0 ] || [ -e /dev/spidev0.1 ]; then
    echo "SPI interface is enabled and ready"
  else
    echo "WARNING: SPI interface not detected. Please reboot and try again."
  fi
  
  # Check if I2C is enabled correctly
  if [ -e /dev/i2c-1 ]; then
    echo "I2C interface is enabled and ready"
    # Check for connected I2C devices
    echo "Checking for connected I2C devices:"
    i2cdetect -y 1
    echo "Looking for ADS1015 ADC at address 0x48"
  else
    echo "WARNING: I2C interface not detected. Please reboot and try again."
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
  # Also run server with sudo for consistency
  if [ "$IS_RASPBERRY_PI" = true ]; then
    sudo python server.py &
  else
    python server.py &
  fi
  SERVER_PID=$!
  echo "Server started with PID: $SERVER_PID"
  sleep 2
fi

if pgrep -f "NORA.py" > /dev/null; then
  echo "NORA GUI is already running"
else
  echo "Starting NORA GUI..."
  cd "$PROJECT_DIR/PI_Vital_Dashboard"
  
  # Make sure GPIOZERO_PIN_FACTORY environment variable is set
  export GPIOZERO_PIN_FACTORY=pigpio
  
  if [ "$IS_RASPBERRY_PI" = true ]; then
    echo "Running NORA with sudo for guaranteed GPIO access"
    # Run with sudo and ensuring environment variables are passed
    sudo GPIOZERO_PIN_FACTORY=pigpio python NORA.py &
    NORA_PID=$!
    echo "NORA GUI started with PID: $NORA_PID with sudo privileges"
  else
    python NORA.py &
    NORA_PID=$!
    echo "NORA GUI started with PID: $NORA_PID"
  fi
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