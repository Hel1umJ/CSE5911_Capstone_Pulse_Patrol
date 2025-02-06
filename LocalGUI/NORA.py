import tkinter as tk
import random as rand
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


#TODO: Retrieve sensor data
#TODO: Send signal back to hardware interface process to actuate the flow rate servo with the current rate

"""
Constants & Data
"""
FONTS = {
    "title": ("Arial", 14, "bold"),
    "subtitle": ("Arial", 12, "bold"),
    "label": ("Arial", 10),
    "bold_label": ("Arial", 10, "bold"),
    "footer": ("Arial", 10, "italic")
}#Tkinter font format is in tuple form; collection of fonts used throughout applet
UPDATE_INTERVAL = 1000 #in ms
vital_labels = {} #dict to store references to each vital's value label; we will use these to update the sensor values
MAX_POINTS = 30 #number of points to store on the graph; 1 point for every tick/update interval

#parallel arrays for graphing purposes.
ecg_data = [] #data buffer to store ekg values
spo2_data = [] #data buffer for blood oxygen values
time_axis = [] #data buffer for coordinates on x (time) axis
t_step = 0 #coutner to store update tick we are on (for x axis labels)
ecg_plot = None 
ecg_canvas = None

"""
Helper Functions
"""

def create_vital_frame(parent, row, label_text, value_text_key, label_dict):
    frame = tk.Frame(parent, bg="white", padx=10, pady=10, bd=2, relief="solid")
    frame.grid(row=row, column=0, sticky="nsew", padx=5, pady=5)
    tk.Label(frame, text=label_text, bg="white", font=FONTS["title"]).pack(side=tk.LEFT)
    val_label = tk.Label(frame, text="", bg="white", font=FONTS["bold_label"])
    val_label.pack(side=tk.RIGHT)

    label_dict[value_text_key] = val_label #store label object in dict so we can easily reference it later
    return frame

def update_vitals(root):
    """
    Called once every UPDATE_INTERVAL to refresh displayed vital values
    """
    global t_step
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
    spo2_data.append(sensor_info["spo2"])
    time_axis.append(t_step)
    t_step = t_step + 1
    if len(ecg_data) > MAX_POINTS:
        ecg_data.pop(0)
        spo2_data.pop(0)
        time_axis.pop(0)

    draw_graphs()

    #TODO: Insert function to control flow rate of medicine here

  
    root.after(UPDATE_INTERVAL, update_vitals, root) #Update with sensor data every 1000ms

def set_vitals(vital_info):
    vital_labels["hr"].config(text=f"{vital_info['hr']} bpm")#heart Rate
    vital_labels["spo2"].config(text=f"{vital_info['spo2']}%")#spo2
    vital_labels["bp"].config(text=f"{vital_info['bp'][0]}/{vital_info['bp'][1]} mmHg")#blood pressure

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

    # SpO₂ plot
    spo2_plot.clear()
    spo2_plot.set_title("SpO₂")
    spo2_plot.set_xlabel("Time (s)")
    spo2_plot.set_ylabel("SpO₂ (%)")
    spo2_plot.set_ylim([0, 110])  # just a fixed Y range for clarity
    spo2_plot.plot(time_axis, spo2_data, color="darkturquoise", marker="o")

    # Now refresh the canvases
    ecg_canvas.draw()
    spo2_canvas.draw()



