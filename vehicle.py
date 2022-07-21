#vehicle.py
#stores the vehicle class and related functionality

import copy #for making shallow copies of schedules, we want the schedule object to be unique but the linked nodes/edges to be the same
import schedule as Schedule
#base vehicle class
class Vehicle:
    #create the vehicle
    def __init__(self,schedule,start_time):
        self.schedule = copy.copy(schedule)
        self.schedule.offset_schedule_times(start_time)#adjust the schedule to reflect the time we started
        self.number_passengers = 0 #current number of passengers aboard the vehicle
    


    


    
        



