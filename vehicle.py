#vehicle.py
#stores the vehicle class and related functionality
import warnings

#schedule class, stores the list of nodes the vehicle is trying to reach, and the edge needed to reach each node
class Schedule:
    
    #initialise the empty schedule
    def __init__(self,start_node):
        self.start_node = start_node #starting node of the schedule, useful for assigning schedules to vehicles
        self.nodes = [] #list of destinations
        self.edges = [] #list of edges to reach each destination from previous location


    #add a destination to the schedule
    def add_destination(self,next_node,next_edge):
        self.nodes.append(next_node)
        self.edges.append(next_edge)

    #provide next destination
    def provide_destination(self):
        if len(self.nodes)==0:
            return False#return false to indicate there are no more destinations, schedule is finished
        else:
            #return true to indicate there is a next destination, provide next destination and how to get there
            return (True,self.nodes[0],self.edges[0])

    #remove the destination we just reached    
    def remove_reached_destination(self):
        if len(self.nodes)==0:
            return False#return false to indicate there are no more destinations, schedule is finished
        else:  
            del self.nodes[0]
            del self.edges[0]
            return True#return true to indicate operation successful
    
    def provide_start(self):
        return self.start_node


#base vehicle class
#class Vehicle:
#    def __init__(self,schedule):
#

