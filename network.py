#network.py
#stores information about the physical network

import warnings #for warnings
import numpy as np #for large scale mathematical operations
import time as time #for benchmarking
import schedule as schedule
import vehicle as vehicle
import copy as copy #for shallow-copying schedules
import random as rand
rand.seed(30699) #consistent seed to ensure consistent results
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
    def __init__(self,name,coordinates,id,network):
        self.name = name
        self.edge_names = []#list of all edges starting at this node
        self.edge_destinations = []#and the destination of each node
        self.edge_times = []#matching list of travel time of each respective edge
        (self.latitude,self.longitude) = extract_coordinates(coordinates)
        self.agents = [] #list of all agents at this stations
        self.schedule_names = [] #list of schedules stopping at this station
        self.schedule_times = [] #times at which vehicles arrive at this node
        self.nodes_after = [] #list of nodes after this node on a schedule
        self.node_times_after = [] #time to reach nodes after the node on the schedule
        self.id = id #id of the node
        self.network = network #network we belong too
        #has the next vehicle of each schedule arriving at the node changed since we lasted found paths
        self.next_vehicle_changed = True #starts at true so that we can use the reset variables process to initialise our variables
        self.num_agents = 0

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
        self.num_agents = self.num_agents + agent.number_passengers #the number of passengers has increased

    #remove agent from the station
    def remove_agent(self,id):
        removed_agent = self.agents.pop(id)
        self.num_agents = self.num_agents - removed_agent.number_passengers #the number of passengers has decreased
        return removed_agent


    #count the number of agents at the station
    def count_agents(self):
        #num_agents = 0
        #for agent in self.agents:
        #    num_agents = num_agents + agent.number_passengers
        return self.num_agents 


    #add a schedule which stops at that station
    def add_stopping_schedule(self,schedule_name,schedule_times,node_offset,nodes_after,node_times_after):
        self.schedule_names.append(schedule_name)
        schedule_times_mod = [schedule_time+node_offset for schedule_time in schedule_times] #offset schedule times by time to reach the node
        self.schedule_times.append(schedule_times_mod)
        self.nodes_after.append(nodes_after)
        self.node_times_after.append(node_times_after)

    #calculate the time till the next service of each schedule arrives at a node
    def time_till_next_vehicles(self,current_time):
        num_schedules = len(self.schedule_names)
        next_service_times = []
        for i in range(num_schedules): #go through all the schedules at a node
            #calculate service data for each particular schedule
            schedule_times = self.schedule_times[i]
            num_future_services = len(schedule_times)
            j = 0 #which service are we looking at
            next_service_time = np.inf #default next service time is infinity
            while j<num_future_services:
                service_time = schedule_times[j]
                if service_time>=current_time:
                    next_service_time = service_time
                    break #we have found a service after (or equal) to the present time, so need to search further
                j = j + 1 #look at the next service
            next_service_times.append(next_service_time)

        return next_service_times            

    #remove vehicles which have already arrived at the node
    def remove_arrived_vehicles(self,current_time):
        num_schedules = len(self.schedule_names)
        for i in range(num_schedules): #go through all the schedules at a node
            while len(self.schedule_times[i])>0:
                if self.schedule_times[i][0]<=current_time: #if this service is in the past
                    self.schedule_times[i].pop(0) #remove it from the list of services
                else:
                    break #as services of a schedule are in order, we only need to evaluate till we find a service in the future
    
    #reset the internal info required for pathfinding 
    def reset_pathfinding_info(self):
        self.num_nodes_in_network = len(self.network.node_names)
        self.distance_to_nodes = np.zeros(self.num_nodes_in_network) + np.inf #initial distance to reach all other nodes will be infinite
        self.evaluated_nodes = np.zeros(self.num_nodes_in_network)  #when a node is evaluated the value in this matrix is set to infinite, ensuring that node is never evaluated again
        self.evaluated_nodes_tf = np.zeros(self.num_nodes_in_network) #as above, but evaluated nodes are set to 1
        self.distance_to_nodes[self.id] = 0 #initial distance to reach the starting node is 0
        #create an array to store the paths to all the other nodes       
        self.path_to_nodes = [[] for _ in range(self.num_nodes_in_network)] #create an empty nested list of the required length to store paths to nodes

    def check_evaluated_destinations(self,destination_nodes):
        num_evaluated_destinations = np.sum(np.logical_and(self.evaluated_nodes,destination_nodes)) 
        return num_evaluated_destinations

    #find a path from this node to all nodes where num_passengers_to_node is greater than 0
    def find_paths(self,num_passengers_to_node,start_time):
        if self.next_vehicle_changed == True:
            self.reset_pathfinding_info() #restart the pathfinding process if the next vehicle arriving at this node has changed
            self.next_vehicle_changed = False #compared to the present, next vehicle has not changed
         #get info about vehicles arriving at the starting node
        start_next_service_times,start_nodes_after,start_node_times_after,start_schedule_names = self.provide_next_services(data_time=start_time,start=True)
        destination_nodes = num_passengers_to_node>0 #determine which nodes we need to calculate paths too (I.E those where passengers are actually going)
        num_destinations = np.sum(destination_nodes) #number of destinations we are trying to reach     
        num_evaluated_destinations = self.check_evaluated_destinations(destination_nodes) #get number of destinations already evaluated
        while True: #loop till we meet an exit conditionx
            expected_distance_to_nodes = self.distance_to_nodes + self.evaluated_nodes #set the distance to reach an already evaluated node to be infinite so we don't choose it as the minimal node
            min_index = np.argmin(expected_distance_to_nodes) #get the index of the node with the lowest expected travel time, evaluate this next
            minimum_distance = expected_distance_to_nodes[min_index] #extract the minimum distance from the starting node
            if minimum_distance == np.inf:
                break #break out of the loop, we have explored all the network we can reach      
            elif num_evaluated_destinations==num_destinations:
                break #break out of the loop, we have already found paths to all the destinations we wish to reach
            else:
                #otherwise, explore paths from the minimal node
                current_time = minimum_distance +  start_time#time at which we reach the node currently being evaluated
                if min_index==self.id: #if at starting node, use precalcuated data about services
                    #use precalculated data from the starting node
                    next_service_times = start_next_service_times
                    nodes_after = start_nodes_after
                    times_after = start_node_times_after
                    schedule_names = start_schedule_names
                else: #otherwise, extract data about the evaluation node at the evaluation time
                    next_service_times,nodes_after,times_after,schedule_names = self.network.nodes[min_index].provide_next_services(start=False,data_time=current_time)


            #now it's time to calculate the path to other nodes
            num_schedules = len(next_service_times)
            for i in range(num_schedules):
                #extract nodes and times after for this specific route            
                next_service_time = next_service_times[i]
                next_service_name = schedule_names[i]
                route_nodes_after = nodes_after[i]
                route_times_after = times_after[i]
                for j,node in enumerate(route_nodes_after):
                    node_index = node.id
                    distance_to_current_node_old_path = self.distance_to_nodes[node_index] #what is the current shortest path to the node we are looking at
                    distance_to_current_node_new_path = minimum_distance + (next_service_time-current_time) + route_times_after[j] #how long to reach next node through evaluation node
                    if distance_to_current_node_new_path<distance_to_current_node_old_path: #we have a better path
                        self.distance_to_nodes[node_index] = distance_to_current_node_new_path
                        route_to_old_node = self.path_to_nodes[min_index] #extract the path to the evaluation node
                        route_to_new_node = copy.copy(route_to_old_node) #path to the next node is path to the evaluation node + new step
                        route_to_new_node.append(next_service_name) #store the next service we need to catch
                        route_to_new_node.append(node.name) #and when we need to get off that service
                        self.path_to_nodes[node_index] = route_to_new_node #store this in the list of all paths
            
            self.evaluated_nodes[min_index] = np.inf #mark the node as evaluated, it will not be evaluated again
            self.evaluated_nodes_tf[min_index] = True #as above
            if destination_nodes[min_index]==True:
                num_evaluated_destinations = num_evaluated_destinations+1

        #once we have found the paths to all nodes, return the paths and number of passengers
        #note we return the number of passengers going to an unreachable station as zero, but we return the number of passengers who failed to reach their destination as well
        num_nodes = len(self.network.nodes)
        num_unreachable_passengers = 0 #keep track of the number of passengers who fail to reach their destination
        for i in range(num_nodes):
            if self.distance_to_nodes[i]==np.inf: #if the passenger cannot reach this node
                num_unreachable_passengers = num_unreachable_passengers + num_passengers_to_node[i] #add them to the total of failed passengers
                num_passengers_to_node[i] = 0 #do not create any passengers trying to reach this node
    
        return self.path_to_nodes,num_passengers_to_node,num_unreachable_passengers
        

    #as previous function, but store the result in a internal variable
    #this is useful for operations at the current time
    def self_time_till_next_vehicles(self,current_time):
        self.next_service_times = self.time_till_next_vehicles(current_time)

    #provide the next service
    def provide_next_services(self,data_time=0,start=False):
        if start==True:
            #we are providing service info at the same time as we are creating a passenger, so use precalculated times
            next_service_times = self.next_service_times
        else:
            #otherwise calculate the time dynamically
            next_service_times = self.time_till_next_vehicles(data_time)
        #in either case, we must return the corresponding following nodes and their time to reach
        return next_service_times,self.nodes_after,self.node_times_after,self.schedule_names

    def test_node(self):
        print('from node ',self.name, ' edges are')
        for i in range(len(self.edge_names)):
            print(self.edge_names[i], ' goes too ',self.edge_destinations[i],' taking ',self.edge_times[i])
        print('node latitude is ',self.latitude, ' longitude is ',self.longitude)
    

