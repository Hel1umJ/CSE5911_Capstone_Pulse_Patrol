import tkinter as tk
from tkinter import ttk
import random as rand
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk
import socketio
import requests
import time
import threading

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

UPDATE_INTERVAL = 1000 #in ms
vital_labels = {} #dict to store references to each vital's value label; we will use these to update the sensor values
MAX_POINTS = 30 #number of points to store on the graph; 1 point for every tick/update interval

#parallel arrays for graphing purposes.
ecg_data = [] #data buffer to store ekg values
time_axis = [] #data buffer for coordinates on x (time) axis
t_step = 0 #counter to store update tick we are on (for x axis labels)
ecg_plot = None 
ecg_canvas = None

flow_rate = 0 #Default, initial flow rate setting in mL/min (whole number)
flow_rate_changed_locally = False  # Flag to track local changes
socket_connected = False  # Flag to track socket connection status

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
        update_flow(flow_rate)
        
        # Update display (need to use Tkinter's after method to safely update UI from another thread)
        if flow_value_label and 'root' in globals():
            root.after(0, lambda: flow_value_label.config(text=f"{flow_rate}"))

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
    
    #TODO: retrieve sensor information and pass it into set vitals here; return it in format below
    #sensor_info = getSensorInfo()
    sensor_info = {
        "hr": rand.randint(70,80), 
        "spo2": rand.randint(96,100), 
        "bp": (rand.randint(70,80),rand.randint(90,100))
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

def update_flow(flow_rate_value):
    """
    Updates the hardware with the current flow rate
    """
    # Add your hardware control code here
    # This function should take the flow_rate value and
    # send the appropriate signals to your hardware
    
    print(f"Setting hardware flow rate to: {flow_rate_value} mL/min")
    return True  # Return  status


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
                   font=FONTS["subtitle"])
    return btn


def create_gui():
    """
    Section Layout:
    Row 0: Header (spans both columns)
    Row 1: Patient Info (column 0); Flow Rate Control (column 1)
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
    
    #HEADER SECTION
    header_frame = ttk.Frame(main_frame, style="Card.TFrame")
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    
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
    
    #FLOW RATE CONTROL SECTION
    flow_frame = ttk.Frame(main_frame, style="Card.TFrame")
    flow_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
    
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
    
    flow_unit_label = tk.Label(flow_value_frame, text="mL/min",
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
        update_flow(flow_rate)
        
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
        update_flow(flow_rate)
        
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
    
    #VITAL SIGNS SECTION
    vitals_frame = ttk.Frame(main_frame)
    vitals_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)
    vitals_frame.columnconfigure(0, weight=1)
    vitals_frame.columnconfigure(1, weight=1)
    vitals_frame.columnconfigure(2, weight=1)
    
    create_vital_frame(vitals_frame, 0, 0, "Heart Rate", "hr", vital_labels, color=COLORS["danger"])
    create_vital_frame(vitals_frame, 0, 1, "Blood Pressure", "bp", vital_labels, color=COLORS["primary"])
    create_vital_frame(vitals_frame, 0, 2, "SpO₂", "spo2", vital_labels, color=COLORS["info"])
    
    #ECG GRAPH SECTION
    graph_frame = ttk.Frame(main_frame, style="Card.TFrame")
    graph_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
    
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
                          text="NORA Vitals Monitor v2.0 | OSU Pulse Patrol",
                          fg=COLORS["text_secondary"], bg=COLORS["bg_main"],
                          font=FONTS["footer"])
    footer_text.pack(side=tk.RIGHT)
    
    return root

if __name__ == "__main__":
    # Create GUI
    app = create_gui()
    
    # Connect to WebSocket in a separate thread
    socket_thread = threading.Thread(target=connect_to_socket, daemon=True)
    socket_thread.start()
    
    # Start the vital signs update loop
    update_vitals(app)
    
    # Start the main loop
    app.mainloop()
    
    # Disconnect socket on exit
    if sio.connected:
        sio.disconnect()