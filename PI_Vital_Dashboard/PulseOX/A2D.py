#!/usr/bin/env python3

import time
import platform

# Check if running on a Raspberry Pi
is_raspberry_pi = platform.system() == "Linux" and platform.machine().startswith(("arm", "aarch"))

# Import GPIO libraries if on Raspberry Pi
if is_raspberry_pi:
    try:
        from gpiozero import MCP3008
        from gpiozero.pins.rpigpio import RPiGPIOFactory
        from gpiozero.pins.lgpio import LGPIOFactory
        from gpiozero.pins.pigpio import PiGPIOFactory
        from gpiozero.pins.native import NativeFactory
        
        # Import backend libraries directly to ensure they're available
        try:
            import RPi.GPIO
            print("RPi.GPIO imported successfully")
        except ImportError:
            print("RPi.GPIO not available")
            
        try:
            import lgpio
            print("lgpio imported successfully")
        except ImportError:
            print("lgpio not available")
            
        try:
            import pigpio
            print("pigpio imported successfully")
        except ImportError:
            print("pigpio not available")
            
        print("Running on Raspberry Pi. gpiozero imported successfully.")
    except ImportError as e:
        print(f"Warning: GPIO import error: {e}")
        print("Analog reading will be simulated.")
        is_raspberry_pi = False
else:
    print("Not running on Raspberry Pi. Analog reading will be simulated.")

# MCP3008 Pin Configuration (same as NORA.py)
PULSEOX_SPI_DIN = 12   # Data in
PULSEOX_SPI_DOUT = 13  # Data out
PULSEOX_SPI_CLK = 14   # Clock
PULSEOX_SPI_CS = 10    # Data channel select pin

# Function to initialize MCP3008 with different GPIO backends
def initialize_mcp3008(channel=0):
    """
    Initialize the MCP3008 with different GPIO backends
    
    Args:
        channel: The MCP3008 channel to read from (0-7)
        
    Returns:
        The MCP3008 object if successful, None otherwise
    """
    if not is_raspberry_pi:
        print("Running in simulation mode - MCP3008 initialization skipped")
        return None
        
    # Try each pin factory in succession, starting with the most modern ones
    factories = [
        ('LGPIOFactory', LGPIOFactory),
        ('RPiGPIOFactory', RPiGPIOFactory),
        ('PiGPIOFactory', PiGPIOFactory),
        ('NativeFactory', NativeFactory)
    ]
    
    for factory_name, factory_class in factories:
        try:
            print(f"Trying {factory_name} for MCP3008...")
            pin_factory = factory_class()
            
            # Initialize MCP3008 with explicit pin factory and pin configuration
            adc = MCP3008(
                channel=channel,
                clock_pin=PULSEOX_SPI_CLK,
                mosi_pin=PULSEOX_SPI_DIN,
                miso_pin=PULSEOX_SPI_DOUT,
                select_pin=PULSEOX_SPI_CS,
                pin_factory=pin_factory
            )
            print(f"MCP3008 initialized successfully on channel {channel} using {factory_name}")
            print(f"Using pins: CLK={PULSEOX_SPI_CLK}, MOSI={PULSEOX_SPI_DIN}, MISO={PULSEOX_SPI_DOUT}, CS={PULSEOX_SPI_CS}")
            return adc
        except Exception as e:
            print(f"Failed to initialize MCP3008 with {factory_name}: {e}")
    
    # If we get here, all attempts failed
    print("\nMCP3008 initialization failed with all pin factories!")
    print("Possible solutions:")
    print("1. Ensure you have GPIO libraries installed:")
    print("   sudo apt-get install python3-lgpio python3-rpi.gpio")
    print("   sudo pip install RPi.GPIO lgpio")
    print("2. Try running with sudo")
    print("3. Verify GPIO permissions (run sudo usermod -a -G gpio $USER)")
    print("4. Make sure SPI is enabled (sudo raspi-config)")
    return None

def read_analog(adc):
    """
    Read the analog value from the MCP3008
    
    Args:
        adc: The MCP3008 object
    
    Returns:
        value: A float between 0 and 1 representing the analog reading
        voltage: The voltage (assuming 3.3V reference)
    """
    if adc is None:
        # Simulation mode - return random values
        import random
        value = random.random()
        voltage = value * 3.3
        return value, voltage
    
    # Read the actual value from the MCP3008
    value = adc.value
    voltage = value * 3.3  # Assuming 3.3V reference voltage
    
    return value, voltage

# Main program to continuously read from MCP3008
if __name__ == "__main__":
    print("MCP3008 A2D Converter Test Program")
    print("----------------------------------")
    print(f"Using Channel Select Pin: {PULSEOX_SPI_CS}")
    print(f"Reading from MCP3008 Channel 0")
    
    # Initialize MCP3008 on channel 0
    adc = initialize_mcp3008(channel=0)
    
    if adc is None:
        print("Could not initialize MCP3008, running in simulation mode")
    
    try:
        print("\nReading analog values (Press CTRL+C to exit)")
        print("Raw Value | Voltage")
        print("-----------------")
        
        while True:
            # Read value
            raw_value, voltage = read_analog(adc)
            
            # Display the readings
            print(f"{raw_value:.4f}   | {voltage:.2f}V")
            
            # Wait before taking another reading
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nExiting program")