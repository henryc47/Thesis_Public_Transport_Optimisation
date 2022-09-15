#schedule.py
#schedule class, stores the list of nodes the vehicle is trying to reach, and the edge needed to reach each node
import numpy as np
import copy as copy

class Schedule:
    #initialise the empty schedule
    def __init__(self,name):
        self.name = name#starting node of the schedule, useful for assigning schedules to vehicles
        self.nodes = [] #list of destinations (reference to a node)
        self.edges = [] #list of edges to reach each destination from previous location (reference to an edge)
        self.schedule_times = [] #list of times when we will reach the nodes we are travelling toos

    #create a shallow copy of the object and all it's internal data-structures, however maintain same references to nodes and edges
    def __copy__(self):
        #create a schedule object
        copy_schedule = Schedule(self.name)
        copy_schedule.nodes = copy.copy(self.nodes)
        copy_schedule.edges = copy.copy(self.edges)
        copy_schedule.schedule_times = copy.copy(self.schedule_times)
        return copy_schedule
        
    #add the first destination to the schedule
    def add_start_node(self,start_node):
        self.nodes.append(start_node)

    #add a destination to the schedule
    def add_destination(self,next_node,next_edge):
        self.nodes.append(next_node)
        self.edges.append(next_edge)

    #provide final destination in the schedule
    def provide_final_destination(self):
        num_nodes = len(self.nodes)
        final_destination = self.nodes[num_nodes-1]
        return final_destination

    #provide next destination, note this requires you to have first deleted the initial destination to work correctly
    def provide_next_destination(self):
        #print('providing next destination, num nodes ',len(self.nodes),' num edges ',len(self.edges)) #DEBUG
        if len(self.nodes)==0:
            return False#return false to indicate there are no more destinations, schedule is finished
        if len(self.nodes)>len(self.edges): #provide the start point if we are yet to remove it
            return (True,self.nodes[0])
        else:
            #return true to indicate there is a next destination, provide next destination and how to get there
            return (True,self.nodes[0],self.edges[0])

    #remove the destination we just reached and the node we used to reach it    
    def remove_reached_destination(self):
        if len(self.nodes)==0:
            return False#return false to indicate there are no more destinations, schedule is finished
        if len(self.nodes)>len(self.edges): #remove the start point if we are yet to remove it
            del self.nodes[0]
            return True
        else:  
            del self.nodes[0]
            del self.edges[0]
            return True#return true to indicate operation successful
    
    def provide_name(self):
        return self.name
    
    #this 
    def add_schedule_times(self,arrival_times):
        self.schedule_times = arrival_times #this is a numpy array

    #offset the schedule times by the current time to obtain time the time the vehicle will reach each node
    def offset_schedule_times(self,current_time):
        self.schedule_times = self.schedule_times + current_time
    
    #provide information about the schedule, namely the list of nodes and edges traversed, and the time when nodes will be reached
    def test_schedule(self):
        print('SCHEDULE ', self.name)
        num_nodes = len(self.nodes)
        for i in range(num_nodes):
            if i>0:
                print('NODE ', self.nodes[i].name, ' TIME ', self.schedule_times[i], ' EDGE ', self.edges[i-1].name) #note, print the edge to reach the displayed node
            else:
                print('NODE ', self.nodes[i].name, ' TIME ', self.schedule_times[i]) #for starting node, there is no edge to reach the displayed node 

