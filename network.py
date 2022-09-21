#network.py
#stores information about the physical network

import pandas as pd #for importing data from csv files
import warnings #for warnings
import numpy as np #for large scale mathematical operations
import time as time #for benchmarking
import schedule as schedule
import vehicle as vehicle
import copy as copy #for shallow-copying schedules
import random as rand
import agent as a

#edge class, represents a (one-way) link between two nodes
#at the moment, only relevant property is travel time taken, but more properties may be added later
#we will be using one second increments for time
class Edge:
    #initialise the node
    def __init__(self,name,start_node,end_node,travel_time):
        self.name = name
        self.start_node = start_node
        self.end_node = end_node
        self.travel_time = travel_time
    
    #provide the destination of the link
    def provide_destination(self):
        return self.end_node
    
    #provide the time to travel along the link
    def provide_travel_time(self):
        return self.travel_time
    
    #provide information about the edge, for testing purposes
    def test_edge(self):
        print(self.name,' is from ',self.start_node,' to ',self.end_node,' a trip taking ',self.travel_time)

#node class, represents a location between which passengers can travel
#the node stores the names of all the nodes which start at it
class Node:
    def __init__(self,name,coordinates):
        self.name = name
        self.edge_names = []#list of all edges starting at this node
        self.edge_destinations = []#and the destination of each node
        self.edge_times = []#matching list of travel time of each respective edge
        (self.latitude,self.longitude) = extract_coordinates(coordinates)
        self.agents = [] #list of all agents at this stations
    
    #add an edge which starts at the node
    def add_edge(self,edge):
        if edge.start_node == self.name:#the edge will be stored with this node only if it starts at the node        
            self.edge_names.append(edge.name)
            self.edge_destinations.append(edge.end_node)
            self.edge_times.append(edge.travel_time)
            return True#Return true to indicate edge has been associated with the node
        else:
            print('edge ', edge.name, ' between ', edge.start_node, ' and ', edge.end_node, ' does not start at node ', self.name)
            return False #Return false to indicate edge has not been associated with the node

    #return the time taken to travel along a particular edge
    #for this function to work correctly, edge names must be unique
    def provide_edge_time(self,edge_name):
        try: 
            edge_index = self.edge_names.index(edge_name)
            time_taken = self.edge_times[edge_index]
            return (True,time_taken) #True to indicate search operation was successful
        except ValueError: #edge name not in list of provided eges
            print('edge ', edge_name, ' not in list of edges starting at this node')
            return False #False to indicate search operation unsuccessful 

    #return the time taken to travel to all neighbouring nodes and the names of the destination 
    def provide_nodes_time(self):
        return (self.edge_times,self.edge_destinations)

    #as above, but also provides the name of the connecting edge
    def provide_nodes_time_edge_name(self):
        return (self.edge_times,self.edge_destinations,self.edge_names)

    #return the time taken to travel to a destination as well as the edge to reach it
    #for this function to work correctly, edge names must be unique
    def provide_node_time(self,destination_name):
        try: 
            node_index = self.edge_destinations.index(destination_name)
            time_taken = self.edge_times[node_index]
            edge_taken = self.edge_names[node_index]
            return (True,time_taken,edge_taken) #True to indicate search operation was successful
        except ValueError: #destination name not in list of provided nodes
            print('node ', destination_name, ' not in list of nodes reachable from this node')
            return False #False to indicate search operation unsuccessful
    
    #add a agent to the station
    def add_agent(self,agent):
        self.agents.append(agent)

    #count the number of agents at the station
    def count_agents(self):
        return len(self.agents)

    def test_node(self):
        print('from node ',self.name, ' edges are')
        for i in range(len(self.edge_names)):
            print(self.edge_names[i], ' goes too ',self.edge_destinations[i],' taking ',self.edge_times[i])
        print('node latitude is ',self.latitude, ' longitude is ',self.longitude)
    

