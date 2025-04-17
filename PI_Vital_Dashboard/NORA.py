import tkinter as tk
from tkinter import ttk
import random as rand
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import socketio
import requests
import time
import threading
import platform


is_raspberry_pi = platform.system() == "Linux" and platform.machine().startswith(("arm", "aarch"))
servo = None
pwm = None  # For direct PWM control

if is_raspberry_pi:
    try:
        # Import GPIO libraries
        from gpiozero import Servo, PWMLED
        from gpiozero.pins.rpigpio import RPiGPIOFactory
        from gpiozero.pins.lgpio import LGPIOFactory
        from gpiozero.pins.pigpio import PiGPIOFactory
        from gpiozero.pins.native import NativeFactory
        
        # Import backend libraries directly to ensure they're available
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)  # Disable warnings
            GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
            print("RPi.GPIO imported successfully and configured")
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
            
        # Import I2C libraries for ADS1015 ADC
        try:
            import board
            import busio
            import adafruit_ads1x15.ads1015 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn
            print("ADS1015 libraries imported successfully")
        except ImportError as e:
            print(f"ADS1015 import error: {e}")
            print("To install required libraries: sudo pip3 install adafruit-circuitpython-ads1x15")
            
        print("Running on Raspberry Pi. GPIO libraries imported successfully.")
    except ImportError as e:
        print(f"Warning: GPIO import error: {e}")
        print("Servo control will be simulated.")
        is_raspberry_pi = False
else:
    print("Not running on Raspberry Pi. Servo control will be simulated.")

# Global variables for ADC and PulseOx
i2c = None
ads = None
adc_channel = None
pulseox_led = None

def initialize_i2c_adc():
    """Initialize I2C and ADS1015 ADC"""
    global i2c, ads, adc_channel
    
    if not is_raspberry_pi:
        print("Simulating ADS1015 ADC in non-Raspberry Pi environment")
        return False
    
    try:
        print("Initializing I2C and ADS1015 ADC...")
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Connect to the ADC at the known address 0x48
        print(f"Connecting to ADS1015 at address 0x{I2C_ADS1015_ADDRESS:02X}")
        ads = ADS.ADS1015(i2c, address=I2C_ADS1015_ADDRESS)
        
        # Configure ADC settings
        ads.gain = 1  # Set gain (options: 2/3, 1, 2, 4, 8, 16)
        ads.data_rate = 1600  # Set data rate (options: 128, 250, 490, 920, 1600, 2400, 3300)
        
        # Create analog input channel 0
        adc_channel = AnalogIn(ads, ADS.P0)
        
        # Try to read a value to confirm connection
        test_val = adc_channel.value
        print(f"Test reading from ADC: {test_val}")
        
        print("ADS1015 ADC initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize ADS1015 ADC: {e}")
        print("If connection fails, check the device address with 'i2cdetect -y 1'")
        return False

def initialize_pulseox_led():
    """Initialize PulseOx LED control"""
    global pulseox_led
    
    if not is_raspberry_pi:
        print("Simulating PulseOx LED in non-Raspberry Pi environment")
        return False
    
    try:
        print(f"Initializing PulseOx LED on GPIO {PULSEOX_PIN_LED}...")
        
        # Configure GPIO pin for LED control
        GPIO.setup(PULSEOX_PIN_LED, GPIO.OUT)
        GPIO.output(PULSEOX_PIN_LED, GPIO.LOW)  # Start with LED off
        
        print("PulseOx LED initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize PulseOx LED: {e}")
        return False

def read_pulseox_with_ads1015():
    """Read PulseOx sensor data using ADS1015 ADC with RED/IR LED toggling"""
    global adc_channel, pulseox_led
    
    if not is_raspberry_pi or adc_channel is None:
        # Return random SpO2 value in simulation mode
        return rand.randint(96, 100)
    
    try:
        # Storage for RED and IR readings
        red_values = []
        ir_values = []
        
        # Take multiple samples for better accuracy
        for _ in range(10):
            # Turn on LED (RED measurement)
            GPIO.output(PULSEOX_PIN_LED, GPIO.HIGH)
            time.sleep(0.05)  # Wait for signal to stabilize
            red_value = adc_channel.value
            red_values.append(red_value)
            
            # Turn off LED (IR measurement)
            GPIO.output(PULSEOX_PIN_LED, GPIO.LOW)
            time.sleep(0.05)  # Wait for signal to stabilize
            ir_value = adc_channel.value
            ir_values.append(ir_value)
        
        # Calculate average values
        avg_red = sum(red_values) / len(red_values)
        avg_ir = sum(ir_values) / len(ir_values)
        
        # Calculate min and max for RED
        min_red = min(red_values)
        max_red = max(red_values)
        
        # Calculate min and max for IR
        min_ir = min(ir_values)
        max_ir = max(ir_values)
        
        # Calculate R value similar to Arduino implementation
        if avg_red > 0 and avg_ir > 0 and (max_red - min_red) > 0 and (max_ir - min_ir) > 0:
            r_value = ((max_red - min_red) / avg_red) / ((max_ir - min_ir) / avg_ir)
            
            # Calculate SpO2 using the same formula as in the Arduino code
            spo2_value = 110 - (25 * r_value)
            
            # Clamp to reasonable SpO2 range
            spo2_value = max(70, min(100, int(spo2_value)))
            
            print(f"SpO2 from ADS1015: {spo2_value}% (R={r_value:.3f})")
            return spo2_value
        else:
            print("Invalid sensor readings, using fallback value")
            return rand.randint(96, 100)
    except Exception as e:
        print(f"Error reading PulseOx sensor: {e}")
        return rand.randint(96, 100)  # Return random value on error

"""
Constants & Data
"""

COLORS = {
    "bg_main": "#F9FAFC", #light background
    "bg_card": "#FFFFFF", #white background for cards
    "primary": "#3F72AF", #main blue
    "accent": "#5E94E4", #light blue
    "danger": "#F05454", #red
    "success": "#4CAF50", #green
    "info": "#00BCD4", #cyan
    "warning": "#FFA726", #orange
    "text_primary": "#2C3E50", #primary text color
    "text_secondary": "#7F8C8D", #secondary text color
    "border": "#E0E7FF" #border
}

FONTS = {
    "header": ("Helvetica", 22, "bold"),
    "title": ("Helvetica", 16, "bold"),
    "subtitle": ("Helvetica", 14, "bold"),
    "label": ("Helvetica", 12),
    "label_small": ("Helvetica", 10),
    "bold_label": ("Helvetica", 20, "bold"),
    "value_label": ("Helvetica", 24, "bold"),
    "footer": ("Helvetica", 10, "italic")
}

"""
GPIO Config
"""
SERVO_PIN = 18  # GPIO pin for servo control (PWM); physical pin 12
# SG90 specific pulse widths - more precise for this specific model
SERVO_MIN_PULSE_WIDTH = 500   # min pulse width in microseconds (0 degrees)
SERVO_MAX_PULSE_WIDTH = 2400  # max pulse width in microseconds (180 degrees)
MIN_FLOW_RATE = 0
MAX_FLOW_RATE = 30
MIN_DESIRED_VOL = 0
MAX_DESIRED_VOL = 50

