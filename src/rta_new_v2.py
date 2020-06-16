import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle

import networkx as nx

from graph import find_longest_path_dfs, find_predecesor, find_successor, find_ancestors, find_descendants, get_subpath_between
from rta_np import rta_np


def EO():
    """ The Eligibility Ordering
    """
    eo_ordering = {}
    return eo_ordering


def load_task(task_idx):
    # << load DAG task <<
    dag_task_file = "../dag-gen-rnd/data/Tau_{:d}.gpickle".format(task_idx)

    # task is saved as NetworkX gpickle format
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


def rta_classic(task_idx, m):
    _, _, _, _, L, W = load_task(task_idx)
    makespan = L + 1 / m * (W - L)
    return makespan


def remove_nodes_in_list(nodes, nodes_to_remove):
    for i in nodes.copy():
        if i in nodes_to_remove:
            nodes.remove(i)


def find_concurrent_nodes(G, node):
    ''' find concurrent nodes
    '''
    ancs = find_ancestors(G, node, path=[])
    decs = find_descendants(G, node, path=[])
    
    V = list(G.keys())
    V.remove(node)
    remove_nodes_in_list(V, ancs)
    remove_nodes_in_list(V, decs)

    return V


def test_parallelism(G, node, n):
    ''' test if delta(node) < n
    '''
    return False