def create_gui(): # Long, gnarly function to setup tkinter window, frames, grids, and widgets
    # reference global variables for graphing section
    global ecg_plot
    global ecg_canvas 
    global spo2_plot
    global spo2_canvas

    root = tk.Tk()
    root.title("NORA")
    root.geometry("800x600")
    root.configure(bg="white")
    root.minsize(600, 425)#Anything smaller and values are cut off or things fall off the window

    #red border frame
    border_frame = tk.Frame(root, bg="red", bd=2)#bd is width of border
    border_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    #main tkinter frame that all widgets will be added to
    content_frame = tk.Frame(border_frame, bg="white")
    content_frame.pack(expand=True, fill=tk.BOTH, padx=4, pady=4)

    #setup frame rows & columns preemptively; 4 rows, 2 columns
    content_frame.rowconfigure(0, weight=1)
    content_frame.rowconfigure(1, weight=1)
    content_frame.rowconfigure(2, weight=1)
    content_frame.rowconfigure(3, weight=1)
    content_frame.columnconfigure(0, weight=1)
    content_frame.columnconfigure(1, weight=1)


    """
    Row 0: patient info; flow rate
    """
    #Patient info
    patient_frame = tk.Frame(content_frame, bg="white", padx=20, pady=10)
    patient_frame.grid(row=0, column=0, sticky="nw")
    tk.Label(patient_frame, text="Patient: Awesome Anesthesia", bg="white",fg="black", font=FONTS["subtitle"]).pack(anchor="w")
    tk.Label(patient_frame, text="DOB: 2077-01-21", bg="white", fg="black", font=FONTS["label"]).pack(anchor="w")
    tk.Label(patient_frame, text="ID: 123456789", bg="white", fg="black", font=FONTS["label"]).pack(anchor="w")

    #Setup flow rate frame, sub-widgets, and declare nested (nesting bad) helper functions
    flow_frame = tk.Frame(content_frame, bg="white", padx=20, pady=10)
    flow_frame.grid(row=0, column=1, sticky="nw")
    flow_data = {"value": 0.0}
    #Add flow rate title label widget
    tk.Label(flow_frame, text="Flow Rate", bg="white",font=FONTS["title"]).pack(side=tk.TOP, anchor="w")
    #add flow rate label
    flow_label = tk.Label(flow_frame, text="0.0 L/min", fg="blue", bg="white", font=("Arial", 16, "bold"))
    flow_label.pack(side=tk.TOP, anchor="e", pady=5)

    def update_flow_label():
        flow_label.config(text=f"{flow_data['value']:.1f} L/min")

    def increase_flow():
        flow_data["value"] += 0.1
        update_flow_label()

    def decrease_flow():
        if(flow_data["value"] >0): #TODO: For some reason this is still going below 0; maybe float arithmetic error?
            flow_data["value"] -= 0.1
        update_flow_label()

    btn_frame = tk.Frame(flow_frame, bg="white")
    btn_frame.pack(side=tk.TOP, pady=10)

    down_button = tk.Button(btn_frame, text="▼", command=decrease_flow, width=3)
    down_button.pack(side=tk.LEFT, padx=5)

    up_button = tk.Button(btn_frame, text="▲", command=increase_flow, width=3)
    up_button.pack(side=tk.LEFT, padx=5)

    """
    Row 1: Blood Pressure; None
    """
    create_vital_frame(content_frame, 1, "Blood Pressure", "bp", vital_labels)

    """
    Row 2: Heart Rate; ECG Graph
    """
    #Heart Rate
    create_vital_frame(content_frame, 2, "Heart Rate", "hr", vital_labels)

    #ECG Graph
    ecg_frame = tk.Frame(content_frame, bg="white")
    ecg_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

    # We'll create a Matplotlib Figure & Canvas for ECG
    ecg_figure = Figure(figsize=(4, 2), dpi=100)
    ecg_plot = ecg_figure.add_subplot(111)  # single subplot

    ecg_canvas = FigureCanvasTkAgg(ecg_figure, master=ecg_frame)
    ecg_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    #placeholder for the graph
    #ecg_label = tk.Label(content_frame, text="ECG Graph", bg="white", fg="black", font=FONTS["subtitle"])
    #ecg_label.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

    """
    Row 3: spo2; spo2 graph
    """
    #spo2 vital
    create_vital_frame(content_frame, 3, "SpO₂", "spo2", vital_labels)

    #spo2 graph
    spo2_frame = tk.Frame(content_frame, bg="white")
    spo2_frame.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)
    spo2_figure = Figure(figsize=(4, 2), dpi=100)
    spo2_plot = spo2_figure.add_subplot(111)

    spo2_canvas = FigureCanvasTkAgg(spo2_figure, master=spo2_frame)
    spo2_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    ##Placeholder for the graph
    #spo2_graph_label = tk.Label(content_frame, text="SpO₂ Graph", bg="white", fg="black", font=FONTS["subtitle"])
    #spo2_graph_label.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)

    return root

if __name__ == "__main__":
    matplotlib.use("TkAgg")# Use TkAgg (Tkinter) backend
    app = create_gui()
    update_vitals(app) #start periodic updates.
    app.mainloop()