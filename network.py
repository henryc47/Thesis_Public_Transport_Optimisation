#network.py
#stores information about the physical network

import pandas as pd #for importing data from csv files
import warnings #for warnings
import numpy as np #for large scale mathematical operations

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
    def __init__(self,name):
        self.name = name
        self.edge_names = []#list of all edges starting at this node
        self.edge_destinations = []#and the destination of each node
        self.edge_times = []#matching list of travel time of each respective edge
        
    
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
    
    def test_node(self):
        print('from node ',self.name, ' edges are')
        for i in range(len(self.edge_names)):
            print(self.edge_names[i], ' goes too ',self.edge_destinations[i],' taking ',self.edge_times[i])


class Network:
    #initalise the physical network
    def __init__(self,nodes_file_path,edges_file_path):
        #where we will store edges and nodes
        self.edges = [] #list of edges 
        self.nodes = [] #list of nodes
        self.edge_names = [] #list of generated edge names
        #extract the raw data
        nodes_csv = pd.read_csv(nodes_file_path,thousands=r',')
        edges_csv = pd.read_csv(edges_file_path,thousands=r',')
        #now extract node data
        self.node_names = nodes_csv["Name"].to_list()
        self.node_passengers = nodes_csv["Daily_Passengers"].to_list()
        #and let's create the nodes
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes.append(Node(self.node_names[i]))
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


    #add an edge between specified start and end node            
    def add_edge(self,start_node,end_node,travel_time):
        name = start_node + ' to ' + end_node
        while name in self.edge_names:#prevent duplicate names
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

    #create a matrix of travel demand between each node using the gravity model
    def create_origin_destination_matrix(self):
        num_passengers = np.array(self.node_passengers)
        self.origin_destination_trips = gravity_assignment(num_passengers,num_passengers,self.distance_to_all,1,5) 
        return self.origin_destination_trips



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
    


#assign trips between origin destination pairs using the gravity model
#starts/stops are number of passengers starting/stopping at particular nodes (1D Numpy array)
#distances is amount of time taken (in ideal world) to travel between each pair of nodes (2D Numpy array)
#length of all these arrays MUST be equal
#distance exponent is how much cost scales with distance
#flat distance is default amount of distance applied on top to all trips
#iterations is how many iterations to converge
#as yet unsure how well this handles 
def gravity_assignment(starts,stops,distances,distance_exponent,flat_distance,verbose=True,required_accuracy=0.001,max_iterations=100):
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
            if verbose:
                print("desired accuracy achieved after ", iter, " iterations")
            break
        elif iter>=max_iterations:
            if verbose:
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

    if verbose:
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




            




    

