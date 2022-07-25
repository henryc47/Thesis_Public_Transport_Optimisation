#vehicle.py
#stores the vehicle class and related functionality

import copy #for making shallow copies of schedules, we want the schedule object to be unique but the linked nodes/edges to be the same
import schedule as Schedule
import network as Network
#base vehicle class
class Vehicle:
    #create the vehicle
    def __init__(self,schedule,start_time,name):
        self.schedule = copy.copy(schedule)
        self.name = name
        self.state = 'at_stop' #vehicle states are 'at_stop' and 'moving'
        self.schedule.offset_schedule_times(start_time)#adjust the schedule to reflect the time we started
        self.number_passengers = 0 #current number of passengers aboard the vehicle
        check,self.previous_stop = self.schedule.provide_next_destination()
        check = self.remove_reached_destination() #remove starting destination from list of destinations
    

    def update(self):
        if self.state == 'at_stop':
            check,self.next_destination,self.next_edge = self.schedule.provide_next_destination() #get the destination we are moving towards and the edge we will move on
            if check==False:#vehicle has reached it's destination
                return False #return false to indicate it should be deleted

            self.schedule.remove_reached_destination() #remove these from the schedule
            self.edge_length = self.next_edge.provide_travel_time() #how long will it take to reach the next destination
            if self.edge_length==1: #minimum traversal time is 1
                self.state = 'at_stop'
                self.previous_stop = self.next_destination #former next destination is now the previous destination
            else:
                self.state = 'moving'
                self.move_timer = 1#start the move timer, we will move 1 unit of time

        elif self.state == 'moving':
            if self.move_timer == self.edge_length-1: # we have reached the next station
                self.state == 'at_stop'
                self.previous_stop = self.next_destination #former next destination is now the previous destination
            else:
                self.state == 'at_stop'
                self.move_timer += 1 #increment the move timer
        
        return True #to indicate update is successful, vehicle has not reached destination

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
    










    


    
        