#network class, represents the overall structure of the transport network
class Network:
    #initalise the physical network
    #note, this assumes that passengers are evenly distributed through the day
    def __init__(self,nodes_csv,edges_csv,schedule_csv,parameters_csv,eval_csv,scenario_csv,verbose=1,segment_csv='',schedule_type='simple',optimiser='hardcoded'):
        time1 = time.time()
        print('optimiser ',optimiser)
        self.verbose = verbose #import verbosity
        #where we will store edges and nodes
        self.edges = [] #list of edges 
        self.nodes = [] #list of nodes
        self.edge_names = [] #list of generated edge names
        self.optimiser = optimiser #optimisers we can use, options are "hardcoded", the set frequency from the schedule and "henryconvex", my own custom convex optimisation function 
        #extract the raw data
        #now extract node data
        self.node_names = nodes_csv["Name"].to_list()
        node_positions = nodes_csv["Location"].to_list() 
        #and let's create the nodes
        num_nodes = len(self.node_names)
        for i in range(num_nodes):
            self.nodes.append(Node(self.node_names[i],node_positions[i],i,self)) #nodes id is it's position in the array

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

        #extract parameter data
        self.vehicle_max_seated = parameters_csv["Vehicle Max Seated"].to_list()[0] #maximum number who can sit inside a vehicle
        self.vehicle_max_standing = parameters_csv["Vehicle Max Standing"].to_list()[0] #maximum number who can fit inside a vehicle seated + standing     
        self.traffic_time_gap = parameters_csv["Traffic Time Gap"].to_list()[0] #gap in timesteps between traffic volume updates
        self.traffic_multiplier = scenario_csv["Traffic Multiplier"].to_list() #traffic multiplier for each time gap of operation
        self.stop_simulation_time = (len(self.traffic_multiplier)-1)*self.traffic_time_gap #time when the simulation should end
        self.vehicle_cost = eval_csv["Vehicle Cost"].to_list()[0] #marginal cost of running a vehicle, $/hour
        self.agent_cost_seated = eval_csv["Agent Cost Seated"].to_list()[0] #marginal value of agents time, $/seated
        self.agent_cost_standing = eval_csv["Agent Cost Standing"].to_list()[0] #marginal value of agents time, higher because standing is unpleasant $/hr
        self.agent_cost_waiting = eval_csv["Agent Cost Waiting"].to_list()[0] #marginal value of agents time, higher because waiting is unpleasant $/hr
        self.unfinished_penalty = eval_csv["Unfinished Penalty"].to_list()[0] #penalty if passengers are unable to reach their destination, based roughly on cost of late night taxi ride
        self.passenger_time_multiplier = float(0) #multiplier on how many passengers are generated per hour, converted to a float as it refuses to become an integer later
        #allocate passengers 
        self.node_passengers = (nodes_csv["Daily Passengers"]).to_list()#passengers per day for each station
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
        #in simple scheduling, schedules are just lists of nodes
        #in complex scheduling, schedules are made up of segments which are lists of nodes
        #note complex schedules are converted to the same immediate format as simple schedules
        self.schedule_csv = schedule_csv
        self.schedule_type = schedule_type #simple schedule type
        self.segment_csv = segment_csv #segments used in the complex schedule
        self.parameters_csv = parameters_csv #segment used 
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
        self.num_failed_agents = 0 #number of agents created who could not find a path and hence were immediately unmade
        self.num_successful_agents = 0 #number of agents who were created and found a path to their destination
        time1 = time.time()
        self.create_schedules() #create the schedules
        if self.optimiser=='hardcoded':
            pass #just use the default schedule gaps from the imported schedule
        elif self.optimiser=='henry_convex':
            self.henry_convex_optimiser() #use this optimiser to generate the schedule gaps
        self.create_dispatch_schedule()
        self.determine_which_nodes_have_schedule() #determine which nodes have which schedules
        time2 = time.time()
        if self.verbose>=1:
            print('time to extract and generate schedules', time2-time1, 'seconds')

    #implemention of my own custom optimisation algorithm
    #which determines the optimal wait time between services based on minimising total service cost + waiting cost
    def henry_convex_optimiser(self):
        schedule_costs = []
        num_nodes = len(self.node_names)
        num_schedules_each_node = np.zeros(num_nodes) #number of schedules at each node
        for schedule in self.schedules:
            length = schedule.get_length()
            cost = (length/60)*self.vehicle_cost #determine the cost of providing a vehicle service
            schedule_costs.append(cost)
            node_names = schedule.node_names #get the name of all the nodes
            for name in node_names:
                node_index = self.get_node_index(name)
                num_schedules_each_node[node_index] = num_schedules_each_node[node_index] + 1 #one more schedule is present at this node

        #now determine the number of passengers starting at each schedule (nodes with multiple schedules have reduced weight)
        for i,schedule in enumerate(self.schedules):
            weighted_passengers = 0
            node_names = schedule.node_names #get the name of all the node
            for name in node_names:
                node_index = self.get_node_index(name)
                node_passengers = self.node_passengers[node_index]*np.mean(self.traffic_multiplier)
                weighted_passengers = weighted_passengers + (node_passengers/num_schedules_each_node[node_index])
            #now use the derived equation (see thesis) to determine the optimal frequency
            optimal_wait_time = np.sqrt((2*schedule_costs[i])/(weighted_passengers*self.agent_cost_waiting))
            optimal_wait_time = int(optimal_wait_time*60) #convert to integers minutes
            print('for schedule ',schedule.name,' optimal wait time is ',optimal_wait_time,' mins') #DEBUG
            self.schedule_gaps[i] = optimal_wait_time


           
        #having determined the length and weighted number of passengers in each schedule, let's calculate the optimal frequency 
    
    

    #update the passenger time multiplier, sets the number of passengers generated to vary throughout the day based on the scenario    
    def update_passenger_time_multiplier(self):
        time_period = int(self.time/self.traffic_time_gap)
        time_period_start = time_period*self.traffic_time_gap  
        if self.time<self.stop_simulation_time:
            end_time_multiplier = self.traffic_multiplier[time_period+1]
            start_time_multiplier = self.traffic_multiplier[time_period]
        else:
            end_time_multiplier = 0
            start_time_multiplier = 0
        
        time_from_start = self.time-time_period_start
        self.passenger_time_multiplier = start_time_multiplier*(1-time_from_start/self.traffic_time_gap) + end_time_multiplier*(time_from_start/self.traffic_time_gap)
        self.passenger_time_multiplier = self.passenger_time_multiplier

    #create a new vehicle and add it to the network
    def create_vehicle(self,schedule):
        vehicle_name = str(self.time) + " " + schedule.provide_name() #calculate the vehicles name
        #produce a shallow copy of the schedule to provide to the vehicle, note we use a class defined implemention of shallow-copying
        copy_schedule = copy.copy(schedule) #copy the schedule object, but maintain keep references to node/edges identical
        if self.verbose>=1:
            print('schedule destinations ',copy_schedule.nodes)
        junk,start_node = copy_schedule.provide_next_destination() #extract the first destination of the schedule
        start_node_index = start_node.id
        self.num_vehicles_started_here[start_node_index] += 1 #record that a vehicle started at a particular node
        self.vehicle_names.append(vehicle_name) #add the vehicles name to the list
        self.vehicles.append(vehicle.Vehicle(copy_schedule,self.time,vehicle_name,seated_capacity=self.vehicle_max_seated,standing_capacity=self.vehicle_max_standing)) #create the vehicle and add it to the list
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
                    print('a vehicle ', vehicle.name, ' has reached the end of its path at time ', self.time)
                del self.vehicles[count] #remove the vehicle when it has reached it's destination

    #create vehicles at nodes as needed by the schedule
    def assign_vehicles_schedule(self):
        #run through the all the schedules in the dispatch list
        num_schedules = len(self.schedules)
        for i in range(num_schedules):
            if len(self.dispatch_schedule2[i])>0: #if there are still schedules left to be dispatched
                if self.time == self.dispatch_schedule2[i][0]: #a vehicle of this schedule is required to be created a the current time
                    self.create_vehicle(self.schedules[i])
                    self.dispatch_schedule2[i].pop(0) #remove the first element of the list as the vehicle has been created at the required time

    #create passengers with pathfinding done at the node level rather than the agent level
    def create_all_passengers_pathfinding(self):
        num_nodes = len(self.node_names)
        for i in range(num_nodes): #go through all the nodes we are starting from
            start_node = self.nodes[i] #extract a reference to the starting node
            num_passengers_to_node = np.zeros(num_nodes)
            #calculate the number of passengers going to each node
            for j in range(num_nodes):
                end_node = self.nodes[j] #extract a reference to that node
                num_passengers_pair = self.origin_destination_trips[i,j] #extract number of passengers going between these node pairs
                num_passengers_per_min = (num_passengers_pair/60)*self.passenger_time_multiplier #we create passengers every minute, but statistics are per hour
                #create the required number of passengers
                int_num_passengers = int(num_passengers_per_min) #rounded-down number of passengers to create
                chance_additional_passenger = num_passengers_per_min-int_num_passengers #chance of an additional passenger being created from the remainder
                num_passengers_to_node[j] = int_num_passengers + random_true(chance_additional_passenger) #get the final number of passengers to be created
            # now determine the path to all the nodes, the number of passengers travelling to each node and the number of passengers which failed to reach their destination
            path_to_nodes,num_passengers_created,num_unreachable_passengers = start_node.find_paths(num_passengers_to_node,self.time)
            self.num_successful_agents = self.num_successful_agents + np.sum(num_passengers_created) #record total successful pathfinding agents
            self.num_failed_agents = self.num_failed_agents + num_unreachable_passengers  #record total failed pathfinding agents

            # now lets create the actual passengers
            for j in range(num_nodes): #go through all the nodes we are ending up at
                num_passengers = num_passengers_created[j]
                if num_passengers>0:
                    end_node = self.nodes[j]
                    path = copy.deepcopy(path_to_nodes[j])
                    new_agent = a.Agent(start_node,end_node,self.agent_id_counter,self.time,self,num_passengers,path) #create the new passenger
                    self.agents.append(new_agent) #create the new passengers and add to the list
                    self.agent_ids.append(self.agent_id_counter) #store the id of the newly created passenger
                    self.agent_id_counter = self.agent_id_counter + 1 #increment the id counter
                    #assign the passenger to their starting station
                    start_node.add_agent(new_agent)
            
    #create new passengers at stations, going between each node pair
    def create_all_passengers(self):
        num_nodes = len(self.node_names)
        for i in range(num_nodes): #go through all the nodes we are starting from
            start_node = self.nodes[i] #extract a reference to that node
            for j in range(num_nodes): #go through all the nodes we are ending up at
                end_node = self.nodes[j] #extract a reference to that node
                num_passengers_pair = self.origin_destination_trips[i,j] #extract number of passengers going between these node pairs
                num_passengers_per_min = (num_passengers_pair/60)*self.passenger_time_multipler #we create passengers every minute, but statistics are per day
                self.create_passengers_pair(start_node,end_node,num_passengers_per_min)

    #create the passengers for a specific pair of nodes and edges
    def create_passengers_pair(self,start_node,end_node,num_passengers_per_min):
        int_num_passengers = int(num_passengers_per_min) #rounded-down number of passengers to create
        chance_additional_passenger = num_passengers_per_min-int_num_passengers #chance of an additional passenger being created from the remainder
        num_passengers = int_num_passengers + random_true(chance_additional_passenger) #get the final number of passengers to be created
        #now create the actual passengers at the stations
        if num_passengers>0:
            self.create_passenger(start_node,end_node,num_passengers)


    #create a single passenger
    def create_passenger(self,start_node,end_node,num_passengers):
        #create the passenger
        new_agent = a.Agent(start_node,end_node,self.agent_id_counter,self.time,self,num_passengers)
        if new_agent.found_path == True:
            #create the new passenger if they can find a path to their destination
            self.agents.append(new_agent) #create the new passengers and add to the list
            self.agent_ids.append(self.agent_id_counter) #store the id of the newly created passenger
            self.agent_id_counter = self.agent_id_counter + 1 #increment the id counter
            #assign the passenger to their starting station
            start_node.add_agent(new_agent)
            self.num_successful_agents = self.num_successful_agents + num_passengers
        else:
            #if we cannot find a path to their destination, uncreate the agent
            self.num_failed_agents = self.num_failed_agents + num_passengers

            

    #update when the next vehicle in each schedule will arrive at each node
    def update_nodes_next_vehicle(self):
        for node in self.nodes:
            #determine when the next service of each schedule will arrive
            node.self_time_till_next_vehicles(self.time)
            #remove services which have already arrived
            node.remove_arrived_vehicles(self.time)


    #passengers alight from vehicles which have stopped
    def alight_passengers(self):
        #loop through all vehicles
        for i,vehicle in enumerate(self.vehicles):
             #if a vehicle is at stop, passengers may alight
            if vehicle.state == 'at_stop':
                stop_node = vehicle.previous_stop #where did the vehicle stop
                #stop_node.next_vehicle_changed = True #the next vehicle stopping at this node will now be different (I don't think this is needed for alighting)
                schedule_name = vehicle.schedule_name
                copy_vehicle_agents = copy.copy(vehicle.agents) #create a shallow copy of the list of agents at the vehicle (agents will be the same, but references will be independent
                num_removed = 0 #keep of number removed so we can pop the right agents
                #go through all the agents on the vehicle
                for j,agent in enumerate(copy_vehicle_agents):
                    alight_status = agent.alight(stop_node.name)
                    if agent.done==True: #we will not waste our time processing agents that have reached their destination
                        pass
                    else:
                        if alight_status == 1: #agent is alighting
                            agent = vehicle.alight_agent(j-num_removed) #remove them from the list of agents at the vehicle
                           # print('type ',type(agent),' name',agent.name) #DEBUG
                            num_removed = num_removed + 1
                            stop_node.add_agent(agent) #and add them to list of agents at the station
                        elif alight_status == 2: #agent is alighting at their destination
                            agent = vehicle.alight_agent(j-num_removed) #remove them from the list of agents at the vehicle
                          #  print('type ',type(agent),' name',agent.name) #DEBUG
                            num_removed = num_removed + 1
                            agent.done = True  #mark the agent as having achieved their goals
                        elif alight_status == 0: #agent is not alighting
                            pass

    #passengers board vehicles which have stopped
    def board_passengers(self):
         #loop through all vehicles
        for i,vehicle in enumerate(self.vehicles):
            if vehicle.state == 'at_stop':
                #if a vehicle is at stop, we need to board passengers
                stop_node = vehicle.previous_stop #where did the vehicle stop
                stop_node.next_vehicle_changed = True #the next vehicle stopping at this node will now be different
                schedule_name = vehicle.schedule_name
                copy_stop_node_agents = copy.copy(stop_node.agents) #create a shallow copy of the list of agents at the node (agents will be the same, but references will be independent)
                num_removed = 0 #keep of number removed so we can pop the right agent
                for j,agent in enumerate(copy_stop_node_agents): #go through all the agents where the vehicle stopped
                    original_path = copy.deepcopy(agent.destination_path)
                    will_board = agent.board(schedule_name)
                    if will_board == True:
                        #if the agent is getting on the vehicles
                        vehicle_capacity = vehicle.get_capacity()
                        agent_passengers = agent.number_passengers
                        if agent_passengers<=vehicle_capacity:
                            agent = stop_node.remove_agent(j-num_removed) #remove them from the list of agents at the node, making sure to account for the change in the array size due to removed agents
                            vehicle.board_agent(agent) #have the agents board the vehicle
                            num_removed = num_removed + 1 #we have removed another agent
                        elif vehicle_capacity==0:
                            agent.destination_path = original_path
                        else:
                            leftover_passengers = agent_passengers-vehicle_capacity
                            agent = stop_node.agents[j-num_removed]
                            copy_agent = a.Agent(agent.start_node,agent.destination_node,agent.id,agent.start_time,agent.network,vehicle_capacity,copy.deepcopy(agent.destination_path))
                            agent.num_passengers = leftover_passengers
                            agent.destination_path = original_path 
                            vehicle.board_agent(copy_agent)
                    else:
                        #if agent is not boarding, we do not need to do anything
                        pass

    #update time by one unit        
    def update_time(self):
        self.update_passenger_time_multiplier()
        if self.verbose>=1:
            print('time ', self.time)
        if self.verbose>=1:
            print('at start num passengers ', len(self.agents))
        self.move_vehicles() #move vehicles around the network
        self.update_nodes_next_vehicle() #update when the next vehicles will arrive at each node
        self.alight_passengers() #passengers alight from vehicles
        if self.verbose>=1:
            print('after alighting num passengers ', len(self.agents))
        #self.remove_arrived_vehicles()  #remove vehicles which have completed their path
        self.assign_vehicles_schedule() #create new vehicles at scheduled locations
        self.create_all_passengers_pathfinding() #create new passengers
        if self.verbose>=1:
            print('after creating new, new passengers ', len(self.agents))
        self.board_passengers() #passengers board vehicles
        if self.verbose>=1:
            print('after boarding num passengers ', len(self.agents)) 
        self.time = self.time + 1 #increment time

    #run for a certain amount of time
    def basic_sim(self):
        self.time = 0
        self.times = []
        final_time = self.stop_simulation_time #determine when the simulation will end
        self.vehicle_logging_init() #initialise vehicle logging
        self.node_logging_init() #initialise node logging
        #create lists to store latitudes,longitudes and names of vehicles over time as lists of lists
        old_real_time = time.time() 
        while self.time<final_time:#till we reach the specified time
            self.update_time() #run the simulation
            self.times.append(self.time) #store the current time
            self.get_vehicle_data_at_time() #extract vehicle data at the current time
            self.get_node_data_at_time() #extract node data at the current time
            print("TIME ", self.time,'step took time ',time.time()-old_real_time)
            old_real_time = time.time()
        print("number of passengers who could reach their destination ",self.num_successful_agents)
        print("number of passengers who failed to reach their destination ",self.num_failed_agents)
        return self.times,self.vehicle_latitudes,self.vehicle_longitudes,self.store_vehicle_names,self.vehicle_passengers,self.node_passengers,self.num_failed_agents,self.num_successful_agents,final_time #return relevant data from the simulation to the calling code
        
    #class to initialise class variables to store data about the vehicles as lists of lists
    def vehicle_logging_init(self):
        self.vehicle_latitudes = []
        self.vehicle_longitudes = []
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
            #extract and store the data at the current time in a list
            latitude,longitude = vehicle.get_coordinates() #get the latitude, longitude and direction of the vehicle
            current_vehicle_latitudes.append(latitude)
            current_vehicle_longitudes.append(longitude)
            current_vehicle_names.append(vehicle.name)
            current_vehicle_passenger_counts.append(vehicle.count_agents())
            if self.verbose>=1:
                print('vehicle ',vehicle.name) #DEBUG
                print('num passengers ',vehicle.count_agents())
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
                   
    #call the correct schedule generation code based on the mode we are using
    def create_schedules(self):
        if self.schedule_type == "simple":
            self.create_schedules_simple()
        elif self.schedule_type == "complex":
            self.create_schedules_complex()
        else:
            print(self.schedule_type,' is not a valid schedule type')

    #create the schedule and functionality needed for scheduling using the complex method
    #this method constructs the schedules out of "segments", which describe a relatively short route through a network
    def create_schedules_complex(self):
        #extract info about the segments
        segment_routes = self.segment_csv["Route"].to_list() #extract the name of the route (start-end)
        segment_modifiers = self.segment_csv["Modifier"].to_list() #extract the modifier of the route description(eg, fast, semi-fast)
        segment_txt_schedules = self.segment_csv["Schedule"].to_list() #extract the actual schedule text of the segment
        segment_reverse_txt_schedules = [] #reverse schedule txts
        segment_names = [] #names of the segments
        segment_reverse_names = [] #names of the reverse segments
        num_segments = len(segment_routes) #how many segments are there
        #calculate names and schedules of segments and their reverses
        for i in range(num_segments):
            segment_reverse_txt_schedules.append(reverse_schedule_list_txt(segment_txt_schedules[i])) #determine the reverse schedule
            #determine names of segments
            if segment_modifiers[i]=="":
                new_segment_name = segment_routes[i]
                reverse_segment_name = reverse_segment_route(segment_routes[i])
            else:
                new_segment_name = segment_routes[i]+ ' ' + segment_modifiers[i]
                reverse_segment_name = reverse_segment_route(segment_routes[i]) + ' ' + segment_modifiers[i]
            #add these to the list of segment names
            segment_names.append(new_segment_name)            
            segment_reverse_names.append(reverse_segment_name)
        #merge regular and reverse list
        segment_names = segment_names + segment_reverse_names
        segment_txt_schedules = segment_txt_schedules + segment_reverse_txt_schedules
        #extract node names from the segments
        all_segment_nodes = []
        for i in range(num_segments*2):
            segment_nodes = extract_schedule_list_txt(segment_txt_schedules[i])
            all_segment_nodes.append(segment_nodes)
        
        #now that we have determined the nodes making up a segment
        #we need to combine the segments into schedules
        self.schedule_names = self.schedule_csv["Name"].to_list() #extract the name of schedules (a route that a vehicle will perform)
        self.schedule_gaps = np.array(self.schedule_csv["Gap"].to_list()) #extract the gap in time (in minutes) between services along a particular route
        self.schedule_offsets = np.array(self.schedule_csv["Offset"].to_list()) #extract the offset from the start of time (in minutes) and when the first service occurs
        self.schedule_finish = np.array(self.schedule_csv["Finish"].to_list()) #time at which the last service of a schedule may depart
        schedule_segments_texts = self.schedule_csv["Schedule Segments"].to_list() #extract the raw text that makes up a schedule as a list of segmentss   
        self.schedules = [] #list to store schedule objects
        schedule_strings = [] #list of schedule strings in the simple format
        num_schedules = len(self.schedule_names)
        for i in range(num_schedules):
            #for each schedule, extract the segments of the schedule
            segments_in_schedule = extract_schedule_list_txt(schedule_segments_texts[i]) #we can reuse this function as it extracts any comma seperated valued list
            num_segments = len(segments_in_schedule)
            first_segment = True
            for j in range(num_segments):
                try:
                    segment_id =  segment_names.index(segments_in_schedule[j])
                except:
                    print('error cannot find "',segments_in_schedule[j], '" in list of segment names')
                else:
                    #if we can find the segment ids
                    segment_nodes = copy.deepcopy(all_segment_nodes[segment_id]) #copy to prevent modifying originals
                    if first_segment==True:
                        #initial list of nodes is just the segment nodes
                        nodes = segment_nodes
                        first_segment = False #
                    else:
                        last_node_previous = nodes[-1] #get the last node of the previous segment
                        first_node_new = segment_nodes[0] #get the first node of the new segment
                        if first_node_new==last_node_previous: #this too must match otherwise the schedule is invalid
                            nodes.pop() #remove last node from the previous segment
                            nodes = nodes + segment_nodes #add the nodes from the new segment
                        else:
                            #DEBUG
                            print('last node of schedule "',segments_in_schedule[j-1],'" "',last_node_previous, '" does not match first node of schedule "',segments_in_schedule[j],'" "',first_node_new,'"')
                            print('hence schedule "',self.schedule_names[i], '" is invalid')

            #once we have extracted the list of nodes
            schedule_string = make_schedule_string(nodes) #convert back into a schedule string
            schedule_strings.append(schedule_string) #and store
        #now create the actual schedule objects
        for i in range(num_schedules):
            self.schedules.append(self.create_schedule(self.schedule_names[i],schedule_strings[i])) #create a schedule object for each schedule
        #create the dispatch schedule
    
    def create_dispatch_schedule(self):
        num_schedules = len(self.schedule_names)
        self.dispatch_schedule2 = []
        for i in range(num_schedules):
            #create the dispatch schedule for each particular schedule
            single_dispatch_schedule = []
            service_time = self.schedule_offsets[i] #extract the starting time of a service
            finish_time = self.schedule_finish[i] #and the last time at which a service can start
            service_gap = self.schedule_gaps[i]
            while service_time<=finish_time:
                single_dispatch_schedule.append(service_time) #add the time of the service to the dispatch schedule
                service_time = service_time + service_gap #calculate when the next service will occur
            #once we have added all the departure times for this service, store it in the overall dispatch schedules
            self.dispatch_schedule2.append(single_dispatch_schedule)


    #create the schedule and functionality needed for scheduling using the simple method
    def create_schedules_simple(self):
        self.schedule_names = self.schedule_csv["Name"].to_list() #extract the name of schedules (a route that a vehicle will perform)
        self.schedule_gaps = np.array(self.schedule_csv["Gap"].to_list()) #extract the gap in time (in minutes) between services along a particular route
        self.schedule_offsets = np.array(self.schedule_csv["Offset"].to_list()) #extract the offset from the start of time (in minutes) and when the first service occurs
        self.schedule_finish = np.array(self.schedule_csv["Finish"].to_list())
        schedule_texts = self.schedule_csv["Schedule"].to_list() #extract the raw text that makes up a schedule
        self.schedules = [] #list to store the schedule objects
        num_schedules = len(self.schedule_names)

        for i in range(num_schedules):
            self.schedules.append(self.create_schedule(self.schedule_names[i],schedule_texts[i])) #create a schedule object for each schedule
        

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
                new_schedule.add_start_node(node,node_name)
                previous_node = node
                previous_node_name = node_name
                node_counter += 1 #we will now be processing the next node
            else:
                edge_name = previous_node_name + ' to ' + node_name #calculate the name of the edge between these two nodes
                edge = self.edges[self.get_edge_index(edge_name)]
                edge_time = edge.provide_travel_time()
                new_schedule.add_destination(node,edge,node_name)
                node_arrival_times[node_counter] = node_arrival_times[node_counter-1] + edge_time
                previous_node = node
                previous_node_name = node_name
                node_counter += 1

        #now store arrivial times in the schedule
        new_schedule.add_schedule_times(node_arrival_times)
        return new_schedule

    #determine which nodes have which schedules present
    def determine_which_nodes_have_schedule(self):
        #go through all the nodes
        for i,node_name in enumerate(self.node_names):
            #find all the nodes
            for j,schedule in enumerate(self.schedules):
                #find out if that node name is in that schedule and if so return nodes 
                node_found,search_node_time,nodes_after,node_times_after = schedule.node_name_in_schedule(node_name)
                if node_found == True:
                    #if we found the node in a schedule, add that schedule to the list of schedules stopping at that node
                    self.nodes[i].add_stopping_schedule(self.schedule_names[j],self.dispatch_schedule2[j],search_node_time,nodes_after,node_times_after)

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
            pass     

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
                    print('WARNING destination name  ', edge_destinations[i], 'is not in the list of node names in this network')
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
            print('WARNING start_node_name  ', start_node_name, 'is not in the list of node names in this network')
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
                    print('WARNING destination name', edge_destinations[i], 'is not in the list of node names in this network')
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
            print('node_name  ', node_name, 'is not in the list of node names in this network')
            return -1 #return -1 to indicate error

    #get the index of an edge name in the list of edges
    def get_edge_index(self,edge_name):
        #try and find the starting node in the list of all nodes
        try:
            index = self.edge_names.index(edge_name)
            return index
        except ValueError:
            #handle case where starting name not in list of names
            print('edge_name  ', edge_name, 'is not in the list of edge names in this network')
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
        start_index = self.get_node_index(self,start_node_name)
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