# Values for servo control with gpiozero
SERVO_MIN_VALUE = -1  # gpiozero servo minimum position value
SERVO_MAX_VALUE = 1   # gpiozero servo maximum position value

# Direct GPIO control for servo
# Set to True to use direct PWM control instead of gpiozero
SERVO_DIRECT_ENABLED = True
# Servo smoothing parameters
SERVO_SMOOTHING_ENABLED = True  # Enable smooth motion
SERVO_SMOOTHING_FACTOR = 0.1  # Lower = smoother but slower (0.01-0.3 is good range)
SERVO_UPDATE_RATE = 50  # Update rate in ms - higher values (lower frequency) are smoother

# New hardware pin configuration
PULSEOX_PIN_LED = 21  # GPIO pin for PulseOx LED control; physical pin 40

# I2C pins for ADS1015 ADC (used via the QWIIC shim)
# These are the default I2C pins on Raspberry Pi
I2C_SDA_PIN = 2  # Physical pin 3
I2C_SCL_PIN = 3  # Physical pin 5

# I2C address for ADS1015 ADC (only 0x48 is now connected)
I2C_ADS1015_ADDRESS = 0x48  # Default ADS1015 address


UPDATE_INTERVAL = 1000 #in ms
vital_labels = {} #dict to store references to each vital's value label; we will use these to update the sensor values
MAX_POINTS = 30 #number of points to store on the graph; 1 point for every tick/update interval

#parallel arrays for graphing purposes.
ecg_data = [] #data buffer to store ekg values
time_axis = [] #data buffer for coordinates on x (time) axis
t_step = 0 #counter to store update tick we are on (for x axis labels)
ecg_plot = None 
ecg_canvas = None

flow_rate = 0 #Default, initial flow rate setting in μL/min (whole number)
flow_rate_changed_locally = False  # Flag to track local changes
desired_vol = 0 #Default, initial flow rate setting in μl (whole number)
desired_vol_changed_locally = False  # Flag to track local changes
socket_connected = False  # Flag to track socket connection status

procedure_running = False  # Flag to track if procedure is running
vol_given = 0.0 # Used to track the total volume that should have been dispensed
actual_vol_given = 0 # Used to track the amount dispensed based on servo position



#Attempt to get Device's IP via socket trick; defaults to localhost
import socket
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) #Google's DNS server
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    
    except:
        return "127.0.0.1"

SERVER_IP = get_local_ip()
SERVER_PORT = 5000
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
SOCKET_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# Initialize Socket.IO client
sio = socketio.Client()

"""
Socket.IO Event Handlers
"""
@sio.event
def connect():
    global socket_connected
    print("Connected to server via WebSocket")
    socket_connected = True
    
    # Update the status indicator if available
    if 'status_label' in globals() and status_label:
        root.after(0, lambda: status_label.config(text="● Connected", fg=COLORS["success"]))

@sio.event
def disconnect():
    global socket_connected
    print("Disconnected from server")
    socket_connected = False
    
    # Update the status indicator if available
    if 'status_label' in globals() and status_label:
        root.after(0, lambda: status_label.config(text="● Disconnected", fg=COLORS["danger"]))
    
    # Try to reconnect
    try_reconnect()

@sio.on("flow_rate_update")
def on_flow_rate_update(data):
    """Handle flow rate updates from server"""
    global flow_rate, flow_value_label, flow_rate_changed_locally
    
    # If we made the change locally, ignore the update to avoid feedback loops
    if flow_rate_changed_locally:
        flow_rate_changed_locally = False
        return
    
    # Update flow rate
    new_flow_rate = int(data.get("flow_rate", flow_rate))
    
    # Update global flow rate
    if new_flow_rate != flow_rate:
        flow_rate = new_flow_rate
        print(f"Flow rate updated from server: {flow_rate}")
        
        # Update hardware
        # update_flow(flow_rate)
        
        # Update display (need to use Tkinter's after method to safely update UI from another thread)
        if flow_value_label and 'root' in globals():
            root.after(0, lambda: flow_value_label.config(text=f"{flow_rate}"))

@sio.on("desired_vol_update")
def on_desired_vol_update(data):
    """Handle desired volume updates from server"""
    global desired_vol, desired_vol_changed_locally
    
    # If we made the change locally, ignore the update to avoid feedback loops
    if desired_vol_changed_locally:
        desired_vol_changed_locally = False
        return
    
    # Update desired volume
    new_desired_vol = int(data.get("desired_vol", desired_vol))
    
    # Update global desired volume
    if new_desired_vol != desired_vol:
        desired_vol = new_desired_vol
        print(f"Desired volume updated from server: {desired_vol}")
        
        # Update display (need to use Tkinter's after method to safely update UI from another thread)
        if 'desired_volume_label' in globals() and 'root' in globals():
            root.after(0, lambda: desired_volume_label.config(text=f"{desired_vol}"))

@sio.on("procedure_state_update")
def on_procedure_state_update(data):
    """Handle procedure state updates from server"""
    global procedure_running, vol_given, actual_vol_given
    
    # Get the new state from data
    new_state = bool(data.get("running", procedure_running))
    
    # Print debug info
    print(f"DEBUG: Received procedure state update from server: {'Running' if new_state else 'Stopped'}")
    print(f"DEBUG: Current state: {'Running' if procedure_running else 'Stopped'}")
    
    # Only update if state is different
    if new_state != procedure_running:
        procedure_running = new_state
        print(f"DEBUG: Procedure state updated from server: {'Running' if procedure_running else 'Stopped'}")
        
        # If starting procedure, reset volume given
        if procedure_running:
            vol_given = 0.0
            if 'actual_vol_given' in globals():
                actual_vol_given = 0.0
        
        # Update UI (need to use Tkinter's after method to safely update UI from another thread)
        if 'procedure_status_label' in globals() and 'start_stop_btn' in globals() and 'root' in globals():
            if procedure_running:
                root.after(0, lambda: procedure_status_label.config(text="Status: Running", fg=COLORS["success"]))
                root.after(0, lambda: start_stop_btn.config(text="Stop Procedure", bg=COLORS["danger"]))
            else:
                root.after(0, lambda: procedure_status_label.config(text="Status: Stopped", fg=COLORS["danger"]))
                root.after(0, lambda: start_stop_btn.config(text="Start Procedure", bg=COLORS["primary"]))
    else:
        print("DEBUG: Ignored server state update - already in that state")

def try_reconnect():
    """Try to reconnect to the WebSocket server"""
    try:
        if not sio.connected:
            sio.connect(SOCKET_URL)
    except Exception as e:
        print(f"Failed to reconnect: {e}")
        # Schedule another attempt
        threading.Timer(5.0, try_reconnect).start()

