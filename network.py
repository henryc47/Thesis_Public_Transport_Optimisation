#network.py
#stores information about the physical network

import pandas as pd #for importing data from csv files


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
        print('foo you')
        #where we will store edges and nodes
        self.edges = [] #list of edges 
        self.nodes = [] #list of nodes
        self.edge_names = [] #list of generated edge names
        #extract the raw data
        nodes_csv = pd.read_csv(nodes_file_path)
        edges_csv = pd.read_csv(edges_file_path)
        #now extract node data
        self.node_names = nodes_csv["Name"]
        self.node_passengers = nodes_csv["Daily_Passengers"]
        #and let's create the nodes
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes.append(Node(self.node_names[i]))
        #extract edge data
        self.edge_starts = edges_csv["Start"]
        self.edge_ends = edges_csv["End"]
        self.edge_times = edges_csv["Time"]
        self.edge_bidirectional = edges_csv["Bidirectional"]
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

    #testing functionality
    def test_nodes(self):
        for i  in range(len(self.nodes)):
            self.nodes[i].test_node()

    def test_edges(self):
        for i in range(len(self.edges)):
            self.edges[i].test_edge()





    

