#vehicle.py
#stores the vehicle class and related functionality

import copy #for making shallow copies of schedules, we want the schedule object to be unique but the linked nodes/edges to be the same
import schedule as Schedule
import network as Network
#base vehicle class
class Vehicle:
    #create the vehicle
    def __init__(self,schedule,start_time,name,seated_capacity=960,standing_capacity=1680):
        self.schedule = copy.copy(schedule)
        self.schedule_name = self.schedule.name
        self.name = name
        self.state = 'at_stop' #vehicle states are 'at_stop' and 'moving'
        self.state_new = True #newly created, will not stop if final_destination = current destination to allow the city circle to function
        self.schedule.offset_schedule_times(start_time)#adjust the schedule to reflect the time we started
        self.number_passengers = 0 #current number of passengers aboard the vehicle
        check,self.previous_stop = self.schedule.provide_next_destination() #get the starting destination which will be stored as the previous stop
        check = self.schedule.remove_reached_destination() #remove starting destination from list of destinations
        self.final_destination = self.schedule.provide_final_destination() #get the final destination as well
        self.at_final_destination = False #mark if a vehicle has reached it's final destination, and will be deleted next update
        self.agents = [] #container to store agents in the vehicle
        self.num_passengers = 0 #number of passengers in the vehicle
        self.max_passengers = 1610 #maximum number of passengers in the vehicle

    #have an agent try and board the vehicle
    def board_agent(self,agent):
        self.agents.append(agent) #add agents to the list of agents on the vehicle
        self.num_passengers = self.num_passengers + agent.number_passengers #the number of passengers has increased

    #have an agent try and leave the vehicle
    def alight_agent(self,id):
        removed_agent = self.agents.pop(id)
        self.num_passengers = self.num_passengers - removed_agent.number_passengers #the number of passengers has decreased
        return removed_agent
    
    def get_capacity(self):
        return self.max_passengers-self.num_passengers

    #move the vehicle around the network according to its schedule
    def update(self):
        if self.state == 'at_stop': #if the vehicle was at a stop
            #add some code to disembark passengers
            #add some code to pick up passengers
            if self.final_destination == self.previous_stop and self.state_new == False: #if vehicle has reached it's destination and not newly created                
                return False #return false to indicate it should be deleted
            #if vehicle has not reached it's final destination
            self.state_new=False
            check,self.next_destination,self.next_edge = self.schedule.provide_next_destination() #extract next destination and how to get there
            self.edge_length = self.next_edge.provide_travel_time() #store the length of the next edge
            if self.edge_length == 1: #if edge takes only 1 time unit to traverse
                #we are immediately at the next destination
                self.state = 'at_stop'
                self.previous_stop = self.next_destination
                self.schedule.remove_reached_destination() #remove the previous destination
            else:
                #we are now moving towards the next destination
                self.state = 'moving'
                self.move_timer = 1#start the move timer, we will move 1 unit of time

        elif self.state == 'moving': #if the vehicle was moving
            if self.move_timer == self.edge_length-1: # we have reached the next station
                self.state = 'at_stop'
                self.previous_stop = self.next_destination
                self.schedule.remove_reached_destination() # remove the previous destination
            else:
                #we are still moving towards the next destination
                self.state = 'moving'
                self.move_timer = self.move_timer + 1
    
        return True          

    #print where the vehicle is
    def verbose_position(self):
        print('vehicle ',self.name, 'is ',self.state,' path is ',self.schedule_name)
        schedule_nodes = self.schedule.nodes
        for node in schedule_nodes:
            print('too ',node.name)
        #print('currently is ',self.state, 'previous stop is ',self.previous_stop.name,' next stop is ',self.next_destination.name,' move timer is ',self.move_timer)
    
    #print when the vehicle is at a stop
    def verbose_stop(self):
        if self.state == 'at_stop':
            print('vehicle ',self.name,' stopped at ', self.previous_stop.name)

    def get_coordinates(self):
        if self.state == 'at_stop':
            #when at stop, vehicle position is the position of the stop (which is previous stop)
            latitude = self.previous_stop.latitude
            longitude = self.previous_stop.longitude
        
        elif self.state == 'moving':
            #when moving, vehicle position is along straight line path between previous node and next node
            fraction_moved = (self.move_timer/self.edge_length)
            latitude = self.previous_stop.latitude*(1-fraction_moved) + (self.next_destination.latitude*fraction_moved)
            longitude = self.previous_stop.longitude*(1-fraction_moved) + (self.next_destination.longitude*fraction_moved)
        
        return latitude,longitude
    

    #count the number of agents in the vehicle
    def count_agents(self):
        #num_agents = 0
        #for agent in self.agents:
        #    num_agents = num_agents + agent.number_passengers
        return self.num_passengers











    


    
        



