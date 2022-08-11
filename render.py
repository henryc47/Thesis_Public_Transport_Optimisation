#display.py
#responsible for displaying a visualisation of activity on the network

import tkinter as tk
import time as time
import pandas as pd
import numpy as np 
import network as n
import warnings as warnings
from os import path#for checking if file exists

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
        self.default_edge_colour = 'black' #what colour will an edge be by default 
        self.path_edge_colour = 'magenta' #what colour will an edge which is part of the drawn path be
        self.path_edge_width = 3 #what width will an edge which is part of the drawn path be

    #set the various flags (and modes) used by the rendering engine to their default value
    def set_default_flags(self):
        self.first_render_flag = True #is this the first render of the visualisation for a network?
        self.simulation_setup_flag = False #has the simulation setup (eg trip distribution) been done already?
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
        self.canvas_width = window_width-200
        self.canvas_height = window_height-100
        self.canvas_center_x = int(self.canvas_width/2)
        self.canvas_center_y = int(self.canvas_height/2)
        self.canvas = tk.Canvas(self.window, bg="white", height=self.canvas_height, width=self.canvas_width)
        self.canvas.pack(side = tk.RIGHT)

    #setup the main control options
    def setup_main_controls(self):
        #create the control panel
        self.main_controls = tk.Frame(master=self.window)
        self.main_controls.pack(side = tk.LEFT)
        #default file paths
        default_nodes = 'nodes_basic.csv'
        default_edges = 'edges_basic.csv'
        default_schedule = 'schedule_basic.csv'
        #options
        #verbose option, determines level of logging to the console
        self.verbose = -1 #default level of logging is  0=none, 1=verbose, 2=super verbose, -1 is placeholder for setup
        self.verbose_button = tk.Button(master=self.main_controls,fg='black',bg='white',command=self.verbose_button_click,width=20)
        self.verbose_button.pack()
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
        #control for importing files 
        self.import_files_button = tk.Button(master=self.main_controls,text='IMPORT FILES',fg='black',bg='white',command=self.import_files_click,width=20)
        self.import_files_button.pack()
        #this button will draw the network
        self.draw_network_button = tk.Button(master=self.main_controls,text="DRAW NETWORK",fg='black',bg='white',command=self.draw_network_click,width=20)
        self.draw_network_button.pack()
        #this button will start the simulation
        self.setup_simulation_button = tk.Button(master=self.main_controls,text="SETUP SIMULATION",fg='black',bg='white',command=self.setup_simulation_click,width=20)
        self.setup_simulation_button.pack()
        #this label will provide information to the user
        self.message_header = tk.Label(master=self.main_controls,text='MESSAGE',fg='black',bg='white',width=20)
        self.message_header.pack()
        self.message = tk.Label(master=self.main_controls,text='',fg='black',bg='white',width=20,height=5)
        self.message.pack()

    #CLICK FUNCTIONS FOR MAIN CONTROLS

    #attempt to import the selected files
    def import_files_click(self):
        #extract the file paths from the entry widgets
        node_files_path = self.node_file_path_entry.get()
        edge_files_path = self.edge_file_path_entry.get()
        schedule_files_path = self.schedule_file_path_entry.get()
        #check that each file path is valid, and if so, import the file
        node_path_valid = path.isfile(node_files_path)
        edge_path_valid = path.isfile(edge_files_path)
        schedule_path_valid = path.isfile(schedule_files_path)
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
        
        #print a relevant message if import successful
        if import_successful:
            import_files_message = import_files_message + " files imported successfully"
        else:
            import_files_message = import_files_message + " file import failed"
        
        #print the message about the result of importing files
        self.message_update(import_files_message)

    #draw the network from the imported files
    def draw_network_click(self):      
        if self.first_render_flag==False:
            self.erase_network_graph()
        if self.simulation_setup_flag:
            self.erase_all_nodes_text()
        self.extract_nodes_graph()
        self.calculate_node_position()
        self.extract_edges_graph()
        self.render_graph()
        self.first_render_flag = False

    #setup the simulated network
    def setup_simulation_click(self):
        time1 = time.time()
        self.sim_network = n.Network(self.nodes_csv,self.edges_csv,self.schedule_csv,self.verbose)
        time2 = time.time()
        simulation_setup_message = "simulation setup in \n" +  "{:.3f}".format(time2-time1) + " seconds"
        self.log_print(simulation_setup_message)
        self.message_update(simulation_setup_message)
        if self.simulation_setup_flag:   #only setup network visulisation tools if they have not already been created
            pass
        else:
            self.setup_network_viz_tools() #setup tools for exploring aspects of the simulated network
            self.simulation_setup_flag = True #flag to indicate that the simulation has been setup

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

    #NETWORK VIZ TOOLS
    #tools for exploring aspects of the simulated network which do not depend on actual simulation
    #eg ideal journey times and paths, and passenger trip distribution

    #setup these tools
    def setup_network_viz_tools(self):
        #create the overall frame
        self.network_viz = tk.Frame(master=self.main_controls)
        self.network_viz.pack(side = tk.TOP)
        self.display_mode_label = tk.Label(master=self.network_viz,text='DISPLAY MODE',fg='black',bg='white',width=20)
        self.display_mode_label.pack()
        #create a button to choose whether we are viewing information "from" a node or "too" a node
        self.too_from_select_button = tk.Button(master=self.network_viz,text="FROM NODE",fg='black',bg='white',command=self.too_from_select_click,width=20)
        self.too_from_select_button.pack()
        self.from_node = True #True = from_node, False= too_node  
        #create a button to select whether to provide a numeric overlay on the canvas to provide information about node relationships
        self.numeric_overlay_button = tk.Button(master=self.network_viz,text="NO NUMERIC OVERLAY",fg='black',bg='white',command=self.numeric_overlay_click,width=20,height=2)
        self.numeric_overlay_button.pack()
        self.numeric_overlay_mode = 'no_info'
        #create a button to select whether to use the size of nodes to provide information about nodes and their relationships
        self.node_size_button = tk.Button(master=self.network_viz,text="CONSTANT NODE SIZE",fg='black',bg='white',command=self.node_size_click,width=20,height=2)
        self.node_size_button.pack()
        self.node_size_type = "constant" #by default, nodes will be a constant size
        #a button to select whether to use the colour of nodes to provide information about node relationships
        self.node_colour_button = tk.Button(master=self.network_viz,text="CONSTANT NODE COLOUR",fg='black',bg='white',command=self.node_colour_click,width=20,height=2)
        self.node_colour_button.pack()
        self.node_colour_type = "constant"

    #delete the network_viz tool controls 
    def clear_network_viz_tools(self):
        self.network_viz.destroy()

    #CLICK FUNCTIONS FOR NETWORK VIZ TOOLS

    #command for button to switch whether numeric information (eg num passengers) will be displayed next to all relevant nodes
    def numeric_overlay_click(self):
        if self.numeric_overlay_mode == 'no_info': #switch to node total mode, where the total traffic too/from each node is displayed
            self.numeric_overlay_mode = 'node_total' 
            self.numeric_overlay_button.config(text="NODE TOTAL OVERLAY")
            self.update_text_same_node()

        elif self.numeric_overlay_mode == 'node_total':#switch to node relative mode, where the traffic too/from the key node is displayed
            self.numeric_overlay_mode = 'node_relative' 
            self.numeric_overlay_button.config(text="NODE RELATIVE OVERLAY")
            self.update_text_same_node()

        elif self.numeric_overlay_mode == 'node_relative':#switch to distance mode, where the distance too/from the key node is displayed
            self.numeric_overlay_mode = 'node_distance'
            self.numeric_overlay_button.config(text="NODE DISTANCE OVERLAY")
            self.update_text_same_node()

        else: #switch back to the default mode of no numeric overlay
            self.numeric_overlay_mode = 'no_info'
            self.numeric_overlay_button.config(text="NO NUMERIC OVERLAY")
            self.update_text_same_node()


    #command for button to switch between options for setting node size
    def node_size_click(self):
        if self.node_size_type == "constant":
            #switch to modes where node size based on traffic coming too/from the clicked node
            self.node_size_type = "node_relative"
            if self.from_node:
                self.node_size_button.config(text="NODE SIZE TRAFFIC \n FROM CLICKED NODE")
            else:
                self.node_size_button.config(text="NODE SIZE TRAFFIC \n TO CLICKED NODE")
        elif self.node_size_type == "node_relative":
            #switch to a mode where node size is based on total traffic too/from each node
            self.node_size_type = "node_total"     
            if self.from_node:   
                self.node_size_button.config(text="NODE SIZE TOTAL TRAFFIC \n FROM NODE")
            else:
                self.node_size_button.config(text="NODE SIZE TOTAL TRAFFIC \n TO NODE")
        else:
            self.node_size_type = "constant"
            self.node_size_button.config(text="CONSTANT NODE SIZE")
        
        #rerender the nodes to be of the correct size
        self.update_nodes()

    #command for button to switch between options for setting node colour
    def node_colour_click(self):
        if self.node_colour_type == "constant":
            #switch to mode where node colour is based on journey distance to/from clicked node
            self.node_colour_type = "distance"
            if self.from_node:
                self.node_colour_button.config(text="NODE COLOUR DISTANCE \n FROM CLICKED NODE")
            else:
                self.node_size_button.config(text="NODE COLOUR DISTANCE \n TO CLICKED NODE")
        elif self.node_colour_type == "distance":
            #switch to mode where node colour is based on total traffic coming too/from the clicked node
            self.node_colour_type = "node_relative"
            if self.from_node:
                self.node_colour_button.config(text="NODE COLOUR TRAFFIC \n FROM CLICKED NODE")
            else:
                self.node_colour_button.config(text="NODE COLOUR TRAFFIC \n TO CLICKED NODE")
        elif self.node_colour_type == "node_relative":
            #switch to a mode where node colour is based on total traffic too/from each node
            self.node_colour_type = "node_total"
            if self.from_node:   
                self.node_colour_button.config(text="NODE COLOUR TOTAL TRAFFIC \n FROM NODE")
            else:
                self.node_colour_button.config(text="NODE COLOUR TOTAL TRAFFIC \n TO NODE") 

        elif self.node_colour_type=="node_total":
            self.node_colour_type = "constant"
            self.node_colour_button.config(text="CONSTANT NODE COLOUR")
        
         #rerender the nodes to be of the correct colour
        self.update_nodes()

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

    #calculate_node_sizes based on provided information
    def calculate_node_sizes(self,nodes_quantity,total_quantity,mode='default'):
        num_nodes = len(nodes_quantity)
        for i in range(num_nodes):
            node_fraction = nodes_quantity[i]/total_quantity#fraction of total amount occuring at that node
            self.nodes_radii[i] = (node_fraction**(1/self.custom_node_exponent))*self.max_node_radius
            if self.nodes_radii[i] < self.min_node_radius: #enforce the minimum size of a node
                self.nodes_radii[i] = self.min_node_radius

    #calculate node colour based on provided information
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
            if node_fraction<=midpoint:
                #colour scale is from blue to green
                green = node_fraction/midpoint
                blue =  1-green
                red = 0
            elif node_fraction>midpoint:
                #colour scale is from green to red
                red = (node_fraction-midpoint)/(1-midpoint)
                green = 1-red
                blue = 0
            
            #convert 24 bit RGB colour to the hex format expected by tkinter 
            self.nodes_colour[i] = RGB_TO_TK_HEX(int(red*255),int(green*255),int(blue*255))

    #FUNCTIONS CONTROLLING RENDERING OF NODES/EDGES

    #wrapper that recalculates node sizes and colours, and redraws the nodes
    def update_nodes(self):
        self.set_node_sizes()
        self.set_node_colours()
        self.render_graph()

    #update text rendering next to nodes without changing the node whose information we are using (eg distance to/from that node)
    def update_text_same_node(self):
        if self.numeric_overlay_mode == 'node_total':
        #if we are overlaying based on total traffic too/from node, the key node does not matter, so we can display info without it
            self.erase_all_nodes_text() #erase all text already displayed
            self.text_total_passengers_node() #replace with new info about total traffic too/from a node    
        #otherwise don't update if no node-specific text was being displayed in the first place
        elif self.last_node_left_click_index == -1:
            self.erase_all_nodes_text() #erase all text already displayed
            pass
        else:         
            last_click_index = self.last_node_left_click_index
            self.erase_all_nodes_text() #erase all text already displayed
            self.last_node_left_click_index = -1 #set this to -1 so update_nodes_viewing_mode correctly renders with a different mode (note keep this here for redunancy in case end up removing the reset from erase_all_nodes_text)
            self.update_nodes_viewing_mode_left_click(last_click_index) #update the render
            self.last_node_left_click_index = last_click_index #set last left click index back to it's previous value so we can still remove info by clicking on that node again

    #update the display relating to nodes in response to a left click
    def update_nodes_viewing_mode_left_click(self,left_click_index):
        if self.numeric_overlay_mode == 'node_total':
             self.text_total_passengers_node() #display the total number of passengers going too/from all nodes
        elif self.last_node_left_click_index == left_click_index: #if the same node has been clicked on again
            self.erase_all_nodes_text() #reset all text
            self.last_node_left_click_index = -1
        else: #otherwise, display info text for new node
            if self.numeric_overlay_mode == 'no_info':
                self.erase_all_nodes_text() #reset all text, as not used in this mode
            elif self.numeric_overlay_mode == 'node_relative':
                self.text_passengers_node(left_click_index) #display the number of passengers going too/from this particular node
            elif self.numeric_overlay_mode == 'node_distance':
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
        self.node_text_ids = ['blank']*num_nodes  #canvas ids for text which could be displayed next to all nodes
        self.node_canvas_ids = ['blank']*num_nodes #canvas ids for the nodes themsleves
        for i in range(num_nodes):
            x,y = self.convert_lat_long_to_x_y(self.node_latitudes[i],self.node_longitudes[i])
            self.nodes_x.append(x)
            self.nodes_y.append(y)

    #FUNCTIONS PERFORMING ACTUAL RENDERING

    #needs to be run after edges have been extracted and nodes have been drawn to work correctly
    def render_edges(self):
        num_edges = len(self.edge_start_indices)
        for i in range(num_edges):
            start_index = self.edge_start_indices[i]
            end_index = self.edge_end_indices[i]
            start_x = self.nodes_x[start_index]
            start_y = self.nodes_y[start_index]
            end_x = self.nodes_x[end_index]
            end_y = self.nodes_y[end_index]
            colour = self.edge_colours[i]
            width = self.edge_widths[i]
            edge_arrow = self.edge_arrows[i]
            #end_size = self.nodes_radii[end_index] #unused, we draw nodes over edges so no need to crop the edges
            if self.edge_canvas_ids[i]!='blank':
                #delete the old line object if one exists
                self.canvas.delete(self.edge_canvas_ids[i])

            id = self.canvas.create_line(start_x,start_y,end_x,end_y,fill=colour,disableddash=width,activewidth=width+self.active_width_addition,arrow=edge_arrow) #draw a line to represent the edge
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

    #combination of render nodes and render edges, in correct order to prevent edges spawning over nodes
    def render_graph(self):
        self.render_edges()
        self.render_nodes()

    #stop displaying all the nodes and edges
    def erase_network_graph(self):
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
        display_text = "Node : " + node_name
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
        display_text_start = "Node : " + self.node_names[start_index]
        display_text_end = "Node : " + self.node_names[end_index]
        #create the text popups, which are not interactive
        self.text_id_line_start = self.canvas.create_text(start_x,start_y-15,text=display_text_start,state=tk.DISABLED)
        self.text_id_line_end = self.canvas.create_text(end_x,end_y-15,text=display_text_end,state=tk.DISABLED)

    #event for when we mouse away from an edge
    def edge_leave(self,event):
        self.canvas.delete(self.text_id_line_start)
        self.canvas.delete(self.text_id_line_end)

    #FUNCTIONS TO GENERATE INFO TEXT ABOVE NODES

    #display the number of passengers travelling to/from a node to all other nodes (per hour as currently setup) as text above the nodes
    def text_passengers_node(self,key_node_index):
        if self.from_node:
            trips = self.sim_network.origin_destination_trips[key_node_index,:] #extract number of trips starting from this node
        else:
            trips = self.sim_network.origin_destination_trips[:,key_node_index] #extract number of trips going to this node

        self.display_text_info_above_node(trips,mode='float') #display the number of trips starting/ending at every other node
    
    def text_total_passengers_node(self):
        if self.from_node:
            trips = np.sum(self.sim_network.origin_destination_trips,0)#extract number of trips starting from all nodes
        else:
            trips = np.sum(self.sim_network.origin_destination_trips,1) #extract number of trips ending at all nodes

        self.display_text_info_above_node(trips,mode='float') #display the number of trips starting/ending at each node node
    
    #display the number of passengers travelling to/from a node to all other nodes (per hour as currently setup) as text above the nodes
    def text_journeys_node(self,key_node_index):
        if self.from_node:
            times = self.sim_network.distance_to_all[key_node_index,:] #extract journey times starting at this node
        else:
            times = self.sim_network.distance_to_all[:,key_node_index] #extract journey times going to this node
        
        self.display_text_info_above_node(times,mode='integer') #display journey times to/from every other node

    #perform the actual text rendering for all nodes
    def display_text_info_above_node(self,info,mode):
        num_nodes = len(self.node_names)
        self.erase_all_nodes_text() #clear any old text
        self.node_text_ids = ['blank']*num_nodes #create a container for the new text ids
        for i in range(num_nodes): #for every node
            node_x = self.nodes_x[i]
            node_y = self.nodes_y[i]
            this_info = info[i]
            if mode=='float':
                this_info = "{:.2f}".format(this_info) #floating point data
            elif mode=='integer':
                this_info = str(this_info) #integer data
            
            self.node_text_ids[i] = self.canvas.create_text(node_x,node_y+15,text=this_info,state=tk.DISABLED) #create a text popup, which is not interactive

    #erase text displayed next to all nodes (eg num passengers/journey time)
    def erase_all_nodes_text(self):
        self.last_node_left_click_index = -1 #we are deleting all nodes text, so reset if any nodes have been clicked
        for id in self.node_text_ids:
            if id!='blank':
                self.canvas.delete(id)
            
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
    

