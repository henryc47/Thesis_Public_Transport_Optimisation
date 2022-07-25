#display.py
#responsible for displaying a visualisation of activity on the network

import tkinter as tk
import pandas as pd 
import network as n

class Display:

    def __init__(self):
        self.setup_window() #create the display window
        self.setup_canvas() #create the canvas where we can draw edges and nodes and vehicles
        self.render_canvas() 
        #a textbox will allow us to select the file to import for visulisations
        controls = tk.Frame(bg='silver')
        controls.pack(side = tk.LEFT)
        node_file_path_label = tk.Label(master=controls,text='NODE FILE PATH',fg='black',bg='white')
        node_file_path_label.pack()
        #file_path_entry = tk.Entry(master=controls,fg='white',bg='red')
        #file_path_entry.pack()
        self.draw_network_button = tk.Button(master=controls,text="DRAW NETWORK",fg='black',bg='white',command=self.draw_network_click)
        self.draw_network_button.pack()
        #display constants 
        self.max_circle_radius = 20
        self.base_node_radius = 5
        self.base_node_color = 'grey'



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

    #extract the list of nodes from a csv file into a python list
    def extract_nodes_graph(self,nodes_file_path):
        nodes_csv = pd.read_csv(nodes_file_path,thousands=r',')
        self.node_names = nodes_csv["Name"].to_list()
        node_positions = nodes_csv["Location"].to_list()
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

    #calculate information about position of nodes
    def calculate_node_position(self):
        num_nodes = len(self.node_names)
        self.nodes_x = []
        self.nodes_y = []
        self.nodes_radii = [self.base_node_radius]*num_nodes #default size for nodes
        self.nodes_colour = [self.base_node_color]*num_nodes #default
        self.node_canvas_ids = ['blank']*num_nodes 
        for i in range(num_nodes):
            x,y = self.convert_lat_long_to_x_y(self.node_latitudes[i],self.node_longitudes[i])
            self.nodes_x.append(x)
            self.nodes_y.append(y)

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
            self.canvas.tag_bind(id,'<Enter>',self.node_enter) #some information about the node will be displayed when it is clicked on
            self.canvas.tag_bind(id,'<Leave>',self.node_leave) #this information will stop being displayed when the mouse is no longer over the node
            self.node_canvas_ids[i] = id #store the id so we can delete the object later

    def draw_network_click(self):
        self.extract_nodes_graph('nodes_medium.csv')
        self.calculate_node_position()
        self.render_nodes()
        
    #def resize_window(self,window_height,window_width):
    #    center_x = int(self.window.winfo_screenwidth()/2)
    #    center_y = int(self.window.winfo_screenheight()/2)
    #    self.window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
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
        print('node viewed ', node_name)
        x = self.nodes_x[id_index]
        y = self.nodes_y[id_index]
        display_text = "Node : " + node_name
        self.text_id = self.canvas.create_text(x,y-15,text=display_text,state=tk.DISABLED) #create a text popup, which is not interactive

    #event for when the mouse leaves a node, remove the text box
    def node_leave(self,event):
        event_id = event.widget.find_withtag('current')[0]
        id_index = self.node_canvas_ids.index(event_id)
        node_name = self.node_names[id_index]
        print('node left ', node_name)
        self.canvas.delete(self.text_id) #delete the text popup from node_enter

    #for testing
    def update_node_size(self,size):
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes_radii[i] = size
        self.render_nodes()
    
    #for testing
    def update_node_colour(self,colour):
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes_colour[i] = colour
        self.render_nodes()