def connect_to_socket():
    """Connect to the WebSocket server"""
    try:
        sio.connect(SOCKET_URL)
    except Exception as e:
        print(f"Failed to connect to socket: {e}")
        # Schedule a reconnection attempt
        threading.Timer(5.0, try_reconnect).start()

"""
Helper Functions
"""
flow_value_label = None #global reference
status_label = None  # Global reference to status label

def update_flow_display():
    """Update the flow rate display label with the current flow_rate value"""
    global flow_value_label
    if flow_value_label:
        # Display as whole number
        flow_value_label.config(text=f"{flow_rate}")

def update_volume_display():
    """Update the flow rate display label with the current flow_rate value"""
    global desired_volume_label
    if desired_volume_label:
        # Display as whole number
        desired_volume_label.config(text=f"{desired_vol}")        

def create_vital_frame(parent, row, col, label_text, value_key, label_dict, color=COLORS["primary"]):
    """Creates a card-style vital sign display with colored accent bar"""
    
    frame = tk.Frame(parent, bg=COLORS["bg_card"], padx=15, pady=15, bd=0)
    frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
    
    #color strip
    color_bar = tk.Frame(frame, bg=color, width=6)
    color_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
    
    #main card content frame
    content = tk.Frame(frame, bg=COLORS["bg_card"])
    content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    #title
    title_frame = tk.Frame(content, bg=COLORS["bg_card"])
    title_frame.pack(fill=tk.X, anchor="w")
    tk.Label(title_frame, text=label_text, bg=COLORS["bg_card"],fg=COLORS["text_primary"], font=FONTS["title"]).pack(side=tk.LEFT)
    

    val_label = tk.Label(content, text="--", bg=COLORS["bg_card"], font=FONTS["value_label"], fg=color)
    val_label.pack(anchor="e", pady=5)
    label_dict[value_key] = val_label #store label in dict so we can reference it later
    return frame

def send_data(sensor_info):
    """
    POST to /data with a timestamp and the current vitals
    """
    bp_sys, bp_dia = sensor_info["bp"]  # sys, dia
    
    payload = {
        "timestamp": time.time(),
        "hr": sensor_info["hr"],
        "spo2": sensor_info["spo2"],
        "bp_sys": bp_sys,
        "bp_dia": bp_dia,
    }
    try:
        requests.post(f"{SERVER_URL}/data", json=payload, timeout=2)
    except Exception as e:
        print("Error sending data to server:", e)


def update_vitals(root):
    """
    Called once every UPDATE_INTERVAL to refresh displayed vital values
    """
    global t_step
    
    # Get SpO2 using the ADS1015 ADC
    try:
        # Use our new function to read PulseOx data
        spo2_value = read_pulseox_with_ads1015()
        print(f"SpO2 from sensor: {spo2_value}%")
    except Exception as e:
        print(f"Error reading SpO2: {e}")
        spo2_value = rand.randint(96, 100)  # Use random value if reading fails
    
    # Populate sensor info with real SpO2 and random values for other vitals
    sensor_info = {
        "hr": rand.randint(70, 80), 
        "spo2": spo2_value, 
        "bp": (rand.randint(70, 80), rand.randint(90, 100))
    }

    set_vitals(sensor_info) 

    # Append data for graphing; update rolling window by chopping off old data.
    ecg_data.append(sensor_info["hr"])
    time_axis.append(t_step)
    t_step = t_step + 1
    if len(ecg_data) > MAX_POINTS:
        ecg_data.pop(0)
        time_axis.pop(0)

    draw_graphs()
    
    send_data(sensor_info) # send data to the server
  
    root.after(UPDATE_INTERVAL, update_vitals, root) #Update with sensor data every 1000ms

# Global variables for servo movement control
last_servo_update = 0
continuous_movement = False
servo_target_position = 0
servo_current_position = 0
SERVO_MOVEMENT_INTERVAL = 20  # Update every 20ms for smoother motion

def update_servo_position():
    """
    Dedicated function for smooth servo movement
    This runs independently of volume calculations and other logic
    for smoother motion
    """
    global servo_current_position, servo_target_position, continuous_movement
    global servo, pwm, last_servo_update
    global procedure_running, flow_rate, desired_vol, vol_given
    
    current_time = time.time() * 1000  # Current time in milliseconds
    
    # Only update if enough time has passed (smooth movement interval)
    if current_time - last_servo_update < SERVO_MOVEMENT_INTERVAL:
        root.after(5, update_servo_position)  # Check again in 5ms
        return
    
    # For direct PWM - SG90 specific duty cycles
    min_duty = 2.5   # 0 degrees - 500μs/20000μs = 2.5% (syringe at 0)
    max_duty = 12.0  # 180 degrees - 2400μs/20000μs = 12.0% (syringe fully depressed)
    
    if is_raspberry_pi:
        # Using direct PWM control
        if SERVO_DIRECT_ENABLED and pwm is not None:
            try:
                # Update servo target position based on current volume ratio
                if procedure_running and flow_rate > 0 and desired_vol > 0:
                    # Calculate target position based on current volume percentage
                    volume_percentage = min(vol_given / desired_vol, 1.0)
                    servo_target_position = min_duty + (max_duty - min_duty) * volume_percentage
                    
                    # If we're at the final position, stop continuous movement
                    if vol_given >= desired_vol:
                        continuous_movement = False
                        servo_target_position = min_duty + (max_duty - min_duty)  # Full extension
                elif not procedure_running:
                    servo_target_position = min_duty  # Return to start position when stopped
                    continuous_movement = False
                
                # Smooth movement: move directly to calculated position based on volume
                # Instead of incremental steps which might cause jittering
                if procedure_running and flow_rate > 0 and desired_vol > 0:
                    # Calculate the direct position based on current volume
                    volume_percentage = min(vol_given / desired_vol, 1.0) if desired_vol > 0 else 0
                    target_duty = min_duty + (max_duty - min_duty) * volume_percentage
                    
                    # Only move if the change is significant enough (reduces jitter from tiny movements)
                    if abs(servo_current_position - target_duty) > 0.1:
                        servo_current_position = target_duty  # Direct position update
                        
                        # Apply the movement to the servo - no gradual steps, go directly to position
                        print(f"DEBUG: Moving servo to {servo_current_position:.2f}% duty ({(servo_current_position-min_duty)/(max_duty-min_duty)*100:.1f}% of range)")
                        
                        # Set position and hold it with continuous signal
                        pwm.ChangeDutyCycle(servo_current_position)
                        
                        # Don't stop PWM during procedure - continuous signal prevents jittering
                        # Let it keep holding the position
                elif not procedure_running:
                    # When not running, stop at min position and turn off PWM
                    if abs(servo_current_position - min_duty) > 0.1:
                        servo_current_position = min_duty
                        pwm.ChangeDutyCycle(min_duty)
                        time.sleep(0.2)  # Give time to reach position
                        pwm.ChangeDutyCycle(0)  # Stop pulses when idle
                    
                    # Record when we made this move
                    last_servo_update = current_time
            
            except Exception as e:
                print(f"Error in servo position update: {e}")
                print(f"Exception details: {str(e)}")
        
        # Using gpiozero Servo
        elif servo is not None:
            try:
                # Calculate positions for gpiozero (-1 to 1 range)
                if procedure_running and flow_rate > 0 and desired_vol > 0:
                    # Calculate target position based on current volume percentage
                    volume_percentage = min(vol_given / desired_vol, 1.0)
                    servo_target_position = SERVO_MIN_VALUE + (SERVO_MAX_VALUE - SERVO_MIN_VALUE) * volume_percentage
                    
                    # If we're at the final position, stop continuous movement
                    if vol_given >= desired_vol:
                        continuous_movement = False
                        servo_target_position = SERVO_MAX_VALUE  # Full extension
                elif not procedure_running:
                    servo_target_position = SERVO_MIN_VALUE  # Return to start position when stopped
                    continuous_movement = False
                
                # Move directly to calculated position based on volume percentage
                if procedure_running and flow_rate > 0 and desired_vol > 0:
                    # Calculate the direct position based on current volume 
                    volume_percentage = min(vol_given / desired_vol, 1.0) if desired_vol > 0 else 0
                    target_position = SERVO_MIN_VALUE + (SERVO_MAX_VALUE - SERVO_MIN_VALUE) * volume_percentage
                    
                    # Only move if the change is significant enough (reduces jitter)
                    if abs(servo_current_position - target_position) > 0.05:
                        servo_current_position = target_position  # Direct position update
                        
                        # Apply the movement to the servo - direct positioning
                        print(f"DEBUG: Moving servo to {servo_current_position:.4f} position ({volume_percentage*100:.1f}% of range)")
                        servo.value = servo_current_position
                elif not procedure_running:
                    # Return to min position when not running
                    if abs(servo_current_position - SERVO_MIN_VALUE) > 0.05:
                        servo_current_position = SERVO_MIN_VALUE
                        servo.value = SERVO_MIN_VALUE
                    
                    # Record when we made this move
                    last_servo_update = current_time
            
            except Exception as e:
                print(f"Error in gpiozero servo position update: {e}")
                print(f"Exception details: {str(e)}")
    
    # Schedule next update
    root.after(5, update_servo_position)

