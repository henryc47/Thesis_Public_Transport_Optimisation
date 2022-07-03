#script.py
#useful scripts for setting up and running simulations, as well as testing

import network as network
import time

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
    print(basic_network.find_distance_to_all())
    time2 = time.time()
    print("finding node distances ", time2-time1, " seconds")