def rta_new_v2(task_idx, m):
    alpha_arr = []
    beta_arr = []

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
                for i_nc in new_consumer:
                    nc_nodes_left.remove(i_nc)

                new_consumer = []
        else:
            # the last node needs special care as it has no successors
            print("New provider:", new_provider)
            providers.append(new_provider)

            # find all consumers (all the left nc nodes)
            nc_nodes_left.sort()
            consumers.append(nc_nodes_left)

    print("Providers:", providers)
    print("Consumers:", consumers)
    print("- - - - - - - - - - - - - - - - - - - -")

    # --------------------------------------------------------------------------
    # III. calculate the finish times of each provider, and the consumers within
    f_dict = {}        # the set of all finish times
    I_dict = {}        # interference workload
    R_i_minus_one = 0  # the response time of the previous provider theta^*_(i - 1)

    # iteratives all providers
    for i, theta_i_star in enumerate(providers):
        print("theta", i, ":", theta_i_star)
        print(consumers[i])  

        # get the finish time of all provider nodes (in provider i)
        for provi_idx, provi_i in enumerate(theta_i_star):
            # (skipped) topoligical order, skipped because guaranteed by the generator
            if provi_idx == 0:
                f_i = C_dict[provi_i] + R_i_minus_one
                f_dict[provi_i] = f_i
                f_theta_i_star = f_i  # finish time. every loop refreshes this
            else:
                previous_i = theta_i_star[provi_idx - 1]
                f_i = C_dict[provi_i] + f_dict[previous_i]
                f_dict[provi_i] = f_i
                f_theta_i_star = f_i
        
        # iteratives all consumers
        # (skipped) topoligical order, skipped because guaranteed by the generator
        # note: consumer can be empty
        theta_i = consumers[i]
        f_v_j_max = 0; f_v_j_max_idx = -1
        for _, theta_ij in enumerate(theta_i):
            print(theta_ij, ":", C_dict[theta_ij])
            
            # the interference term
            if test_parallelism(G_dict, theta_ij, m - 1):
                # sufficient parallism
                interference = 0
            else:
                # not enough cores
                # concurrent nodes of ij. Can be empty.
                con_ij = find_concurrent_nodes(G_dict, theta_ij)
                #print("Con nodes:", con_ij)

                int_ij = con_ij.copy()
                remove_nodes_in_list(int_ij, lamda)

                ans_ij = find_ancestors(G_dict, theta_ij)
                remove_nodes_in_list(ans_ij, lamda)
                #print("Ans nodes:", ans_ij)

                for ij in ans_ij:
                    ans_int = I_dict[ij]
                    for ijij in ans_int:
                        if ijij in int_ij:
                            int_ij.remove(ijij)
                #print("Int nodes:", int_ij)

                I_dict[theta_ij] = int_ij

                int_c_sum = sum(C_dict[ij] for ij in con_ij)
                interference = math.ceil(1.0 / (m-1) * int_c_sum)

            # find the max finish time of all its predecences
            f_ij_pre_max = 0

            predecsor_of_ij = find_predecesor(G_dict, theta_ij)
            for pre_i in predecsor_of_ij:
                if f_dict[pre_i] > f_ij_pre_max:
                    f_ij_pre_max = f_dict[pre_i]

            # calculate the finish time
            f_ij = C_dict[theta_ij] + f_ij_pre_max + interference
            f_dict[theta_ij] = f_ij

            # find max(f_vj)
            if f_ij > f_v_j_max:
                f_v_j_max = f_ij
                f_v_j_max_idx = theta_ij
        
        R_i_m_minus_one = f_v_j_max

        # start to calculate the response time of provider i
        Wi_nc = sum(C_dict[ij] for ij in theta_i)
        Li = sum(C_dict[ij] for ij in theta_i_star)
        Wi = Wi_nc + Li 

        # --------------------------------------------------------------------------
        # IV. bound alpha and beta
        # For Case A (has no delay to the critical path):
        if (R_i_m_minus_one <= f_theta_i_star):
            print("** Case A **")
            alpha_i = Wi_nc
            beta_i = 0

        # For Case B (has delay to the critical path):
        else:
            print("** Case B **")

            # search for lamda_ve
            ve = f_v_j_max_idx  # end node & backward search
            lamda_ve = [ve]
            len_lamda_ve = C_dict[ve]

            while True:
                # find pre of ve
                pre_of_ve = find_predecesor(G_dict, ve)  # pre_of_ve can be empty!

                # only care about those within this provider
                for ij in pre_of_ve.copy():
                    if ij not in theta_i:
                        pre_of_ve.remove(ij)

                if pre_of_ve:
                    # calculate the finish times, and the maximum
                    f_pre_of_ve = []
                    for ij in pre_of_ve:
                        f_pre_of_ve.append(f_dict[ij])

                    max_value = max(f_pre_of_ve)
                    max_index = f_pre_of_ve.index(max_value)

                    if max_value > f_theta_i_star:
                        ve = pre_of_ve[max_index]
                        lamda_ve.append(ve)
                        len_lamda_ve = len_lamda_ve + C_dict[ve]
                    else:
                        break
                else:
                    break

            print("Lamda Ve:", lamda_ve, "Len:", len_lamda_ve)

            # beta_i
            beta_i = min(R_i_m_minus_one - f_theta_i_star, len_lamda_ve)

            # alpha (a): find alpha by estimation of finish times
            alpha_hat_class_a = []
            alpha_hat_class_b = []

            for _, theta_ij in enumerate(theta_i):
                if f_dict[theta_ij] <= f_theta_i_star:
                    alpha_hat_class_a.append(theta_ij)
                elif f_dict[theta_ij] < f_theta_i_star + C_dict[theta_ij]:
                    alpha_hat_class_b.append(theta_ij)
                else:
                    pass

            print("A:", alpha_hat_class_a, "B:", alpha_hat_class_b)

            alpha_i_hat = sum(C_dict[ij] for ij in alpha_hat_class_a) + \
                          sum(f_theta_i_star - (f_dict[ij] - C_dict[ij]) for ij in alpha_hat_class_b)
            

            # alpha case (b): find alpha by approximation

            # find the m - 1 longest path and their finish times within the provider



            # calculate the finish time on m cores



            # calculate f_delta = sum(f_ve - f_theta)
            f_delta = 0







            # approxiation of alpha
            alpha_i_new = Wi - Li - f_delta

            # alpha_i is the max of the two
            alpha_i = max(alpha_i_hat, alpha_i_new)
        
        # calculate the response time based on alpha_i and beta_i
        Ri = Li + math.ceil( 1.0 / m * (Wi - Li - max(alpha_i - (m-1) * beta_i, 0)) )
        print("Ri:", Ri)

        R_i_minus_one = R_i_minus_one + Ri
        print("Ri-1: ", R_i_minus_one)

        alpha_arr.append(alpha_i)
        beta_arr.append(beta_i)

    R = R_i_minus_one

    return R, alpha_arr, beta_arr


if __name__ == "__main__":
    task_idx = 9; m = 4 # (2, 4, 8, 16)

    R0 = rta_classic(task_idx, m)
    R, alpha, beta = rta_new_v2(task_idx, m)
    print("R0 = {}".format(R0))
    print("R1 = {}, alpha = {}, beta = {}".format(R, alpha, beta))