def update_flow():
    """
    Updates values based on flow rate - now separated from servo control
    This function primarily monitors status and provides status updates
    """
    global servo, pwm
    global actual_vol_given
    global vol_given
    global SERVO_MAX_VALUE
    global desired_vol
    global continuous_movement, servo_target_position, servo_current_position
    
    # Print status info (but less frequently to reduce console spam)
    if procedure_running and flow_rate > 0 and desired_vol > 0:
        # Log current procedure status
        percent_complete = (vol_given / desired_vol * 100) if desired_vol > 0 else 0
        print(f"DEBUG: Procedure active - {vol_given:.2f}/{desired_vol}μL ({percent_complete:.1f}%) at {flow_rate}μL/min")
    else:
        # Only log once every few cycles to avoid spam
        if not hasattr(update_flow, "counter"):
            update_flow.counter = 0
        update_flow.counter += 1
        
        if update_flow.counter % 5 == 0:  # Log every 5th call
            if not procedure_running:
                print(f"DEBUG: Procedure not running")
            elif flow_rate == 0:
                print(f"DEBUG: Flow rate is 0")
            elif desired_vol <= 0:
                print(f"DEBUG: Invalid desired volume: {desired_vol}")
    
    # Schedule next flow update (reduced frequency)
    root.after(1000, update_flow)  # Update every second is enough
    
    return True



def update_volume_given():
    """
    Updates the volume given based on flow rate and time.
    """
    global vol_given
    global procedure_running

    # Only increment volume if procedure is running and we have flow
    if procedure_running and flow_rate > 0:
        # Calculate increment based on flow rate (μL/min)
        # We update once per second, so divide by 60 to get per-second rate
        vol_increment = flow_rate / 60.0
        vol_given += vol_increment
        
        # Ensure we don't exceed desired volume
        if vol_given > desired_vol and desired_vol > 0:
            vol_given = desired_vol
            
        print(f"DEBUG: Incremented volume by {vol_increment:.2f}μL to {vol_given:.2f}μL")

    # Update UI elements
    if 'progress_bar' in globals() and 'vol_given_label' in globals():
        progress_bar["maximum"] = desired_vol if desired_vol > 0 else 1
        progress_bar["value"] = vol_given
        vol_given_label.config(text=f"Volume Given: {vol_given:.2f} / {desired_vol} μL")
    
    # Print detailed debug information
    print(f"DEBUG: Procedure running: {procedure_running}, Vol: {vol_given:.2f}/{desired_vol}, Flow rate: {flow_rate}")
    
    # Send the updated volume given to the server via WebSocket
    try:
        if sio.connected:
            sio.emit("update_vol_given", {"vol_given": vol_given})
    except Exception as e:
        print(f"Error sending volume given update: {e}")

    # Check if we've reached target volume
    if procedure_running and vol_given >= desired_vol and desired_vol > 0:
        print("DEBUG: Target volume reached! Stopping procedure...")
        procedure_running = False
        
        # Update UI
        if 'procedure_status_label' in globals() and 'start_stop_btn' in globals():
            procedure_status_label.config(text="Status: Stopped", fg=COLORS["danger"])
            start_stop_btn.config(text="Start Procedure", bg=COLORS["primary"])
        
        # Send procedure stopped state to server
        try:
            if sio.connected:
                print("DEBUG: Sending procedure stopped state to server...")
                sio.emit("procedure_state", {"running": False})
        except Exception as e:
            print(f"Error sending procedure state update: {e}")

    # Schedule next update (1 second)
    root.after(1000, update_volume_given)

def set_vitals(vital_info):
    """Update vital sign displays with new values"""
    vital_labels["hr"].config(text=f"{vital_info['hr']} bpm", fg=COLORS["danger"])
    vital_labels["spo2"].config(text=f"{vital_info['spo2']}%", fg=COLORS["info"])
    vital_labels["bp"].config(text=f"{vital_info['bp'][0]}/{vital_info['bp'][1]} mmHg", fg=COLORS["primary"])

