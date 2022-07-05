#script.py
#useful scripts for setting up and running simulations, as well as testing

import network as network
import time
import numpy as np

def setup_basic_simulation():
    #relative file paths to node/edge documents
    time1 = time.time()
    nodes_basic_path = 'nodes_basic.csv'
    edges_basic_path = 'edges_basic.csv'
    time2 = time.time()
    print("loading network data from csv ", time2-time1, " seconds")
    time1 = time.time()
    basic_network = network.Network(nodes_basic_path,edges_basic_path)
    time2 = time.time()
    print("setting up network objects ", time2-time1, " seconds")
    #now perform some tests
    #basic_network.test_edges()
    #basic_network.test_nodes()
    #basic_network.test_dijistraka('Hornsby')
    #basic_network.test_dijistraka('Gordon')
    #basic_network.test_dijistraka('Chatswood')
    time1 = time.time()
    distance_to_all = basic_network.find_distance_to_all()
    time2 = time.time()
    print('distance to all',distance_to_all)
    print("finding node distances ", time2-time1, " seconds")
    time1 = time.time()
    origin_destination_trips = basic_network.create_origin_destination_matrix()
    time2 = time.time()
    np.set_printoptions(precision=3,suppress=True)
    print('trip origin and destination matrix ',origin_destination_trips)
    print("assigning trip origin and destinations ", time2-time1, " seconds")
    basic_network.test_origin_destination_matrix_all()        

    
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