#network class, represents the overall structure of the transport network
class Network:
    #initalise the physical network
    #note, this assumes that passengers are evenly distributed through the day
    def __init__(self,nodes_csv,edges_csv,schedule_csv,verbose=1):
        time1 = time.time()
        self.verbose = verbose #import verbosity
        #where we will store edges and nodes
        self.edges = [] #list of edges 
        self.nodes = [] #list of nodes
        self.edge_names = [] #list of generated edge names
        #extract the raw data
        #now extract node data
        self.node_names = nodes_csv["Name"].to_list()
        node_positions = nodes_csv["Location"].to_list() 
        #and let's create the nodes
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes.append(Node(self.node_names[i],node_positions[i]))

        #extract edge data
        self.edge_starts = edges_csv["Start"].to_list()
        self.edge_ends = edges_csv["End"].to_list()
        self.edge_times = edges_csv["Time"].to_list()
        self.edge_bidirectional = edges_csv["Bidirectional"].to_list()
        #and let's create the edges
        num_edges = len(self.edge_starts)
        for i in range(num_edges):
            if (self.edge_bidirectional[i]=='Yes'):#if input edge is two-way
                #create two edges, one "UP" (by convention towards central), one "DOWN", (away from central)
                self.add_edge(self.edge_starts[i],self.edge_ends[i],self.edge_times[i])#UP
                self.add_edge(self.edge_ends[i],self.edge_starts[i],self.edge_times[i])#DOWN
            else:
                #if input edge is one way
                self.add_edge(self.edge_starts[i],self.edge_ends[i],self.edge_times[i])#UP



        #allocate passengers 
        #this will be replaced by a more sophisticated method of passenger allocation later
        num_hours = 12#
        self.node_passengers = (nodes_csv["Daily_Passengers"]/num_hours).to_list()#passengers per hour for each station
        time2 = time.time()
        if self.verbose>=1:
            print('time to extract and process network data - ', time2-time1, ' seconds')
        time1 = time.time()
        self.find_distance_to_all_path()#find the shortest distance between all edges on the network, as well as the paths between them
        time2 = time.time()
        if self.verbose>=1:
            print('time to find ideal travel time between all nodes - ', time2-time1, ' seconds')
        time1 = time.time()
        self.create_origin_destination_matrix()#create the origin destination matrix for the network
        time2 = time.time()
        if self.verbose>=1:
            print('time to assign passengers to origin destination pairs - ', time2-time1, ' seconds')
        time1 = time.time()
        self.find_expected_edge_traffic()
        time2 = time.time()
        if self.verbose>=1:
            print('time to calculate traffic along each edge ',time2-time1, ' seconds')

        self.schedule_csv = schedule_csv
        #setup for vehicle simulations
        self.num_vehicles_started_here = np.zeros(num_nodes) #store the number of vehicles on the network which started from a particular node
        self.vehicles = [] #container to store vehicles in
        self.vehicle_names = [] #container to store vehicle names in, note this is just schedule name followed by initial departure time 
        #set the simulation timestamp to be 0 (start of simulation)
        self.time = 0
        #containers to store agents (passengers) and agent ids
        self.agents = []
        self.agent_ids = []
        self.agent_id_counter = 0 #id of the next agent to be generated

    #create a new vehicle and add it to the network
    def create_vehicle(self,schedule):
        vehicle_name = str(self.time) + " " + schedule.provide_name() #calculate the vehicles name
        #produce a shallow copy of the schedule to provide to the vehicle, note we use a class defined implemention of shallow-copying
        copy_schedule = copy.copy(schedule) #copy the schedule object, but maintain keep references to node/edges identical
        junk,start_node = copy_schedule.provide_next_destination() #extract the first destination of the schedule
        start_node_index = self.get_node_index(start_node.name)
        self.num_vehicles_started_here[start_node_index] += 1 #record that a vehicle started at a particular node
        self.vehicle_names.append(vehicle_name) #add the vehicles name to the list
        self.vehicles.append(vehicle.Vehicle(copy_schedule,self.time,vehicle_name)) #create the vehicle and add it to the list
        if self.verbose>=1:
            print('a vehicle ', vehicle_name, ' has been created at ',start_node.name, ' at time ',self.time)

    #this function updates all the vehicle objects in the network
    def move_vehicles(self):
        for count,vehicle in enumerate(self.vehicles):
            #logging
            if self.verbose==1:
                vehicle.verbose_stop()
            elif self.verbose>=2:
                vehicle.verbose_position()
            not_reached_destination = vehicle.update()
            if not_reached_destination == False:
                if self.verbose>=1:
                    print('a vehicle ', vehicle.name, ' has reached the end of its path ', vehicle.next_destination.name ," at time ", self.time)
                del self.vehicles[count] #remove the vehicle when it has reached it's destination

    #create vehicles at nodes as needed by the schedule
    def assign_vehicles_schedule(self):
        #run through the all the schedules in the dispatch list
        num_schedules = len(self.schedules)
        for i in range(num_schedules):
            if self.time == self.dispatch_schedule[i]:#if a schedule is too be dispatched at the current time
                #a vehicle is to be dispatched, so create a vehicle here
                self.create_vehicle(self.schedules[i])
                self.dispatch_schedule[i] = self.dispatch_schedule[i] + self.schedule_gaps[i] #next service on this route will dispatch after a period of time

    #create new passengers at stations, going between each node pair
    def create_all_passengers(self):
        num_nodes = len(self.node_names)
        for i in range(num_nodes): #go through all the nodes we are starting from
            start_node = self.nodes[i] #extract a reference to that node
            for j in range(num_nodes): #go through all the nodes we are ending up at
                end_node = self.nodes[j] #extract a reference to that node
                num_passengers_pair = self.origin_destination_trips[i,j] #extract number of passengers going between these node pairs
                num_passengers_per_min = num_passengers_pair/60 #we create passengers every minute, but statistics are per hour
                self.create_passengers_pair(start_node,end_node,num_passengers_per_min)

    #create the passengers for a specific pair of nodes and edges
    def create_passengers_pair(self,start_node,end_node,num_passengers_per_min):
        int_num_passengers = int(num_passengers_per_min) #rounded-down number of passengers to create
        chance_additional_passenger = num_passengers_per_min-int_num_passengers #chance of an additional passenger being created from the remainder
        num_passengers = int_num_passengers + random_true(chance_additional_passenger) #get the final number of passengers to be created
        #now create the actual passengers at the stations
        for i in range(num_passengers):
            self.create_passenger(start_node,end_node)

    #create a single passenger
    def create_passenger(self,start_node,end_node):
        #create the passenger
        self.agent_ids.append(self.agent_id_counter) #store the id of the newly created passenger
        self.agents.append(a.Agent(start_node,end_node,self.agent_id_counter)) #create the new passengers and add to the list
        self.agent_id_counter = self.agent_id_counter + 1 #increment the id counter
        #assign the passenger to their starting station
        start_node.add_agent(start_node)

    #update time by one unit        
    def update_time(self):
        if self.verbose>=1:
            print('time ', self.time)
        
        self.move_vehicles() #move vehicles around the network
        #self.alight_passengers() #passengers alight from vehicles
        #self.remove_arrived_vehicles()  #remove vehicles which have completed their path
        self.assign_vehicles_schedule() #create new vehicles at scheduled locations
        self.create_all_passengers() #create new passengers
        #self.board_passengers() #passengers board vehicles 
        self.time = self.time + 1 #increment time

    #run for a certain amount of time
    def basic_sim(self,stop_time):
        self.create_schedules(self.schedule_csv)
        self.time = 0
        self.times = []
        self.vehicle_logging_init() #initialise vehicle logging
        self.node_logging_init() #initialise node logging
        #create lists to store latitudes,longitudes and names of vehicles over time as lists of lists 
        while self.time<stop_time:#till we reach the specified time
            self.update_time() #run the simulation
            self.times.append(self.time) #store the current time
            self.get_vehicle_data_at_time() #extract vehicle data at the current time
            self.get_node_data_at_time() #extract node data at the current time

        #del self.vehicle_names[0] # dealing with Whacko47
        return self.times,self.vehicle_latitudes,self.vehicle_longitudes,self.store_vehicle_names,self.vehicle_passengers,self.node_passengers #return relevant data from the simulation to the calling code
        
    #class to initialise class variables to store data about the vehicles as lists of lists
    def vehicle_logging_init(self):
        self.vehicle_latitudes = []
        self.vehicle_longitudes = []
        #self.vehicle_names = ['placeholder'] # dealing with Whacko47
        self.store_vehicle_names = []
        self.vehicle_passengers = []

    #class to initalise class variables to store data about nodes as lists of lists
    def node_logging_init(self):
        self.node_passengers = []

    #get relevant data about all vehicles in the network at the present time and store them in lists
    def get_vehicle_data_at_time(self):
        current_vehicle_latitudes = []
        current_vehicle_longitudes = []
        current_vehicle_names = []
        current_vehicle_passenger_counts = []
        for vehicle in self.vehicles:
            #print('single')
            #extract and store the data at the current time in a list
            latitude,longitude = vehicle.get_coordinates() #get the latitude, longitude and direction of the vehicle
            current_vehicle_latitudes.append(latitude)
            current_vehicle_longitudes.append(longitude)
            current_vehicle_names.append(vehicle.name)
            current_vehicle_passenger_counts.append(vehicle.count_agents())
            #print(vehicle.name) #DEBUG
            #print(longitude) #DEBUG
        #and store that list in a list containing data for all time
        self.vehicle_latitudes.append(current_vehicle_latitudes)
        self.vehicle_longitudes.append(current_vehicle_longitudes)
        self.store_vehicle_names.append(current_vehicle_names)
        self.vehicle_passengers.append(current_vehicle_passenger_counts)

    #get relevant data about all nodes in the network at the present time and store them in lists
    def get_node_data_at_time(self):
        current_node_passenger_counts = []
        for node in self.nodes:
            current_node_passenger_counts.append(node.count_agents())
        self.node_passengers.append(current_node_passenger_counts)
                   
    #create the schedule and functionality needed for scheduling
    def create_schedules(self,schedule_csv):
        self.schedule_names = schedule_csv["Name"].to_list() #extract the name of schedules (a route that a vehicle will perform)
        self.schedule_gaps = np.array(schedule_csv["Gap"].to_list()) #extract the gap in time (in minutes) between services along a particular route
        self.schedule_offsets = np.array(schedule_csv["Offset"].to_list()) #extract the offset from the start of time (the hour) and when the first service occurs
        schedule_texts = schedule_csv["Schedule"].to_list() #extract the raw text that makes up a schedule
        self.schedules = [] #list to store the schedule objects
        num_schedules = len(self.schedule_names)

        for i in range(num_schedules):
            self.schedules.append(self.create_schedule(self.schedule_names[i],schedule_texts[i])) #create a schedule object for each schedule
        
        #now that we have created the list of schedules, time to initalise the list of timestamps when services are to be dispatched
        self.dispatch_schedule = np.zeros(num_schedules) + self.schedule_offsets

    #create a schedule object from a name and a text string
    def create_schedule(self,name,schedule_string):
        node_names = extract_schedule_list_txt(schedule_string) #extract node names from the schedule string
        num_nodes = len(node_names)
        node_arrival_times = np.zeros(num_nodes)#arrival times at each node, starting from 0 at the starting node
        node_counter = 0 #which node is currently the next destination
        new_schedule = schedule.Schedule(name)
        previous_node_name = ""
        #add nodes and edges to the schedule
        for node_name in node_names:
            #when processing the starting node, we just add the node to the schedule
            node = self.nodes[self.get_node_index(node_name)]
            if previous_node_name == "":
                new_schedule.add_start_node(node)
                previous_node = node
                previous_node_name = node_name
                node_counter += 1 #we will now be processing the next node
            else:
                edge_name = previous_node_name + ' to ' + node_name #calculate the name of the edge between these two nodes
                edge = self.edges[self.get_edge_index(edge_name)]
                edge_time = edge.provide_travel_time()
                new_schedule.add_destination(node,edge)
                node_arrival_times[node_counter] = node_arrival_times[node_counter-1] + edge_time
                previous_node = node
                previous_node_name = node_name
                node_counter += 1

        #now store arrivial times in the schedule
        new_schedule.add_schedule_times(node_arrival_times)
        return new_schedule

    #add an edge between specified start and end node            
    def add_edge(self,start_node,end_node,travel_time):
        name = start_node + ' to ' + end_node
        while name in self.edge_names:#prevent duplicate names
            #note, that duplicate edge names cause problems with the creation of schedules, so try and avoid them
            warnings.warn('duplicate edge name ', name, ' this is poorly supported, try and only have one edge directly between two nodes')
            name = name + ' alt '
        self.edge_names.append(name)#update the list of edge names
        new_edge = Edge(name,start_node,end_node,travel_time)
        self.edges.append(new_edge)#and create the new edge
        #let's also add the edge to the list of edges at the node it starts from
        i = 0 #temporary counter variable
        for node_name in self.node_names:
            if node_name == start_node:#if node names matches with the starting node
                #add edge to the node
                self.nodes[i].add_edge(new_edge)
            else:
                pass
            i = i+1 
            #increment the counter     

    #find the time taken to travel from the specified node to all other nodes in the network
    #note, this is making the assumption that all nodes are always traversible, the ideal case which does not apply for real passengers
    def find_distance_dijistraka(self,start_node_name):
        #try and find the starting node in the list of all nodes
        try:
            start_index = self.node_names.index(start_node_name)
        except ValueError:
            #handle case where starting name not in list of names
            warnings.warn('start_node_name  ', start_node_name, 'is not in the list of node names in this network')
            return False #return false to indicate error
        #if there was not an error, continue
        num_nodes = len(self.node_names)
        distance_to_nodes = np.ones(num_nodes)*np.inf #set initial cost to reach to be infinite, index order is same as in node names
        nodes_visited = np.zeros(num_nodes) #has node been visited yet, 0 if false, infinite if true
        distance_to_nodes[start_index] =  0 #cost to reach starting node is of course zero
        while True:
            distance_to_use = distance_to_nodes + nodes_visited#consider the cost to reach already visited nodes to be infinite, to prevent the need to look at them twice
            min_distance = np.min(distance_to_use)#get the minimum distance in the array
            if min_distance == np.inf: #if all nodes are either visited or have an infinite known cost to reach, we have explored the network as much as possible
                break#hence break
            min_index = distance_to_use.tolist().index(min_distance)#get the index of the first minimum value
            (edge_times,edge_destinations) = self.nodes[min_index].provide_nodes_time()
            num_edges = len(edge_times)
            for i in range(num_edges):
                try:
                    destination_index = self.node_names.index(edge_destinations[i])
                except ValueError:
                    #handle case where destination name not in list of names
                    warnings.warn('destination name  ', edge_destinations[i], 'is not in the list of node names in this network')
                    continue #skip remaining computation steps

                new_distance = min_distance + edge_times[i] #calculate distance to reach destination through the current node
                if new_distance < distance_to_nodes[destination_index]:#if distance through current node is less than the current minimum distance
                    distance_to_nodes[destination_index] = new_distance #update the distance
            #now we have looked at this node, update the nodes we have visited
            nodes_visited[min_index] =  np.inf #indicate we have visited the node
        
        return distance_to_nodes #return the distance to all the nodes

    #this is the same as find_distance_dijistraka, but it also stores the path as a list of nodes
    def find_distance_dijistraka_path(self,start_node_name):
        #try and find the starting node in the list of all nodes
        try:
            start_index = self.node_names.index(start_node_name)
        except ValueError:
            #handle case where starting name not in list of names
            warnings.warn('start_node_name  ', start_node_name, 'is not in the list of node names in this network')
            return False #return false to indicate error
        #if there was not an error, continue
        num_nodes = len(self.node_names)
        distance_to_nodes = np.ones(num_nodes)*np.inf #set initial cost to reach to be infinite, index order is same as in node names
        #create paths array, this will be a list of paths, with each path a list of edges
        paths = [[] for _ in range(num_nodes)]
        nodes_visited = np.zeros(num_nodes) #has node been visited yet, 0 if false, infinite if true
        distance_to_nodes[start_index] =  0 #cost to reach starting node is of course zero
        while True:
            distance_to_use = distance_to_nodes + nodes_visited#consider the cost to reach already visited nodes to be infinite, to prevent the need to look at them twice
            min_distance = np.min(distance_to_use)#get the minimum distance in the array to a node we know how to reach
            if min_distance == np.inf: #if all nodes are either visited or have an infinite known cost to reach, we have explored the network as much as possible
                break#hence break
            min_index = distance_to_use.tolist().index(min_distance)#get the index of the first minimum value
            (edge_times,edge_destinations,edge_names) = self.nodes[min_index].provide_nodes_time_edge_name()
            num_edges = len(edge_times)
            for i in range(num_edges):
                try:
                    destination_index = self.node_names.index(edge_destinations[i])
                except ValueError:
                    #handle case where destination name not in list of names
                    warnings.warn('destination name', edge_destinations[i], 'is not in the list of node names in this network')
                    continue #skip remaining computation steps

                new_distance = min_distance + edge_times[i] #calculate distance to reach destination through the current node
                if new_distance < distance_to_nodes[destination_index]:#if distance through current node is less than the current minimum distance
                    distance_to_nodes[destination_index] = new_distance #update the distance
                    minimum_path = paths[min_index].copy()
                    minimum_path.append(edge_names[i])  #add the new edge to the minimum path to start node to get the minimum path to the end node
                    paths[destination_index] = minimum_path #store the shortest path to the new node

            #now we have looked at this node, update the nodes we have visited
            nodes_visited[min_index] =  np.inf #indicate we have visited the node
        
        return distance_to_nodes,paths #return the distance to all the nodes


    #find the distance to travel to all nodes from all nodes
    def find_distance_to_all(self):
        num_nodes = len(self.node_names)
        distance_arrays = [] #list to store distance arrays from a particular node
        #generate the distance arrays from each node
        for i in range(num_nodes):
            distance_arrays.append(self.find_distance_dijistraka(self.node_names[i]))
        #and merge them into a numpy array
        
        self.distance_to_all = np.stack(distance_arrays)
        return self.distance_to_all
    
    #as above, but also store the routes taken
    def find_distance_to_all_path(self):
        num_nodes = len(self.node_names)
        distance_arrays = [] #list to store distance arrays from a particular node
        path_arrays = [] #list to store path lists from each node
        #generate the distance arrays from each node
        for i in range(num_nodes):
            new_distance,new_paths = (self.find_distance_dijistraka_path(self.node_names[i]))
            distance_arrays.append(new_distance)
            path_arrays.append(new_paths)

        #and merge them into a numpy array
        
        self.distance_to_all = np.stack(distance_arrays)
        self.paths_to_all = path_arrays
        return self.distance_to_all
    
    #find the expected traffic along each edge in each direction
    def find_expected_edge_traffic(self):
        #create the array 
        num_edges = len(self.edge_names)
        self.edge_traffic = np.zeros(num_edges)
        #go through all the shortest path between node_pairs
        for outer_index,paths in enumerate(self.paths_to_all):
            for inner_index,path in enumerate(paths):
                #extract the amount of traffic along the path between the selected nodes
                node_to_node_traffic = self.origin_destination_trips[outer_index,inner_index]
                for edge_name in path:#go through all the edge names in the path
                    edge_index = self.get_edge_index(edge_name) #find the index of the edge we are pathing through
                    self.edge_traffic[edge_index] = self.edge_traffic[edge_index] + node_to_node_traffic #add the traffic from the new edge
        
    #create a matrix of travel demand between each node using the gravity model
    def create_origin_destination_matrix(self):
        num_passengers = np.array(self.node_passengers)
        #use gravity model with 1D distance dropoff and 5 minute flat distance (these fudge factors are decided because they produce good results)
        self.origin_destination_trips = gravity_assignment(starts=num_passengers,stops=num_passengers,distances=self.distance_to_all,distance_exponent=1,flat_distance=5,verbose=self.verbose) 
        return self.origin_destination_trips

    #get the index of a node name in the list of nodes
    def get_node_index(self,node_name):
        #try and find the starting node in the list of all nodes
        try:
            index = self.node_names.index(node_name)
            return index
        except ValueError:
            #handle case where starting name not in list of names
            warnings.warn('node_name  ', node_name, 'is not in the list of node names in this network')
            return -1 #return -1 to indicate error

    #get the index of an edge name in the list of edges
    def get_edge_index(self,edge_name):
        #try and find the starting node in the list of all nodes
        try:
            index = self.edge_names.index(edge_name)
            return index
        except ValueError:
            #handle case where starting name not in list of names
            warnings.warn('edge_name  ', edge_name, 'is not in the list of edge names in this network')
            return -1 #return -1 to indicate error

    #get the time taken to traverse a node
    def get_edge_time(self,edge_name):
        index = self.get_edge_index(edge_name)
        time_taken = self.edges[index].provide_travel_time()
        return time_taken

    #get the traffic through a node
    def get_edge_traffic(self,edge_name):
        index = self.get_edge_index(edge_name)
        traffic = self.edge_traffic[index]
        return traffic

    #provide a breakdown of where passengers starting at a particular node are going
    def test_origin_destination_matrix(self,start_node_name):
        #try and find the starting node in the list of all nodes
        start_index = get_node_index(self,start_node_name)
        if start_index==-1:
            return False
        #if there was not an error, continue
        num_nodes = len(self.node_names)
        trips_from_start = self.origin_destination_trips[start_index:start_index+1,:][0]
        print(trips_from_start)
        num_trips = np.sum(trips_from_start)
        percent_trips = trips_from_start/num_trips
        print('from ',start_node_name,' ',num_trips, ' passengers travel')
        for i in range(num_nodes):
            with np.printoptions(precision=2,suppress=True):
                print(' to ',self.node_names[i],' ', trips_from_start[i], ' passengers which is', percent_trips[i]*100 ,' %')
    
    def test_origin_destination_matrix_all(self):
        num_nodes = len(self.node_names)
        stops = np.sum(self.origin_destination_trips,0)
        total_stops = np.sum(stops)
        percent_trips = stops/total_stops
        print('across all nodes, passengers travel')
        for i in range(num_nodes):
            with np.printoptions(precision=2,suppress=True):
                print(' to ',self.node_names[i],' ', stops[i], ' passengers which is', percent_trips[i]*100 ,' %')
            #print(' to ',self.node_names[i],' ', f"{stops[i]:.2f}", ' passengers which is', f"{percent_trips[i]*100:.2f}" ,' %')
        for i in range(num_nodes):
            self.test_origin_destination_matrix(self.node_names[i])

    #testing functionality
    def test_nodes(self):
        for i  in range(len(self.nodes)):
            self.nodes[i].test_node()

    def test_edges(self):
        for i in range(len(self.edges)):
            self.edges[i].test_edge()

    def test_dijistraka(self,start_node):
        print('from ', start_node, ' time to reach is ')
        best_distance_to_nodes = self.find_distance_dijistraka(start_node)
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            print(self.node_names[i], ' time ',best_distance_to_nodes[i])
    
    def test_schedules(self):
        num_schedules = len(self.schedule_names)
        #test all the schedules in the network
        for i in range(num_schedules):
            self.schedules[i].test_schedule()
        
    def test_verbose(self):
        print('verbosity = ',self.verbose)
        if self.verbose==0:
            print('verbosity is 0')
        if self.verbose>=1:
            print('verbosity is greater or equal to 1')
        if self.verbose>=2:
            print('verbosity is greater or equal to 2')