def draw_graphs():
    """
    Clears & redraws ECG graph
    """
    global ecg_plot
    global ecg_canvas
    global ecg_data
    global time_axis 

    plt_bg_color = COLORS["bg_card"]
    plt_text_color = COLORS["text_primary"]
    ecg_plot.clear()
    ecg_plot.set_facecolor(plt_bg_color)
    ecg_plot.set_title("ECG", color=plt_text_color, fontsize=12, fontweight='bold')
    ecg_plot.set_xlabel("Time (s)", color=plt_text_color, fontsize=10)
    ecg_plot.plot(time_axis, ecg_data, color=COLORS["danger"], marker="o", markersize=4, linewidth=2, alpha=0.8)[0]
    ecg_plot.fill_between(time_axis, ecg_data, color=COLORS["danger"], alpha=0.1)
    ecg_plot.grid(True, linestyle='--', linewidth=0.5, color="#E5E5E5")
    
    #style graph edges
    for spine in ecg_plot.spines.values():
        spine.set_color("#E5E5E5") #Make spines a nice dark
        spine.set_linewidth(0.5)
    
    #style graph interval lines
    ecg_plot.tick_params(axis='x', colors=plt_text_color, direction='out', length=5)
    ecg_plot.tick_params(axis='y', colors=plt_text_color, direction='out', length=5)
    
    ecg_canvas.figure.tight_layout()
    ecg_canvas.draw()

def create_styled_button(parent, text, command, width=8, height=3, color=COLORS["primary"]):
    """Creates a styled button with flat relief and custom colors"""
    btn = tk.Button(parent, text=text, command=command, width=width, height=height,
                   relief="flat", bg=color, fg="white", 
                   activebackground=COLORS["accent"], activeforeground="white",
                   font=FONTS["label"])
    return btn

