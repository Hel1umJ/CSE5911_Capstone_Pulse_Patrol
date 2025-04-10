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
        from gpiozero import Servo, PWMLED, MCP3008
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
            
        # Import direct SPI for MCP3008
        try:
            import spidev
            print("spidev imported successfully")
        except ImportError:
            print("spidev not available")
            
        print("Running on Raspberry Pi. GPIO libraries imported successfully.")
    except ImportError as e:
        print(f"Warning: GPIO import error: {e}")
        print("Servo control will be simulated.")
        is_raspberry_pi = False
else:
    print("Not running on Raspberry Pi. Servo control will be simulated.")

#TODO: Retrieve sensor data

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
SERVO_PIN = 18  # GPIO pin for servo control (PWM); pin 12 or 6th pin down from top right.
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

PULSEOX_PIN_LED = 17

PULSEOX_SPI_MOSI = 10
PULSEOX_SPI_MISO = 9
PULSEOX_SPI_SCLK = 11
PULSEOX_SPI_CE0 = 8   # Data channel select pin


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
    
    # Get SpO2 from the MCP3008 if available
    try:
        from PulseOX.A2D import read_mcp3008_direct
        _, raw_value = read_mcp3008_direct(0)
        
        # Convert raw value to SpO2 percentage using the simplified approach
        if raw_value > 0:
            # Simple mapping function as a placeholder
            simulated_ratio = 0.5 + (0.7 * (1023 - raw_value) / 1023)
            spo2_value = 110 - (25 * simulated_ratio)
            
            # Clamp to reasonable SpO2 range
            spo2_value = max(70, min(100, int(spo2_value)))
            print(f"SpO2 from sensor: {spo2_value}%")
        else:
            spo2_value = rand.randint(96, 100)  # Use random value as fallback
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