#assign trips between origin destination pairs using the gravity model
#starts/stops are number of passengers starting/stopping at particular nodes (1D Numpy array)
#distances is amount of time taken (in ideal world) to travel between each pair of nodes (2D Numpy array)
#length of all these arrays MUST be equal
#distance exponent is how much cost scales with distance
#flat distance is default amount of distance applied on top to all trips
#iterations is how many iterations to converge
#as yet unsure how well this handles 
def gravity_assignment(starts,stops,distances,distance_exponent,flat_distance,verbose=1,required_accuracy=0.001,max_iterations=100):
    distances = (distances+flat_distance)**distance_exponent #calculate distance after transforms
    num_nodes = len(starts)
    destination_importance_factors = np.ones(num_nodes)#correction factor used to ensure convergence of number of trips to a node with recorded number of stops at that node
    list_trips = [] #list to store the number of trips pending conversion to a numpy array
    for j in range(num_nodes):#go through all the starting nodes
        this_node_starts = starts[j]#record the number of trips starting at a node
        trip_importance = np.zeros(num_nodes)#importance of trips to each node from this node
        for k in range(num_nodes):#go through each destination from all nodes
            if k==j:#don't evaluate number of trips from a node to itself
                continue
            else:
                distance_between = (distances[k,j]+distances[j,k]) #use the round-trip distance, as most passengers intend to return to their origin so this is what determines expected cost of the trip

                trip_importance[k] = ((destination_importance_factors[k]*stops[k])/distance_between)
        
        num_trips = (trip_importance/np.sum(trip_importance))*this_node_starts #calculate the number of trips from this node to all other nodes
        list_trips.append(num_trips)
        
    calc_trips = np.stack(list_trips)#merge the number of trips from each node to each destination into a numpy array
    iter = 0
    while True:
        calc_stops = np.sum(calc_trips,0)
        calc_starts = np.sum(calc_trips,1)
        stop_correction_factor = stops/calc_stops
        start_correction_factor = starts/calc_starts
        abs_start_error = np.abs(start_correction_factor-1)
        abs_stop_error = np.abs(stop_correction_factor-1)
        if (max(abs_stop_error)<required_accuracy) and (max(abs_start_error)<required_accuracy):
            if verbose>=1:
                print("desired accuracy achieved after ", iter, " iterations")
            break
        elif iter>=max_iterations:
            if verbose>=1:
                print("failed to converge after ",max_iterations," iterations")
            break
        else:
            iter = iter+1    
        #now apply the stop correction factor to traffic
        for j in range(num_nodes):#go through starting node
            for k in range(num_nodes):#go through destination node
                calc_trips[j,k] = calc_trips[j,k]*stop_correction_factor[k] #multiply the number of trips going to each destination node by the stop correction factor of that destination
        calc_stops = np.sum(calc_trips,0)
        calc_starts = np.sum(calc_trips,1)
        start_correction_factor = starts/calc_starts
        #print('start correction factors ',start_correction_factor)
        #now apply the start correction factor to traffic
        for j in range(num_nodes):#go through starting node
            for k in range(num_nodes):#go through destination node
                calc_trips[j,k] = calc_trips[j,k]*start_correction_factor[j]  #multiply the number of trips from each origin by the start correction factor of that origin

        
        #print('after start calibration')

    if verbose>=2:
        print('at the end') 
        calc_stops = np.sum(calc_trips,0)
        print('calc stops ',calc_stops)
        stop_error = (calc_stops/stops)
        print('stop correctness ',stop_error)
        calc_starts = np.sum(calc_trips,1)
        print('calc starts ',calc_starts)
        start_error = calc_starts/starts
        print('start correctness ',start_error)
        print('biggest errors rates are')
        abs_start_error = np.abs(start_error-1)
        abs_stop_error = np.abs(stop_error-1)
        print('for start, max error ', np.max(abs_start_error),' mean error ',np.mean(abs_start_error))
        print('for stop, max error ', np.max(abs_stop_error),' mean error ',np.mean(abs_stop_error))
        print('end testing')
    return calc_trips


#extract latitude and longitude from a string of coordinates (in the format provided by google maps)
def extract_coordinates(coordinates):
    #extract the latitude and longitude strings
    latitude = ''
    longitude = ''
    extracting_longitude = False
    i = 0
    while i < len(coordinates):
        if coordinates[i] == ',':
            extracting_longitude = True
            i = i + 2
        else:
            if extracting_longitude:
                longitude += coordinates[i]
            else:
                latitude += coordinates[i]
            i = i + 1
        
    return float(latitude),float(longitude)

#extract a list of nodes in a schedule from a text string
def extract_schedule_list_txt(schedule_string):
    new_node = []
    nodes = []
    for letter in schedule_string:
        if letter==',': #move onto the next node when the delimiter is reached
            nodes.append("".join(new_node))#append the node name to the list of nodes
            new_node = [] #reset the node
        else:
            new_node.append(letter) #append the letter to the node name
    #also add on the final node (after the last comma)
    nodes.append("".join(new_node))
    return nodes

#return true if random generated number is less than provided chance 
#input chance is equal to the chance of the output being true
def random_true(chance):
    random_number = rand.random() #random number between 0 and 1
    if random_number<=chance:
        return True
    else:
        return False
