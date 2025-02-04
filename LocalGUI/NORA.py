import tkinter as tk
import random as rand

#TODO: insert SPO2 & ECG Graphs
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
   
    #TODO: retrieve sensor information and pass it into set vitals here; return it in format below
    #sensor_info = getSensorInfo()
    #sensor_info = {"hr": 0, "spo2": 0, "bp": (0,0)}
    sensor_info = {"hr": rand.randint(60,110), "spo2": rand.randint(90,100), "bp": (rand.randint(70,80),rand.randint(90,110))}
    set_vitals(sensor_info) 
    #draw_graphs() #TODO: Once graphs are added, populate this method and uncomment 

    root.after(UPDATE_INTERVAL, update_vitals, root) #Update with sensor data every 1000ms

def set_vitals(vital_info):
    vital_labels["hr"].config(text=f"{vital_info['hr']} bpm")#heart Rate
    vital_labels["spo2"].config(text=f"{vital_info['spo2']}%")#spo2
    vital_labels["bp"].config(text=f"{vital_info['bp'][0]}/{vital_info['bp'][1]} mmHg")#blood pressure


def create_gui(): # Long, gnarly function to setup tkinter window, frames, grids, and widgets
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
    create_vital_frame(content_frame, 2, "Heart Rate", "hr", vital_labels)

    #TODO: Remove this; this is just a placeholder for the graph
    ecg_label = tk.Label(content_frame, text="ECG Graph", bg="white", fg="black", font=FONTS["subtitle"])
    ecg_label.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

    """
    Row 3: spo2; spo2 graph
    """
    create_vital_frame(content_frame, 3, "SpO₂", "spo2", vital_labels)

    #TODO: Remove this; this is just a placeholder for the graph
    spo2_graph_label = tk.Label(content_frame, text="SpO₂ Graph", bg="white", fg="black", font=FONTS["subtitle"])
    spo2_graph_label.grid(row=3, column=1, sticky="nsew", padx=5, pady=5)

    return root

if __name__ == "__main__":
    app = create_gui()
    update_vitals(app) #start periodic updates.
    app.mainloop()








#TODO: Base your graphing utility off of this.


##import tkinter for GUI
#import tkinter as tk
#from tkinter import ttk
##font types
#LARGE_FONT = ("Verdana", 12)

##import stuff for graph
#import matplotlib
#import matplotlib.ticker as mticker
#from matplotlib import pyplot as plt
#matplotlib.use("TkAgg")
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
#from matplotlib.figure import Figure

##import animation to make graph live
#import matplotlib.animation as animation
#from matplotlib import style
##style.use("seaborn-darkgrid")
##animate function
#f = Figure(figsize=(20,20), dpi=100)
#plot1 = f.add_subplot(211)
#plot2 = f.add_subplot(212)
#def animate(ii):
#    pullData = open("/media/pi/68D2-7E93/test2.csv","r").read()
#    dataList = pullData.split('\n')
#    tList = []
#    vList = []
#    v1List = []
#    for eachLine in dataList:
#        if len(eachLine) >1:
#            timedate, t, voltage, voltage1 = eachLine.split(',')
#            tList.append(float(t))
#            vList.append(float(voltage))
#            v1List.append(float(voltage1))

#    #plot graphs
#    plot1.clear()
#    plot1.plot(tList, vList, 'r')
#    plot2.clear()
#    plot2.plot(tList, v1List, 'b')
#    #add labels and config axis
#    plot1.set_title("Aquaponic Sensors")
#    plot1.set_autoscaley_on(False)
#    plot1.set_autoscalex_on(False)
#    plot1.set_ylabel("pH (v)")
#    #plot1.set_xlim(t-60,t)
#    #plot1.axes.set_ybound(0,1)
#    #plot1.set_ylim(2,4)
#    #plot1.set_xlim(500, 510)

#    plot2.set_ylabel("Temperature (v)")
#    plot2.set_xlabel("Time (s)")
#    #plot2.set_ybound(0,5)



