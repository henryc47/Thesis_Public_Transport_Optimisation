class Evaluator:
    #initalise the evaluators with the standard costs of a system
    def __init__(self,eval_csv,parameters_csv):
        self.vehicle_cost = eval_csv["Vehicle Cost"].to_list()[0] #marginal cost of running a vehicle, $/hour
        self.agent_cost_seated = eval_csv["Agent Cost Seated"].to_list()[0] #marginal value of agents time, $/seated
        self.agent_cost_standing = eval_csv["Agent Cost Standing"].to_list()[0] #marginal value of agents time, higher because standing is unpleasant $/hr
        self.agent_cost_waiting = eval_csv["Agent Cost Waiting"].to_list()[0] #marginal value of agents time, higher because waiting is unpleasant $/hr
        self.unfinished_penalty = eval_csv["Unfinished Penalty"].to_list()[0] #penalty if passengers are unable to reach their destination, based roughly on cost of late night taxi ride
        self.vehicle_max_seated = parameters_csv["Vehicle Max Seated"].to_list()[0] #maximum number who can sit inside a vehicle
        self.vehicle_max_standing = parameters_csv["Vehicle Max Standing"].to_list()[0] #maximum number who can fit inside a vehicle seated + standing
        self.timesteps_per_hour = 60

    def evaluate(self,sim_times,sim_vehicle_passengers,sim_node_passengers,num_failed_passengers,num_successful_passengers):
        seated_passenger_time = 0 #amount of minutes passengers spend seated
        waiting_passenger_time = 0 #amount they spend waiting
        standing_passenger_time = 0 #amount they standing
        vehicle_time = 0 #amount of minutes vehicles are used for
        max_num_vehicles_at_once = 0
        max_passengers_in_a_vehicle = 0
        for i,time in enumerate(sim_times):
            #go through all the time_steps and extract relevant data
            vehicle_passengers = sim_vehicle_passengers[i]
            node_passengers = sim_node_passengers[i]
            new_seated_time,new_standing_time,num_vehicles,max_passengers =  self.passenger_time_vehicles(vehicle_passengers)
            new_waiting_time =  self.passenger_time_nodes(node_passengers)
            seated_passenger_time = seated_passenger_time + new_seated_time
            standing_passenger_time = standing_passenger_time + new_standing_time
            waiting_passenger_time = waiting_passenger_time + new_waiting_time
            vehicle_time = vehicle_time + num_vehicles
            if num_vehicles>max_num_vehicles_at_once:
                max_num_vehicles_at_once = num_vehicles
            if max_passengers>max_passengers_in_a_vehicle:
                max_passengers_in_a_vehicle = max_passengers
        #convert resource use time from minutes into hours
        seated_passenger_time = seated_passenger_time/self.timesteps_per_hour #amount of minutes passengers spend seated
        waiting_passenger_time = waiting_passenger_time/self.timesteps_per_hour #amount they spend waiting
        standing_passenger_time = waiting_passenger_time/self.timesteps_per_hour #amount they standing
        vehicle_time = vehicle_time/self.timesteps_per_hour #amount of minutes vehicles are used for
        total_passenger_time = seated_passenger_time + waiting_passenger_time + standing_passenger_time
        cost_seated_passenger_time = standing_passenger_time*self.agent_cost_seated
        cost_standing_passenger_time = standing_passenger_time*self.agent_cost_standing
        cost_waiting_passenger_time = waiting_passenger_time*self.agent_cost_waiting
        cost_passenger_time = cost_seated_passenger_time + cost_standing_passenger_time + cost_waiting_passenger_time
        cost_passenger_failure = num_failed_passengers*self.unfinished_penalty
        cost_vehicle_time = vehicle_time*self.vehicle_cost
        total_cost = cost_passenger_time + cost_vehicle_time + cost_passenger_failure
        #calculate some per capita stats
        num_passengers = num_failed_passengers+num_successful_passengers
        time_per_passenger = (total_passenger_time/num_passengers) #time in hours for each passenger
        time_per_passenger_seated = (seated_passenger_time/num_passengers)
        time_per_passenger_standing = (standing_passenger_time/num_passengers)
        time_per_passenger_waiting = (waiting_passenger_time/num_passengers)
        failure_rate = (num_failed_passengers/num_passengers)
        cost_per_passenger = cost_vehicle_time/num_passengers#just the financial cost
        total_cost_per_passenger = total_cost/num_passengers #holistic cost
        message = ""
        message = message + "Num Passenger Trips = " + f'{num_passengers:,}' + '\n'
        message = message + "% Trips Did Not Destination = " + f'{(failure_rate*100):.2f}' + '% \n'
        message = message + "Total Time per Passenger = " + f'{(time_per_passenger*self.timesteps_per_hour):.2f}' + ' Mins \n'
        message = message + "Time Standing = " + f'{(time_per_passenger_standing*self.timesteps_per_hour):.2f}' + ' Mins \n'
        message = message + "Time Seated = " + f'{(time_per_passenger_seated*self.timesteps_per_hour):.2f}' + ' Mins \n'
        message = message + "Time Waiting = " + f'{(time_per_passenger_waiting*self.timesteps_per_hour):.2f}' + ' Mins \n'
        message = message + "Cost of Vehicle Operation = $" + f'{cost_vehicle_time:,.0f}' + "\n"
        message = message + "Max Number of Vehicles at Once = " + f'{max_num_vehicles_at_once:,.0f}' + "\n"
        message = message + "Max Passengers in a Vehicle = " + f'{max_passengers_in_a_vehicle:,.0f}' + "\n"
        message = message + "Combined Financial and Time Cost = $" + f'{total_cost:,.2f}' + "\n"
        message = message + "Financial Cost per Passenger = $" + f'{cost_per_passenger:.2f}' + "\n"
        message = message + "Total Cost per Passenger = $" + f'{total_cost_per_passenger:.2f}' + "\n"
        return message

    #get how many minutes passengers were sitting/standing in vehicles at this timestep
    def passenger_time_vehicles(self,vehicle_passengers):
        seated = 0
        standing = 0
        max_passengers = 0
        try:
            num_vehicles = len(vehicle_passengers)
        except:
            num_vehicles = 0
        for num_passengers in vehicle_passengers:
            if num_passengers>max_passengers:
                max_passengers = num_passengers
            if num_passengers<=self.vehicle_max_seated:
                seated = seated + num_passengers
            else:
                seated = seated + self.vehicle_max_seated
                standing = standing + num_passengers-self.vehicle_max_seated
        return seated,standing,num_vehicles,max_passengers

    #get how many minutes passengers were waiting at nodes at this timestep
    def passenger_time_nodes(self,node_passengers):
        waiting = 0
        for num_passengers in node_passengers:
            waiting = waiting + num_passengers

        return waiting
