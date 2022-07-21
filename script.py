#script.py
#useful scripts for setting up and running simulations, as well as testing

import network as network
import time
import numpy as np
 

def setup_basic_sim():
    time1 = time.time()
    nodes_basic_path = 'nodes_basic.csv'
    edges_basic_path = 'edges_basic.csv'
    schedule_basic_path = 'schedule_basic.csv'
    time2 = time.time()
    print("loading network data from csv ", time2-time1, " seconds")
    basic_network = network.Network(nodes_basic_path,edges_basic_path,schedule_basic_path)
    basic_network.test_schedules()


def setup_medium_sim(test=True):
    time1 = time.time()
    nodes_basic_path = 'nodes_medium.csv'
    edges_basic_path = 'edges_medium.csv'
    time2 = time.time()
    print("loading network data from csv ", time2-time1, " seconds")
    basic_network = network.Network(nodes_basic_path,edges_basic_path)
    if test:
        #basic_network.test_edges()
        #basic_network.test_nodes()
        basic_network.test_dijistraka('Central')
        basic_network.test_origin_destination_matrix('Chatswood')
        basic_network.test_origin_destination_matrix('Newtown')
        basic_network.test_origin_destination_matrix('Central')
        basic_network.test_origin_destination_matrix('Mount Colah')
        basic_network.test_origin_destination_matrix('Penrith')

def test_basic_gravity_model(iterations):
    starts = np.array((10,20,40,10))
    stops =  np.array((10,20,40,10))
    distances = np.array(([0,3,5,7],[3,0,2,4],[5,2,0,2],[7,4,2,0]))
    time1 = time.time()
    trips = network.gravity_assignment(starts,stops,distances,2,0,iterations)
    time2 = time.time()
    print(trips)
    #print(stop_accuracy)
    print("evaluating gravity model ", time2-time1, " seconds")