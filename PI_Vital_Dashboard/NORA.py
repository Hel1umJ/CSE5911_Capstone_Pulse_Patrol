import tkinter as tk
import random as rand
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk

#TODO: Retrieve sensor data
#TODO: Send signal back to hardware interface process to actuate the flow rate servo with the current rate (flow rate control)

"""
Constants & Data
"""
FONTS = {
    "title": ("Helvetica", 14, "bold"),
    "subtitle": ("Helvetica", 12, "bold"),
    "label": ("Helvetica", 10),
    "bold_label": ("Helvetica", 18, "bold"),
    "footer": ("Helvetica", 10, "italic")
}#Tkinter font format is in tuple form; collection of fonts used throughout applet
BG_COLOR = "#F4F4F4"
UPDATE_INTERVAL = 1000 #in ms
vital_labels = {} #dict to store references to each vital's value label; we will use these to update the sensor values
MAX_POINTS = 30 #number of points to store on the graph; 1 point for every tick/update interval

#parallel arrays for graphing purposes.
ecg_data = [] #data buffer to store ekg values
#spo2_data = [] #data buffer for blood oxygen values
time_axis = [] #data buffer for coordinates on x (time) axis
t_step = 0 #coutner to store update tick we are on (for x axis labels)
ecg_plot = None 
ecg_canvas = None

flow_rate = 3.0 # Default, initial flow rate setting.


"""
Helper Functions
"""

def create_vital_frame(parent, row, col, label_text, value_key, label_dict):
    frame = tk.Frame(parent, bg=BG_COLOR, padx=10, pady=10, bd=1, relief="groove")
    frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
    tk.Label(frame, text=label_text, bg=BG_COLOR, font=FONTS["title"]).pack(side=tk.LEFT, anchor="w")
    val_label = tk.Label(frame, text="", bg=BG_COLOR, font=("Helvetica", 18, "bold"))
    val_label.pack(side=tk.RIGHT, anchor="e")
    
    label_dict[value_key] = val_label #store label in dict so we can reference it later
    return frame

def update_vitals(root):
    """
    Called once every UPDATE_INTERVAL to refresh displayed vital values
    """
    global t_step
    global flow_rate
    #TODO: retrieve sensor information and pass it into set vitals here; return it in format below
    #sensor_info = getSensorInfo()
    #sensor_info = {"hr": 0, "spo2": 0, "bp": (0,0)}
    sensor_info = {
        "hr": rand.randint(70,75), 
        "spo2": rand.randint(96,100), 
        "bp": (rand.randint(70,80),rand.randint(90,100))
    }

    set_vitals(sensor_info) 

    #Graphing Stuff

    #Note: graphing will be on a rolling basis, and only a rolling window of MAX_POINTS datapoints
    #will be displayed. Any datapoints that fall out of that window will be removed.
    
    # Append data for graphing; update rolling window by chopping off old data.
    ecg_data.append(sensor_info["hr"])
    #spo2_data.append(sensor_info["spo2"])
    time_axis.append(t_step)
    t_step = t_step + 1
    if len(ecg_data) > MAX_POINTS:
        ecg_data.pop(0)
        #spo2_data.pop(0)
        time_axis.pop(0)

    draw_graphs()

    #TODO: Implement flow rate control
    update_flow(flow_rate)
  
    root.after(UPDATE_INTERVAL, update_vitals, root) #Update with sensor data every 1000ms

def update_flow(flow_rate):
    return 1 #TODO: Implement updating of flow rate.


def set_vitals(vital_info):
    vital_labels["hr"].config(text=f"{vital_info['hr']} bpm", fg="red", font=FONTS["bold_label"])#heart Rate
    vital_labels["spo2"].config(text=f"{vital_info['spo2']}%", fg="dodgerblue",font=FONTS["bold_label"])#spo2
    vital_labels["bp"].config(text=f"{vital_info['bp'][0]}/{vital_info['bp'][1]} mmHg", fg="black",font=FONTS["bold_label"])#blood pressure

def draw_graphs():
    """
    Clears & redraws ECG and SpO₂ graphs.
    """
    global ecg_plot
    global ecg_canvas
    global ecg_data
    global spo2_data 
    global time_axis 

    # ECG plot
    ecg_plot.clear()
    ecg_plot.set_title("ECG")
    ecg_plot.set_xlabel("Time (s)")
    ecg_plot.set_ylabel("HR (bpm)")
    ecg_plot.plot(time_axis, ecg_data, color="firebrick", marker="o")
    #ecg_canvas.figure.tight_layout()

    # SpO₂ plot
    #spo2_plot.clear()
    #spo2_plot.set_title("SpO₂")
    #spo2_plot.set_xlabel("Time (s)")
    #spo2_plot.set_ylabel("SpO₂ (%)")
    #spo2_plot.set_ylim([0, 110])  # just a fixed Y range for clarity
    #spo2_plot.plot(time_axis, spo2_data, color="darkturquoise", marker="o")

    ecg_canvas.draw()
    #spo2_canvas.draw()