def create_gui():
    """
    Section Layout:
    Row 0: Header (spans both columns)
    Row 1: Patient Info (column 0); Flow Rate Control (column 0); Target Volume (column 1); Start Procedure (column 1)
    Row 2: Vital Signs Three equal cards spanning both columns
    Row 3: ECG Graph (spans both columns)
    Row 4: Footer (spans both columns)
    """
    global ecg_plot
    global ecg_canvas
    global root
    global status_label
    
    matplotlib.use("TkAgg")
    
    root = tk.Tk()
    root.title("NORA Vital Monitor")
    root.geometry("900x680")
    root.configure(bg=COLORS["bg_main"])
    root.minsize(900, 680)
    
    style = ttk.Style()
    style.configure("TFrame", background=COLORS["bg_main"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
    
    main_frame = ttk.Frame(root, style="TFrame")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
    
    for i in range(5):
        main_frame.rowconfigure(i, weight=0)
    main_frame.rowconfigure(5, weight=1)#ALlow last row to expand and fill space
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(2, weight=1)
    main_frame.columnconfigure(3, weight=1)
    
    #HEADER SECTION
    header_frame = ttk.Frame(main_frame, style="Card.TFrame")
    header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=10)
    
    try:
        logo_img = Image.open("hospital_logo2.jpg")
        logo_img = logo_img.resize((80, 80), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(header_frame, image=logo_photo, bg=COLORS["bg_card"])
        logo_label.image = logo_photo
        logo_label.pack(side=tk.LEFT, padx=20, pady=15)
    except Exception as e:
        print("Error loading logo:", e)
    
    title_container = tk.Frame(header_frame, bg=COLORS["bg_card"])
    title_container.pack(side=tk.LEFT, padx=10, fill=tk.Y, expand=True)
    
    header_label = tk.Label(title_container, text="NORA Vitals Monitor", 
                           bg=COLORS["bg_card"], fg=COLORS["primary"], 
                           font=FONTS["header"])
    header_label.pack(anchor="w")
    
    subtitle_label = tk.Label(title_container, text="Real-time patient monitoring system",
                             bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                             font=FONTS["subtitle"])
    subtitle_label.pack(anchor="w")
    
    status_frame = tk.Frame(header_frame, bg=COLORS["bg_card"])
    status_frame.pack(side=tk.RIGHT, padx=20)
    
    # Initialize with disconnected status until socket connects
    status_label = tk.Label(status_frame, text="● Disconnected", fg=COLORS["danger"],
                          bg=COLORS["bg_card"], font=FONTS["label"])
    status_label.pack()
    
    web_url = f"{SERVER_URL}/nora"
    server_url_label = tk.Label(status_frame, text=f"Web Dashboard: {web_url}",
                              fg=COLORS["primary"], bg=COLORS["bg_card"],
                              font=FONTS["label_small"], cursor="hand2")
    server_url_label.pack(pady=(2, 0))
    
    server_url_label.bind("<Enter>", lambda e: server_url_label.config(fg=COLORS["accent"], font=(FONTS["label_small"][0], FONTS["label_small"][1], "underline")))
    server_url_label.bind("<Leave>", lambda e: server_url_label.config(fg=COLORS["primary"], font=FONTS["label_small"]))
    
    #PATIENT INFO SECTION
    patient_frame = ttk.Frame(main_frame, style="Card.TFrame")
    patient_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    
    patient_title = tk.Label(patient_frame, text="Patient Information", 
                           bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                           font=FONTS["title"])
    patient_title.pack(anchor="w", padx=20, pady=(15, 10))
    
    patient_info_frame = tk.Frame(patient_frame, bg=COLORS["bg_card"], padx=20, pady=10)
    patient_info_frame.pack(fill=tk.X)
    
    tk.Label(patient_info_frame, text="Patient:", bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"], font=FONTS["label"]).grid(row=0, column=0, sticky="w", pady=2)
    tk.Label(patient_info_frame, text="Awesome Anesthesia", bg=COLORS["bg_card"],
            fg=COLORS["text_primary"], font=FONTS["subtitle"]).grid(row=0, column=1, sticky="w", padx=10, pady=2)
    
    tk.Label(patient_info_frame, text="DOB:", bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"], font=FONTS["label"]).grid(row=1, column=0, sticky="w", pady=2)
    tk.Label(patient_info_frame, text="2077-01-21", bg=COLORS["bg_card"],
            fg=COLORS["text_primary"], font=FONTS["label"]).grid(row=1, column=1, sticky="w", padx=10, pady=2)
    
    tk.Label(patient_info_frame, text="ID:", bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"], font=FONTS["label"]).grid(row=2, column=0, sticky="w", pady=2)
    tk.Label(patient_info_frame, text="123456789", bg=COLORS["bg_card"],
            fg=COLORS["text_primary"], font=FONTS["label"]).grid(row=2, column=1, sticky="w", padx=10, pady=2)
    
    #DESIRED VOLUME CONTROL SECTION
    volume_frame = ttk.Frame(main_frame, style="Card.TFrame")
    volume_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
    
    volume_title = tk.Label(volume_frame, text="Desired Volume", 
                        bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                        font=FONTS["title"])
    volume_title.pack(anchor="w", padx=20, pady=(15, 10))
    
    volume_display_frame = tk.Frame(volume_frame, bg=COLORS["bg_card"])
    volume_display_frame.pack(fill=tk.X, padx=20, pady=10)
    
    volume_value_frame = tk.Frame(volume_display_frame, bg=COLORS["bg_card"])
    volume_value_frame.pack(pady=10)
    
    global desired_volume_label
    desired_volume_label = tk.Label(volume_value_frame, text=f"{desired_vol}",
                              font=("Helvetica", 36, "bold"), fg=COLORS["primary"],
                              bg=COLORS["bg_card"])
    desired_volume_label.pack(side=tk.LEFT)
    
    volume_unit_label = tk.Label(volume_value_frame, text="μl",
                             font=FONTS["label"], fg=COLORS["text_secondary"],
                             bg=COLORS["bg_card"])
    volume_unit_label.pack(side=tk.LEFT, padx=(5, 0), anchor="s", pady=(0, 8))
    
    volume_control_frame = tk.Frame(volume_display_frame, bg=COLORS["bg_card"])
    volume_control_frame.pack(pady=10)
    
    def increase_volume():
        global desired_vol, desired_vol_changed_locally
        
        # Check socket connection
        if not socket_connected:
            print("Warning - socket disconnected")
            
        # Increase by 1 to match the React frontend
        desired_vol += 1
        if desired_vol > 50:
            desired_vol = 50
        
        # Set flag to ignore echo from server
        desired_vol_changed_locally = True
        
        # Update the display
        update_volume_display()
        
        # Send to server via WebSocket
        try:
            sio.emit("update_desired_vol", {"desired_vol": desired_vol})
            print(f"Sent desired volume update via WebSocket: {desired_vol}")
        except Exception as e:
            print(f"Error sending desired volume update: {e}")
            # Try to reconnect
            if not sio.connected:
                try_reconnect()
    
    def decrease_volume():
        global desired_vol, desired_vol_changed_locally
        
        # Check socket connection
        if not socket_connected:
            print("Warning - socket disconnected")
            
        # Decrease by 1 to match the React frontend
        if desired_vol > 0:
            desired_vol -= 1
        
        # Set flag to ignore echo from server
        desired_vol_changed_locally = True
        
        # Update the display
        update_volume_display()
        
        # Send to server via WebSocket
        try:
            sio.emit("update_desired_vol", {"desired_vol": desired_vol})
            print(f"Sent desired volume update via WebSocket: {desired_vol}")
        except Exception as e:
            print(f"Error sending desired volume update: {e}")
            # Try to reconnect
            if not sio.connected:
                try_reconnect()
    
    decrease_btn = create_styled_button(volume_control_frame, "−", decrease_volume, width=5, height=2)
    decrease_btn.pack(side=tk.LEFT, padx=10)
    
    increase_btn = create_styled_button(volume_control_frame, "＋", increase_volume, width=5, height=2)
    increase_btn.pack(side=tk.LEFT, padx=10)
    
    #FLOW RATE CONTROL SECTION
    flow_frame = ttk.Frame(main_frame, style="Card.TFrame")
    flow_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
    
    flow_title = tk.Label(flow_frame, text="Flow Rate Control", 
                        bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                        font=FONTS["title"])
    flow_title.pack(anchor="w", padx=20, pady=(15, 10))
    
    flow_display_frame = tk.Frame(flow_frame, bg=COLORS["bg_card"])
    flow_display_frame.pack(fill=tk.X, padx=20, pady=10)
    
    flow_value_frame = tk.Frame(flow_display_frame, bg=COLORS["bg_card"])
    flow_value_frame.pack(pady=10)
    
    global flow_value_label
    flow_value_label = tk.Label(flow_value_frame, text=f"{flow_rate}",
                              font=("Helvetica", 36, "bold"), fg=COLORS["primary"],
                              bg=COLORS["bg_card"])
    flow_value_label.pack(side=tk.LEFT)
    
    flow_unit_label = tk.Label(flow_value_frame, text="μL/min",
                             font=FONTS["label"], fg=COLORS["text_secondary"],
                             bg=COLORS["bg_card"])
    flow_unit_label.pack(side=tk.LEFT, padx=(5, 0), anchor="s", pady=(0, 8))
    
    flow_control_frame = tk.Frame(flow_display_frame, bg=COLORS["bg_card"])
    flow_control_frame.pack(pady=10)
    
    def increase_flow():
        global flow_rate, flow_rate_changed_locally
        
        # Check socket connection
        if not socket_connected:
            print("Warning - socket disconnected")
            
        # Increase by 1 to match the React frontend
        flow_rate += 1
        if flow_rate > 30:
            flow_rate = 30
        
        # Set flag to ignore echo from server
        flow_rate_changed_locally = True
        
        # Update the display
        update_flow_display()
        
        # Update the hardware
        # update_flow(flow_rate)
        
        # Send to server via WebSocket
        try:
            sio.emit("update_flow_rate", {"flow_rate": flow_rate})
            print(f"Sent flow rate update via WebSocket: {flow_rate}")
        except Exception as e:
            print(f"Error sending flow rate update: {e}")
            # Try to reconnect
            if not sio.connected:
                try_reconnect()
    
    def decrease_flow():
        global flow_rate, flow_rate_changed_locally
        
        # Check socket connection
        if not socket_connected:
            print("Warning - socket disconnected")
            
        # Decrease by 1 to match the React frontend
        if flow_rate > 0:
            flow_rate -= 1
        
        # Set flag to ignore echo from server
        flow_rate_changed_locally = True
        
        # Update the display
        update_flow_display()
        
        # Update the hardware
        # update_flow(flow_rate)
        
        # Send to server via WebSocket
        try:
            sio.emit("update_flow_rate", {"flow_rate": flow_rate})
            print(f"Sent flow rate update via WebSocket: {flow_rate}")
        except Exception as e:
            print(f"Error sending flow rate update: {e}")
            # Try to reconnect
            if not sio.connected:
                try_reconnect()
    
    decrease_btn = create_styled_button(flow_control_frame, "−", decrease_flow, width=5, height=2)
    decrease_btn.pack(side=tk.LEFT, padx=10)
    
    increase_btn = create_styled_button(flow_control_frame, "＋", increase_flow, width=5, height=2)
    increase_btn.pack(side=tk.LEFT, padx=10)

    #START/STOP PROCEDURE SECTION
    procedure_frame = ttk.Frame(main_frame, style="Card.TFrame")
    procedure_frame.grid(row=1, column=3, sticky="nsew", padx=10, pady=10)

    procedure_title = tk.Label(procedure_frame, text="Procedure Control", 
                            bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                            font=FONTS["title"])
    procedure_title.pack(anchor="w", padx=20, pady=(15, 10))

    global vol_given_label
    vol_given_label = tk.Label(procedure_frame, text="Volume Given: 0 mL", 
                                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"], 
                                 font=FONTS["label"])
    vol_given_label.pack(anchor="w", padx=20, pady=10)

    global progress_bar
    progress_bar = ttk.Progressbar(procedure_frame, length=300, mode="determinate")
    progress_bar.pack(pady=5)

    global procedure_status_label
    procedure_status_label = tk.Label(procedure_frame, text="Status: Stopped",
                                    bg=COLORS["bg_card"], fg=COLORS["danger"],
                                    font=FONTS["subtitle"])
    procedure_status_label.pack(pady=10)

    def toggle_procedure():
        """Toggle procedure running state and sync with server"""
        global procedure_running, vol_given, actual_vol_given
        global servo_current_position, servo_target_position, continuous_movement
        
        # Toggle the state
        procedure_running = not procedure_running
        
        # Print debug info
        print(f"DEBUG: Manually toggling procedure to: {'Running' if procedure_running else 'Stopped'}")
        
        if procedure_running:
            # Reset volume given when starting procedure
            vol_given = 0.0
            actual_vol_given = 0.0  # Reset this too 
            
            # Reset servo position tracking variables
            if SERVO_DIRECT_ENABLED and is_raspberry_pi:
                servo_current_position = 2.5  # Min duty cycle
                servo_target_position = 2.5
            else:
                servo_current_position = SERVO_MIN_VALUE
                servo_target_position = SERVO_MIN_VALUE
                
            # Engage continuous movement mode
            continuous_movement = True
            
            # Show detailed debug info about the procedure parameters
            print(f"DEBUG: Starting procedure with flow_rate={flow_rate}, desired_vol={desired_vol}")
            
            procedure_status_label.config(text="Status: Running", fg=COLORS["success"])
            start_stop_btn.config(text="Stop Procedure", bg=COLORS["danger"])
            
            # Force initial servo position to starting position
            if SERVO_DIRECT_ENABLED and pwm is not None and is_raspberry_pi:
                print("DEBUG: Setting servo to initial position")
                pwm.ChangeDutyCycle(2.5)  # Starting position (0 degrees)
                time.sleep(0.3)
                pwm.ChangeDutyCycle(0)  # Stop sending pulses
            elif servo is not None and is_raspberry_pi:
                print("DEBUG: Setting servo to initial position")
                servo.value = SERVO_MIN_VALUE
                time.sleep(0.3)
        else:
            # Additional debug info when stopping
            print(f"DEBUG: Stopping procedure after delivering {vol_given:.2f}/{desired_vol} μL")
            
            # Disengage continuous movement
            continuous_movement = False
            
            # Set target to return to start position
            if SERVO_DIRECT_ENABLED and is_raspberry_pi:
                servo_target_position = 2.5  # Min duty cycle
            else:
                servo_target_position = SERVO_MIN_VALUE
            
            procedure_status_label.config(text="Status: Stopped", fg=COLORS["danger"])
            start_stop_btn.config(text="Start Procedure", bg=COLORS["primary"])
        
        # Send procedure state update to the server
        try:
            if sio.connected:
                print(f"DEBUG: Sending manual procedure state update: {'Running' if procedure_running else 'Stopped'}")
                sio.emit("procedure_state", {"running": procedure_running})
            else:
                print("DEBUG: Socket not connected! Cannot sync procedure state.")
        except Exception as e:
            print(f"Error sending procedure state update: {e}")

    global start_stop_btn
    start_stop_btn = create_styled_button(procedure_frame, "Start Procedure", toggle_procedure, width=20, height=2)
    start_stop_btn.pack(pady=10)

    #VITAL SIGNS SECTION
    vitals_frame = ttk.Frame(main_frame)
    vitals_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=10)
    vitals_frame.columnconfigure(0, weight=1)
    vitals_frame.columnconfigure(1, weight=1)
    vitals_frame.columnconfigure(2, weight=1)
    
    create_vital_frame(vitals_frame, 0, 0, "Heart Rate", "hr", vital_labels, color=COLORS["danger"])
    create_vital_frame(vitals_frame, 0, 1, "Blood Pressure", "bp", vital_labels, color=COLORS["primary"])
    create_vital_frame(vitals_frame, 0, 2, "SpO₂", "spo2", vital_labels, color=COLORS["info"])
    
    #ECG GRAPH SECTION
    graph_frame = ttk.Frame(main_frame, style="Card.TFrame")
    graph_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
    
    graph_title = tk.Label(graph_frame, text="ECG Monitoring", 
                          bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                          font=FONTS["title"])
    graph_title.pack(anchor="w", padx=20, pady=(15, 10))
    
    ecg_container = tk.Frame(graph_frame, bg=COLORS["bg_card"], padx=20, pady=10)
    ecg_container.pack(fill=tk.BOTH, expand=True)
    
    ecg_figure = Figure(figsize=(8, 3), dpi=100, facecolor=COLORS["bg_card"])
    ecg_plot = ecg_figure.add_subplot(111)
    
    ecg_plot.set_facecolor(COLORS["bg_card"])
    
    ecg_canvas = FigureCanvasTkAgg(ecg_figure, master=ecg_container)
    ecg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
    
    #FOOTER SECTION
    footer_frame = tk.Frame(main_frame, bg=COLORS["bg_main"])
    footer_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(20, 0))
    
    footer_text = tk.Label(footer_frame, 
                          text="NORA Vitals Monitor v2.0",
                          fg=COLORS["text_secondary"], bg=COLORS["bg_main"],
                          font=FONTS["footer"])
    footer_text.pack(side=tk.RIGHT)
    
    return root


def initialize_servo():
    """Initialize and configure the servo motor"""
    global servo, pwm, is_raspberry_pi
    
    if not is_raspberry_pi:
        print("Running in simulation mode - servo initialization skipped")
        return True
    
    print(f"Initializing servo on GPIO pin {SERVO_PIN}...")
    
    # Try direct PWM control with RPi.GPIO first (more reliable for servos)
    if SERVO_DIRECT_ENABLED:
        try:
            import RPi.GPIO as GPIO
            
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(SERVO_PIN, GPIO.OUT)
            
            # Initialize PWM at 50Hz (standard for servos)
            # SG90 works best at 50Hz (20ms period)
            # Some servos have less jitter at different frequencies, but SG90 is designed for 50Hz
            pwm = GPIO.PWM(SERVO_PIN, 50)
            
            # Calculate duty cycle for initial position (typically 2-12%)
            # For a standard servo at 50Hz, 2.5% duty cycle is 0°, 12.5% is 180°
            # Start at middle position
            initial_duty_cycle = 7.25  # Middle position for SG90 (90°)
            
            # Start PWM and initialize servo
            pwm.start(initial_duty_cycle)
            time.sleep(1.0)  # Allow time for servo to position at startup
            pwm.ChangeDutyCycle(0)  # Stop pulses to prevent jittering during initialization
            print(f"Direct PWM servo control initialized on GPIO pin {SERVO_PIN}")
            
            # Test servo movement
            print("Testing servo movement with direct PWM...")
            try:
                # Test different positions with anti-jitter pattern
                # SG90 specific values for 0°, 90°, and 180°
                print("Moving servo to 2.5% (0°)")
                pwm.ChangeDutyCycle(2.5)  # Move to 0°
                time.sleep(0.5)
                pwm.ChangeDutyCycle(0)    # Stop pulses to prevent jittering
                time.sleep(0.5)
                
                print("Moving servo to 7.25% (90°)")
                pwm.ChangeDutyCycle(7.25)  # Move to 90° (SG90 often needs slightly less than 7.5)
                time.sleep(0.5)
                pwm.ChangeDutyCycle(0)    # Stop pulses to prevent jittering
                time.sleep(0.5)
                
                print("Moving servo to 12.0% (180°)")
                pwm.ChangeDutyCycle(12.0)  # Move to 180° (SG90 often needs 12.0 instead of 12.5)
                time.sleep(0.5)
                pwm.ChangeDutyCycle(0)     # Stop pulses to prevent jittering
                time.sleep(0.5)
                
                # Return to initial position
                print("Moving servo back to 7.25% (90°)")
                pwm.ChangeDutyCycle(7.25)   # Middle position for SG90
                time.sleep(0.3)
                pwm.ChangeDutyCycle(0)     # Stop pulses to prevent jittering
                time.sleep(0.2)
                
                print("Direct PWM servo test complete!")
                
                # Read MCP3008 for testing
                try:
                    from PulseOX.A2D import read_mcp3008_direct
                    _, raw_value = read_mcp3008_direct(0)
                    print(f"MCP3008 test reading: {raw_value}")
                except Exception as e:
                    print(f"MCP3008 reading failed: {e}")
                
                return True
            except Exception as e:
                print(f"Warning: Direct PWM servo test failed: {e}")
                # Continue to try gpiozero as a fallback
        except Exception as e:
            print(f"Failed to initialize direct PWM control: {e}")
            print("Falling back to gpiozero servo control")
    
    # If direct PWM failed or is disabled, try gpiozero
    # Try each pin factory in succession
    factories = [
        ('LGPIOFactory', LGPIOFactory),
        ('RPiGPIOFactory', RPiGPIOFactory),
        ('PiGPIOFactory', PiGPIOFactory),
        ('NativeFactory', NativeFactory)
    ]
    
    for factory_name, factory_class in factories:
        try:
            print(f"Trying gpiozero with {factory_name}...")
            pin_factory = factory_class()
            
            # Initialize servo with explicit pin factory and custom min/max pulse width
            servo = Servo(
                SERVO_PIN,
                pin_factory=pin_factory,
                min_pulse_width=SERVO_MIN_PULSE_WIDTH/1000000,  # Convert to seconds
                max_pulse_width=SERVO_MAX_PULSE_WIDTH/1000000   # Convert to seconds
            )
            
            # Set initial position to minimum (corresponds to 0 flow rate)
            servo.value = SERVO_MAX_VALUE
            print(f"Servo initialized successfully on GPIO pin {SERVO_PIN} using {factory_name}")
            
            # Test servo movement
            print("Testing servo movement...")
            try:
                # Move to different positions to confirm servo is working
                print("Moving servo to 0.0")
                servo.value = 0.0
                time.sleep(0.5)
                print("Moving servo to -0.5")
                servo.value = -0.5
                time.sleep(0.5)
                print("Moving servo to 0.5")
                servo.value = 0.5
                time.sleep(0.5)
                # Return to initial position
                print("Moving servo back to max")
                servo.value = SERVO_MAX_VALUE
                print("Servo test complete!")
            except Exception as e:
                print(f"Warning: Servo test movement failed: {e}")
            
            # Read MCP3008 for testing
            try:
                from PulseOX.A2D import read_mcp3008_direct
                _, raw_value = read_mcp3008_direct(0)
                print(f"MCP3008 test reading: {raw_value}")
            except Exception as e:
                print(f"MCP3008 reading failed: {e}")
            
            return True
        except Exception as e:
            print(f"Failed to initialize with {factory_name}: {e}")
    
    # If we got here, all attempts failed
    print("\nServo initialization failed with all methods!")
    print("Possible solutions:")
    print("1. Ensure you have GPIO libraries installed:")
    print("   sudo apt-get install python3-lgpio python3-rpi.gpio")
    print("   sudo pip install RPi.GPIO lgpio")
    print("2. Try running with sudo: sudo python NORA.py")
    print("3. Verify GPIO permissions (run sudo usermod -a -G gpio $USER)")
    print("4. Check servo wiring - power, ground, signal on correct pins")
    print("5. Continuing in simulation mode...")
    
    # Fallback to simulation mode if initialization fails
    is_raspberry_pi = False
    return False

def cleanup_servo():
    """Clean up servo resources"""
    global servo, pwm
    
    if is_raspberry_pi:
        # Clean up direct PWM if used
        if SERVO_DIRECT_ENABLED and pwm is not None:
            try:
                # Stop PWM
                pwm.stop()
                # Clean up GPIO
                import RPi.GPIO as GPIO
                GPIO.cleanup(SERVO_PIN)
                print("Direct PWM servo resources cleaned up")
            except Exception as e:
                print(f"Error cleaning up direct PWM: {e}")
        
        # Clean up gpiozero if used
        elif servo is not None:
            try:
                servo.detach()
                print("Gpiozero servo resources cleaned up")
            except Exception as e:
                print(f"Error cleaning up gpiozero servo: {e}")
                
        # Clean up any remaining GPIO resources
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            print("All GPIO resources cleaned up")
        except:
            pass

if __name__ == "__main__":
    # Initialize servo motor
    servo_initialized = initialize_servo()
    if not servo_initialized and is_raspberry_pi:
        print("WARNING: Servo motor initialization failed!")
    
    # Initialize PulseOx LED
    pulseox_initialized = initialize_pulseox_led()
    if not pulseox_initialized and is_raspberry_pi:
        print("WARNING: PulseOx LED initialization failed!")
    
    # Initialize I2C and ADS1015 ADC
    adc_initialized = initialize_i2c_adc()
    if not adc_initialized and is_raspberry_pi:
        print("WARNING: ADS1015 ADC initialization failed!")
    
    # Initialize servo position variables
    if is_raspberry_pi and SERVO_DIRECT_ENABLED and pwm is not None:
        servo_current_position = 2.5  # Start at min position (matches initialization)
        servo_target_position = 2.5
    elif is_raspberry_pi and servo is not None:
        servo_current_position = SERVO_MIN_VALUE  # Start at min position
        servo_target_position = SERVO_MIN_VALUE
    
    # Create GUI
    app = create_gui()
    
    # Connect to WebSocket in a separate thread
    socket_thread = threading.Thread(target=connect_to_socket, daemon=True)
    socket_thread.start()
    
    # Start update loops - note the new servo position update function
    update_vitals(app)
    update_volume_given()
    update_flow()
    update_servo_position()  # Start the new dedicated servo control loop

    try:
        # Start the main loop
        app.mainloop()
    finally:
        # Disconnect socket on exit
        if sio.connected:
            sio.disconnect()
        
        # Turn off PulseOx LED
        if is_raspberry_pi and GPIO is not None:
            try:
                GPIO.output(PULSEOX_PIN_LED, GPIO.LOW)
            except:
                pass
        
        # Clean up servo
        cleanup_servo()
        
        # Clean up GPIO
        if is_raspberry_pi and GPIO is not None:
            try:
                GPIO.cleanup()
            except:
                pass