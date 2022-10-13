import numpy as np
import copy as copy
#agent.py
#stores the agent class and related functionality

#route_step = [next_service_name,node.name]

class Agent:
    def __init__(self,start_node,destination_node,id,start_time,network,number_passengers,path):
        self.start_node = start_node 
        self.destination_node = destination_node
        self.id = id
        self.start_time = start_time
        self.network = network #reference to the network object
        self.destination_path = path #path of actions to the destination node
        self.number_passengers = number_passengers #number of passengers represented by this agent
        #self.found_path = self.pathfind()
        self.done = False #has the agent reached their destination yet
        

    #calculate a path from the start to the destination
    #store this path inside the agent
    def pathfind(self):
        #print('start ',self.start_node.name,' destination ',self.destination_node.name) #DEBUG
        #get info about vehicles arriving at the starting node
        start_next_service_times,start_nodes_after,start_node_times_after,start_schedule_names = self.start_node.provide_next_services(data_time=self.start_time,start=True)
        #get index (id) of starting and ending nodes in the network structure
        start_node_index = self.start_node.id
        destination_node_index = self.destination_node.id
        #create an array to store the paths to all the other nodes
        num_nodes_in_network = len(self.network.node_names)
        distance_to_nodes = np.zeros(num_nodes_in_network) + np.inf #initial distance to reach all other nodes will be infinite
        evaluated_nodes = np.zeros(num_nodes_in_network)  #when a node is evaluated the value in this matrix is set to infinite, ensuring that node is never evaluated again
        distance_to_nodes[start_node_index] = 0 #initial distance to reach the starting node is 0
        distance_to_final_destination = self.network.distance_to_all[:,destination_node_index]
        path_to_nodes = [[] for _ in range(num_nodes_in_network)] #create an empty nested list of the required length to store paths to nodes
        #now that we have extracted preliminary data, start the pathfinding operation
        while True: #loop till we meet an exit condition
            expected_distance_to_nodes = distance_to_nodes + distance_to_final_destination + evaluated_nodes #expected (minimal) distance to reach a node
            min_index = np.argmin(expected_distance_to_nodes) #get the index of the node with the lowest expected travel time, evaluate this next
            minimum_expected_distance = expected_distance_to_nodes[min_index]
            #print('evaluating ',self.network.nodes[min_index].name,' which takes ',distance_to_nodes[min_index],' to reach from start') #DEBUG
            #print('and ',expected_distance_to_nodes[min_index],' to reach final through') #DEBUG
            if minimum_expected_distance == np.inf:
                break #break out of the loop, we have explored all the network we can reach
            elif min_index == destination_node_index:
                #print('we have found the destination node')
                self.destination_path = path_to_nodes[destination_node_index]
                #print(self.destination_path)
                break
            else:
                minimum_distance = distance_to_nodes[min_index] #extract the time taken to reach the node being evaluated
                current_time = minimum_distance + self.start_time #time at which we reach the node currently being evaluated
                #otherwise, explore paths from the minimal node
                if min_index==start_node_index:
                    #use precalculated data from the starting node
                    next_service_times = start_next_service_times
                    nodes_after = start_nodes_after
                    times_after = start_node_times_after
                    schedule_names = start_schedule_names

                else:
                    #otherwise calculate data about vehicle arrivials at nodes on the fly
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
                        distance_to_current_node_old_path = distance_to_nodes[node_index] #what is the current shortest path to the node we are looking at
                        distance_to_current_node_new_path = minimum_distance + (next_service_time-current_time) + route_times_after[j] #how long to reach next node through evaluation node
                        #print('to reach ',node.name,' current best is ',distance_to_current_node_old_path,' new path is ',distance_to_current_node_new_path) #DEBUG
                        if distance_to_current_node_new_path<distance_to_current_node_old_path:
                            #if so, we have found a better path
                            #print('we have found a better path') #DEBUG
                            distance_to_nodes[node_index] = distance_to_current_node_new_path
                            route_to_old_node = path_to_nodes[min_index] #extract the path to the evaluation node
                            #print('route to previous node ',route_to_old_node) #DEBUG
                            #print('route step ',route_step)
                            route_to_new_node = copy.copy(route_to_old_node) #path to the next node is path to the evaluation node + new step
                            route_to_new_node.append(next_service_name) #store the next service we need to catch
                            route_to_new_node.append(node.name) #and when we need to get off that service
                            #print('new route ',route_to_new_node) #DEBUG
                            path_to_nodes[node_index] = route_to_new_node #store this in the list of all paths
                
                #mark the evaluated node as evaluated, it will not be evaluated again
                evaluated_nodes[min_index] = np.inf

        if distance_to_nodes[destination_node_index]==np.inf: #we have not found a path to our destination
            #hence the passenger should pop back out of existance
            return False #the passenger did not find a path to their destination
        else:
            return True #indicate we successfully found a path to their destination
    #ask the agent if it wishes to board a vehicle of a particular schedule
    def board(self,schedule_name):
        #print('boarding' ,self.destination_path)
        if schedule_name==self.destination_path[0]:
            #print('boarding boarding')
            #board if schedule name matches with next schedule to board
            del self.destination_path[0] #we only wish to board this service once
            #print('boarding',self.destination_path)
            return True
        else:
            return False

    #ask the agent if it wishes to alight a vehicle at a particular node
    def alight(self,node_name):
        #print('alighting',self.destination_path)
        #print('node name ',node_name)
        if node_name==self.destination_path[0]:
            #print('alighting alighting')
            #alight if node name matches with next node to alight at
            del self.destination_path[0] #we only wish to alight at this node once
            #print('alighting',self.destination_path)
            if len(self.destination_path)==0:
                return 2 #indicate agent has come to the end of its journey after alighting here
            else:
                return 1 #indicate agent has alighted here, but still exists
        else:
            return 0 #indicate not alighting here

    #print the path from the start destination to the end destination
    def test_agent_path(self):
        print('START ',self.start_node.name)
        print('DESTINATION ',self.destination_node.name)
        print("PATH ",self.destination_path)
        





        


