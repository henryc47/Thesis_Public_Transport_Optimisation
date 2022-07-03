#script.py
#useful scripts for setting up and running simulations, as well as testing

import network as network

def setup_basic_simulation():
    #relative file paths to node/edge documents
    nodes_basic_path = 'nodes_basic.csv'
    edges_basic_path = 'edges_basic.csv'
    basic_network = network.Network(nodes_basic_path,edges_basic_path)
    #now perform some tests
    #basic_network.test_edges()
    #basic_network.test_nodes()
    #basic_network.test_dijistraka('Hornsby')
    #basic_network.test_dijistraka('Gordon')
    #basic_network.test_dijistraka('Chatswood')
    print(basic_network.find_distance_to_all())