##initialization
#class AllWindow(tk.Tk):
#    def __init__(self, *args, **kwargs):
#        tk.Tk.__init__(self, *args, **kwargs)
#        #add title
#        tk.Tk.wm_title(self, "NU Aquaponics")

#        container = tk.Frame(self)      
#        container.pack(side="top", fill="both", expand=True)      
#        container.grid_rowconfigure(0, weight=1)
#        container.grid_columnconfigure(0, weight=1)      
#        #show the frames
#        self.frames = {}
#        for F in (HomePage, ControlPanel, Settings):
#            frame = F(container, self)
#            self.frames[F] = frame
#            frame.grid(row=0, column=0, sticky="nsew")
#        self.show_frame(HomePage)

#    def show_frame(self, cont):       
#        frame = self.frames[cont]
#        frame.tkraise()


##add home page
#class HomePage(tk.Frame):
#    def __init__(self, parent, controller):
#        tk.Frame.__init__(self,parent)
#        label = tk.Label(self, text="Dashboard", font = LARGE_FONT)
#        label.pack(pady=10, padx=10)

#        #quit button
#        quitButton = tk.Button(self, text="QUIT", fg='red',
#                                command=quit)
#        quitButton.pack()
#        #navigation button
#        navibutton1 = ttk.Button(self, text="Control Panel",
#                            command=lambda: controller.show_frame(ControlPanel))
#        navibutton1.pack()
#        navibutton2 = ttk.Button(self, text="Settings",
#                            command=lambda: controller.show_frame(Settings))
#        navibutton2.pack()

#        #add graph to dashboard

#        #bring up canvas
#        canvas = FigureCanvasTkAgg(f, self)
#        canvas.draw()
#        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand = True)
#        #add navigation bar
#        toolbar = NavigationToolbar2Tk(canvas, self)
#        toolbar.update()
#        canvas._tkcanvas.pack()
#        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand = True)


##add control panel page
#class ControlPanel(tk.Frame):
#    def __init__(self, parent, controller):
#        tk.Frame.__init__(self, parent)
#        label = tk.Label(self, text="Control Panel", font = LARGE_FONT)
#        label.pack(pady=10, padx=10)

#        #control buttons
#        self.lightButton = tk.Button(self,
#                             text="Light OFF",
#                             bg= "red",
#                             command=self.toggle_light)
#        self.lightButton.pack()

#        #navigation button
#        navibutton1 = ttk.Button(self, text="Back to Dashboard",
#                            command=lambda: controller.show_frame(HomePage))
#        navibutton1.pack()
#        navibutton2 = ttk.Button(self, text="Settings",
#                            command=lambda: controller.show_frame(Settings))
#        navibutton2.pack()

#        #fcns triggered by control button
#        #fcn to turn LED on or off
#    def toggle_light(self):
#        #if LED1.value == 0:
#     #       LED1.value = 1
#        #change light button color
#            self.lightButton.configure(bg= "green")
#            self.lightButton.configure(fg= "white")
#            self.lightButton.configure(text = "Light ON")
#    #    else:
#    #  #      LED1.value = 0
#    #    #change light button color to red if light off
#    #        self.lightButton.configure(bg= "red")
#    #        self.lightButton.configure(text = "Light OFF")
##add settings page
#class Settings(tk.Frame):
#    def __init__(self, parent, controller):
#        tk.Frame.__init__(self, parent)
#        label = tk.Label(self, text="Settings", font = LARGE_FONT)
#        label.pack(pady=10, padx=10)
#        #navigation button
#        navibutton1 = ttk.Button(self, text="Back to Dashboard",
#                            command=lambda: controller.show_frame(HomePage))
#        navibutton1.pack()
#        navibutton2 = ttk.Button(self, text="Go to Control Panel",
#                            command=lambda: controller.show_frame(ControlPanel))
#        navibutton2.pack()

#app = AllWindow()
#app.geometry('1025x690')
##update animation first
#ani = animation.FuncAnimation(f, animate, interval=1000)
#app.mainloop()
