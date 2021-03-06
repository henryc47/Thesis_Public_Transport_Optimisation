#display.py
#responsible for displaying a visualisation of activity on the network

import tkinter as tk
import time as time
import pandas as pd 
import network as n
import warnings as warnings
from os import path, times #for checking if file exists

class Display:

    def __init__(self):
        self.setup_window() #create the display window
        self.setup_canvas() #create the canvas where we can draw edges and nodes and vehicles
        self.render_canvas() #setup the canvas on which we will draw our visulisation
        self.setup_controls() #setup the widgets which will allow us to control the simulation and canvas 
        #display constants 
        self.max_circle_radius = 20
        self.base_node_radius = 5
        self.base_node_color = 'grey'
        self.line_width = 2
        self.active_width = 3
        self.line_colour = 'black'
        self.first_render = True #if it is not the first render, we need to delete rendering objects before drawing new ones
        self.simulation_setup = False #flag to indicate if simulation has been setup before
        self.gui_mode = 'view_nodes' #mode of the display, view_nodes mean that hovering over nodes/edges will display node + edge names
        self.last_node_left_click_id = -1 #index of last node left-click, -1 indicates that no nodes have been clicked yet

    #setup the control options
    def setup_controls(self):
        #create the control panel
        self.controls = tk.Frame(master=self.window)
        self.controls.pack(side = tk.LEFT)
        #default file paths
        default_nodes = 'nodes_basic.csv'
        default_edges = 'edges_basic.csv'
        default_schedule = 'schedule_basic.csv'
        #options
        #verbose option, determines level of logging to the console
        self.verbose = -1 #default level of logging is  0=none, 1=verbose, 2=super verbose, -1 is placeholder for setup
        self.verbose_button = tk.Button(master=self.controls,fg='black',bg='white',command=self.verbose_button_click,width=20)
        self.verbose_button.pack()
        self.verbose_button_click() #display initial message
        #label and input to import node files
        self.node_file_path_label = tk.Label(master=self.controls,text='NODE FILE PATH',fg='black',bg='white',width=20)
        self.node_file_path_label.pack()
        self.node_file_path_entry = tk.Entry(master=self.controls,fg='black',bg='white',width=20)
        self.node_file_path_entry.insert(0,default_nodes)
        self.node_file_path_entry.pack()
        #label and input to import edge files
        self.edge_file_path_label = tk.Label(master=self.controls,text='EDGE FILE PATH',fg='black',bg='white',width=20)
        self.edge_file_path_label.pack()
        self.edge_file_path_entry = tk.Entry(master=self.controls,fg='black',bg='white',width=20)
        self.edge_file_path_entry.insert(0,default_edges)
        self.edge_file_path_entry.pack()
        #label and input to import schedule files
        self.schedule_file_path_label = tk.Label(master=self.controls,text='SCHEDULE FILE PATH',fg='black',bg='white',width=20)
        self.schedule_file_path_label.pack()
        self.schedule_file_path_entry = tk.Entry(master=self.controls,fg='black',bg='white',width=20)
        self.schedule_file_path_entry.insert(0,default_schedule)
        self.schedule_file_path_entry.pack()
        #control for importing files 
        self.import_files_button = tk.Button(master=self.controls,text='IMPORT FILES',fg='black',bg='white',command=self.import_files_click,width=20)
        self.import_files_button.pack()
        #this button will draw the network
        self.draw_network_button = tk.Button(master=self.controls,text="DRAW NETWORK",fg='black',bg='white',command=self.draw_network_click,width=20)
        self.draw_network_button.pack()
        #this button will start the simulation
        self.setup_simulation_button = tk.Button(master=self.controls,text="SETUP SIMULATION",fg='black',bg='white',command=self.setup_simulation_click,width=20)
        self.setup_simulation_button.pack()
        #this label will provide information to the user
        self.message_header = tk.Label(master=self.controls,text='MESSAGE',fg='black',bg='white',width=20)
        self.message_header.pack()
        self.message = tk.Label(master=self.controls,text='',fg='black',bg='white',width=20,height=5)
        self.message.pack()

    #run the simulation
    def setup_simulation_click(self):
        time1 = time.time()
        self.sim_network = n.Network(self.nodes_csv,self.edges_csv,self.schedule_csv,self.verbose)
        time2 = time.time()
        simulation_setup_message = "simulation setup in \n" +  "{:.3f}".format(time2-time1) + " seconds"
        self.log_print(simulation_setup_message)
        self.message_update(simulation_setup_message)
        if self.simulation_setup:   #only setup network visulisation tools if they have not already been created
            pass
        else:
            self.setup_network_viz_tools() #setup tools for exploring aspects of the simulated network
        self.simulation_setup = True #flag to indicate that the simulation has been setup
        
    
    #setup tools for exploring aspects of the simulated network which do not depend on actual simulation
    #eg ideal journey times and paths, and passenger trip distribution
    def setup_network_viz_tools(self):
        self.network_viz = tk.Frame(master=self.controls)
        self.network_viz.pack(side = tk.TOP)
        self.display_mode_label = tk.Label(master=self.network_viz,text='DISPLAY MODE',fg='black',bg='white',width=20)
        self.display_mode_label.pack()
        #a button to choose viewing details about trip distribution
        self.view_passengers_button =  tk.Button(master=self.network_viz,text="PASSENGERS",fg='black',bg='white',command=self.view_passengers_click,width=20)
        self.view_passengers_button.pack()
        #a button to choose viewing details about ideal journeys
        self.view_journeys_button =  tk.Button(master=self.network_viz,text="JOURNEYS",fg='black',bg='white',command=self.view_journeys_click,width=20)
        self.view_journeys_button.pack()
        #a button to choose whether we are viewing information "from" a node or "too" a node
        self.too_from_select_button = tk.Button(master=self.network_viz,text="FROM NODE",fg='black',bg='white',command=self.too_from_select_click,width=20)
        self.too_from_select_button.pack()
        self.from_node = True #True = from_node, False= too_node
        #a button to select whether to use numeric text to provide information about node relationships
        self.numeric_text_button = tk.Button(master=self.network_viz,text="NUMERIC INFO",fg='black',bg='white',command=self.numeric_text_click,width=20)
        self.numeric_text_button.pack()
        self.numeric_text = True

    #command for button to switch numeric information (eg num passengers) being displayed when nodes clicked on
    def numeric_text_click(self):
        if self.numeric_text: #switch to no numeric info mode
            self.numeric_text = False
            self.numeric_text_button.config(text='NO NUMERIC INFO')
            self.update_render_same_node()
        else: #switch to numeric info mode
            self.numeric_text = True
            self.numeric_text_button.config(text='NUMERIC INFO')
            self.update_render_same_node()


    #update node rendering without changing the id of the node whose information we are using
    def update_render_same_node(self):
        #don't update if no node-specific text was being displayed in the first place
        if self.last_node_left_click_id == -1:
            pass
        else:         
            last_click_id = self.last_node_left_click_id
            self.erase_all_nodes_text() #erase all text already displayed
            self.last_node_left_click_id = -1 #set this to -1 so update_nodes_viewing_mode correctly renders with a different mode (note keep this here for redunancy in case end up removing the reset from erase_all_nodes_text)
            self.update_nodes_viewing_mode(last_click_id) #update the render
            self.last_node_left_click_id = last_click_id #set last left click id back to it's previous value so we can still remove info by clicking on that node again

    #switch between viewing information too a node or from a node
    def too_from_select_click(self):
        if self.from_node:
            self.from_node = False
            self.too_from_select_button.config(text='TOO NODE')
            self.update_render_same_node()
        else:
            self.from_node = True
            self.too_from_select_button.config(text='FROM NODE')
            self.update_render_same_node()

    #function called by pressing the view passengers button, switch to view passengers viewing mode
    def view_passengers_click(self):
        if self.gui_mode == 'view_passengers': #if we already selected the mode selected by the button, switch to the default mode
            self.gui_mode = 'view_nodes'
            self.erase_all_nodes_text()
            self.message_update("default view mode selected")
        else:
            self.gui_mode = 'view_passengers'
            self.update_render_same_node()
            self.message_update("viewing passenger \n trip distribution")

    #function called by pressing the view passengers button, switch to view journeys viewing mode
    def view_journeys_click(self):
        if self.gui_mode == 'view_journeys': #if we already selected the mode selected by the button, switch to the default mode
            self.gui_mode = 'view_nodes'
            self.message_update("default view mode selected")
        else:
            self.gui_mode = 'view_journeys'
            self.message_update("viewing journey times")
            self.update_render_same_node()
    


    #prints a message to the console only if the logging level is at a certain level (default=1)
    def log_print(self,message,log_level=1):
        if self.verbose>=log_level:
            print(message)

    #update the control message board
    def message_update(self,string):
        self.message.config(text=string)

    #switch logging level upwards on click
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
        
    #import the requested files
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
            
    #setup the window object
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

    def render_canvas(self):
        self.canvas.pack(side = tk.RIGHT)

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
        pixels_per_degree_vertical = (self.canvas_height-(self.max_circle_radius*4))/range_latitude
        pixels_per_degree_horizontal = (self.canvas_width-(self.max_circle_radius*4))/range_longitude
        #the lower value is the limiting factor for an undistorted map
        self.pixels_per_degree = min(pixels_per_degree_vertical,pixels_per_degree_horizontal) 

    #extract the list of edges from a csv file into a python list, and calculate global geographical information for plotting
    #this needs to be run after nodes have been extracted so start/end node index assignment can be done
    def extract_edges_graph(self):
        edge_starts = self.edges_csv["Start"].to_list()
        edge_ends = self.edges_csv["End"].to_list()
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

            self.edge_start_indices.append(start_index)
            self.edge_end_indices.append(end_index)

        self.edge_canvas_ids = ['blank']*num_edges #store edge canvas ids in a list so we can delete them later, 'blank' indicates they have not yet been created

    #needs to be run after edges have been extracted and nodes have been drawn to work correctly
    def render_edges(self):
        num_edges = len(self.edge_start_indices)
        for i in range(num_edges):
            start_index = self.edge_start_indices[i]
            end_index = self.edge_end_indices[i]
            start_x = self.nodes_x[start_index]
            start_y = self.nodes_y[start_index]
            start_size = self.nodes_radii[start_index]
            end_x = self.nodes_x[end_index]
            end_y = self.nodes_y[end_index]
            end_size = self.nodes_radii[end_index]
            if self.edge_canvas_ids[i]!='blank':
                #delete the old line object if one exists
                self.canvas.delete(self.edge_canvas_ids[i])
            id = self.canvas.create_line(start_x,start_y,end_x,end_y,fill=self.line_colour,disableddash=self.line_width,activewidth=self.active_width) #draw a circle to represent the node
            self.canvas.tag_bind(id,'<Enter>',self.edge_enter) #some information about the start and end nodes will be displayed when we mouse over an edge
            self.canvas.tag_bind(id,'<Leave>',self.edge_leave) #this information will stop being displayed when the mouse is no longer over the node
            self.edge_canvas_ids[i] = id

    #calculate information about position of nodes
    def calculate_node_position(self):
        num_nodes = len(self.node_names)
        self.nodes_x = []
        self.nodes_y = []
        self.nodes_radii = [self.base_node_radius]*num_nodes #default size for nodes
        self.nodes_colour = [self.base_node_color]*num_nodes #default
        self.node_text_ids = ['blank']*num_nodes  #canvas ids for text which could be displayed next to all nodes
        self.node_canvas_ids = ['blank']*num_nodes #canvas ids for the nodes themsleves
        for i in range(num_nodes):
            x,y = self.convert_lat_long_to_x_y(self.node_latitudes[i],self.node_longitudes[i])
            self.nodes_x.append(x)
            self.nodes_y.append(y)

    #draw the nodes on the canvas
    def render_nodes(self):
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            #extract data
            x = self.nodes_x[i]
            y = self.nodes_y[i]
            radius = self.nodes_radii[i]
            colour = self.nodes_colour[i]
            if self.node_canvas_ids[i]!='blank':
                #delete the old oval object if one exists
                self.canvas.delete(self.node_canvas_ids[i])
            id = self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=colour) #draw a circle to represent the node
            self.canvas.tag_bind(id,'<Enter>',self.node_enter) #some information about the node will be displayed when the mouse is hovered over it
            self.canvas.tag_bind(id,'<Leave>',self.node_leave) #this information will stop being displayed when the mouse is no longer over the node
            self.canvas.tag_bind(id,'<Button-1>',self.node_left_click) #depending on gui_mode, information about the nodes relationship to other nodes will be displayed
            self.canvas.tag_bind(id,'<Button-2>',self.node_right_click) #depending on gui_mode, information about the nodes relationship to other nodes will be displayed
            self.node_canvas_ids[i] = id #store the id so we can delete the object later
            #self.origin_destination_trips


    def draw_network_click(self):
        
        if self.first_render==False:
            self.erase_network_graph()
        if self.simulation_setup:
            self.erase_all_nodes_text()
        self.extract_nodes_graph()
        self.calculate_node_position()
        self.extract_edges_graph()
        self.render_edges()
        self.render_nodes()
        self.first_render = False

    #erase the network graph 
    def erase_network_graph(self):
        #erase all edges
        for id in self.edge_canvas_ids:
            if id!='blank':
                self.canvas.delete(id)
        #erase all nodes
        for id in self.node_canvas_ids:
            if id!='blank':
                self.canvas.delete(id)
        
    def convert_lat_long_to_x_y(self,latitude,longitude):
        latitude_offset = latitude-self.central_latitude
        longitude_offset = longitude-self.central_longitude
        y = self.canvas_center_y-(latitude_offset*self.pixels_per_degree) #we need to flip the offset along the y axis, as higher values mean further down (south) in canvas coordinates
        x = self.canvas_center_x+(longitude_offset*self.pixels_per_degree)
        return (x,y)

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
        self.update_nodes_viewing_mode(id_index)

    #update the display of nodes based on viewing mode
    def update_nodes_viewing_mode(self,id_index):
        if self.last_node_left_click_id == id_index: #if the same node has been clicked on again
            self.erase_all_nodes_text() #reset all text
            self.last_node_left_click_id = -1
        else: #otherwise, display info text for new node
            if self.gui_mode == 'view_nodes':
                self.erase_all_nodes_text() #reset all text, as not used in this mode
            elif self.gui_mode == 'view_passengers':
                self.view_passengers_from_node(id_index)
            elif self.gui_mode == 'view_journeys':
                self.view_journeys_from_node(id_index)
            self.last_node_left_click_id = id_index #record this was the last node we clicked on
    
    #event for when we right-click on a node
    def node_right_click(self,event):
        print('placeholder for node right click')

    #display the number of passengers travelling from a node to all other nodes (per hour as currently setup)
    def view_passengers_from_node(self,id_index):
        if self.from_node:
            trips = self.sim_network.origin_destination_trips[id_index,:] #extract number of trips starting from this node
        else:
            trips = self.sim_network.origin_destination_trips[:,id_index] #extract number of trips going to this node

        self.display_text_info_above_node(trips,mode='float') #display the number of trips starting/ending at every other node
    
    def view_journeys_from_node(self,id_index):
        if self.from_node:
            times = self.sim_network.distance_to_all[id_index,:] #extract journey times starting at this node
        else:
            times = self.sim_network.distance_to_all[:,id_index] #extract journey times going to this node
        
        self.display_text_info_above_node(times,mode='integer') #display journey times to/from every other node

    #perform the actual rendering for the view_passengers_from_node function
    def display_text_info_above_node(self,info,mode):
        num_nodes = len(self.node_names)
        self.erase_all_nodes_text() #clear any old text
        if self.numeric_text: #only display numeric text above node if we are in a viewing mode that allows that
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
        self.last_node_left_click_id = -1 #we are deleting all nodes text, so reset if any nodes have been clicked
        for id in self.node_text_ids:
            if id!='blank':
                self.canvas.delete(id)
            




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

    def edge_leave(self,event):
        #event_id = event.widget.find_withtag('current')[0]
        #id_index = self.edge_canvas_ids.index(event_id)
        self.canvas.delete(self.text_id_line_start)
        self.canvas.delete(self.text_id_line_end)




    #for testing
    def update_node_size(self,size):
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes_radii[i] = size
        self.render_nodes()
        self.render_edges()
    
    #for testing
    def update_node_colour(self,colour):
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes_colour[i] = colour
        self.render_nodes()
        self.render_edges()




