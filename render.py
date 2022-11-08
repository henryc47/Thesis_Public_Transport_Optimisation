#display.py
#responsible for displaying a visualisation of activity on the network

import tkinter as tk
import time as time
import pandas as pd
import numpy as np 
import network as n
import evaluator as e
import warnings as warnings
import cProfile as profile
import pstats
from os import path
from pstats import SortKey


class Display:

    #create the Display object
    def __init__(self):
        self.setup_display_constants() #set display constants which control default appearace of edges and nodes
        self.set_default_flags() #set the flags and modes of the rendering engine to be their default value
        self.setup_window() #create the display window, where all of our GUI will be displayed
        self.setup_canvas() #create the canvas where we can draw edges and nodes and vehicles
        self.setup_main_controls() #setup the widgets which will allow us to control the simulation and visualisation

    ##SETUP FUNCTIONS

    #setup the constants which control the default physical appearance of the network display
    def setup_display_constants(self):
        #node constants 
        self.max_node_radius = 30 #maximum node radius if node size scaled
        self.default_node_radius = 5 #node size if nodes unscaled
        self.min_node_radius = 2 #minimum node size if nodes scaled
        self.custom_node_exponent = 3 #how does node radii scale with amount of stuff happening at that node (if nodes scaled)  
        self.default_node_colour = 'grey' #node colour if nodes uncoloured
        #edge constants
        self.default_edge_width = 2 #default width of an edge
        self.active_width_addition = 2 #how much will the edge grow in size when clicked on
        self.min_edge_width = 1 #minimum width of an edge if edges scaled
        self.max_edge_width = 10 #maximum width of an edge if edges scaled
        self.custom_edge_exponent = 2 #how does edge width scale with amount of stuff happening at that edge (if edge scaled)
        self.default_edge_colour = 'black' #what colour will an edge be by default 
        self.path_edge_colour = 'magenta' #what colour will an edge which is part of the drawn path be
        self.path_edge_width = 3 #what width will an edge which is part of the drawn path be
        #vehicle constants
        self.default_vehicle_length = 3
        self.default_vehicle_colour = 'blue'
        #node text constants
        self.default_node_text_colour = 'black'
        self.default_edge_text_colour = 'purple'
        #scroll constants
        self.scroll_gain = 1 #how rapid should pan and scanning be
        #id of text above nodes at ends of activated edges, needs to be deleted when the edge is left
        self.text_id_line_end = -1 #default value, to indicate no such object
        self.text_id_line_start = -1 #default value, to indicate no such object
        self.sim_frame_time = 1 #how many seconds between simulation view updates, reciprocal of frame-rate
        #index of vehicle text popups
        self.index_vehicle_text_popup = -1 #default value, to indicate no such object
        self.name_vehicle_text_popup = -1 #default value, to indicate no such object
        #default vehicle capacities, used for determining vehicle colours based on crowding levels
        #note standing capacity is standing + seated capacity
        self.vehicle_seated_capacity = 960 #sydney trains A/B class, 8 carriage
        self.vehicle_standing_capacity = 1680 #sydney trains A/B class, 8 carriage, roughly 4 pax/m^2 open space

    #set the various flags (and modes) used by the rendering engine to their default value
    def set_default_flags(self):
        self.first_render_flag = True #is this the first render of the visualisation for a network?
        self.simulation_setup_flag = False #has the simulation setup (eg trip distribution) been done already?
        self.simulation_run_flag = False #has the simulation been run yet?
        self.simulation_view_flag = False #is the simulation currently being viewed
        self.simulation_past_vehicles_flag = False #are old vehicles from previous simulations still displayed
        self.secondary_control_mode = 'none' #which set of secondary controls (eg network_viz tools,simulation_viz_tools ) is being displayed
        self.last_node_left_click_index = -1 #index of last node left-clicked, -1 indicates that no nodes have been clicked yet
        self.last_node_right_click_index = -1 #index of last node right-clicked, -1 indicates that no nodes have been right clicked yet
        self.path_edge_arrows = True #will arrows be drawn on plotted routes between nodes, indicating direction of travel

    #setup the window object, in which all of our GUI will be contained
    def setup_window(self): 
        window = tk.Tk()
        window.attributes("-fullscreen", True) #make the window full screen
        #window.eval('tk::PlaceWindow . center')
        window.title('Network Simulation')
        window_width = window.winfo_screenwidth()
        window_height = window.winfo_screenheight()
        center_x = int(window_width/2)
        center_y = int(window_height/2)
        #window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        #window.geometry(f'{window_width}x{window_height}') #this code renders the window in the corret position
        self.window = window

    #setup the canvas object, on which we draw our represention of the network
    def setup_canvas(self):
        window_width = self.window.winfo_screenwidth()
        window_height = self.window.winfo_screenheight()
        self.canvas_width = window_width-440
        self.canvas_height = window_height-100
        self.canvas_center_x = int(self.canvas_width/2)
        self.canvas_center_y = int(self.canvas_height/2)
        self.canvas = tk.Canvas(self.window, bg="white", height=self.canvas_height, width=self.canvas_width)
        self.canvas.pack(side = tk.RIGHT) 
        #bind canvas to scroll options
        self.canvas.bind("<MouseWheel>",self.zoom_canvas)
        self.canvas.bind("<ButtonPress-1>",self.pan_start)
        self.canvas.bind("<B1-Motion>",self.pan_end)
        self.current_zoom = 1 #current zoom level
        self.current_zoom_offset_x = 0 #how much is the display x origin offset from the true x origin
        self.current_zoom_offset_y = 0 #how much is the display y origin offset from the true y origin
        
    #setup the main control options
    def setup_main_controls(self):
        #create the control panel
        self.main_controls = tk.Frame(master=self.window)
        #self.main_controls.pack(side = tk.LEFT,anchor=tk.N)
        self.main_controls.place(x=0,y=50)
        #default file paths
        default_nodes = 'nodes_sydney.csv'
        default_edges = 'edges_sydney.csv'
        default_schedule = 'schedule_sydney.csv'
        default_segment_schedule = 'schedule_segments_sydney.csv'
        default_parameters = 'parameters_sydney.csv'
        default_eval = 'eval_sydney.csv'
        default_scenario = 'ScenarioFixed.csv'
        #options
        #verbose option, determines level of logging to the console
        self.verbose = -1 #default level of logging is  0=none, 1=verbose, 2=super verbose, -1 is placeholder for setup
        self.verbose_button = tk.Button(master=self.main_controls,fg='black',bg='white',command=self.verbose_button_click,width=20)
        self.verbose_button.pack(side = tk.TOP)
        self.verbose_button_click() #display initial message
        #label and input to import node files
        self.node_file_path_label = tk.Label(master=self.main_controls,text='NODE FILE PATH',fg='black',bg='white',width=20)
        self.node_file_path_label.pack()
        self.node_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20)
        self.node_file_path_entry.insert(0,default_nodes)
        self.node_file_path_entry.pack()
        #label and input to import edge files
        self.edge_file_path_label = tk.Label(master=self.main_controls,text='EDGE FILE PATH',fg='black',bg='white',width=20)
        self.edge_file_path_label.pack()
        self.edge_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20)
        self.edge_file_path_entry.insert(0,default_edges)
        self.edge_file_path_entry.pack()
        #label and input to import schedule files
        self.schedule_file_path_label = tk.Label(master=self.main_controls,text='SCHEDULE FILE PATH',fg='black',bg='white',width=20)
        self.schedule_file_path_label.pack()
        self.schedule_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20)
        self.schedule_file_path_entry.insert(0,default_schedule)
        self.schedule_file_path_entry.pack()
        #including the segment files which are used to construct more complex schedules
        self.schedule_segment_file_path_label = tk.Label(master=self.main_controls,text='SEGMENTS FILE PATH',fg='black',bg='white',width=20)
        self.schedule_segment_file_path_label.pack()
        #note that an empty schedule will cause us to use the simple method of schedule extraction
        self.schedule_segment_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20) 
        self.schedule_segment_file_path_entry.insert(0,default_segment_schedule)
        self.schedule_segment_file_path_entry.pack()
        #csv file for importing the network parameters
        self.parameters_file_path_label = tk.Label(master=self.main_controls,text='PARAMETERS FILE PATH',fg='black',bg='white',width=20)
        self.parameters_file_path_label.pack()
        self.parameters_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20)
        self.parameters_file_path_entry.insert(0,default_parameters)
        self.parameters_file_path_entry.pack()
        #csv file for importing evaluation costs
        self.eval_file_path_label = tk.Label(master=self.main_controls,text='EVALUATION FILE PATH',fg='black',bg='white',width=20)
        self.eval_file_path_label.pack()
        self.eval_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20)
        self.eval_file_path_entry.insert(0,default_eval)
        self.eval_file_path_entry.pack()   
        #csv file for importing scenario info
        self.scenario_file_path_label = tk.Label(master=self.main_controls,text='SCENARIO FILE PATH',fg='black',bg='white',width=20)
        self.scenario_file_path_label.pack()
        self.scenario_file_path_entry = tk.Entry(master=self.main_controls,fg='black',bg='white',width=20)
        self.scenario_file_path_entry.insert(0,default_scenario)
        self.scenario_file_path_entry.pack()   
        #control for importing files 
        self.import_files_button = tk.Button(master=self.main_controls,text='IMPORT FILES',fg='black',bg='white',command=self.import_files_click,width=20)
        self.import_files_button.pack()
        #this button will draw the network
        self.draw_network_button = tk.Button(master=self.main_controls,text="DRAW NETWORK",fg='black',bg='white',command=self.draw_network_click,width=20)
        self.draw_network_button.pack()
        #create a button to select whether to display all node names
        self.node_names_button = tk.Button(master=self.main_controls,text="HOVER NODE NAMES",fg='black',bg='white',command=self.node_names_click,width=20,height=1)
        self.node_names_button.pack()
        self.node_names_mode = 'no_names'
        #this button will setup the simulation
        self.setup_simulation_button = tk.Button(master=self.main_controls,text="SETUP SIMULATION",fg='black',bg='white',command=self.setup_simulation_click,width=20)
        self.setup_simulation_button.pack()
        #this button will run the basic simulation
        #self.run_simulation_button = tk.Button(master=self.main_controls,text="RUN SIMULATION",fg='black',bg='white',command=self.run_simulation_click,width=20)
        #this option with profiling
        self.run_simulation_button = tk.Button(master=self.main_controls,text="RUN SIMULATION",fg='black',bg='white',command=self.run_simulation_click,width=20)
        self.run_simulation_button.pack()
        #this button will play back the basic simulation
        self.view_simulation_button = tk.Button(master=self.main_controls,text="VIEW SIMULATION",fg='black',bg='white',command=self.view_simulation_click,width=20)
        self.view_simulation_button.pack()
        #this label will provide information to the user
        self.message_header = tk.Label(master=self.main_controls,text='MESSAGE',fg='black',bg='white',width=20)
        self.message_header.pack()
        self.message = tk.Label(master=self.main_controls,text='',fg='black',bg='white',width=20,height=5)
        self.message.pack()
        #run evaluation button
        self.run_evaluation_button = tk.Button(master=self.main_controls,text="RUN EVALUATION",fg='black',bg='white',command=self.run_evaluation_click,width=20)
        self.run_evaluation_button.pack()
        #set optimiser
        self.optimiser_label = tk.Label(master=self.main_controls,text="TIMETABLE OPTIMISER",fg='black',bg='white',width=20)
        self.optimiser_label.pack()
        self.optimiser_button = tk.Button(master=self.main_controls,text="CSV TIMETABLE",fg='black',bg='white',width=20,command=self.switch_optimiser)
        self.optimiser_button.pack()
        self.optimiser = 'hardcoded'
        #create the underlying visulisation controls
        #this button will allow choosing different types of controls
        self.secondary_controls = tk.Frame(master=self.window)
        self.secondary_controls.place(x=220,y=50)
        #self.control_mode_select_button = tk.Button(master=self.secondary_controls,text="CONTROL SELECT",fg='black',bg='white',command=self.control_mode_select_click,width=20)
        #self.control_mode_select_button.pack()
        #self.control_mode = 'none'
        self.setup_network_viz_tools()
        self.setup_simulation_viz_tools()
        #they are created hidden, and will be unhidden later

    #CLICK FUNCTIONS FOR MAIN CONTROL
    def switch_optimiser(self):
        if self.optimiser=="hardcoded":
            self.optimiser_button.config(text="HENRY CONVEX")
            self.optimiser = 'henry_convex'
        else:
            self.optimiser_button.config(text="CSV TIMETABLE")
            self.optimiser = 'hardcoded'
        if self.simulation_setup_flag==True:
            self.message_update('note you must resetup the simulation to apply a new optimiser')

    def run_evaluation_click(self):
        if self.simulation_run_flag==True:
            evaluator_message = self.evaluator.evaluate(self.sim_times,self.sim_vehicle_passengers,self.sim_node_passengers,self.num_failed_passengers,self.num_successful_passengers)
            self.message_update('please see terminal\n for evaluation printout')
            print(evaluator_message)
        
        elif self.simulation_run_flag==False:
            self.message_update('simulation must be \n run for evaluation')
            self.log_print('simulation must be run for evaluation')

    #callback for button which allows us to switch between control modes for viewing network info vs controls for viewing simulation results
    def control_mode_select_click(self):
        #update control mode
        if self.control_mode == 'none':
            if self.simulation_setup_flag == True:
                self.control_mode = 'network_viz'
            elif self.simulation_run_flag == True:
                self.control_mode = 'simulation_viz'
            else:
                self.log_print("SETUP AND RUN SIMULATION TO VIEW RESULTS")
                self.message_update("SETUP AND RUN SIMULATION \n TO VIEW RESULTS")
                self.control_mode = 'none'
        elif self.control_mode == 'network_viz':
            if self.simulation_run_flag == True:
                self.control_mode = 'simulation_viz'
            else:
                self.log_print("SETUP AND RUN SIMULATION TO VIEW RESULTS")
                self.message_update("RUN SIMULATION \n TO VIEW SIMULATION RESULTS")
                self.control_mode = 'none'
            
        elif self.control_mode == 'simulation_viz':
            self.control_mode = 'none'
        
        self.control_mode_update() #now that the control has been selected, perform the tasks associated with updating the control mode

    #update the displayed controls so that we can switch between viewing different types of info
    def control_mode_update(self):
        if self.control_mode == 'none':
            #no controls will be displayed
            self.control_mode_select_button.config(text='CONTROL SELECT')
            self.clear_network_viz_tools()
            self.clear_simulation_viz_tools()
        elif self.control_mode == 'network_viz':
            #display controls for viewing unsimulated aspects of the network
            self.control_mode_select_button.config(text='NETWORK VIEW CONTROLS')
            self.clear_simulation_viz_tools()
            self.view_network_viz_tools()   
        elif self.control_mode == 'simulation_viz':
            #display controls for viewing simulation results
            self.control_mode_select_button.config(text='SIMULATION VIEW CONTROLS')
            self.clear_network_viz_tools()
            self.view_simulation_viz_tools()

    #attempt to import the selected files
    def import_files_click(self):
        #extract the file paths from the entry widgets
        node_files_path = self.node_file_path_entry.get()
        edge_files_path = self.edge_file_path_entry.get()
        schedule_files_path = self.schedule_file_path_entry.get()
        schedule_segment_files_path = self.schedule_segment_file_path_entry.get()
        parameter_files_path = self.parameters_file_path_entry.get()
        eval_files_path = self.eval_file_path_entry.get()
        scenario_files_path = self.scenario_file_path_entry.get()
        #check that each file path is valid, and if so, import the file
        node_path_valid = path.isfile(node_files_path)
        edge_path_valid = path.isfile(edge_files_path)
        schedule_path_valid = path.isfile(schedule_files_path)
        parameter_path_valid = path.isfile(parameter_files_path)
        eval_path_valid = path.isfile(eval_files_path)
        scenario_path_valid = path.isfile(scenario_files_path)
        #determine type of schedule
        if schedule_segment_files_path == "":
            #we won't be using schedule segments to construct our schedule
            self.schedule_type = "simple"
            segment_path_valid = True #we are not using the segment path, so it might as well be valid
            self.log_print("using simple schedule generation")
        else:
            #we will be using schedule segments to construct our schedule
            self.schedule_type = "complex"
            segment_path_valid = path.isfile(schedule_segment_files_path)
            self.log_print("using complex schedule generation")
        
        #if user path invalid, inform the user of this
        import_files_message = ""
        import_successful = True #assume we imported unless it fails
        if node_path_valid==False:
            import_files_message = import_files_message + node_files_path + " is not a valid file \n"
            self.log_print(node_files_path + " is not a valid file")
            import_successful = False
        if edge_path_valid==False:
            import_files_message = import_files_message + edge_files_path + " is not a valid file \n"
            self.log_print(edge_files_path + " is not a valid file")
            import_successful = False
        if schedule_path_valid==False:
            import_files_message = import_files_message + schedule_files_path + " is not a valid file \n"
            self.log_print(schedule_files_path + " is not a valid file")
            import_successful = False
        if segment_path_valid == False:
            import_files_message = import_files_message + schedule_segment_files_path + " is not a valid file \n"
            self.log_print(schedule_segment_files_path + " is not a valid file")
            import_successful = False
        if parameter_path_valid == False:
            import_files_message = import_files_message + parameter_files_path + " is not a valid file \n"
            self.log_print(parameter_files_path + " is not a valid file")
            import_successful = False
        if eval_path_valid == False:
            import_files_message = import_files_message + eval_files_path + " is not a valid file \n"
            self.log_print(eval_files_path + " is not a valid file")
            import_successful = False
        if scenario_path_valid == False:
            import_files_message = import_files_message + scenario_files_path + " is not a valid file \n"
            self.log_print(scenario_files_path + " is not a valid file")
            import_successful = False

        if import_successful:
            #if file path is valid, actually import the files
            import_files_message = import_files_message + "files are valid \n"
            #try and import the nodes
            try:
                self.nodes_csv = pd.read_csv(node_files_path,thousands=r',')
            except:
                import_files_message = import_files_message + " import of " + node_files_path + " failed \n not a valid csv file\n"
                import_successful = False
            #try and import the edges
            try:
                self.edges_csv = pd.read_csv(edge_files_path,thousands=r',')
            except:
                import_files_message = import_files_message + " import of " + edge_files_path + " failed  \n not a valid csv file\n"
                import_successful = False
            #try and import the schedule
            try:
                self.schedule_csv = pd.read_csv(schedule_files_path,thousands=r',')
            except:
                import_files_message = import_files_message + " import of " + schedule_files_path + " failed  \n not a valid csv file\n"
                import_successful = False
            #try and import the network/simulation parameters
            try:
                self.parameter_csv = pd.read_csv(parameter_files_path,thousands=r',')
            except:
                import_files_message = import_files_message + " import of " + parameter_files_path  + " failed  \n not a valid csv file\n"
                import_successful = False
            try:
                self.eval_csv = pd.read_csv(eval_files_path,thousands=r',')
            except:
                import_files_message = import_files_message + " import of " + eval_files_path  + " failed  \n not a valid csv file\n"
                import_successful = False
            try:
                self.scenario_csv = pd.read_csv(scenario_files_path,thousands=r',')
            except:
                import_files_message = import_files_message + " import of " + scenario_files_path  + " failed  \n not a valid csv file\n"
            #if we are in complex schedule mode, try and import segment info
            if self.schedule_type=='complex':
                try:
                    self.schedule_segments_csv = pd.read_csv(schedule_segment_files_path,thousands=r',',keep_default_na=False)
                    #keep_default_na false so that empty values in a column are
                except:
                    import_files_message = import_files_message + " import of " + schedule_segment_files_path + " failed  \n not a valid csv file\n"
                    import_successful = False
            elif self.schedule_type=='simple':
                self.schedule_segments_csv = "" #we don't need the schedule segments file in simple scheduling
        
        #print a relevant message if import successful
        if import_successful:
            import_files_message = import_files_message + " files imported successfully"
            self.simulation_setup_flag = False #we have not setup the simulation for the new files
        else:
            import_files_message = import_files_message + " file import failed"
        
        #print the message about the result of importing files
        self.message_update(import_files_message)

    #draw the network from the imported files
    def draw_network_click(self):      
        if self.first_render_flag==False:
            self.erase_network_graph()
            self.erase_all_nodes_text('both')
            self.erase_all_edges_text()
        if self.simulation_setup_flag:
            self.erase_all_edges_text() 
        self.extract_nodes_graph()
        self.calculate_node_position()
        self.extract_edges_graph()
        self.calculate_edges_midpoints()
        self.render_graph()
        self.first_render_flag = False

    #setup the simulated network
    def setup_simulation_click(self):
        #we need to draw the network before we can setup up the simulation
        if self.first_render_flag==True:
            self.draw_network_click()
        
        time1 = time.time()
        self.sim_network = n.Network(nodes_csv=self.nodes_csv,edges_csv=self.edges_csv,schedule_csv=self.schedule_csv,parameters_csv=self.parameter_csv,verbose=self.verbose,segment_csv=self.schedule_segments_csv,eval_csv=self.eval_csv,scenario_csv=self.scenario_csv,schedule_type=self.schedule_type,optimiser=self.optimiser)
        time2 = time.time()
        simulation_setup_message = "simulation setup in \n" +  "{:.3f}".format(time2-time1) + " seconds"
        self.log_print(simulation_setup_message)
        self.message_update(simulation_setup_message)
        #if self.simulation_setup_flag:   #only setup network visulisation tools if they have not already been created
        #    #if they have been recreated we need to destroy the old tools
        #    self.clear_network_viz_tools()
        #    self.setup_network_viz_tools()
        #else:
        #    self.setup_network_viz_tools() #setup tools for exploring aspects of the simulated network
        #also setup the evaulator
        self.setup_evaluator()
        self.simulation_setup_flag = True #flag to indicate that the simulation has been setup

    def setup_evaluator(self):
        self.evaluator = e.Evaluator(self.eval_csv,self.parameter_csv)

    #run the simulation click using Cprofile to determine running times
    def profile_run_simulation_click(self):
        profile.runctx("self.run_simulation_click()",globals(),locals(), 'restats')
        #print how long inside the function call does each called function take
        p = pstats.Stats('restats')
        p.strip_dirs()
        p.sort_stats(SortKey.TIME)
        p.print_stats()

    #run the basic simulation
    def run_simulation_click(self):
        if self.simulation_setup_flag == True:
            simulation_start_message = 'simulation started'
            self.log_print(simulation_start_message)
            self.message_update(simulation_start_message)
            time1 = time.time()
            self.sim_times,self.sim_vehicle_latitudes,self.sim_vehicle_longitudes,self.sim_vehicle_names,self.sim_vehicle_passengers,self.sim_node_passengers,self.num_failed_passengers,self.num_successful_passengers,self.sim_time_taken = self.sim_network.basic_sim() #run the simulation and store the data
            self.setup_default_sim_current_values() #set default values for information about specific timesteps
            self.simulation_run_flag = True #simulation has been run and relevant values have been stored
            time2 = time.time()
            simulation_finished_message = "simulation finished in \n " + "{:.3f}".format(time2-time1) + " seconds \n The simulation represented \n" + str(self.sim_time_taken) + " minutes"
            self.log_print(simulation_finished_message)
            self.message_update(simulation_finished_message)
        else:
            self.message_update('simulation not yet setup \n cannot run')
            self.log_print('simulation not yet setup cannot run')
    
    #set default values for current sim variables, to avoid errors if we try and render them outside of a timestep
    def setup_default_sim_current_values(self):
        num_nodes = len(self.node_names)
        self.sim_node_current_passengers = np.zeros(num_nodes)
        self.sim_vehicles_current_names = []
        self.sim_vehicles_current_latitudes = []
        self.sim_vehicles_current_longitudes = []
        self.sim_vehicles_current_passengers = []
        self.sim_vehicles_current_colour = []
        self.sim_vehicles_current_length = []

    def view_simulation_click(self):
        if self.simulation_run_flag == False: #simulation needs to be run to be displayed
            self.message_update('simulation not yet run \n run simulation to view results')
            self.log_print('simulation not yet run,  run simulation to view results')
        elif self.simulation_run_flag == True:
            #go through all time
            if self.simulation_view_flag == True:
                #continue the current simulation if it is already being viewed
                self.message_update('simulation already \n being viewed')
                self.log_print('simulation already being viewed')
            else:
                if self.simulation_past_vehicles_flag == True:
                    #we need to delete any lingering past vehicles
                    self.derender_vehicles(override=True)
                self.num_sim_times = len(self.sim_times)
                time_index = 0
                #self.render_simulation_update(time_index)
                self.render_simulation_update(time_index) 

    #render a simulation update after a delay
    def render_simulation_update(self,index):
        if self.paused == False: #if we are playing back the simulation, play the next frame
            start_render_time = time.time() #get the time at the start of renderings
            end_render_time = start_render_time + self.sim_frame_time  #calculate what time we need to move to the next frame to maintain a steady frame-rate
            #extract the data for the current timestep
            sim_time = self.sim_times[index]
            #update the time display
            time_text = 'TIME ' + str(sim_time)
            self.time_label.config(text=time_text)
            #extract other information from the calculate vehicles
            self.extract_current_vehicles_info(index) #extract info about the vehicles in the current simulation timesteps
            self.update_vehicle_text_index() #update the index of the vehicle whose info we are displaying as a popup
            self.extract_current_nodes_info(index) #extract info about the nodes in the current simulation timesteps
            self.calculate_vehicle_position() #calculate the position of the vehicles in the network
            self.simulation_view_flag = True #simulation view has been setup
            self.update_nodes()
            self.update_text_same_node() 
            self.generate_edge_overlay_text()
            #after rendering, wait till we reach the time set for the next visual update
            remaining_frame_time = end_render_time-time.time()
            index = index + 1 #index of the next batch of data
            if index>=self.num_sim_times: #we have finished displaying the simulation
                self.log_print("Simulation Display Finished")
                self.message_update("Simulated Display Finished")
                self.simulation_view_flag = False #simulation is no longer being run
                self.simulation_past_vehicles_flag = True #past vehicles still exist that will need to be deleted if we replay the simulation
            elif index < self.num_sim_times:
                #call the callback again once we have waited long enough
                self.time_label.after(int(remaining_frame_time*1000),self.render_simulation_update,index)
        if self.paused == True:
            self.time_label.after(10,self.render_simulation_update,index) #check to see if we are still paused 100 times per second
    
    #update the index of the vehicle whose info we are displaying as a popup
    def update_vehicle_text_index(self):
        try:
            #get the new index of the vehicle
            new_index = self.sim_vehicles_current_names.index(self.name_vehicle_text_popup) 
        except ValueError:
            #in this case, the vehicle no longer exists
            #hence delete text popups
            #delete text popups
            self.derender_hover_vehicle_text()
            #and reset index of vehicle whom we are providing info about
            self.name_vehicle_text_popup = -1
            self.index_vehicle_text_popup = -1
        else:
            #change the stored index to reflect the new position in the list of current vehicles
            self.index_vehicle_text_popup = new_index

    def extract_current_vehicles_info(self,index):
        #extract the info for the current time (given by index)
        self.sim_vehicles_current_names = self.sim_vehicle_names[index]
        self.sim_vehicles_current_latitudes = self.sim_vehicle_latitudes[index]
        self.sim_vehicles_current_longitudes = self.sim_vehicle_longitudes[index]
        self.sim_vehicles_current_passengers = self.sim_vehicle_passengers[index]

    def extract_current_nodes_info(self,index):
        #extract the info for the current time (given by index)
        self.sim_node_current_passengers = self.sim_node_passengers[index]

    #switch logging levels (verbosity level)
    def verbose_button_click(self):
        if self.verbose==0:
            self.verbose_button.config(text='VERBOSE')
            self.verbose = 1
        elif self.verbose==1:
            self.verbose_button.config(text='SUPER VERBOSE')
            self.verbose = 2
        else: #if verbosity already at highest level or is unset, select minimum verbosity 
            self.verbose_button.config(text='NO LOGGING')
            self.verbose = 0
        if self.simulation_setup_flag == True:#also update the logging level in the simulation if it exists
            self.log_print('SIMULATION LOG LEVEL UPDATED TO '+ str(self.verbose),2)
            self.sim_network.verbose = self.verbose

    #NETWORK VIZ TOOLS
    #tools for exploring aspects of the simulated network which do not depend on actual simulation
    #eg ideal journey times and paths, and passenger trip distribution

    #setup these tools
    def setup_network_viz_tools(self):
        #create the overall frame
        self.network_viz = tk.Frame(master=self.secondary_controls)
        #self.network_viz.pack(side = tk.TOP)
        self.network_viz_label = tk.Label(master=self.network_viz,text='NETWORK VIEW OPTIONS',fg='white',bg='cyan',width=20)
        self.network_viz_label.pack()
        #A label for the too/from select button
        self.display_mode_label = tk.Label(master=self.network_viz,text='DIRECTION SELECT',fg='black',bg='white',width=20)
        self.display_mode_label.pack()
        #create a button to choose whether we are viewing information "from" a node or "too" a node
        self.too_from_select_button = tk.Button(master=self.network_viz,text="FROM NODE",fg='black',bg='white',command=self.too_from_select_click,width=20)
        self.too_from_select_button.pack()
        self.from_node = True #True = from_node, False= too_node
        #create a button to choose which edge direction will be used for edge related plotting
        self.edge_direction_button = tk.Button(master=self.network_viz,text="BOTH EDGE DIRECTIONS",fg='black',bg='white',command=self.edge_direction_select_click,width=20)
        self.edge_direction_button.pack()
        self.edge_direction_mode = 'both'
        #A label for the nodes numeric overlay button
        self.nodes_numeric_overlay_label = tk.Label(master=self.network_viz,text='NUMERIC OVERLAY MODE',fg='black',bg='white',width=20)
        self.nodes_numeric_overlay_label.pack()
        #create a button to select whether to provide a numeric overlay on the canvas to provide information about node relationships
        self.nodes_numeric_overlay_button = tk.Button(master=self.network_viz,text="NO NODE OVERLAY",fg='black',bg='white',command=self.nodes_numeric_overlay_click,width=20,height=2)
        self.nodes_numeric_overlay_button.pack()
        self.nodes_numeric_overlay_mode = 'no_info'
        #create a button to select whether to provide a numeric overlay on the canvas to provide information about edges
        self.edges_numeric_overlay_button = tk.Button(master=self.network_viz,text="NO EDGE OVERLAY",fg='black',bg='white',command=self.edges_numeric_overlay_click,width=20,height=2)
        self.edges_numeric_overlay_button.pack()
        self.edges_numeric_overlay_mode = 'no_info'
        #A label for the node appearance controls
        self.nodes_appearance_label = tk.Label(master=self.network_viz,text='NODE APPEARANCE',fg='black',bg='white',width=20)
        self.nodes_appearance_label.pack()
        #create a button to select whether to use the size of nodes to provide information about nodes and their relationships
        self.node_size_button = tk.Button(master=self.network_viz,text="CONSTANT NODE SIZE",fg='black',bg='white',command=self.node_size_click,width=20,height=2)
        self.node_size_button.pack()
        self.node_size_type = "constant" #by default, nodes will be a constant size
        #a button to select whether to use the colour of nodes to provide information about node relationships
        self.node_colour_button = tk.Button(master=self.network_viz,text="CONSTANT NODE COLOUR",fg='black',bg='white',command=self.node_colour_click,width=20,height=2)
        self.node_colour_button.pack()
        self.node_colour_type = "constant"
        #A label for the edge appearance controls
        self.edges_appearance_label = tk.Label(master=self.network_viz,text='EDGE APPEARANCE',fg='black',bg='white',width=20)
        self.edges_appearance_label.pack()
        #create a button to select whether to use the size of edges to provide information about the edges
        self.edge_width_button = tk.Button(master=self.network_viz,text="CONSTANT EDGE WIDTH",fg='black',bg='white',command=self.edge_width_click,width=20,height=2)
        self.edge_width_button.pack()
        self.edge_width_type = "constant" #by default, edges will be a constant size
        #create a button to select whether to use the colour of edges to provide information about the edges
        self.edge_colour_button = tk.Button(master=self.network_viz,text="CONSTANT EDGE COLOUR",fg='black',bg='white',command=self.edge_colour_click,width=20,height=2)
        self.edge_colour_button.pack()
        self.edge_colour_type = "constant" #by default, edges will be a constant size
        self.secondary_control_mode = 'network_viz' #network viz mode is being displayed
        self.network_viz.pack()

    def setup_simulation_viz_tools(self):
        #create the overall frame
        self.secondary_control_mode = 'simulation_viz' #simulation viz mode is being displayed
        self.simulation_viz = tk.Frame(master=self.secondary_controls)
        #label for simulation viz mode
        self.simulation_viz_label = tk.Label(master=self.simulation_viz,text='SIM VIEW OPTIONS',fg='white',bg='cyan',width=20)
        self.simulation_viz_label.pack()
        #create a label to display the time
        self.time_label = tk.Label(master=self.simulation_viz,text='TIME',fg='black',bg='white',width=20)
        self.time_label.pack()
        #create a button to enable us to control whether the simulation is running
        self.pause_play_button = tk.Button(master=self.simulation_viz,text='PLAYING',fg='black',bg='white',width=20,command=self.pause_play_button_click)
        self.paused = False #simulation visualisation starts paused
        self.pause_play_button.pack()
        #create controlsn to enable us to control the speed of the simulation
        #first a label to indicate this
        #note the label is set for self.sim_frame_time = 1
        self.simulation_speed_label = tk.Label(master=self.simulation_viz,text='UPDATES PER SECOND = 1',fg='black',bg='white',width=20)
        self.simulation_speed_label.pack()
        #add a entry to enable us to enter the frame speed
        self.simulation_speed_entry = tk.Entry(master=self.simulation_viz,fg='black',bg='white',width=20)
        self.simulation_speed_entry.insert(0,self.sim_frame_time)
        self.simulation_speed_entry.pack()
        #add a button to update the frame speed
        self.simulation_speed_update_button = tk.Button(master=self.simulation_viz,text='UPDATE SPEED',fg='black',bg='white',command=self.simulation_speed_update_click,width=20)
        self.simulation_speed_update_button.pack()
        #add controls for vehicle appearance rendering
        self.vehicle_appearance_label = tk.Label(master=self.simulation_viz,text='VEHICLE APPEARANCE',fg='black',bg='white',width=20)
        self.vehicle_appearance_label.pack()
        #add button to control vehicle colour
        self.vehicle_colour_button = tk.Button(master=self.simulation_viz,text="VEHICLE COLOUR BASED \n ON CROWDING",fg='black',bg='white',command=self.vehicle_colour_click,width=20,height=2)
        self.vehicle_colour_type = "crowding" #by default, vehicle colours will be based off the level of crowding in the vehicle
        self.vehicle_colour_button.pack()
        self.simulation_viz.pack()

    def vehicle_colour_click(self):
        if self.vehicle_colour_type == "crowding":
            self.vehicle_colour_type = "constant"
        elif self.vehicle_colour_type == "constant":
            self.vehicle_colour_type = "crowding"
        
        self.vehicle_colour_button_text_update()
        self.calculate_vehicle_position #rerender vehicles to match the new colour scheme 
    
    def vehicle_colour_button_text_update(self):
        if self.vehicle_colour_type == "crowding":
            self.vehicle_colour_button.config(text="VEHICLE COLOUR BASED \n ON CROWDING")
        elif self.vehicle_colour_type == "constant":
            self.vehicle_colour_button.config(text="CONSTANT")
    

    def simulation_speed_update_click(self):
        #extract the new updates per second
        new_updates_per_second = self.simulation_speed_entry.get()
        try:
            #if it can be convert to a float 
            new_updates_per_second = float(new_updates_per_second)

        except:
            error_text = str(new_updates_per_second) + " Is not numeric, please enter a numeric frame-rate"
            self.log_print(error_text)
        else:
            #calculate the new time between frames
            self.sim_frame_time = 1/new_updates_per_second
            updates_per_second_text = 'UPDATES/SECOND = ' + str(new_updates_per_second)
            self.simulation_speed_label.config(text=updates_per_second_text)

       
    #control whether the simulation visulisation is paused or playing
    def pause_play_button_click(self):
        if self.paused == True:
            self.paused = False
            self.pause_play_button.config(text="PLAYING")
        elif self.paused == False:
            self.paused = True
            self.pause_play_button.config(text="PAUSED")

    #hide the network_viz tool controls 
    def clear_network_viz_tools(self):
        if self.secondary_control_mode == 'network_viz':
            self.network_viz.pack_forget() #hide the network viz controls

    #redisplay the network_viz tools
    def view_network_viz_tools(self):
        self.network_viz.pack(side = tk.TOP)
        self.secondary_control_mode = 'network_viz'

    #hide the network_viz tool controls 
    def clear_simulation_viz_tools(self):
        if self.secondary_control_mode == 'simulation_viz':
            self.simulation_viz.pack_forget() #hide the simulation viz controls

    def view_simulation_viz_tools(self):
        self.simulation_viz.pack(side = tk.TOP)
        self.secondary_control_mode = 'simulation_viz'

    #CLICK FUNCTIONS FOR NETWORK VIZ TOOLS
    #command for button to switch between displaying and not displaying node names
    def node_names_click(self):
        #update mode
        if self.node_names_mode == 'no_names':
            self.node_names_mode = 'display_names'
        elif self.node_names_mode == 'display_names':
            self.node_names_mode = 'no_names'
        #perform the actual update of the button and the rendering
        self.node_names_update()    
    
    #perform the actual update between displaying and not displaying node names
    def node_names_update(self):
        if self.node_names_mode == 'no_names':
            self.node_names_button.config(text="HOVER NODE NAMES")
            self.erase_all_nodes_text(mode='above') #clear away node name text
        elif self.node_names_mode == 'display_names':
            self.node_names_button.config(text="DISPLAY NODE NAMES")
            self.display_text_info_node(self.node_names,where_mode='above') #display node names on the map


    #command for button to switch whether numeric information (eg num passengers) will be displayed next to all relevant nodes
    def nodes_numeric_overlay_click(self):
        if self.nodes_numeric_overlay_mode == 'no_info': #switch to node total mode, where the total traffic too/from each node is displayed
            self.nodes_numeric_overlay_mode = 'node_total'  

        elif self.nodes_numeric_overlay_mode == 'node_total':#switch to node relative mode, where the traffic too/from the key node is displayed
            self.nodes_numeric_overlay_mode = 'node_relative'

        elif self.nodes_numeric_overlay_mode == 'node_relative':#switch to distance mode, where the distance too/from the key node is displayed
            self.nodes_numeric_overlay_mode = 'node_distance'

        elif self.nodes_numeric_overlay_mode == 'node_distance' and self.simulation_run_flag==True:
            #if simulation has been run, switch to a mode where we display the actual number of waiting passengers (at each simulation timestep)
            self.nodes_numeric_overlay_mode = 'waiting_passengers'
        
        else: #switch back to the default mode of no numeric overlay
            self.nodes_numeric_overlay_mode = 'no_info'

        self.nodes_numeric_overlay_button_text_update() #update the text on the button
        self.update_text_same_node() #update the numeric overlay

    #update the text in the nodes numeric overlay button
    def nodes_numeric_overlay_button_text_update(self):
        text = "INVALID MODE FOR \n NODES NUMERIC OVERLAY"
        if self.nodes_numeric_overlay_mode == 'no_info':
            text = "NO NODE OVERLAY"
        elif self.nodes_numeric_overlay_mode == 'node_total':
            if self.from_node: 
               text="NODES OVERLAY \n TOTAL TRAFFIC FROM NODES"
            else:
                text="NODES OVERLAY \n TOTAL TRAFFIC TOO NODES"
        elif self.nodes_numeric_overlay_mode == 'node_relative':
            if self.from_node: 
               text="NODES OVERLAY TRAFFIC \n FROM CLICKED NODE"
            else:
                text="NODES OVERLAY TRAFFIC \n TOO CLICKED NODE"
        elif self.nodes_numeric_overlay_mode == 'node_distance':
            if self.from_node: 
               text="NODES OVERLAY DISTANCE \n FROM CLICKED NODE"
            else:
                text="NODES OVERLAY DISTANCE \n TOO CLICKED NODE"
        
        elif self.nodes_numeric_overlay_mode == 'waiting_passengers':
            text = "NODE OVERLAY \n PASSENGERS AT NODE"
        self.nodes_numeric_overlay_button.config(text=text)

    #command for button to switch whether edge statistics will be displayed forward/reverse
    def edge_direction_select_click(self):
        if self.edge_direction_mode == 'both':
             self.edge_direction_button.config(text='FORWARD EDGE DIRECTION')
             self.edge_direction_mode = 'forward'
        elif self.edge_direction_mode == 'forward':
            self.edge_direction_button.config(text='REVERSE EDGE DIRECTION')
            self.edge_direction_mode = 'reverse'
        elif self.edge_direction_mode == 'reverse':
            self.edge_direction_button.config(text='BOTH EDGE DIRECTIONS')
            self.edge_direction_mode = 'both'
        
        self.edges_overlay_button_text_update()  #update the text on the button
        self.generate_edge_overlay_text()       #update the overlay rendering
        self.edge_width_button_text_update() #update the text on the buttons
        self.edge_colour_button_text_update()
        self.update_edges() #update the rendering of the edges
           
    #command for button to switch whether numeric information (eg num passengers) will be displayed along relevant edges
    def edges_numeric_overlay_click(self):
        if self.edges_numeric_overlay_mode == 'no_info': #switch to distance mode, where the length of the node forward/reverse is displayed
            self.edges_numeric_overlay_mode = 'distance'
        elif self.edges_numeric_overlay_mode == 'distance':
            self.edges_numeric_overlay_mode = 'traffic' #switch to each traffic, where the amount of traffic forward/reverse an edge is displayed
        elif self.edges_numeric_overlay_mode == 'traffic':
            self.edges_numeric_overlay_mode = 'total_traffic' #switch to total traffic, where the combined amount of traffic on an edge is displayed
        else:
            self.edges_numeric_overlay_mode = 'no_info' #switch back to the default mode of no numeric overlay
    

        self.edges_overlay_button_text_update() #update the text on the button
        self.generate_edge_overlay_text()       #update the overlay rendering

    #function to correctly set the text for the edges numeric overlay button
    def edges_overlay_button_text_update(self):
        if self.edges_numeric_overlay_mode == 'no_info': 
            self.edges_numeric_overlay_button.config(text="NO EDGE OVERLAY")
        elif self.edges_numeric_overlay_mode == 'distance':
            if self.edge_direction_mode == 'both':
                self.edges_numeric_overlay_button.config(text="FORWARD + REVERSE \n EDGE TRAVEL TIME")
            elif self.edge_direction_mode == 'forward':
                self.edges_numeric_overlay_button.config(text="FORWARD EDGE \n TRAVEL TIME")
            elif self.edge_direction_mode == 'reverse':
                self.edges_numeric_overlay_button.config(text="REVERSE EDGE \n TRAVEL TIME")

        elif self.edges_numeric_overlay_mode == 'traffic':
            if self.edge_direction_mode == 'both':
                self.edges_numeric_overlay_button.config(text="FORWARD + REVERSE \n EDGE TRAFFIC")
            elif self.edge_direction_mode == 'forward':
                self.edges_numeric_overlay_button.config(text="FORWARD TRAFFIC \n THROUGH EDGE")
            elif self.edge_direction_mode == 'reverse':
                self.edges_numeric_overlay_button.config(text="REVERSE TRAFFIC \n THROUGH EDGE")

        elif self.edges_numeric_overlay_mode == 'total_traffic':
            self.edges_numeric_overlay_button.config(text="TOTAL TRAFFIC \n THROUGH EDGE")
            
    #command for button to switch between options for setting node size
    def node_size_click(self):
        #switch to the new mode
        if self.node_size_type == "constant":
            #switch to mode where node size is based on traffic going too/from the clicked node to other nodes
            self.node_size_type = "node_relative"
        elif self.node_size_type == "node_relative":
            #switch to mode where node size is based on total traffic coming too/from the clicked node
            self.node_size_type = "node_total" 
        elif self.node_size_type == "node_total":
            #switch to mode where node size is based on the number of waiting passengers
            self.node_size_type = "node_passengers"
        elif self.node_size_type == "node_passengers":
            self.node_size_type = "constant"
        #update the text of the button
        self.node_size_button_text_update()
        #rerender the nodes to be of the correct size
        self.update_nodes()

    #command for the node size button to update to the correct text for it's mode of operation
    def node_size_button_text_update(self):
        if self.node_size_type == "node_relative":
            if self.from_node:
                self.node_size_button.config(text="NODE SIZE TRAFFIC \n FROM CLICKED NODE")
            else:
                self.node_size_button.config(text="NODE SIZE TRAFFIC \n TO CLICKED NODE")
        elif self.node_size_type == "node_total":
            if self.from_node:   
                self.node_size_button.config(text="NODE SIZE TOTAL TRAFFIC \n FROM NODE")
            else:
                self.node_size_button.config(text="NODE SIZE TOTAL TRAFFIC \n TO NODE")
        elif self.node_size_type == "constant":
            self.node_size_button.config(text="CONSTANT NODE SIZE")
        elif self.node_size_type == "node_passengers":
            self.node_size_button.config(text="NODE SIZE NUM PASSENGES \n WAITING AT NODE")
    
    #command for button to switch between options for setting node colour
    def node_colour_click(self):
        if self.node_colour_type == "constant":
            #switch to mode where node colour is based on journey distance to/from clicked node
            self.node_colour_type = "distance"
        elif self.node_colour_type == "distance":
            #switch to mode where node colour is based on total traffic coming too/from the clicked node
            self.node_colour_type = "node_relative"
        elif self.node_colour_type == "node_relative":
            #switch to mode where node colour is based on traffic going too/from the clicked node to other nodes
            self.node_colour_type = "node_total"
        elif self.node_colour_type=="node_total":
            #switch to node colour being based on number of passengers waiting at the node
            self.node_colour_type = "node_passengers"    
        elif self.node_colour_type == "node_passengers":
            #switch to constant node colour
            self.node_colour_type = "constant"
            
        
        #update the text of the button
        self.node_colour_button_text_update()
        #rerender the nodes to be of the correct colour
        self.update_nodes()

    #command for the node colour button to update to the correct text for it's mode of operation
    def node_colour_button_text_update(self):
        if self.node_colour_type == "distance":
            if self.from_node:
                self.node_colour_button.config(text="NODE COLOUR DISTANCE \n FROM CLICKED NODE")
            else:
                self.node_colour_button.config(text="NODE COLOUR DISTANCE \n TO CLICKED NODE")
        elif self.node_colour_type == "node_relative":
            if self.from_node:
                self.node_colour_button.config(text="NODE COLOUR TRAFFIC \n FROM CLICKED NODE")
            else:
                self.node_colour_button.config(text="NODE COLOUR TRAFFIC \n TO CLICKED NODE")
        elif self.node_colour_type == "node_total":
            if self.from_node:   
                self.node_colour_button.config(text="NODE COLOUR TOTAL TRAFFIC \n FROM NODE")
            else:
                self.node_colour_button.config(text="NODE COLOUR TOTAL TRAFFIC \n TO NODE") 
        elif self.node_colour_type=="constant":
            self.node_colour_button.config(text="CONSTANT NODE COLOUR")
        elif self.node_colour_type=="node_passengers":
            self.node_colour_button.config(text="NODE COLOUR NUM PASSENGERS \n WAITING AT NODE")

    #command for the edge width button to switch between options for setting edge width 
    def edge_width_click(self):
        #switch to the new mode
        if self.edge_width_type == "constant":
            #switch to mode where edge width is based on traffic going forward/reverse through nodes
            self.edge_width_type = "traffic"
        elif self.edge_width_type == "traffic":
            #switch to mode where edge width is constant
            self.edge_width_type = "constant"

        #update the text of the button
        self.edge_width_button_text_update()
        #rerender the nodes to be of the correct size
        self.update_edges() 

     #command for the edge width button to update to the correct text for it's mode of operation
    def edge_width_button_text_update(self):
        if self.edge_width_type == "constant":
            self.edge_width_button.config(text="CONSTANT EDGE WIDTH")
        elif self.edge_width_type == "traffic":
            if self.edge_direction_mode == 'forward':
                self.edge_width_button.config(text="EDGE WIDTH \n FORWARD TRAFFIC")
            elif self.edge_direction_mode == 'reverse':
                self.edge_width_button.config(text="EDGE WIDTH \n REVERSE TRAFFIC")
            elif self.edge_direction_mode == 'both':
                self.edge_width_button.config(text="EDGE WIDTH \n COMBINED TRAFFIC")

    #command for the edge colour button
    def edge_colour_click(self):
        #switch to the new mode
        if self.edge_colour_type == "constant":
            #switch to mode where edge colour is based on traffic going forward/reverse through nodes
            self.edge_colour_type = "traffic"
        elif self.edge_colour_type == "traffic":
            #switch to mode where edge colour is based on travel time
            self.edge_colour_type = "time"
        elif self.edge_colour_type == "time":
            #switch to mode where edge colour is constant
            self.edge_colour_type = "constant"

        #update the text of the button
        self.edge_colour_button_text_update()
        #rerender the nodes to be of the correct size
        self.update_edges()

    #function to update the text of the edge colour button
    def edge_colour_button_text_update(self):
        if self.edge_colour_type == "constant":
            self.edge_colour_button.config(text="CONSTANT EDGE COLOUR")
        elif self.edge_colour_type == "traffic":
            if self.edge_direction_mode == 'forward':
                self.edge_colour_button.config(text="EDGE COLOUR \n FORWARD TRAFFIC")
            elif self.edge_direction_mode == 'reverse':
                self.edge_colour_button.config(text="EDGE COLOUR \n REVERSE TRAFFIC")
            elif self.edge_direction_mode == 'both':
                self.edge_colour_button.config(text="EDGE COLOUR \n COMBINED TRAFFIC")

        elif self.edge_colour_type == "time":
            if self.edge_direction_mode == 'forward':
                self.edge_colour_button.config(text="EDGE COLOUR \n FORWARD TRAVEL TIME")
            elif self.edge_direction_mode == 'reverse':
                self.edge_colour_button.config(text="EDGE COLOUR \n REVERSE TRAVEL TIME")
            elif self.edge_direction_mode == 'both':
                self.edge_colour_button.config(text="EDGE COLOUR \n AVERAGE TRAVEL TIME")
        

    #switch between viewing information too a node or from a node
    def too_from_select_click(self):
        if self.from_node:
            self.from_node = False
            self.too_from_select_button.config(text='TOO NODE')
            self.update_text_same_node()
        else:
            self.from_node = True
            self.too_from_select_button.config(text='FROM NODE')
            self.update_text_same_node()

        #update the other buttons text
        self.nodes_numeric_overlay_button_text_update()
        self.node_colour_button_text_update()
        self.node_size_button_text_update()

    #FUNCTIONS TO DETERMINE NODE SIZE/COLOUR

    #set node sizes in accordance with the mode choosen
    def set_node_sizes(self):
        num_nodes = len(self.node_names)
        if self.node_size_type =="constant":
            self.nodes_radii = [self.default_node_radius]*num_nodes
            
        elif self.node_size_type == "node_relative":
            if self.last_node_left_click_index == -1:
                self.nodes_radii = [self.default_node_radius]*num_nodes
                self.message_update("click on a node to set node sizes based on traffic too/from that node") #node sizes will not be updated till users click on a node
            else:
                if self.from_node:
                    trips = self.sim_network.origin_destination_trips[self.last_node_left_click_index,:] #extract number of trips starting from this node
                    total = np.sum(trips)
                else:
                    trips = self.sim_network.origin_destination_trips[:,self.last_node_left_click_index] #extract number of trips going to this node
                    total = np.sum(trips)
                self.calculate_node_sizes(trips,total)

        elif self.node_size_type == "node_total":
            total = np.sum(self.sim_network.origin_destination_trips) #use the total number of trips
            if self.from_node:
                trips = np.sum(self.sim_network.origin_destination_trips,0) #extract number of trips starting from all nodes
            else:
                trips = np.sum(self.sim_network.origin_destination_trips,1) #extract number of trips ending at all nodes
            self.calculate_node_sizes(trips,total)
        
        elif self.node_size_type == "node_passengers":
            passengers = self.sim_node_current_passengers
            total = np.sum(self.sim_network.origin_destination_trips) #use the total number of trips, we need a constant total to prevent nodes shrinking as number of passengers grows
            self.calculate_node_sizes(passengers,total)
        else:
            warnings.warn("node_size_type " + self.node_size_type + " not yet impleneted using constant node size instead")
            #other modes not yet implemented, use constant node sizes instead
            self.nodes_radii = [self.default_node_radius]*num_nodes


    #set node colours in accordance with the mode choosen
    def set_node_colours(self):
        num_nodes = len(self.node_names)
        if self.node_colour_type =="constant":
            self.nodes_colour = [self.default_node_colour]*num_nodes
        
        #set colour based on number of journeys too/from node to clicked node
        elif self.node_colour_type == "node_relative":
            if self.last_node_left_click_index == -1:
                self.nodes_colour = [self.default_node_colour]*num_nodes    
                self.message_update("click on a node to set node colours based on traffic too/from that node") #users need to select a node to update the colours
            else:
                if self.from_node:
                    trips = self.sim_network.origin_destination_trips[self.last_node_left_click_index,:] #extract number of trips starting from this node
                    total = np.sum(trips)
                else:
                    trips = self.sim_network.origin_destination_trips[:,self.last_node_left_click_index] #extract number of trips going to this node
                    total = np.sum(trips)
                self.calculate_node_colours(trips,total)

        #set colour based on journeys too/from node in total
        elif self.node_colour_type == "node_total":
            total = np.sum(self.sim_network.origin_destination_trips) #use the total number of trips
            if self.from_node:
                trips = np.sum(self.sim_network.origin_destination_trips,0) #extract number of trips starting from all nodes
            else:
                trips = np.sum(self.sim_network.origin_destination_trips,1) #extract number of trips ending at all nodes
            self.calculate_node_colours(trips,total)

        #set node colour based on ideal distance to clicked node
        elif self.node_colour_type == "distance":
            if self.last_node_left_click_index == -1:
                self.nodes_colour = [self.default_node_colour]*num_nodes    
                self.message_update("click on a node to set node colours based on distance too/from that node") #users need to select a node to update the colours
            else:
                max_time = np.amax(self.sim_network.distance_to_all)
                if self.from_node:
                    times = self.sim_network.distance_to_all[self.last_node_left_click_index,:] #extract journey times starting at this node
                else:
                    times = self.sim_network.distance_to_all[:,self.last_node_left_click_index] #extract journey times going to this node
                self.calculate_node_colours(times,max_time,mode='linear')
        
        #set node colour based on number of passengers waiting at the node
        elif self.node_colour_type== "node_passengers":
            passengers = self.sim_node_current_passengers
            total = np.sum(self.sim_network.origin_destination_trips) #use the total number of trips, we need a constant total to prevent nodes shrinking as number of passengers grows
            self.calculate_node_colours(passengers,total)

    #calculate_node_sizes based on provided information
    def calculate_node_sizes(self,nodes_quantity,total_quantity,mode='default'):
        total_quantity = total_quantity + 1 #add 1 to prevent divide by zero errors
        num_nodes = len(nodes_quantity)
        for i in range(num_nodes):
            node_fraction = nodes_quantity[i]/total_quantity#fraction of total amount occuring at that node
            self.nodes_radii[i] = (node_fraction**(1/self.custom_node_exponent))*self.max_node_radius
            if self.nodes_radii[i] < self.min_node_radius: #enforce the minimum size of a node
                self.nodes_radii[i] = self.min_node_radius

    #calculate and perform final setting of node colour based on provided information
    def calculate_node_colours(self,nodes_quantity,total_quantity,mode='default'):
        num_nodes = len(nodes_quantity)
        for i in range(num_nodes):
            node_fraction = nodes_quantity[i]/total_quantity#fraction of total amount occuring at that node
            #determine how far along the spectrum from blue to red through green the colour is
            if mode=='default': #use custom scaling (by default cubic), good for passenger volumes
                node_colour_fraction = (node_fraction**(1/self.custom_node_exponent))
            elif mode=='linear': #use linear scaling, good for distance to travel in smaller maps
                node_colour_fraction = node_fraction
            #convert node_colour_fraction to RGB, blue at 0, green at 0.3, red at 1

            midpoint = 0.3 #midpoint of colour scale is green
            if node_colour_fraction<=midpoint:
                #colour scale is from blue to green
                green = node_colour_fraction/midpoint
                blue =  1-green
                red = 0
            elif node_colour_fraction>midpoint:
                #colour scale is from green to red
                red = (node_colour_fraction-midpoint)/(1-midpoint)
                green = 1-red
                blue = 0
            
            #convert 24 bit RGB colour to the hex format expected by tkinter 
            self.nodes_colour[i] = RGB_TO_TK_HEX(int(red*255),int(green*255),int(blue*255))

    #calculate vehicle colours based on how crowded the vehicles are
    #note at the moment, this code requires all vehicles to all have the same capacity
    def calculate_vehicle_colours_crowding(self,vehicle_num_passengers,seated_capacity,standing_capacity):
        #blue is empty, green is half seated capacity, yellow is full seated capacity, red is full standing capacity
        num_vehicles = len(vehicle_num_passengers)
        for i in range(num_vehicles):
            this_vehicle_num_passengers = vehicle_num_passengers[i]
            if this_vehicle_num_passengers<=seated_capacity:
                fraction_seated_capacity = this_vehicle_num_passengers/seated_capacity
                midpoint = 0.5
                if fraction_seated_capacity<=midpoint:
                    #for less than half seats occupied
                    #no red, smooth transition from blue to green
                    red = 0
                    green = fraction_seated_capacity/midpoint
                    blue = 1 - green
                else:
                    #for more than half seats occupied but no standing
                    #smooth transition from green to yellow
                    red = (fraction_seated_capacity-midpoint)/(1-midpoint)
                    green = 1
                    blue = 0
            elif this_vehicle_num_passengers<=standing_capacity:
                fraction_standing_capacity = (this_vehicle_num_passengers-seated_capacity)/(standing_capacity-seated_capacity)
                #smooth transition from yellow at no-standing to red at max standing
                red = 1
                green = 1-fraction_standing_capacity
                blue = 0
            else:
                #for overloaded vehicles
                red = 1
                green = 0
                blue = 0
            #now set the colour of the vehicle
            self.sim_vehicles_current_colour[i] = RGB_TO_TK_HEX(int(red*255),int(green*255),int(blue*255))

    #FUNCTIONS TO DETERINE EDGE WIDTH/COLOUR
    #set edge width based on data about the edge (which data depends on mode)
    def set_edge_widths(self):
        num_edges = len(self.edge_end_indices)
        if self.edge_width_type == "constant":
            self.edge_widths = [self.default_edge_width]*num_edges
        else:
            (forward_edge_data,reverse_edge_data) = self.extract_data_edges(self.edge_width_type)
            if self.edge_direction_mode == 'forward':
                data = np.asarray(forward_edge_data)
            elif self.edge_direction_mode == 'reverse':
                data = np.asarray(reverse_edge_data)
            elif self.edge_direction_mode == 'both':
                if self.edge_width_type == 'traffic':
                    data = np.asarray(reverse_edge_data) + np.asarray(reverse_edge_data) #for both in traffic mode, combine the forward and reverse traffic for display
                elif self.edge_width_type == 'time':
                    data = (np.asarray(reverse_edge_data) + np.asarray(reverse_edge_data))/2 #in time mode(which is not yet implemented) , take the average 
            
            self.calculate_edge_widths(data)      

    #calculate and perform final setting of edge width based on provided information        
    def calculate_edge_widths(self,edges_quantity,mode='default'):
        num_edges = len(edges_quantity)
        total_quantity = np.max(edges_quantity)
        for i in range(num_edges):
            edge_fraction = edges_quantity[i]/total_quantity#fraction of total amount occuring at that node
            self.edge_widths[i] = (edge_fraction**(1/self.custom_edge_exponent))*self.max_edge_width
            if self.edge_widths[i] < self.min_edge_width: #enforce the minimum size of a node
                self.edge_widths[i] = self.min_edge_width
        
    def set_edge_colours(self):
        num_edges = len(self.edge_end_indices)
        if self.edge_colour_type =="constant":
            self.edge_colours = [self.default_edge_colour]*num_edges
        else:
            (forward_edge_data,reverse_edge_data) = self.extract_data_edges(self.edge_colour_type)
            if self.edge_direction_mode == 'forward':
                data = np.asarray(forward_edge_data)
            elif self.edge_direction_mode == 'reverse':
                data = np.asarray(reverse_edge_data)
            elif self.edge_direction_mode == 'both':
                if self.edge_colour_type == 'traffic':
                    data = np.asarray(reverse_edge_data) + np.asarray(reverse_edge_data) #for both in traffic mode, combine the forward and reverse traffic for display
                elif self.edge_colour_type == 'time':
                    data = (np.asarray(reverse_edge_data) + np.asarray(reverse_edge_data))/2 #in time mode, take the average 
            
            self.calculate_edge_colours(data)

    #calculate and perform final setting of edge width based on provided information        
    def calculate_edge_colours(self,edges_quantity,mode='default'):
        num_edges = len(edges_quantity)
        total_quantity = np.max(edges_quantity)
        for i in range(num_edges):
            edge_fraction = edges_quantity[i]/total_quantity#fraction of total amount occuring at that node
            #determine how far along the spectrum from blue to red through green the colour is
            if mode=='default': #use custom scaling (by default square), good for passenger volumes
                edge_colour_fraction = (edge_fraction**(1/self.custom_edge_exponent))
            elif mode=='linear': #use linear scaling, good for distance to travel in smaller maps
                edge_colour_fraction = edge_fraction
            #convert node_colour_fraction to RGB, blue at 0, green at 0.3, red at 1

            midpoint = 0.3 #midpoint of colour scale is green
            if edge_colour_fraction<=midpoint:
                #colour scale is from blue to green
                green = edge_colour_fraction/midpoint
                blue =  1-green
                red = 0
            elif edge_colour_fraction>midpoint:
                #colour scale is from green to red
                red = (edge_colour_fraction-midpoint)/(1-midpoint)
                green = 1-red
                blue = 0
            
            #convert 24 bit RGB colour to the hex format expected by tkinter
            self.edge_colours[i] = RGB_TO_TK_HEX(int(red*255),int(green*255),int(blue*255))

    #FUNCTIONS CONTROLLING RENDERING OF NODES/EDGES
    #wrapper that recalculates node sizes and colours, and redraws the nodes
    def update_nodes(self):
        self.set_node_sizes()
        self.set_node_colours()
        self.render_graph()

     #wrapper that recalculates edge sizes and colours, and redraws the edges
    def update_edges(self):
        self.set_edge_widths()
        self.set_edge_colours()
        self.render_graph()

    #update text rendering next to nodes without changing the node whose information we are using (eg distance to/from that node)
    def update_text_same_node(self):
        if self.nodes_numeric_overlay_mode == 'node_total':
        #if we are overlaying based on total traffic too/from node, the key node does not matter, so we can display info without it
            self.text_total_passengers_node() #replace with new info about total traffic too/from a node
        elif self.nodes_numeric_overlay_mode == 'waiting_passengers':
            self.text_waiting_passengers_node() #replace with new info about passengers waiting at a node  

        #otherwise don't update if no node-specific text was being displayed in the first place
        elif self.last_node_left_click_index == -1:
            self.erase_all_nodes_text('below') #erase all text already displayed
        else:         
            last_click_index = self.last_node_left_click_index
            self.erase_all_nodes_text('below') #erase all text already displayed
            self.last_node_left_click_index = -1 #set this to -1 so update_nodes_viewing_mode correctly renders with a different mode (note keep this here for redunancy in case end up removing the reset from erase_all_nodes_text)
            self.update_nodes_viewing_mode_left_click(last_click_index) #update the render
            self.last_node_left_click_index = last_click_index #set last left click index back to it's previous value so we can still remove info by clicking on that node again

    #update the display relating to nodes in response to a left click
    def update_nodes_viewing_mode_left_click(self,left_click_index):
        if self.nodes_numeric_overlay_mode == 'node_total':
             self.text_total_passengers_node() #display the total number of passengers going too/from all nodes
        elif self.last_node_left_click_index == left_click_index: #if the same node has been clicked on again
            self.erase_all_nodes_text('below') #reset all text
            self.last_node_left_click_index = -1
        else: #otherwise, display info text for new node
            if self.nodes_numeric_overlay_mode == 'no_info':
                self.erase_all_nodes_text('below') #reset all text, as not used in this mode
            elif self.nodes_numeric_overlay_mode == 'node_relative':
                self.text_passengers_node(left_click_index) #display the number of passengers going too/from this particular node
            elif self.nodes_numeric_overlay_mode == 'node_distance':
                self.text_journeys_node(left_click_index) #display the time taken to travel from this node too/from all other nodes

            self.last_node_left_click_index = left_click_index #record this was the last node we clicked on

    #UTILITY FUNCTIONS

    #prints a message to the console only if the logging level is at a certain level (default=1)
    def log_print(self,message,log_level=1):
        if self.verbose>=log_level:
            print(message)

    #update the control message board
    def message_update(self,string):
        self.message.config(text=string)

    def convert_lat_long_to_x_y(self,latitude,longitude):
        latitude_offset = latitude-self.central_latitude
        longitude_offset = longitude-self.central_longitude
        y = self.canvas_center_y-(latitude_offset*self.pixels_per_degree) #we need to flip the offset along the y axis, as higher values mean further down (south) in canvas coordinates
        x = self.canvas_center_x+(longitude_offset*self.pixels_per_degree)
        return (x,y)

    #FUNCTIONS TO IMPORT DATA NEEDED FOR THE NETWORK

    #extract the list of nodes from a csv file into a python list, and calculate global geographical information for plotting
    def extract_nodes_graph(self):
        self.node_names = self.nodes_csv["Name"].to_list()
        node_positions = self.nodes_csv["Location"].to_list()
        self.node_latitudes = []
        self.node_longitudes = []
        for position in node_positions:
            latitude,longitude = n.extract_coordinates(position)
            self.node_latitudes.append(latitude)
            self.node_longitudes.append(longitude)

        #get the minimum/maximum longitude and latitude
        min_latitude = min(self.node_latitudes)
        max_latitude = max(self.node_latitudes)
        min_longitude = min(self.node_longitudes)
        max_longitude = max(self.node_longitudes)
        self.central_latitude = (min_latitude + max_latitude)/2
        self.central_longitude = (min_longitude + max_longitude)/2
        #now determine conversion factors between coordinates and pixels
        #note the canvas needs to be created first
        range_latitude = max_latitude-min_latitude
        range_longitude = max_longitude-min_longitude
        #extract the scaling factor between the canvas and the real world
        pixels_per_degree_vertical = (self.canvas_height-(self.max_node_radius*4))/range_latitude
        pixels_per_degree_horizontal = (self.canvas_width-(self.max_node_radius*4))/range_longitude
        #the lower value is the limiting factor for an undistorted map
        self.pixels_per_degree = min(pixels_per_degree_vertical,pixels_per_degree_horizontal) 

    #extract the list of edges from a csv file into a python list, and calculate global geographical information for plotting
    #this needs to be run after nodes have been extracted so start/end node index assignment can be done
    def extract_edges_graph(self):
        edge_starts = self.edges_csv["Start"].to_list()
        edge_ends = self.edges_csv["End"].to_list()
        self.edge_names = [] #name of the edge from start to end
        self.edge_reverse_names = [] #name of the edge from end to start
        num_edges = len(edge_starts)#for the purpose of plotting, a bidirectional edge is one edge
        #find the index of edge starts and ends in the list of nodes
        self.edge_start_indices = []
        self.edge_end_indices = []
        for i in range(num_edges):
            #get the start index
            try:
                start_index = self.node_names.index(edge_starts[i])
            except ValueError:
                warnings.warn('edge start ', edge_starts[i],' not present in list of node names')
                start_index = -1 #this will cause a crash later (by design), as our program a non-existent start node
            
            #get the end index
            try:
                end_index = self.node_names.index(edge_ends[i])
            except ValueError:
                warnings.warn('edge end ', edge_ends[i],' not present in list of node names')
                end_index = -1 #this will cause a crash later (by design), as our program contains a non-existent end node

            self.edge_names.append(edge_starts[i] + ' to ' + edge_ends[i])
            self.edge_reverse_names.append(edge_ends[i] + ' to ' + edge_starts[i])
            self.edge_start_indices.append(start_index)
            self.edge_end_indices.append(end_index)

        self.edge_canvas_ids = ['blank']*num_edges #store edge canvas ids in a list so we can delete them later, 'blank' indicates they have not yet been created
        self.edge_widths = [self.default_edge_width]*num_edges #store the default width of every edge
        self.edge_colours = [self.default_edge_colour]*num_edges #store the default colour of every edge
        self.edge_arrows = [tk.NONE]*num_edges #by default there will be no arrows on an edge

    #calculate information about position of nodes
    def calculate_node_position(self):
        num_nodes = len(self.node_names)
        self.nodes_x = []
        self.nodes_y = []
        self.nodes_radii = [self.default_node_radius]*num_nodes #default size for nodes
        self.nodes_colour = [self.default_node_colour]*num_nodes #default
        self.node_below_text_ids = ['blank']*num_nodes  #canvas ids for text which could be displayed below all nodes
        self.node_above_text_ids = ['blank']*num_nodes  #canvas ids for text which could be displayed above all nodes
        self.node_canvas_ids = ['blank']*num_nodes #canvas ids for the nodes themsleves
        for i in range(num_nodes):
            x,y = self.convert_lat_long_to_x_y(self.node_latitudes[i],self.node_longitudes[i])
            self.nodes_x.append(x)
            self.nodes_y.append(y)
        #original copy of node position, so that scaling can be calculated relative to the original values
        self.nodes_x_original = self.nodes_x
        self.nodes_y_original = self.nodes_y

    #calculate the midpoint of edges, used for plotting overlay text on edges
    #this needs to be done after node positions are calculated
    def calculate_edges_midpoints(self):
        num_edges = len(self.edge_names)
        self.edges_midpoint_x = []
        self.edges_midpoint_y = []
        self.edge_text_ids = ['blank']*num_edges  #canvas ids for text which could be displayed next to all edges
        for i in range(num_edges):
            #extract the location of the nodes which the edge connects
            edge_start_index = self.edge_start_indices[i] 
            edge_end_index = self.edge_end_indices[i]
            #and then calculate the midpoint of the edge
            edge_midpoint_x = (self.nodes_x[edge_start_index] + self.nodes_x[edge_end_index])/2
            edge_midpoint_y = (self.nodes_y[edge_start_index] + self.nodes_y[edge_end_index])/2
            #and store this calculated value in a list
            self.edges_midpoint_x.append(edge_midpoint_x)
            self.edges_midpoint_y.append(edge_midpoint_y)
        
        #original copy of edge midpoints, so that scaling can be calculated relative to the original values
        self.edges_midpoint_x_original = self.edges_midpoint_x
        self.edges_midpoint_y_original = self.edges_midpoint_y

    #calculate the position, colour and size of vehicles
    def calculate_vehicle_position(self):
        #as vehicle quantities change from timestep to timestep, need to delete old vehicles first
        self.derender_vehicles()    
        num_vehicles = len(self.sim_vehicles_current_names)
        self.sim_vehicles_current_x = []
        self.sim_vehicles_current_y = []
        self.sim_vehicles_current_length = [self.default_vehicle_length]*num_vehicles
        self.set_vehicle_colours() #set the vehicle colour based on the choosen mode
        self.vehicle_canvas_ids = ['blank']*num_vehicles #canvas ids for the nodes themsleves
        for i in range(num_vehicles):
            x,y = self.convert_lat_long_to_x_y(self.sim_vehicles_current_latitudes[i],self.sim_vehicles_current_longitudes[i])
            x,y = self.apply_accumlated_zoom(x,y)#apply accumulated zoom to new vehicle objects
            self.sim_vehicles_current_x.append(x)
            self.sim_vehicles_current_y.append(y)
        self.sim_vehicles_current_x_original = self.sim_vehicles_current_x
        self.sim_vehicles_current_y_original = self.sim_vehicles_current_y

    #function to set the colour of vehicles
    def set_vehicle_colours(self):
        num_vehicles = len(self.sim_vehicles_current_names)
        self.sim_vehicles_current_colour = [self.default_vehicle_colour]*num_vehicles
        if self.vehicle_colour_type == "constant":
            pass #default colours have already been set
        elif self.vehicle_colour_type == "crowding":
            self.calculate_vehicle_colours_crowding(self.sim_vehicles_current_passengers,self.vehicle_seated_capacity,self.vehicle_standing_capacity)
        else:
            #default to the default colour, which has already been set
            message = "INVALID COLOUR TYPE " + self.vehicle_colour_type + "\n COLOUR SET TO DEFAULT"
            self.log_print(message)
            
    #FUNCTIONS PERFORMING ACTUAL RENDERING
    #derender displayed vehicles
    def derender_vehicles(self,override=False):
        #delete all existing vehicles
        #overide option allows the function to operate even simulation_view_flag is false
        if self.simulation_view_flag==True or override==True:
            num_vehicles_old = len(self.vehicle_canvas_ids)
            for i in range(num_vehicles_old):
                if self.vehicle_canvas_ids[i]!='blank':
                        #delete the old oval object if one exists
                        self.canvas.delete(self.vehicle_canvas_ids[i])

    #derender the text produced by hovering over a vehicle
    def derender_hover_vehicle_text(self):
        if self.index_vehicle_text_popup ==-1:
            pass #there are no vehicle hover text and hence no need to derender it
        else:
            self.canvas.delete(self.text_id_vehicle_lower)
            self.canvas.delete(self.text_id_vehicle_upper)

    #rerender the text after the vehicle has been moved/zoomed in/out
    def render_hover_vehicle_text(self):
        if self.index_vehicle_text_popup ==-1:
            pass #there are no vehicle hover text and hence no need to render it
        else:
            x = self.sim_vehicles_current_x[self.index_vehicle_text_popup]
            y = self.sim_vehicles_current_y[self.index_vehicle_text_popup]
            vehicle_name = self.sim_vehicles_current_names[self.index_vehicle_text_popup]
            lower_text = self.sim_vehicles_current_passengers[self.index_vehicle_text_popup]
            self.text_id_vehicle_upper = self.canvas.create_text(x,y-30,text=vehicle_name,state=tk.DISABLED)
            self.text_id_vehicle_lower = self.canvas.create_text(x,y-15,text=lower_text,state=tk.DISABLED)

    #derender edge text created by hovering
    def derender_hover_edge_text(self):
        if self.text_id_line_end != -1: #if such text exists
            self.canvas.delete(self.text_id_line_end)
            self.canvas.delete(self.text_id_line_start)
            self.text_id_line_start =  -1
            self.text_id_line_end = -1

    #needs to be run after edges have been extracted and nodes have been drawn to work correctly
    def render_edges(self):
        self.derender_hover_edge_text()#derender additional edge text if it exists
        num_edges = len(self.edge_start_indices)
        for i in range(num_edges):
            start_index = self.edge_start_indices[i]
            end_index = self.edge_end_indices[i]
            start_x = self.nodes_x[start_index]
            start_y = self.nodes_y[start_index]
            end_x = self.nodes_x[end_index]
            end_y = self.nodes_y[end_index]
            colour = self.edge_colours[i]
            width = int(self.edge_widths[i]) #interesting thing about tkinter, circles can have non-integer sizes but lines need integer sizes
            edge_arrow = self.edge_arrows[i]
            #end_size = self.nodes_radii[end_index] #unused, we draw nodes over edges so no need to crop the edges
            #print('width ', width)
            #print('activewidth ',width+self.active_width_addition)
            if self.edge_canvas_ids[i]!='blank':
                #delete the old line object if one exists
                self.canvas.delete(self.edge_canvas_ids[i])
                
            id = self.canvas.create_line(start_x,start_y,end_x,end_y,fill=colour,width=width,activewidth=width+self.active_width_addition,arrow=edge_arrow) #draw a line to represent the edge
            self.canvas.tag_bind(id,'<Enter>',self.edge_enter) #some information about the start and end nodes will be displayed when we mouse over an edge
            self.canvas.tag_bind(id,'<Leave>',self.edge_leave) #this information will stop being displayed when the mouse is no longer over the node
            self.edge_canvas_ids[i] = id

    #draw the nodes on the canvas
    def render_nodes(self):
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            #extract data
            x = self.nodes_x[i]
            y = self.nodes_y[i]
            radius = self.nodes_radii[i]
            colour = self.nodes_colour[i]
            try:
                self.canvas.delete(self.text_id) #delete the text popup if one exists
            except AttributeError:
                pass #if it does not exist, don't delete it
            #delete all old node objects
            if self.node_canvas_ids[i]!='blank':
                #delete the old oval object if one exists
                self.canvas.delete(self.node_canvas_ids[i])
            id = self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=colour) #draw a circle to represent the node
            self.canvas.tag_bind(id,'<Enter>',self.node_enter) #some information about the node will be displayed when the mouse is hovered over it
            self.canvas.tag_bind(id,'<Leave>',self.node_leave) #this information will stop being displayed when the mouse is no longer over the node
            self.canvas.tag_bind(id,'<Button-1>',self.node_left_click) #depending on gui_mode, information about the nodes relationship to other nodes will be displayed
            self.canvas.tag_bind(id,'<Button-2>',self.node_right_click) #depending on gui_mode, information about the nodes relationship to other nodes will be displayed
            self.node_canvas_ids[i] = id #store the id so we can delete the object later

    #draw the vehicle objects on the canvas
    def render_vehicles(self):
        num_vehicles = len(self.sim_vehicles_current_names)
        self.derender_hover_vehicle_text() #remove existing vehicle hover text
        #loop through all the current vehicles
        for i in range(num_vehicles):
            #extract data
            x = self.sim_vehicles_current_x[i]
            y = self.sim_vehicles_current_y[i]
            length = self.sim_vehicles_current_length[i]
            colour = self.sim_vehicles_current_colour[i]
            #delete all old vehicle objects
            if self.vehicle_canvas_ids[i]!='blank':
                #delete the old rectangle object if one exists
                self.canvas.delete(self.vehicle_canvas_ids[i])
            id = self.canvas.create_rectangle(x-length,y-length,x+length,y+length,fill=colour)
            self.canvas.tag_bind(id,'<Enter>',self.vehicle_enter) #some information about the vehicle will be displayed when the mouse is hovered over it
            self.canvas.tag_bind(id,'<Leave>',self.vehicle_leave) #this information will be displayed when the mouse is no longer over the vehicle
            self.canvas.tag_bind(id,'<Button-1>',self.vehicle_left_click) #this information will be displayed when the mouse is no longer over the vehicle
            self.canvas.tag_bind(id,'<Button-2>',self.vehicle_right_click) #this information will be displayed when the mouse is no longer over the vehicle
            #add code to display info about the vehicle when we hover over it
            self.vehicle_canvas_ids[i] = id #store the id so we can delete the object later

        self.render_hover_vehicle_text() #recreate old vehicle hover text at the new location

    #combination of render nodes and render edges, in correct order to prevent edges spawning over nodes
    def render_graph(self):
        self.render_edges()
        self.render_nodes()
        if self.simulation_run_flag == True:
            self.render_vehicles() #render vehicles if we are in simulation view mode

    #stop displaying all the nodes and edges
    def erase_network_graph(self):
        self.derender_hover_edge_text()
        #erase all edges
        for id in self.edge_canvas_ids:
            if id!='blank':
                self.canvas.delete(id)
        #erase all nodes
        for id in self.node_canvas_ids:
            if id!='blank':
                self.canvas.delete(id)
    
    #EVENT HANDLERS (eg clicking, hovering) FOR CANVAS NODES

    #event for when we mouse over a node, create a text box revealling node name and (planned) number of waiting passengers   
    def node_enter(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.node_canvas_ids.index(event_id)
        node_name = self.node_names[id_index]
        self.log_print('node viewed ' + node_name)
        x = self.nodes_x[id_index]
        y = self.nodes_y[id_index]
        display_text = node_name
        self.text_id = self.canvas.create_text(x,y-15,text=display_text,state=tk.DISABLED) #create a text popup, which is not interactive

    #event for when the mouse leaves a node, remove the text box
    def node_leave(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.node_canvas_ids.index(event_id)
        node_name = self.node_names[id_index]
        self.log_print('node left ' + node_name)
        self.canvas.delete(self.text_id) #delete the text popup from node_enter

    #event for when we left-click on a node, outcome will depend on viewing mode
    def node_left_click(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.node_canvas_ids.index(event_id) #get the index of the node which has been clicked on
        if self.last_node_right_click_index !=-1: #if a node has been right clicked on
            self.reset_edges_plot() #remove any old route
            self.plot_path_nodes(id_index,self.last_node_right_click_index,text_nodes=False,arrows=True) #draw a path from the left clicked node to the right clicked node
        
        self.update_nodes_viewing_mode_left_click(id_index) #update the viewing mode due to the click
        #rerender the nodes to be of the correct size after the new click
        self.update_nodes()

    #event for when we right-click on a node
    def node_right_click(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.node_canvas_ids.index(event_id) #get the index of the node which has been clicked on
        if id_index == self.last_node_left_click_index: #right clicking on a node we just left clicked on will do nothing for now
            pass
        elif self.last_node_left_click_index == -1: #as will right clicking if no left click has occured
            pass
        else:
            self.reset_edges_plot() #remove any old route
            self.plot_path_nodes(self.last_node_left_click_index,id_index,text_nodes=False,arrows=True) #draw a path from the left clicked node to the right clicked node
            self.render_graph() #re-render the network
            self.last_node_right_click_index = id_index

    #EVENT HANDLERS FOR CANVAS EDGES

    #event for when we mouse over an edge, display text boxes above connected nodes
    def edge_enter(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.edge_canvas_ids.index(event_id)
        #find the nodes at the ends of the edge
        start_index = self.edge_start_indices[id_index]
        end_index = self.edge_end_indices[id_index]
        #find the x and y positions of these nodes
        start_x = self.nodes_x[start_index]
        start_y = self.nodes_y[start_index]
        end_x = self.nodes_x[end_index]
        end_y = self.nodes_y[end_index]
        #decide on the text popup above each node
        display_text_start = self.node_names[start_index]
        display_text_end = self.node_names[end_index]
        #create the text popups, which are not interactive
        if self.text_id_line_start != -1:
            #delete any existing popups
            self.canvas.delete(self.text_id_line_start)    
            self.canvas.delete(self.text_id_line_end)
        self.text_id_line_start = self.canvas.create_text(start_x,start_y-15,text=display_text_start,state=tk.DISABLED)
        self.text_id_line_end = self.canvas.create_text(end_x,end_y-15,text=display_text_end,state=tk.DISABLED)


    #event for when we mouse away from an edge
    def edge_leave(self,event):
        self.derender_hover_edge_text() #delete any hovering text related to the edge

    #event for when we mouse over a vehicle
    def vehicle_enter(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.vehicle_canvas_ids.index(event_id)
        vehicle_name = self.sim_vehicles_current_names[id_index]
        #delete hover text if it exists
        self.derender_hover_vehicle_text()
        #create new text popups
        self.index_vehicle_text_popup = id_index #record the index of the vehicle whose text popup we are creating
        self.name_vehicle_text_popup = vehicle_name #and also record the name, this is used to handle situations where the lists of vehicles changes
        self.render_hover_vehicle_text()
        
        
    #event for when we mouse away from a vehicle
    def vehicle_leave(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.vehicle_canvas_ids.index(event_id)
        #at the moment, we don't actually do anything here as we still want to display info about the vehicle when we are hovering over it
    
    #event for when we left click a vehicle
    def vehicle_left_click(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.vehicle_canvas_ids.index(event_id)
        #placeholder for future functionality
    
    #event for when we right click a vehicle
    def vehicle_right_click(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.vehicle_canvas_ids.index(event_id)
        #right clicks will reset the vehicle popup text rendering
        self.derender_hover_vehicle_text()
        self.index_vehicle_text_popup = -1
        self.name_vehicle_text_popup = -1
        #placeholder for future functionality
        
    #GENERAL CANVAS EVENT HANDLERS (FOR SCROLLING and ZOOMING IN/OUT)
    #zoom in/out
    def zoom_canvas(self,event):
        #get position of mouse during scroll
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        #print('mouse x ',mouse_x,' mouse y ',mouse_y)
        zoom_delta = 0.01*event.delta #zoom is in proportion to scroll wheel direction and magnitude
        self.current_zoom = self.current_zoom*(1+zoom_delta) #update the accumulated zoom level
        self.current_zoom_offset_x = self.current_zoom_offset_x*(1+zoom_delta) - mouse_x*zoom_delta#calculate the new offset for x
        self.current_zoom_offset_y = self.current_zoom_offset_y*(1+zoom_delta) - mouse_y*zoom_delta#calculate the new offset for y
        self.apply_correct_zoom(zoom_delta,mouse_x,mouse_y) #perform the zoom on all objects in an image
    
    #recreate existing objects in the correctly zoomed position
    def apply_correct_zoom(self,zoom_delta,mouse_x,mouse_y):
        #update the graph
        self.recalculate_nodes_position(zoom_delta,mouse_x,mouse_y)
        self.recalculate_edge_midpoints(zoom_delta,mouse_x,mouse_y)
        if self.simulation_run_flag == True: #only recalculate vehicle position if vehicles exists
            self.recalculate_vehicle_position(zoom_delta,mouse_x,mouse_y)
        self.render_graph()
        self.node_names_update() #update the rendering of node names
        #update text overlays if simulation has been setup
        if self.simulation_setup_flag:
            self.update_text_same_node() 
            self.generate_edge_overlay_text()

    #apply the accumulated zoom to newly created objects
    def apply_accumlated_zoom(self,x,y):
        new_x = (x*self.current_zoom)+(self.current_zoom_offset_x)
        new_y = (y*self.current_zoom)+(self.current_zoom_offset_y)
        return new_x,new_y 

    #recalculate all node positions in response to the zoom action
    def recalculate_nodes_position(self,zoom_delta,mouse_x,mouse_y):
        num_nodes = len(self.nodes_x)
        #recalculate the position of all nodes
        for i in range(num_nodes):
            new_x,new_y = self.recalculate_zoom_position(self.nodes_x[i],self.nodes_y[i],zoom_delta,mouse_x,mouse_y)
            self.nodes_x[i] = new_x
            self.nodes_y[i] = new_y
    
    #recalculate the midpoint of all edges in response to zooming
    def recalculate_edge_midpoints(self,zoom_delta,mouse_x,mouse_y):
        num_edges = len(self.edges_midpoint_x)
        #recalculate the position of all edge midpoints
        for i in range(num_edges):
            new_x,new_y = self.recalculate_zoom_position(self.edges_midpoint_x[i],self.edges_midpoint_y[i],zoom_delta,mouse_x,mouse_y)
            self.edges_midpoint_x[i] = new_x
            self.edges_midpoint_y[i] = new_y

    #recalculate the position of all vehicles in response to zooming
    def recalculate_vehicle_position(self,zoom_delta,mouse_x,mouse_y):
        num_vehicles = len(self.sim_vehicles_current_names)
        #recalculate the position of all vehicles
        for i in range(num_vehicles):
            new_x,new_y = self.recalculate_zoom_position(self.sim_vehicles_current_x[i],self.sim_vehicles_current_y[i],zoom_delta,mouse_x,mouse_y)
            self.sim_vehicles_current_x[i] = new_x
            self.sim_vehicles_current_y[i] = new_y

    #recalculate the position of an object to be correct under the new zoom regime
    def recalculate_zoom_position(self,x,y,zoom_delta,mouse_x,mouse_y):
        new_x = x*(1+zoom_delta)-(mouse_x*zoom_delta)
        new_y = y*(1+zoom_delta)-(mouse_y*zoom_delta)
        return new_x,new_y

    #define pan function
    def pan_start(self,event):
        #get position of mouse at start of pan
        #mouse_x = int(self.canvas.canvasx(event.x))
        #mouse_y = int(self.canvas.canvasy(event.y))
        #print('mouse x ',mouse_x,' mouse y ',mouse_y)
        self.canvas.scan_mark(event.x, event.y) #record the position of start of scan
    
    #define scan function
    def pan_end(self,event):
        #get position of mouse at start of pan
        #mouse_x = int(self.canvas.canvasx(event.x))
        #mouse_y = int(self.canvas.canvasy(event.y))
        #print('mouse x ',mouse_x,' mouse y ',mouse_y)
        self.canvas.scan_dragto(event.x, event.y,gain=self.scroll_gain) #record the position of start of scan

    #FUNCTIONS TO GENERATE INFO TEXT ABOVE NODES

    #display the number of passengers travelling to/from a clicked node to all other nodes (per hour as currently setup) as text above the nodes
    def text_passengers_node(self,key_node_index):
        if self.from_node:
            trips = self.sim_network.origin_destination_trips[key_node_index,:] #extract number of trips starting from this node
        else:
            trips = self.sim_network.origin_destination_trips[:,key_node_index] #extract number of trips going to this node

        self.display_text_info_node(trips,where_mode='below',type_mode='float') #display the number of trips starting/ending at every other node

    #display the number of passengers travelling to/from a node to all other nodes combined (per hour as currently setup) as text above the nodes 
    def text_total_passengers_node(self):
        if self.from_node:
            trips = np.sum(self.sim_network.origin_destination_trips,0)#extract number of trips starting from all nodes
        else:
            trips = np.sum(self.sim_network.origin_destination_trips,1) #extract number of trips ending at all nodes

        self.display_text_info_node(trips,where_mode='below',type_mode='float') #display the number of trips starting/ending at each node node
    
    #display the number of passengers waiting at a node
    def text_waiting_passengers_node(self):
        self.display_text_info_node(self.sim_node_current_passengers,where_mode='below',type_mode='int') #display the number of waiting passengers at each node

    #display the journey time from the clicked node to other nodes as text above the node
    def text_journeys_node(self,key_node_index):
        if self.from_node:
            times = self.sim_network.distance_to_all[key_node_index,:] #extract journey times starting at this node
        else:
            times = self.sim_network.distance_to_all[:,key_node_index] #extract journey times going to this node
        
        self.display_text_info_node(times,type_mode='integer',where_mode='below') #display journey times to/from every other node

    #perform the actual text rendering of text near all nodes
    #whether this happens above or below all nodes can be selected 
    def display_text_info_node(self,info,where_mode='below',type_mode='text'):
        num_nodes = len(self.node_names)
        self.erase_all_nodes_text(mode=where_mode) #clear any old text
        if where_mode=='below':
            self.node_below_text_ids = ['blank']*num_nodes #create a container for the new text ids
        elif where_mode=='above':
            self.node_above_text_ids = ['blank']*num_nodes #create a container for the new text ids
        for i in range(num_nodes): #for every node
            node_x = self.nodes_x[i]
            node_y = self.nodes_y[i]
            this_info = info[i]
            if type_mode=='float':
                this_info = "{:.2f}".format(this_info) #floating point data
            elif type_mode=='integer':
                this_info = str(this_info) #integer data
            if where_mode=='below':
                self.node_below_text_ids[i] = self.canvas.create_text(node_x,node_y+15,text=this_info,state=tk.DISABLED,fill=self.default_node_text_colour) #create a text popup, which is not interactive
            elif where_mode=='above':
                self.node_above_text_ids[i] = self.canvas.create_text(node_x,node_y-15,text=this_info,state=tk.DISABLED,fill=self.default_node_text_colour) #create a text popup, which is not interactive

    #erase text displayed next to all nodes (eg num passengers/journey time)
    def erase_all_nodes_text(self,mode='both'):
        #self.last_node_left_click_index = -1 #we are deleting all nodes text, so reset if any nodes have been clicked
        #text to delete depends on mode
        if mode == 'above':
            text_ids = self.node_above_text_ids
        elif mode == 'below':
            text_ids = self.node_below_text_ids
        elif mode == 'both':
            text_ids = self.node_above_text_ids + self.node_below_text_ids
        #delete the selected text
        for id in text_ids:
            if id!='blank':
                self.canvas.delete(id)

    #FUNCTIONS TO GENERATE INFO TEXT ABOVE EDGES

    #get data about a specific edge from the network
    #valid types are "time" and "traffic"
    def get_edge_data(self,edge_name,type):
        index = self.sim_network.get_edge_index(edge_name)#get the index of the edge in the network data structure
        if type == 'time':
            data = self.sim_network.get_edge_time(edge_name)
        elif type == 'traffic':
            data = self.sim_network.get_edge_traffic(edge_name)
        return data

    def extract_data_edges(self,type):
        forward_edge_data = []
        reverse_edge_data = []
        for forward_edge_name in self.edge_names: #extract data from the forward edges
            forward_edge_data.append(self.get_edge_data(forward_edge_name,type))
        for reverse_edge_name in self.edge_reverse_names:
            reverse_edge_data.append(self.get_edge_data(reverse_edge_name,type))
        return forward_edge_data,reverse_edge_data

    #determine the actual text which will be displayed on the edges
    #if combine is true, the data will be added together for display
    def determine_edges_text(self,type,combine):
        (forward_edge_data,reverse_edge_data) = self.extract_data_edges(type) #extract forward and edge data
        edges_text = []
        num_edges = len(forward_edge_data)
        if combine:
            for i in range(num_edges):
               combined_data =  reverse_edge_data[i] + forward_edge_data[i]
               edges_text.append(format(combined_data,'.2f'))

        else:
            if self.edge_direction_mode == 'forward':
                for i in range(num_edges):
                    edges_text.append(format(forward_edge_data[i],'.2f'))
            elif self.edge_direction_mode == 'reverse':
                for i in range(num_edges):
                    edges_text.append(format(reverse_edge_data[i],'.2f'))
            elif self.edge_direction_mode == 'both':
                for i in range(num_edges):
                    edges_text.append(format(reverse_edge_data[i],'.2f') + '/' + format(reverse_edge_data[i],'.2f'))

        return edges_text

    #generate and plot the overlay text for edges
    def generate_edge_overlay_text(self):
        if self.edges_numeric_overlay_mode == 'no_info':
            self.erase_all_edges_text() #delete any existing edge text
            return #exit the function, we don't need to do anything more 
        elif self.edges_numeric_overlay_mode == 'distance':
            edges_text = self.determine_edges_text('time',False)
        elif self.edges_numeric_overlay_mode == 'traffic':
            edges_text = self.determine_edges_text('traffic',False)
        elif self.edges_numeric_overlay_mode == 'total_traffic':
            edges_text = self.determine_edges_text('traffic',True)
        #display the text previously generated
        self.display_text_info_above_edges(edges_text)

    def display_text_info_above_edges(self,info):
        num_edges = len(self.edge_names)
        self.erase_all_edges_text() #clear any old text
        self.edge_text_ids = ['blank']*num_edges #create a container for the new text ids
        for i in range(num_edges): #for every edge
            edge_x = self.edges_midpoint_x[i]
            edge_y = self.edges_midpoint_y[i]
            self.edge_text_ids[i] = self.canvas.create_text(edge_x,edge_y,text=info[i],state=tk.DISABLED,fill=self.default_edge_text_colour) #create a text popup, which is not interactive

    #render edge names
    def render_edge_names(self):
        self.display_text_info_above_edges(self.edge_names)

    #erase text displayed next to all edges
    def erase_all_edges_text(self):
        self.last_edge_left_click_index = -1 #we are deleting all nodes text, so reset if any edges have been clicked
        for id in self.edge_text_ids:
            if id!='blank':
                self.canvas.delete(id)

    #FUNCTIONS TO GENERATE INFO TEXT ABOVE VEHICLES


    #FUNCTIONS TO PLOT A PATH BETWEEN TWO NODES

    #extract the path between two node based on their indices
    def extract_path_node_indices(self,start_node_index,end_node_index):
        edges_path = self.sim_network.paths_to_all[start_node_index][end_node_index]
        return edges_path

    #extract the path between two nodes
    def extract_path_nodes(self,start_node,end_node):
        start_id = self.node_names.index(start_node) #get the id's of the starting node
        end_id = self.node_names.index(end_node) #and the ending node
        edges_path = self.extract_path_node_indices(start_id,end_id)
        return edges_path

    #reset edge names and colours to their default values
    def reset_edges_plot(self):
        num_edges = len(self.edge_names)
        for i in range(num_edges):
            self.edge_colours[i] = self.default_edge_colour
            self.edge_widths[i] = self.default_edge_width
            self.edge_arrows[i] = tk.NONE

    #plot the path between two nodes
    def plot_path_nodes(self,start_node,end_node,text_nodes=True,arrows='auto'):
        #if text_nodes = True, we select the path using the verbose names of the nodes, rather than just their index
        if text_nodes:
            edges_path = self.extract_path_nodes(start_node,end_node)
        else:
            edges_path = self.extract_path_node_indices(start_node,end_node)
        #will arrows be present on plotted path
        if arrows=='auto':
            arrows = self.path_edge_arrows #by default, choose initally defined default option

        for edge_name in edges_path:
            #go through all the edges in the edges path
            try:
                #if the edge is from start to finish
                edge_index = self.edge_names.index(edge_name)
                reverse = False
            except ValueError: 
                #if the edge is from finish to start
                try:
                    edge_index = self.edge_reverse_names.index(edge_name)
                    reverse = True
                except ValueError:
                    #edge is in neither list
                    warnings.warn('edge ',edge_name,' not present in list of edges')
                    continue
            
            #now update edge names and colours for nodes on the path
            self.edge_colours[edge_index] = self.path_edge_colour
            self.edge_widths[edge_index] = self.path_edge_width
            if arrows==True:#if we are plotting arrows
                if reverse: #draw an arrow pointing towards the starting node
                    self.edge_arrows[edge_index] = tk.FIRST
                else: #draw an arrow pointing away from the starting node
                    self.edge_arrows[edge_index] = tk.LAST
            else: #if we are not plotting arrows
                self.edge_arrows[edge_index] = tk.NONE #don't plot arrows

    
#EXTERNAL UTILITY FUNCTIONS

#convert 24bit RGB colour to the hex format used by tkinter
def RGB_TO_TK_HEX(red,green,blue):
    #convert to hex and remove leading 0x
    red_string = int_to_2hex(red) #extract from 3rd element in string to last element
    green_string = int_to_2hex(green)
    blue_string = int_to_2hex(blue)
    output_string = "#" + red_string + green_string + blue_string #combine components into the correct format
    return output_string

#converts integers to hexs of at least length 2(so can represent numbers 0-255)
def int_to_2hex(num):#converts an integer to a length 2 hex
    string = hex(num)[2:]
    #prepend 0's if hex is too short
    if len(string)==1:
        string = '0' + string
    elif len(string)==0:
        string = '00'
    
    return string

#utility which takes as input an edge name and produces the name an edge going between the same nodes but in the opposite direction
#note this utility cannot handle destinations where " to " is part of the name
def reverse_edge_name(edge_name):
    divider_string = ' to '
    divider_start = edge_name.find(divider_string) #start of the division between origin and destination
    origin = edge_name[0:divider_start] #extract origin name
    destination = edge_name[divider_start+len(divider_string):] #and destination name
    output_string = destination + divider_string + origin #create the reversed string
    return output_string 
    