#reverse the order of nodes in a schedule string
def reverse_schedule_list_txt(schedule_string):
    nodes = extract_schedule_list_txt(schedule_string) #get the list of node names
    nodes.reverse() #reverse the list of nodes
    #reconvert it back into a text string
    schedule_string = ""
    for node in nodes:
        schedule_string = schedule_string + node + ','
    #remove the trailing comma
    schedule_string = schedule_string[:-1]
    return schedule_string

#reverse the route name of a segment
def reverse_segment_route(route_name_string):
    start_node_name = ""
    end_node_name = ""
    start_node_extracted = False
    for letter in route_name_string:
        if start_node_extracted==False:
            if letter=='-':
                start_node_extracted = True
            else:
                start_node_name = start_node_name + letter
        else:
            end_node_name = end_node_name + letter

    reverse_name = end_node_name + "-" + start_node_name
    return reverse_name


#return true if random generated number is less than provided chance 
#input chance is equal to the chance of the output being true
def random_true(chance):
    random_number = rand.random() #random number between 0 and 1
    if random_number<=chance:
        return True
    else:
        return False
#turn a list of nodes into a schedule string
def make_schedule_string(nodes):
    schedule_string = ""
    for node in nodes:
        #add each node name to the schedule string
        schedule_string = schedule_string + node + ','
    schedule_string = schedule_string[:-1] #remove trailing comma
    return schedule_string