def update_flow():
    """
    Updates the hardware with the current flow rate
    Controls the servo to move from 0 to the angle corresponding to desired_vol
    at a speed determined by flow_rate
    """
    global servo, pwm
    global actual_vol_given
    global vol_given
    global SERVO_MAX_VALUE
    global desired_vol
    
    # Constants for 50 μL syringe
    MAX_SYRINGE_VOLUME = 50.0  # 50 μL syringe
    
    # For direct PWM - SG90 specific duty cycles
    min_duty = 2.5   # 0 degrees - 500μs/20000μs = 2.5% (syringe at 0)
    max_duty = 12.0  # 180 degrees - 2400μs/20000μs = 12.0% (syringe fully depressed)
    
    # Try to read from MCP3008 if available
    try:
        from PulseOX.A2D import read_mcp3008_direct
        _, raw_value = read_mcp3008_direct(0)
        print(f"DEBUG: MCP3008 raw reading: {raw_value}")
    except Exception as e:
        print(f"DEBUG: MCP3008 read error: {e}")
    
    if is_raspberry_pi:
        # Using direct PWM control
        if SERVO_DIRECT_ENABLED and pwm is not None:
            try:
                # Print current state for debugging
                print(f"DEBUG: procedure_running={procedure_running}, flow_rate={flow_rate}, desired_vol={desired_vol}, vol_given={vol_given}")
                
                if procedure_running and flow_rate > 0 and desired_vol > 0:
                    if vol_given < desired_vol:
                        # Calculate what percentage of the target volume has been given
                        # This determines how far along the motion range we should be
                        volume_percentage = vol_given / desired_vol
                        
                        # Calculate the full sweep range for the servo regardless of desired_vol
                        # This ensures we're using the full motion range of the servo
                        target_duty = min_duty + (max_duty - min_duty) * volume_percentage
                        
                        # Set the servo position based on current volume percentage
                        print(f"DEBUG: Volume {vol_given:.2f}/{desired_vol} = {volume_percentage*100:.1f}%")
                        print(f"DEBUG: Setting PWM duty cycle to {target_duty:.2f}%")
                        
                        # Update servo position - force movement by always setting the duty cycle
                        # This is critical to ensure the servo actually moves
                        pwm.ChangeDutyCycle(target_duty)
                        
                        # Give the servo time to move, but don't stop sending the signal
                        # until it really needs to move again
                        time.sleep(0.2)
                    else:
                        # Target volume reached - ensure servo is at final position
                        print(f"DEBUG: Target volume reached: {vol_given:.2f}/{desired_vol}")
                        
                        # Move to the full extent (100% of the range)
                        pwm.ChangeDutyCycle(max_duty)
                        time.sleep(0.3)  # Longer time to ensure position is reached
                        pwm.ChangeDutyCycle(0)  # Stop sending pulses once in position
                elif not procedure_running:
                    # Procedure is not running - reset to initial position
                    print(f"DEBUG: Procedure not running, resetting servo position")
                    pwm.ChangeDutyCycle(min_duty)  # Return to minimum position
                    time.sleep(0.3)
                    pwm.ChangeDutyCycle(0)  # Stop sending pulses once in position
                elif flow_rate == 0:
                    # Flow rate is 0 - maintain current position
                    print(f"DEBUG: Flow rate is 0, maintaining position")
                    # Don't send any signal to maintain position
                
                # Schedule next update
                root.after(100, update_flow)  # Update 10 times per second
                
            except Exception as e:
                print(f"Error controlling servo with direct PWM: {e}")
                print(f"Exception details: {str(e)}")
                return False
                
        # Using gpiozero Servo - similar logic as above but with gpiozero API
        elif servo is not None:
            try:
                # Print current state for debugging
                print(f"DEBUG: (gpiozero) procedure_running={procedure_running}, flow_rate={flow_rate}, desired_vol={desired_vol}, vol_given={vol_given}")
                
                if procedure_running and flow_rate > 0 and desired_vol > 0:
                    if vol_given < desired_vol:
                        # Calculate what percentage of the target volume has been given
                        volume_percentage = vol_given / desired_vol
                        
                        # Map this percentage to the servo's full range (-1 to 1)
                        # For SG90 with gpiozero, we use -1 to 1 range
                        target_position = SERVO_MIN_VALUE + (SERVO_MAX_VALUE - SERVO_MIN_VALUE) * volume_percentage
                        
                        # Update servo position - force movement
                        print(f"DEBUG: Volume {vol_given:.2f}/{desired_vol} = {volume_percentage*100:.1f}%")
                        print(f"DEBUG: Setting servo position to {target_position:.4f}")
                        servo.value = target_position
                    else:
                        # Target volume reached - ensure servo is at final position
                        print(f"DEBUG: Target volume reached, setting final position")
                        servo.value = SERVO_MAX_VALUE  # Move to maximum position
                elif not procedure_running:
                    # Procedure stopped - reset to initial position
                    print(f"DEBUG: Procedure stopped, resetting servo position")
                    servo.value = SERVO_MIN_VALUE  # Return to minimum position
                elif flow_rate == 0:
                    # Flow rate is 0 - maintain current position
                    print(f"DEBUG: Flow rate is 0, maintaining position")
                    # Don't change servo value to maintain position
                
                # Schedule next update
                root.after(100, update_flow)  # Update 10 times per second
                
            except Exception as e:
                print(f"Error controlling servo with gpiozero: {e}")
                print(f"Exception details: {str(e)}")
                return False
        else:
            # No servo control method available
            print("No servo control method available - running in simulation mode")
            root.after(1000, update_flow)
    else:
        # Not running on Pi - simulation mode
        print(f"Servo flow rate set to {flow_rate} μL/min (simulation mode)")
        if procedure_running and flow_rate > 0:
            # We don't increment volume here as that's done in update_volume_given
            print(f"DEBUG: Simulated volume: {vol_given:.2f}/{desired_vol}μL")
        
        root.after(1000, update_flow)
    
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
        
        # Toggle the state
        procedure_running = not procedure_running
        
        # Print debug info
        print(f"DEBUG: Manually toggling procedure to: {'Running' if procedure_running else 'Stopped'}")
        
        if procedure_running:
            # Reset volume given when starting procedure
            vol_given = 0.0
            actual_vol_given = 0.0  # Reset this too 
            
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
        else:
            # Additional debug info when stopping
            print(f"DEBUG: Stopping procedure after delivering {vol_given:.2f}/{desired_vol} μL")
            
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
    
    # Create GUI
    app = create_gui()
    
    # Connect to WebSocket in a separate thread
    socket_thread = threading.Thread(target=connect_to_socket, daemon=True)
    socket_thread.start()
    
    # Start the vital signs update loop
    update_vitals(app)
    update_volume_given()
    update_flow()

    try:
        # Start the main loop
        app.mainloop()
    finally:
        # Disconnect socket on exit
        if sio.connected:
            sio.disconnect()
        
        cleanup_servo()