def create_gui(): # Long, gnarly function to setup tkinter window, frames, grids, and widgets
    # reference global variables for graphing section
    global ecg_plot
    global ecg_canvas 
    #global spo2_plot
    #global spo2_canvas
    
    matplotlib.use("TkAgg")# Use TkAgg (Tkinter) backend for embedded matplot charts.

    root = tk.Tk()
    root.title("NORA")
    root.geometry("750x560")
    root.configure(bg=BG_COLOR)
    root.minsize(750, 560)#Anything smaller and values are cut off or things fall off the window

    ##red border frame
    #border_frame = tk.Frame(root, bg="red", bd=2)#bd is width of border
    #border_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    #main tkinter frame that all widgets will be added to
    content_frame = tk.Frame(root, bg=BG_COLOR)
    content_frame.pack(expand=True, fill=tk.BOTH, padx=4, pady=4)

    #setup frame rows & columns preemptively; 4 rows, 2 columns
    content_frame.rowconfigure(0, weight=0)
    content_frame.rowconfigure(1, weight=0)
    content_frame.rowconfigure(2, weight=0)
    content_frame.rowconfigure(3, weight=0)
    content_frame.rowconfigure(4, weight=0)
    content_frame.rowconfigure(5, weight=1) # Last row is whitespace at bottom of GUI; let it expand, everything else is static
    content_frame.columnconfigure(0, weight=1)
    content_frame.columnconfigure(1, weight=1)


    """
    Row 0: App Name; Logo
    """
    
    try:
        logo_img = Image.open("hospital_logo.jpg")
        logo_img = logo_img.resize((100, 100), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img)
    except Exception as e:
        print("Error loading logo:", e)
        logo_photo = None

    logo_frame = tk.Frame(content_frame, bg=BG_COLOR)
    logo_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=10)
    logo_frame.columnconfigure(0, weight=0)
    logo_frame.columnconfigure(1, weight=1)

    header_label = tk.Label(logo_frame, text="NORA Vitals Monitor", bg=BG_COLOR, fg="black", font=("Helvetica", 20, "bold"))
    header_label.grid(row=0, column=1, sticky="w", padx=20)
    if logo_photo != None:
        logo_label = tk.Label(logo_frame, image=logo_photo, bg=BG_COLOR)
        logo_label.image = logo_photo
        logo_label.grid(row=0, column=0, sticky="w", padx=10)

    """
    Row 1: patient info; None
    """
    #Patient info
    patient_frame = tk.Frame(content_frame, bg=BG_COLOR, padx=20, pady=10)
    patient_frame.grid(row=1, column=0, sticky="nw")
    tk.Label(patient_frame, text="Patient: Awesome Anesthesia", bg=BG_COLOR,fg="black", font=FONTS["subtitle"]).pack(anchor="w")
    tk.Label(patient_frame, text="DOB: 2077-01-21", bg=BG_COLOR, fg="black", font=FONTS["label"]).pack(anchor="w")
    tk.Label(patient_frame, text="ID: 123456789", bg=BG_COLOR, fg="black", font=FONTS["label"]).pack(anchor="w")

    """
    Row 2: Blood Pressure; Flow
    """
    #Blood pressure vital
    create_vital_frame(content_frame, row=2, col=0, label_text="Blood Pressure", value_key="bp", label_dict=vital_labels)

    """
    Row 3: Spo2; Flow
    """
    create_vital_frame(content_frame, row=3, col=0, label_text="SpO₂", value_key="spo2", label_dict=vital_labels)

    """
    Row 2&3 Flow Widget
    """
    #Setup flow rate frame, sub-widgets, and declare nested (nesting bad) helper functions
    flow_frame = tk.Frame(content_frame, bg=BG_COLOR, padx=20, pady=10)
    flow_frame.grid(row=2, column=1, rowspan=2, sticky="nsew") #Rowspan sets it to take up 2 rows in parent grid
    flow_data = {"value": flow_rate}

    tk.Label(flow_frame, text="Flow Rate", bg=BG_COLOR,
             font=FONTS["title"]).pack(side=tk.TOP, anchor="w")
    flow_label = tk.Label(flow_frame, text=f"{flow_rate} L/min", fg="blue",
                          bg=BG_COLOR, font=("Helvetica", 16, "bold"))
    flow_label.pack(side=tk.TOP, pady=5)

    def update_flow_label():
        flow_label.config(text=f"{flow_data['value']:.1f} L/min")

    def increase_flow():
        flow_data["value"] += 0.1
        update_flow_label()

    def decrease_flow():
        if flow_data["value"] > 0:
            flow_data["value"] -= 0.1
        update_flow_label()

    btn_frame = tk.Frame(flow_frame, bg=BG_COLOR)
    btn_frame.pack(side=tk.TOP, pady=10)
    down_button = tk.Button(btn_frame, text="▼", command=decrease_flow, width=3)
    down_button.pack(side=tk.LEFT, padx=5)
    up_button = tk.Button(btn_frame, text="▲", command=increase_flow, width=3)
    up_button.pack(side=tk.LEFT, padx=5)

   
    """
    Row 4: Heart Rate; ECG Graph
    """
    
    #Heart Rate
    create_vital_frame(content_frame, 4, 0, "Heart Rate", "hr", vital_labels)

    #ECG Graph
    ecg_frame = tk.Frame(content_frame, bg=BG_COLOR)
    ecg_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=5)

    # We'll create a Matplotlib Figure & Canvas for ECG
    ecg_figure = Figure(figsize=(4, 2), dpi=100)
    ecg_plot = ecg_figure.add_subplot(111)  # single subplot

    ecg_canvas = FigureCanvasTkAgg(ecg_figure, master=ecg_frame)
    ecg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    #placeholder for the graph
    #ecg_label = tk.Label(content_frame, text="ECG Graph", bg=BG_COLOR, fg="black", font=FONTS["subtitle"])
    #ecg_label.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)

    return root

if __name__ == "__main__":
    app = create_gui()
    update_vitals(app) #start periodic updates.
    app.mainloop()