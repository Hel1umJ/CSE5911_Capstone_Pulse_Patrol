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
            
        # Try to import spidev for direct SPI access
        try:
            import spidev
            print("spidev imported successfully")
        except ImportError:
            print("spidev not available")
            
        print("Running on Raspberry Pi. gpiozero imported successfully.")
    except ImportError as e:
        print(f"Warning: GPIO import error: {e}")
        print("Analog reading will be simulated.")
        is_raspberry_pi = False
else:
    print("Not running on Raspberry Pi. Analog reading will be simulated.")

# MCP3008 Pin Configuration (same as NORA.py)
PULSEOX_SPI_MOSI = 12   # Data in (MOSI)
PULSEOX_SPI_MISO = 13  # Data out (MISO)
PULSEOX_SPI_SCLK = 14   # Clock
PULSEOX_SPI_CE0 = 10    # Data channel select pin (CS/SHDN)

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
                clock_pin=PULSEOX_SPI_SCLK,
                mosi_pin=PULSEOX_SPI_MOSI,
                miso_pin=PULSEOX_SPI_MISO,
                select_pin=PULSEOX_SPI_CE0,
                pin_factory=pin_factory
            )
            print(f"MCP3008 initialized successfully on channel {channel} using {factory_name}")
            print(f"Using pins: CLK={PULSEOX_SPI_SCLK}, MOSI={PULSEOX_SPI_MOSI}, MISO={PULSEOX_SPI_MISO}, CS={PULSEOX_SPI_CE0}")
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

# Direct SPI implementation to bypass gpiozero
def read_mcp3008_direct(channel=0):
    """
    Read directly from MCP3008 using spidev
    
    Args:
        channel: The MCP3008 channel to read from (0-7)
        
    Returns:
        value: A float between 0 and 1 representing the reading
        raw_value: The raw integer value (0-1023)
    """
    if not is_raspberry_pi:
        import random
        raw_value = int(random.random() * 1023)
        return raw_value / 1023.0, raw_value
        
    try:
        import spidev
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Open SPI bus 0, device 0
        spi.max_speed_hz = 1000000  # 1MHz
        
        # MCP3008 expects:
        # First byte: Start bit (1) followed by single/diff bit (1 for single) and part of channel
        # Second byte: Rest of channel bits followed by don't care bits
        cmd = [0x01, (0x08 + channel) << 4, 0x00]
        resp = spi.xfer2(cmd)
        
        # The returned data will be in the second and third bytes
        # Use the lower 2 bits from the second byte and all 8 bits from the third byte
        raw_value = ((resp[1] & 0x03) << 8) + resp[2]
        normalized_value = raw_value / 1023.0
        
        spi.close()
        return normalized_value, raw_value
    except Exception as e:
        print(f"Error in direct SPI reading: {e}")
        return 0, 0

# Debugging function for MCP3008
def debug_mcp3008(adc, channel=0):
    """
    Print debug information about the MCP3008 connection
    """
    print("\nDEBUG INFORMATION:")
    print(f"Raspberry Pi Detected: {is_raspberry_pi}")
    print(f"SPI Pins Configured: CLK={PULSEOX_SPI_SCLK}, MOSI={PULSEOX_SPI_MOSI}, MISO={PULSEOX_SPI_MISO}, CS={PULSEOX_SPI_CE0}")
    
    if adc is None:
        print("DEBUG: No MCP3008 object available (initialization failed or simulation mode)")
    else:
        print(f"ADC Object Type: {type(adc)}")
        print(f"ADC Channel: {adc.channel}")
        print(f"ADC Pin Factory: {adc.pin_factory}")
    
    # Check for SPI interface
    if is_raspberry_pi:
        import os
        if os.path.exists("/dev/spidev0.0"):
            print("\nSPI Device: /dev/spidev0.0 exists")
        else:
            print("\nWARNING: /dev/spidev0.0 does not exist!")
            print("SPI may not be enabled. Run 'sudo raspi-config' and enable SPI interface")
    
    # Try direct SPI method
    print("\nTesting direct SPI access:")
    try:
        value, raw = read_mcp3008_direct(channel)
        print(f"Direct SPI read successful from channel {channel}")
        print(f"Raw value: {raw} (0-1023)")
        print(f"Normalized value: {value:.4f}")
        print(f"Voltage estimate: {value * 3.3:.2f}V")
    except Exception as e:
        print(f"Direct SPI access failed: {e}")
    
    print("\nPossible issue causes if readings are 0:")
    print("1. Incorrect wiring - double check all connections")
    print("2. MCP3008 not powered correctly - verify VDD and VREF connections")
    print("3. SPI not enabled - run 'sudo raspi-config' and enable SPI")
    print("4. Sensor not providing a signal to channel 0")
    print("5. Pin configuration in code doesn't match hardware connections")
    print("6. Channel selection is incorrect - ensure sensor is on channel 0")

# Main program to continuously read from MCP3008
if __name__ == "__main__":
    print("MCP3008 A2D Converter Test Program")
    print("----------------------------------")
    print(f"Using Channel Select Pin: {PULSEOX_SPI_CE0}")
    print(f"Reading from MCP3008 Channel 0")
    
    # Initialize MCP3008 on channel 0
    adc = initialize_mcp3008(channel=0)
    
    if adc is None:
        print("Could not initialize MCP3008 through gpiozero, will try direct SPI")
    
    # Run the debug function first
    debug_mcp3008(adc)
    
    try:
        print("\nStarting continuous reading (Press CTRL+C to exit)")
        print("Method   | Raw Value  | Voltage")
        print("------------------------------")
        
        while True:
            # Try both methods
            gpiozero_value, gpiozero_voltage = read_analog(adc)
            direct_value, direct_raw = read_mcp3008_direct(0)
            direct_voltage = direct_value * 3.3
            
            # Display the readings
            print(f"GPIOZero | {gpiozero_value:.4f} | {gpiozero_voltage:.2f}V")
            print(f"Direct   | {direct_value:.4f} ({direct_raw}) | {direct_voltage:.2f}V")
            print("-" * 30)
            
            # Wait before taking another reading
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nExiting program")