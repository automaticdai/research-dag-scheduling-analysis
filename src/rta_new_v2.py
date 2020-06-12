import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle

import networkx as nx

from graph import find_longest_path_dfs, find_predecesor, find_successor, find_ancestors, find_descendants, get_subpath_between


def EO():
    """ The Eligibility Ordering
    """
    eo_ordering = {}
    return eo_ordering


def load_task(task_idx):
    # << load DAG task <<
    dag_task_file = "../dag-gen-rnd/data/Tau_{:d}.gpickle".format(task_idx)
    G = nx.read_gpickle(dag_task_file)

    # formulate the graph list
    G_dict = {}
    C_dict = {}
    V_array = []
    max_key = 0
    for u, v, weight in G.edges(data='label'):
        if u not in G_dict:
            G_dict[u] = [v]
        else:
            G_dict[u].append(v)

        if v > max_key:
            max_key = v
        
        if u not in V_array:
            V_array.append(u)
        if v not in V_array:
            V_array.append(v)
        
        C_dict[u] = weight
    C_dict[max_key] = 1

    G_dict[max_key] = []

    # formulate the c list (c[0] is c for v1!!)
    C_exp = []
    for key in sorted(C_dict):
        C_exp.append(C_dict[key])

    V_array.sort()
    L, lamda = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_exp)
    W = sum(C_exp)

    VN_array = V_array.copy()

    for i in lamda:
        if i in VN_array:
            VN_array.remove(i)

    # >> end of load DAG task >>
    return G_dict, C_dict, lamda, VN_array, L, W


def remove_nodes_in_list(nodes, nodes_to_remove):
    for i in nodes.copy():
        if i in nodes_to_remove:
            nodes.remove(i)


def find_concurrent_nodes(G, node):
    ancs = find_ancestors(G, node, path=[])
    decs = find_descendants(G, node, path=[])
    
    V = list(G.keys())
    V.remove(node)
    remove_nodes_in_list(V, ancs)
    remove_nodes_in_list(V, decs)

    return V


def test_parallelism(G, n):
    pass


def rta_new_v2(task_idx, m):
    R = 0
    alpha = 0
    beta = 0

    providers = []
    consumers = []

    # --------------------------------------------------------------------------
    # I. load the DAG task
    G_dict, C_dict, lamda, VN_array, L, W = load_task(task_idx)

    # --------------------------------------------------------------------------
    # II. providers and consumers
    # iterative all critical nodes
    # after this, all provides and consumers will be collected
    new_provider = []
    nc_nodes_left = VN_array.copy()
    for key, i in enumerate(lamda):
        if new_provider == []:
            new_provider = [i]

        if ((key+1) < len(lamda)):
            pre_nodes = find_predecesor(G_dict, lamda[key+1])

            print("Checking: ", i, "Pre: ", pre_nodes)

            if pre_nodes == [i]:    
                new_provider.append(lamda[key+1])
            else:
                print("New provider:", new_provider)
                providers.append(new_provider)
                new_provider = []

                # remove critical nodes
                remove_nodes_in_list(pre_nodes, lamda)

                # find all consumers
                new_consumer = []
                for pre_node in pre_nodes:
                    # add this pre-node first
                    if pre_node in nc_nodes_left:
                        new_consumer.append(pre_node)

                    # find any ancestor of this pre-node
                    ancestors_of_node = find_ancestors(G_dict, pre_node, path=[])
                    remove_nodes_in_list(ancestors_of_node, lamda)
                    if ancestors_of_node:
                        for anc_v in ancestors_of_node:
                            if anc_v not in new_consumer and anc_v in nc_nodes_left:  new_consumer.append(anc_v)

                        print(ancestors_of_node)

                new_consumer.sort()
                consumers.append(new_consumer)

                # remove from NC list
                for i_nc in new_consumer:  nc_nodes_left.remove(i_nc)

                new_consumer = []
        else:
            # the last node needs special care as it has no successors
            print("New provider:", new_provider)
            providers.append(new_provider)

            # find all consumers (all the left nc nodes)
            nc_nodes_left.sort()
            consumers.append(nc_nodes_left)

    print(providers)
    print(consumers)

    # --------------------------------------------------------------------------
    # III. bound alpha and beta
    interference = 0
    print(find_concurrent_nodes(G_dict, 4))

    


    # get m_i

    # calc finish time

    # Case A:
    # calc alpha
    # calc beta


    # Case B:
    
    return R, alpha, beta


if __name__ == "__main__":
    R, alpha, beta = rta_new_v2(task_idx=3, m=4)
    print("R={}, alpha={}, beta={}".format(R, alpha, beta))