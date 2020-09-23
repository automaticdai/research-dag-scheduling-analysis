import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle
from operator import itemgetter
import time, datetime

from tqdm import tqdm
import networkx as nx
import copy

from graph import find_longest_path_dfs, find_predecesor, find_successor, find_ancestors, find_descendants, get_subpath_between
from bisect import bisect_left

TASKSET_TO_EVALUATE = 10
A_VERY_LARGE_NUMBER = 1000000

def print_debug(*args, **kw):
    #print(args)
    pass


dag_base_folder = "data/data-generic/"
L_ratio = -1
def load_task(task_idx):
    # << load DAG task <<
    dag_task_file = dag_base_folder + "Tau_{:d}.gpickle".format(task_idx)

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
    C_array = []
    for key in sorted(C_dict):
        C_array.append(C_dict[key])

    V_array.sort()
    L, lamda = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_array)
    W = sum(C_array)

    VN_array = V_array.copy()

    for i in lamda:
        if i in VN_array:
            VN_array.remove(i)

    # scale L (the length of the critical path)
    if L_ratio != -1:
        # print("Old L ratio:", L * 1.0 / W)

        L_old = L
        vol_old = W - L

        L_new = L_ratio * W
        vol_new = (1 - L_ratio) * W

        L_multiplier = L_new / L_old

        L = 0
        for i in lamda:
            C_dict[i] = max(round(C_dict[i] * L_multiplier), 1)
            L = L + C_dict[i] 

        vol_multiplier = vol_new / vol_old
        for i in VN_array:
            C_dict[i] = max(round(C_dict[i] * vol_multiplier), 1)

        # formulate the c list (c[0] is c for v1!!)
        C_array = []
        for key in sorted(C_dict):
            C_array.append(C_dict[key])

        # check critical path!!!!
        L_prime, lamda_prime = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_array)

        if lamda_prime != lamda or L_prime != L:
            raise Exception("Lambda does not hold!")

    # >> end of load DAG task >>
    return G_dict, C_dict, C_array, lamda, VN_array, L, W


def load_taskset_metadata(dag_base_folder):
    number_of_tasks_in_set = 10
    Taskset = {}

    aTau = []
    aT = []
    aC = []

    for task_idx in range(number_of_tasks_in_set):
        # << load DAG task <<
        dag_task_file = dag_base_folder + "/Tau_{:d}.gpickle".format(task_idx)

        # task is saved as NetworkX gpickle format
        G = nx.read_gpickle(dag_task_file)

        Ti = G.graph["T"]
        Wi = G.graph["W"]
        Ui = G.graph["U"]
    
        ############################################################################
        # assign priorities according to RMPO / DMPO
        idx = bisect_left(aT, Ti)

        aTau.insert(idx, task_idx)
        aT.insert(idx, Ti)
        aC.insert(idx, Wi)

    for i, task_idx in enumerate(aTau):
        Taskset[i] = {}
        Taskset[i]["tau"] = aTau[i]
        Taskset[i]["T"] = aT[i]
        Taskset[i]["C"] = aC[i]

    return Taskset


def remove_nodes_in_list(nodes, nodes_to_remove):
    for i in nodes.copy():
        if i in nodes_to_remove:
            nodes.remove(i)


def get_nodes_volume(nodes, C_list):
    ''' sum of workload
    nodes can be individual nodes or from a path
    '''
    volume = 0

    for i in nodes:
        volume = volume + C_list[i]
    
    return volume


def remove_nodes_in_graph(G, nodes):
    ''' remove nodes (and its related edges) from a graph
    '''
    for key, value in G.copy().items():
        if key in nodes:
            G.pop(key)
        else:
            for v in value:
                if v in nodes:
                    value.remove(v)


################################################################################
################################################################################
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

    # start to iterative delta
    delta = 0
    node_left = node.copy()

    while node_left:
        # this search is limited to node, 
        # so all keys and values that do not contain node_left will be removed
        G_new = copy.deepcopy(G)

        for key, value in G_new.copy().items():
            if key not in node_left:
                del G_new[key]
            else:
                value_new = value.copy()
                for j in value:
                    if j not in node_left:
                        value_new.remove(j)
                
                G_new[key] = value_new
        
        delta = delta + 1
        if delta >= n:
            #print_debug("PARALLISM: False")
            return False

        finished = False
        while not finished:
            for ve in node_left.copy():
                if find_predecesor(G_new, ve) == []:
                    node_left.remove(ve)
                    finished = True
                    break

        suc_ve = find_successor(G_new, ve)
        while suc_ve:
            suc_ve_first = suc_ve[0]
            if suc_ve_first in node_left:
                node_left.remove(suc_ve_first)
            suc_ve = find_successor(G_new, suc_ve_first)

    #print_debug("PARALLISM: True")
    return True


def find_providers_consumers(G_dict, lamda, VN_array):
    """ Find providers and consumers
    """
    providers = []
    consumers = []

    new_provider = []
    nc_nodes_left = VN_array.copy()
    for key, i in enumerate(lamda):
        if new_provider == []:
            new_provider = [i]

        if ((key+1) < len(lamda)):
            pre_nodes = find_predecesor(G_dict, lamda[key+1])

            #print_debug("Checking: ", i, "Pre: ", pre_nodes)
            if pre_nodes == [i]:    
                new_provider.append(lamda[key+1])
            else:
                #print_debug("New provider:", new_provider)
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

                        #print_debug(ancestors_of_node)

                new_consumer.sort()
                consumers.append(new_consumer)

                # remove from NC list
                for i_nc in new_consumer:
                    nc_nodes_left.remove(i_nc)

                new_consumer = []
        else:
            # the last node needs special care as it has no successors
            #print_debug("New provider:", new_provider)
            providers.append(new_provider)

            # find all consumers (all the left nc nodes)
            nc_nodes_left.sort()
            consumers.append(nc_nodes_left)

    return providers, consumers


def find_G_theta_i_star(G, providers, consumers, i):
    G_theta_i_star = []

    # collect all consumer nodes in the following providers
    number_of_providers = len(providers) 
    if i == number_of_providers - 1:
        # skip as this is the last provider
        return []

    theta_i = consumers[i]


    all_later_consumer_nodes = []
    for l in range(i + 1, number_of_providers):
        for k in consumers[l]:
            all_later_consumer_nodes.append(k)



    for theta_ij in theta_i:
        con_ij = find_concurrent_nodes(G, theta_ij)

        for k in con_ij:
            if k in all_later_consumer_nodes:
                if k not in G_theta_i_star:
                    G_theta_i_star.append(k)

    return G_theta_i_star


def rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=False):
    """ Response time analysis using alpha_beta
    """
    # --------------------------------------------------------------------------
    # I. load the DAG task
    G_dict, C_dict, C_array, lamda, VN_array, L, W = load_task(task_idx)

    # --------------------------------------------------------------------------
    # II. providers and consumers
    # iterative all critical nodes
    # after this, all provides and consumers will be collected
    providers, consumers = find_providers_consumers(G_dict, lamda, VN_array)
    print_debug("Providers:", providers)
    print_debug("Consumers:", consumers)

    # --------------------------------------------------------------------------
    # III. calculate the finish times of each provider, and the consumers within
    f_dict = {}        # the set of all finish times
    I_dict = {}        # interference workload
    I_e_dict = {}      # interference workload (for EO)
    R_i_minus_one = 0  # the response time of the previous provider theta^*_(i - 1)

    alpha_arr = []
    beta_arr = []

    if EOPA:
        Prio = Eligiblity_Ordering_PA(G_dict, C_dict)
        print_debug("Prioirties", Prio)
    elif TPDS:
        Prio = TPDS_Ordering_PA(G_dict, C_dict)
        # reverse the order
        for i in Prio:
            Prio[i] = A_VERY_LARGE_NUMBER - Prio[i]
        print_debug("Prioirties", Prio)

    # ==========================================================================
    # iteratives all providers (first time, to get all finish times)
    for i, theta_i_star in enumerate(providers):
        print_debug("- - - - - - - - - - - - - - - - - - - -")
        print_debug("theta(*)", i, ":", theta_i_star)
        print_debug("theta", i, ":", consumers[i])  

        # get the finish time of all provider nodes (in provider i)
        for _, provi_i in enumerate(theta_i_star):
            # (skipped) sort with topoligical order, skipped because guaranteed by the generator
            # find the max finish time of all its predecences
            f_provider_i_pre_max = 0

            predecsor_of_ij = find_predecesor(G_dict, provi_i)
            for pre_i in predecsor_of_ij:
                if f_dict[pre_i] > f_provider_i_pre_max:
                    f_provider_i_pre_max = f_dict[pre_i]

            f_i = C_dict[provi_i] + f_provider_i_pre_max

            f_dict[provi_i] = f_i
            f_theta_i_star = f_i # finish time of theta_i_star. every loop refreshes this
        
        # iteratives all consumers
        # (skipped) topoligical order, skipped because guaranteed by the generator
        # note: consumer can be empty
        theta_i = consumers[i]
        f_v_j_max = 0; f_v_j_max_idx = -1
        for _, theta_ij in enumerate(theta_i):
            # the interference term
            con_nc_ij = find_concurrent_nodes(G_dict, theta_ij)
            remove_nodes_in_list(con_nc_ij, lamda)
            if test_parallelism(G_dict, con_nc_ij, m - 1):
                # sufficient parallism
                interference = 0
                I_dict[theta_ij] = []
                I_e_dict[theta_ij] = []
            else:
                # not enough cores
                # start to search interference nodes >>>
                # concurrent nodes of ij. Can be empty.
                con_ij = find_concurrent_nodes(G_dict, theta_ij)
                #print_debug("Con nodes:", con_ij)

                int_ij = con_ij.copy()
                remove_nodes_in_list(int_ij, lamda)

                ans_ij = find_ancestors(G_dict, theta_ij, path=[])
                remove_nodes_in_list(ans_ij, lamda)
                #print_debug("Ans nodes:", ans_ij)

                for ij in ans_ij:
                    ans_int = I_dict[ij]
                    for ijij in ans_int:
                        if ijij in int_ij:
                            int_ij.remove(ijij)
                #print_debug("Int nodes:", int_ij)

                I_dict[theta_ij] = int_ij
                

                if EOPA or TPDS:
                    # for EOPA, only the (m - 1) longest lower priority interference node is kept
                    int_ij_EO = []
                    int_ij_EO_less_candidates = []
                    int_ij_EO_less_candidates_C = []

                    if int_ij:
                        for int_ij_k in int_ij:
                            if Prio[int_ij_k] > Prio[theta_ij]:
                                # E_k > E_i, add with confidence
                                int_ij_EO.append(int_ij_k)
                            else:
                                # E_k < E_i, put into a list and later will only get longest m - 1
                                int_ij_EO_less_candidates.append( int_ij_k )
                                int_ij_EO_less_candidates_C.append( C_dict[int_ij_k] )

                        # sort nodes by C (if it exists), and append (m-1) longest to int_ij_EO
                        if int_ij_EO_less_candidates:
                            list_of_less_EO_nodes_C = int_ij_EO_less_candidates_C
                            indices, _ = zip(*sorted(enumerate(list_of_less_EO_nodes_C), key=itemgetter(1), reverse=True))
                            #indices = [i[0] for i in sorted(enumerate(list_of_less_EO_nodes_C), key=lambda x:x[1])]
                            int_ij_EO_less_candidates_sorted = []

                            for idx_ in range(len(list_of_less_EO_nodes_C)):
                                int_ij_EO_less_candidates_sorted.append(int_ij_EO_less_candidates[indices[idx_]])

                            # adding (m - 1) lower EO nodes
                            for xxx in range(1, m):
                                if len(int_ij_EO_less_candidates) >= xxx:
                                    int_ij_EO.append( int_ij_EO_less_candidates_sorted[xxx - 1] )

                        int_ij = int_ij_EO.copy()
                
                    I_e_dict[theta_ij] = int_ij
                # >>> end of searching interference nodes

                int_c_sum = sum(C_dict[ij] for ij in int_ij)
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
            print_debug("f_theta({}) : {}".format(theta_ij, f_dict[theta_ij]))



    # ==========================================================================
    # iteratives all providers (2nd time)
    # the finish times of provider nodes have to be calculated again to get f_theta_i_star
    # the finish times of consumer nodes have to be calculated again to get lambda_ve
    for i, theta_i_star in enumerate(providers):
        print_debug("- - - - - - - - - - - - - - - - - - - -")
        print_debug("theta(*)", i, ":", theta_i_star)
        print_debug("theta", i, ":", consumers[i])  

        # get the finish time of all provider nodes (in provider i)
        for _, provi_i in enumerate(theta_i_star):
            # (skipped) sort with topoligical order, skipped because guaranteed by the generator
            # find the max finish time of all its predecences
            f_provider_i_pre_max = 0

            predecsor_of_ij = find_predecesor(G_dict, provi_i)
            for pre_i in predecsor_of_ij:
                if f_dict[pre_i] > f_provider_i_pre_max:
                    f_provider_i_pre_max = f_dict[pre_i]

            f_i = C_dict[provi_i] + f_provider_i_pre_max

            f_dict[provi_i] = f_i
            f_theta_i_star = f_i # finish time of theta_i_star. every loop refreshes this
        
        print_debug("finish time of theta(*)", f_theta_i_star)

        # iteratives all consumers
        # (skipped) topoligical order, skipped because guaranteed by the generator
        # note: consumer can be empty
        theta_i = consumers[i]
        f_v_j_max = 0; f_v_j_max_idx = -1
        for _, theta_ij in enumerate(theta_i):
            print_debug(theta_ij, ":", C_dict[theta_ij])
            
            # the interference term
            con_nc_ij = find_concurrent_nodes(G_dict, theta_ij)
            remove_nodes_in_list(con_nc_ij, lamda)
            if test_parallelism(G_dict, con_nc_ij, m - 1):
                # sufficient parallism
                interference = 0
                I_dict[theta_ij] = []
                I_e_dict[theta_ij] = []
            else:
                # not enough cores
                # start to search interference nodes >>>
                # concurrent nodes of ij. Can be empty.
                con_ij = find_concurrent_nodes(G_dict, theta_ij)
                #print_debug("Con nodes:", con_ij)

                int_ij = con_ij.copy()
                remove_nodes_in_list(int_ij, lamda)

                ans_ij = find_ancestors(G_dict, theta_ij, path=[])
                remove_nodes_in_list(ans_ij, lamda)
                #print_debug("Ans nodes:", ans_ij)

                for ij in ans_ij:
                    ans_int = I_dict[ij]
                    for ijij in ans_int:
                        if ijij in int_ij:
                            int_ij.remove(ijij)
                #print_debug("Int nodes:", int_ij)

                I_dict[theta_ij] = int_ij


                if EOPA or TPDS:
                    # for EOPA, only the (m - 1) longest lower priority interference node is kept
                    int_ij_EO = []
                    int_ij_EO_less_candidates = []
                    int_ij_EO_less_candidates_C = []

                    if int_ij:
                        for int_ij_k in int_ij:
                            if Prio[int_ij_k] > Prio[theta_ij]:
                                # E_k > E_i, add with confidence
                                int_ij_EO.append(int_ij_k)
                            else:
                                # E_k < E_i, put into a list and later will only get longest m - 1
                                int_ij_EO_less_candidates.append( int_ij_k )
                                int_ij_EO_less_candidates_C.append( C_dict[int_ij_k] )

                        # sort nodes by C (if it exists), and append (m-1) longest to int_ij_EO
                        if int_ij_EO_less_candidates:
                            list_of_less_EO_nodes_C = int_ij_EO_less_candidates_C
                            indices, _ = zip(*sorted(enumerate(list_of_less_EO_nodes_C), key=itemgetter(1), reverse=True))
                            #indices = [i[0] for i in sorted(enumerate(list_of_less_EO_nodes_C), key=lambda x:x[1])]
                            int_ij_EO_less_candidates_sorted = []

                            for idx_ in range(len(list_of_less_EO_nodes_C)):
                                int_ij_EO_less_candidates_sorted.append(int_ij_EO_less_candidates[indices[idx_]])

                            # adding (m - 1) lower EO nodes
                            for xxx in range(1, m):
                                if len(int_ij_EO_less_candidates) >= xxx:
                                    int_ij_EO.append( int_ij_EO_less_candidates_sorted[xxx - 1] )

                        int_ij = int_ij_EO.copy()

                    I_e_dict[theta_ij] = int_ij
                # >>> end of searching interference nodes

                int_c_sum = sum(C_dict[ij] for ij in int_ij)
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
            print_debug("f_theta({}) : {}".format(theta_ij, f_dict[theta_ij]))

            # find max(f_vj)
            if f_ij > f_v_j_max:
                f_v_j_max = f_ij
                f_v_j_max_idx = theta_ij
        
        # --------------------------------------------------------------------------
        # start to calculate the response time of provider i
        Wi_nc = sum(C_dict[ij] for ij in theta_i)
        Li = sum(C_dict[ij] for ij in theta_i_star)
        Wi = Wi_nc + Li 


        if not EOPA and not TPDS:
            # G(theta_i^*) needs to be added for random
            # Wi and Wi_nc will be updated
            G_theta_i_star = find_G_theta_i_star(G_dict, providers, consumers, i)

            Wi_G = sum(C_dict[ij] for ij in G_theta_i_star)
            Wi_nc = Wi_nc + Wi_G
            Wi = Wi_nc + Li

        # --------------------------------------------------------------------------
        # IV. bound alpha and beta
        # For Case A (has no delay to the critical path):
        if (f_theta_i_star >= f_v_j_max):
            print_debug("** Case A **")
            alpha_i = Wi_nc
            beta_i = 0
        # For Case B (has delay to the critical path):
        else:
            print_debug("** Case B **")
            # search for lamda_ve
            ve = f_v_j_max_idx  # end node & backward search
            lamda_ve = [ve]
            len_lamda_ve = 0

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
                    else:
                        break
                else:
                    break

            # calculate accmulative intererence
            for ve_i in lamda_ve:
                if f_dict[ve_i] - C_dict[ve_i] >= f_theta_i_star:
                    len_lamda_ve = len_lamda_ve + C_dict[ve_i]
                else:
                    len_lamda_ve = len_lamda_ve + max((f_dict[ve_i] - f_theta_i_star), 0)
            
            print_debug("lamda_ve:", lamda_ve, "len:", len_lamda_ve)

            # beta_i
            beta_i = len_lamda_ve

            # alpha (a): find alpha by estimation of finish times
            alpha_hat_class_a = []
            alpha_hat_class_b = []

            for _, theta_ij in enumerate(theta_i):
                if f_dict[theta_ij] <= f_theta_i_star:
                    if theta_ij not in alpha_hat_class_a:
                        alpha_hat_class_a.append(theta_ij)
                elif f_dict[theta_ij] < f_theta_i_star + C_dict[theta_ij]:
                    if theta_ij not in alpha_hat_class_b:
                        alpha_hat_class_b.append(theta_ij)
                else:
                    pass

            if not EOPA and not TPDS:
                # for random, the alpha_i is different
                for _, theta_ij in enumerate(G_theta_i_star):
                    if f_dict[theta_ij] <= f_theta_i_star:
                        if theta_ij not in alpha_hat_class_a:
                            alpha_hat_class_a.append(theta_ij)
                    elif f_dict[theta_ij] < f_theta_i_star + C_dict[theta_ij]:
                        if theta_ij not in alpha_hat_class_b:
                            alpha_hat_class_b.append(theta_ij)
                    else:
                        pass

            print_debug("A:", alpha_hat_class_a, "B:", alpha_hat_class_b)

            alpha_i_hat = sum(C_dict[ij] for ij in alpha_hat_class_a) + \
                            sum(f_theta_i_star - (f_dict[ij] - C_dict[ij]) for ij in alpha_hat_class_b)
            

            # # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # # alpha case (b): find alpha by approximation
            # theta_i_llen = theta_i.copy()
            # llen_i = {}
            # len_llen_i = {}

            # # find the m - 1 longest path and their finish times within the provider
            # # n = 1, m - 1
            # for n in range(1, m):
            #     # no more candidates, searching is finished
            #     if theta_i_llen == []:
            #         llen_i[n] = []
            #         len_llen_i[n] = 0
            #         continue

            #     f_theta_i_llen = []

            #     for ij in theta_i_llen:
            #         f_theta_i_llen.append(f_dict[ij])

            #     max_value = max(f_theta_i_llen)
            #     max_index = f_theta_i_llen.index(max_value)
            #     ve = theta_i_llen[max_index]

            #     # find the path (backward search)
            #     llen_ij = [ve]
            #     len_llen_ij = C_dict[ve]

            #     while(True):
            #         pre_of_ij = find_predecesor(G_dict, ve)
            #         for ij in pre_of_ij:
            #             if ij not in theta_i:
            #                 pre_of_ij.remove(ij)

            #         if pre_of_ij:
            #             # find the maximum finish time, within the provider
            #             f_pre_of_ij = []
            #             for ij in pre_of_ij:
            #                 f_pre_of_ij.append(f_dict[ij])

            #             max_value = max(f_pre_of_ij)
            #             max_index = f_pre_of_ij.index(max_value)

            #             if max_value > f_theta_i_star:
            #                 ve = pre_of_ij[max_index]
            #                 llen_ij.append(ve)
            #                 len_llen_ij = len_llen_ij + C_dict[ve]
            #             else:
            #                 break
            #         else:
            #             break

            #     # remove the nodes in the path from theta_i_llen
            #     for ij in llen_ij:
            #         if ij in theta_i_llen:
            #             theta_i_llen.remove(ij)
                
            #     # save the llen_ij
            #     llen_i[n] = llen_ij
            #     len_llen_i[n] = len_llen_ij

            # # update the finish time of nodes in len_i
            # U_llen = []
            # for key in llen_i:
            #     if llen_i[key]:
            #         # topological sort, to ensure finish time is calculated in the right order
            #         llen_i[key].sort()

            #         # update the UNION(llen(k))
            #         for theta_ij in llen_i[key]:
            #             U_llen.append(theta_ij)

            #         # iterative all nodes in the (key)th longest path
            #         for theta_ij in llen_i[key]:
            #             # the interference term
            #             con_nc_ij = find_concurrent_nodes(G_dict, theta_ij)
            #             remove_nodes_in_list(con_nc_ij, lamda)
            #             if test_parallelism(G_dict, con_nc_ij, m - 1):
            #                 # sufficient parallism
            #                 interference = 0
            #             else:
            #                 # not enough cores
            #                 # start to search interference nodes >>>
            #                 # concurrent nodes of ij. Can be empty.
            #                 con_ij = find_concurrent_nodes(G_dict, theta_ij)
            #                 #print_debug("Con nodes:", con_ij)

            #                 int_ij = con_ij.copy()
            #                 remove_nodes_in_list(int_ij, lamda)

            #                 ans_ij = find_ancestors(G_dict, theta_ij, path=[])
            #                 remove_nodes_in_list(ans_ij, lamda)
            #                 #print_debug("Ans nodes:", ans_ij)

            #                 for ij in ans_ij:
            #                     ans_int = I_dict[ij]
            #                     for ijij in ans_int:
            #                         if ijij in int_ij:
            #                             int_ij.remove(ijij)
            #                 #print_debug("Int nodes:", int_ij)

            #                 I_dict[theta_ij] = int_ij
            #                 # >>> end of searching interference nodes

            #                 # one more step: remove all Union(llen(k))
            #                 for ij in U_llen:
            #                     if ij in int_ij:
            #                         int_ij.remove(ij)

            #                 int_c_sum = sum(C_dict[ij] for ij in int_ij)
            #                 interference = math.ceil(1.0 / (m-1) * int_c_sum)

            #             # find the max finish time of all its predecences
            #             f_ij_pre_max = 0

            #             predecsor_of_ij = find_predecesor(G_dict, theta_ij)
            #             for pre_i in predecsor_of_ij:
            #                 if f_dict[pre_i] > f_ij_pre_max:
            #                     f_ij_pre_max = f_dict[pre_i]

            #             # calculate the finish time
            #             f_ij = C_dict[theta_ij] + f_ij_pre_max + interference

            #             print_debug("Finish time of {:} updated from {:} to {:}".format(theta_ij, f_dict[theta_ij], f_ij))
            #             f_dict[theta_ij] = f_ij

            # # calculate f_delta = sum[(f_ve - f_theta_i_star)]0
            # f_delta_sum = 0
            # for iii_f in range(1, m):
            #     if llen_i[iii_f]:
            #         llen_i_ve = llen_i[iii_f][-1]
            #         f_delta = max(f_dict[llen_i_ve] - f_theta_i_star, 0)
            #         f_delta_sum = f_delta_sum + f_delta
            #     else:
            #         pass
            # # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

            # approxiation of alpha
            # (!) note: alpha_i_new is removed as it is unsafe
            #alpha_i_new = Wi - Li - f_delta_sum
            alpha_i_new = 0

            # alpha_i is the max of the two
            alpha_i = max(alpha_i_hat, alpha_i_new)
        
        if not EOPA and not TPDS:
            # RTA-CFP
            # calculate the response time based on alpha_i and beta_i
            Ri = Li + beta_i + math.ceil(1.0 / m * (Wi - Li - alpha_i - beta_i))
            # this improved is to bound Ri to be better than classic bound
            #Ri = Li + math.ceil(1.0 / m * (Wi - Li - max(alpha_i - (m-1) * beta_i, 0)))
        else:
            # RTA-CFP + EOPA
            if beta_i == 0:
                Ri = Li
            else:
                I_e_lambda_ve = []
                I_e_lambda_ve_candidates = []
                I_e_lambda_ve_candidates_I = []

                len_I_lambda_ve = {}

                # I_lambda_ve calculation
                for v_k in lamda_ve:
                    I_v_k = I_dict[v_k]

                    for v_j in I_v_k:
                        if f_dict[v_j] > f_theta_i_star:
                            if Prio[v_j] > Prio[v_k]:
                                # E_k > E_i, add with confidence
                                I_e_lambda_ve.append(v_j)

                                if f_dict[v_j] - C_dict[v_j] >= f_theta_i_star:
                                    I_lambda_ve_j = C_dict[v_j]
                                else:
                                    I_lambda_ve_j = f_dict[v_j] - f_theta_i_star
                                
                                len_I_lambda_ve[v_j] = I_lambda_ve_j
                            else:
                                # E_k < E_i, put into a list and later will only get longest m - 1
                                I_e_lambda_ve_candidates.append(v_j)

                                # get I_lambda_ve_j
                                if f_dict[v_j] - C_dict[v_j] >= f_theta_i_star:
                                    I_lambda_ve_j = C_dict[v_j]
                                else:
                                    I_lambda_ve_j = f_dict[v_j] - f_theta_i_star

                                I_e_lambda_ve_candidates_I.append(I_lambda_ve_j)

                                len_I_lambda_ve[v_j] = I_lambda_ve_j
                
                # sort nodes by I (if it exists), and append (m-1) longest to int_ij_EO
                if I_e_lambda_ve_candidates:
                    indices, _ = zip(*sorted(enumerate(I_e_lambda_ve_candidates_I), key=itemgetter(1), reverse=True))
                    I_e_lambda_ve_candidates_sorted = []

                    for idx_ in range(len(I_e_lambda_ve_candidates_I)):
                        I_e_lambda_ve_candidates_sorted.append(I_e_lambda_ve_candidates[indices[idx_]])

                    # adding (m) lower EO nodes
                    for xxx in range(1, m+1):
                        if len(I_e_lambda_ve_candidates) >= xxx:
                            I_e_lambda_ve.append(I_e_lambda_ve_candidates_sorted[xxx - 1])

                # test parallelism of I_lambda_ve
                if test_parallelism(G_dict, I_e_lambda_ve, m):
                    I_term_for_EO = 0
                else:
                    # calculate I_ve
                    I_ve = 0

                    for v_j in I_e_lambda_ve:
                        len_I_lambda_ve_j = len_I_lambda_ve[v_j]
                        I_ve = I_ve + len_I_lambda_ve_j


                    I_term_for_EO = math.ceil(1.0 / m * I_ve)

                    # check: I_ve should <= (Wi - Li - alpha_i - beta_i)
                    #print_debug("(DEBUG) Wi - Li - alpha_i - beta_i: {}".format( Wi - Li - alpha_i - beta_i ))
                    #print_debug("(DEBUG) I_ve: {}".format( I_ve ))

                Ri = Li + beta_i + I_term_for_EO

        print_debug("R_i:", Ri)

        R_i_minus_one = R_i_minus_one + Ri
        print_debug("R_sum: ", R_i_minus_one)

        alpha_arr.append(alpha_i)
        beta_arr.append(beta_i)

    R = R_i_minus_one


    # bound R to the classic bound
    # if not EOPA and not TPDS:
    #     R_classic = rta_np_classic(task_idx, m)
    #     R = min(R, R_classic)


    return R, alpha_arr, beta_arr


def EO_Compute_Length(G, C):
    lf = {}
    lb = {}
    l = {}

    # topological ordering
    # (skipped as this is guaranteed by the generator)
    G_new = copy.deepcopy(G)
    theta_i = G_new.keys()
    
    for theta_ij in theta_i:
        # calculate the length
        C_i = C[theta_ij]

        # forward searching in G_new
        lf_i = C_i

        pre_ij = find_predecesor(G_new, theta_ij)
        while pre_ij:
            max_c = 0
            max_v = -1
            for idx in pre_ij:
                if C[idx] > max_c:
                    max_c = C[idx]
                    max_v = idx
            
            lf_i = lf_i + max_c
            ve = max_v
            pre_ij = find_predecesor(G_new, ve)

        # backward searching in G_new
        lb_i = C_i

        suc_ij = find_successor(G_new, theta_ij)
        while suc_ij:
            max_c = 0
            max_v = -1
            for idx in suc_ij:
                if C[idx] > max_c:
                    max_c = C[idx]
                    max_v = idx
            
            lb_i = lb_i + max_c
            ve = max_v
            suc_ij = find_successor(G_new, ve)

        # calculate l
        l_i = lf_i + lb_i - C_i
        
        # assign to length
        l[theta_ij] = l_i
        lf[theta_ij] = lf_i
        lb[theta_ij] = lb_i

    return l, lf, lb


e = A_VERY_LARGE_NUMBER # this has to be global, or be passed by reference

def EO_iter(G_dict, C_dict, providers, consumers, Prio):
    global e
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    nodes = []
    for theta_star_i in providers:
        for theta_star_ij in theta_star_i:
            nodes.append(theta_star_ij)

    for theta_i in consumers:
        for theta_ij in theta_i:
            nodes.append(theta_ij)

    for iii in nodes:
        if Prio[iii] != -1:
            raise Exception("Some prioirities are already assigned!")
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    for theta_star_i in providers:
        for i in theta_star_i:
            Prio[i] = e
    
    e = e - 1

    for i, theta_star_i in enumerate(providers):
        theta_i = consumers[i]
        while theta_i:
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            for iii in theta_i:
                if Prio[iii] != -1:
                    raise Exception("Some prioirities are already assigned!")
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

            # --------------------------------------------------------------------------
            # build up a new (temporal) DAG with only the consumers
            G_new = copy.deepcopy(G_dict)
            for key, value in copy.deepcopy(G_new).items():
                if (key not in theta_i):
                    del G_new[key]
                else:
                    value_new = value.copy()
                    for j in value:
                        if (j not in theta_i):
                            value_new.remove(j)
                    G_new[key] = value_new

            # --------------------------------------------------------------------------
            # find the longest local path in theta_i
            # find l(v_i)
            l, lf, lb = EO_Compute_Length(G_new, C_dict)

            lamda_ve = []

            # find ve
            ve = -1
            l_max = -1
            for theta_ij in theta_i:
                if not find_successor(G_new, theta_ij):
                    if l[theta_ij] > l_max:
                        l_max = l[theta_ij]
                        ve = theta_ij

            # found ve, then found lamda_ve
            if ve != -1:
                lamda_ve.append(ve)
                pre_ve = find_predecesor(G_new, ve)
                while pre_ve:
                    ve = -1
                    l_max = -1
                    for theta_ij in pre_ve:
                        # if not find_predecesor(G_new, theta_ij):
                        if l[theta_ij] > l_max:
                            l_max = l[theta_ij]
                            ve = theta_ij
                    if ve != -1:
                        lamda_ve.append(ve)
                    pre_ve = find_predecesor(G_new, ve)

            # find an existed vj
            found_vj = False
            lamda_ve.sort()
            for vj in lamda_ve:
                pre_vj = find_predecesor(G_new, vj)
                if len(pre_vj) > 1:
                    found_vj = True

            if found_vj:
                # update VN_array
                V_array = list(copy.deepcopy(G_new).keys())
                V_array.sort()
                VN_array = V_array.copy()
                for lamda_ve_i in lamda_ve:
                    VN_array.remove(lamda_ve_i)
                
                # find new providers and consumers
                providers_new, consumers_new = find_providers_consumers(G_new, lamda_ve, VN_array)
                EO_iter(G_new, C_dict, providers_new, consumers_new, Prio)
                break
            else:
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                for vjjj in lamda_ve:
                    if Prio[vjjj] != -1:
                        pass
                        #raise Exception("Priority abnormal!")
                # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                
                for vj in lamda_ve:
                    Prio[vj] = e; e = e - 1

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                for vjjj in lamda_ve:
                    if Prio[vjjj] <= 0:
                        pass
                        #raise Exception("Priority abnormal!")
                # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

                remove_nodes_in_list(theta_i, lamda_ve)


def Eligiblity_Ordering_PA(G_dict, C_dict):

    Prio = {}
    
    # --------------------------------------------------------------------------
    # I. load task parameters
    C_exp = []
    for key in sorted(C_dict):
        C_exp.append(C_dict[key])

    V_array = list(copy.deepcopy(G_dict).keys())
    V_array.sort()
    _, lamda = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_exp)

    VN_array = V_array.copy()

    for i in lamda:
        if i in VN_array:
            VN_array.remove(i)

    # --------------------------------------------------------------------------
    # II. initialize eligbilities to -1
    for i in G_dict:
        Prio[i] = -1

    # --------------------------------------------------------------------------
    # III. providers and consumers
    # iterative all critical nodes
    # after this, all provides and consumers will be collected
    providers, consumers = find_providers_consumers(G_dict, lamda, VN_array)

    # --------------------------------------------------------------------------
    # IV. Start iteration
    # >> for time measurement
    global time_diff
    begin_time = time.time()
    # << for time measurement

    EO_iter(G_dict, C_dict, providers, consumers, Prio)

    # >> for time measurement
    time_diff = time.time() - begin_time
    # << for time measurement

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    for i in Prio:
        if Prio[i] <= 1:
            raise Exception("Some prioirities are not assigned!")
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    return Prio


def Eligiblity_Ordering_PA_legacy(G_dict, C_dict):
    """ The Eligibility Ordering priority assignment
    """
    Prio = {}
    E_MAX = A_VERY_LARGE_NUMBER

    # --------------------------------------------------------------------------
    # I. load task parameters
    C_exp = []
    for key in sorted(C_dict):
        C_exp.append(C_dict[key])

    V_array = list(copy.deepcopy(G_dict).keys())
    V_array.sort()
    _, lamda = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_exp)

    VN_array = V_array.copy()

    for i in lamda:
        if i in VN_array:
            VN_array.remove(i)

    # --------------------------------------------------------------------------
    # II. providers and consumers
    # iterative all critical nodes
    # after this, all provides and consumers will be collected
    providers, consumers = find_providers_consumers(G_dict, lamda, VN_array)

    # --------------------------------------------------------------------------
    # III. start eligibility ordering
    iter_idx = 0
    E_next = E_MAX - 1
    for theta_star_i in providers:
        for i in theta_star_i:
            Prio[i] = E_MAX

        # within each consumers, sort the order by the longest path that pass over theta_ij
        theta_i = consumers[iter_idx]
        l_i_arr = []
        
        # build up a new (temporal) DAG with only the consumers
        G_new = copy.deepcopy(G_dict)

        for key, value in copy.deepcopy(G_new).items():
            if (key not in theta_i): # and (key not in theta_star_i):
                del G_new[key]
            else:
                value_new = value.copy()
                for j in value:
                    if (j not in theta_i): # and (j not in theta_star_i):
                        value_new.remove(j)
                G_new[key] = value_new
        
        for theta_ij in theta_i:
            # 1. calculate the length
            C_i = C_dict[theta_ij]

            # forward searching in G_new
            lf_i = C_i

            pre_ij = find_predecesor(G_new, theta_ij)

            while pre_ij:
                max_c = 0
                max_v = -1
                for idx in pre_ij:
                    if C_dict[idx] > max_c:
                        max_c = C_dict[idx]
                        max_v = idx
                
                lf_i = lf_i + max_c
                ve = max_v
                pre_ij = find_predecesor(G_new, ve)

            # backward searching in G_new
            lb_i = C_i

            suc_ij = find_successor(G_new, theta_ij)

            while suc_ij:
                max_c = 0
                max_v = -1
                for idx in suc_ij:
                    if C_dict[idx] > max_c:
                        max_c = C_dict[idx]
                        max_v = idx
                
                lb_i = lb_i + max_c
                ve = max_v
                suc_ij = find_successor(G_new, ve)

            # calculate l
            l_i = lf_i + lb_i - C_i
            l_i_arr.append(l_i)

        # 2. sort theta_i according to l(i)
        if l_i_arr:
            list_of_li = l_i_arr
            indices, L_sorted = zip(*sorted(enumerate(list_of_li), reverse=True, key=itemgetter(1)))
            theta_i_sorted = []
            for idx_ in range(len(list_of_li)):
                theta_i_sorted.append(theta_i[indices[idx_]])

            # 3. assign priorities according to l(i)
            for j in theta_i_sorted:
                Prio[j] = E_next
                E_next = E_next - 1
                if E_next <= 0:
                    raise Exception("Eligbility runs out!")

        iter_idx = iter_idx + 1

    return Prio


################################################################################
################################################################################
def rta_multi_calc_R_diamond(Taskset, R_i, max_Rj, hp, R_KEY):
    R_diamond = R_i
    R_diamond_new = 0

    iteration = 0
    iter_max = 100

    while abs(R_diamond_new - R_diamond) > 5:
        R_diamond = R_diamond_new
        sum_R_hp = 0
        for j in hp:
            sum_R_hp = sum_R_hp + math.ceil(R_diamond * 1.0 / Taskset[j]["T"]) * Taskset[j][R_KEY] 

        R_diamond_new = R_i + max_Rj + sum_R_hp

        iteration = iteration + 1
        if iteration > iter_max:
            #print("Overflow!")
            break

    return R_diamond


def rta_schedulability_test(m, u):
    """ rta for multi-DAGs
    """
    global dag_base_folder
    
    RND_sched_count = 0
    EO_sched_count = 0
    TPDS_sched_count = 0

    for taskset_idx in tqdm(range(TASKSET_TO_EVALUATE)): # taskset from 0 to 999
        #print("----------")
        #print("Taskset:", taskset_idx) 
        dag_base_folder = "data/data-multi-m6-u{:.1f}/{}/".format(u, taskset_idx)
        Taskset = load_taskset_metadata(dag_base_folder)
        #print(Taskset)

        # the first iteration is to collect all response times
        for i in Taskset:
            # solve task response times
            task_idx = Taskset[i]["tau"]
            R_i_random = rta_np_classic(task_idx, m)
            R_i_EO, _, _ = rta_alphabeta_new(task_idx, m, EOPA=True, TPDS=False)
            R_i_TPDS = TPDS_rta(task_idx, m)
            Taskset[i]["R_i_random"] = R_i_random
            Taskset[i]["R_i_EO"] = R_i_EO
            Taskset[i]["R_i_TPDS"] = R_i_TPDS

        # ---------------------------------------------------------------------
        # R_i_random
        # the second iteration is to work out all the WCRTs
        R_key = "R_i_random"
        schedualbe = True
        for i in Taskset:
            Taskset[i]["R_i"] = Taskset[i][R_key]
            D_i = Taskset[i]["T"]

            # get higher prioirty taskset
            hp = []
            for j in range(i):
                hp.append(j)

            # get the maximum Rj in lp(i)
            max_Rj = 0
            if i < len(Taskset) - 1:
                for j in range(i+1, len(Taskset)):
                    if Taskset[j][R_key] > max_Rj: 
                        max_Rj = Taskset[j][R_key]

            # calculate the response time
            max_Rj = 0
            R_diamond = rta_multi_calc_R_diamond(Taskset, R_i_EO, max_Rj, hp, R_key)
            
            # even one deadline miss means unschedulable
            if (R_diamond > D_i):
                schedualbe = False

        if schedualbe:
            # no deadline miss means taskset is schedulable
            #print("Schedulable!")
            RND_sched_count = RND_sched_count + 1
        else:
            pass
            #print("Not schedulable!")

        # ---------------------------------------------------------------------
        # R_i_EO
        # the second iteration is to work out all the WCRTs
        R_key = "R_i_EO"
        schedualbe = True
        for i in Taskset:
            Taskset[i]["R_i"] = Taskset[i][R_key]
            D_i = Taskset[i]["T"]

            # get higher prioirty taskset
            hp = []
            for j in range(i):
                hp.append(j)

            # get the maximum Rj in lp(i)
            max_Rj = 0
            if i < len(Taskset) - 1:
                for j in range(i+1, len(Taskset)):
                    if Taskset[j][R_key] > max_Rj: 
                        max_Rj = Taskset[j][R_key]

            # calculate the response time
            max_Rj = 0
            R_diamond = rta_multi_calc_R_diamond(Taskset, R_i_EO, max_Rj, hp, R_key)
            
            # even one deadline miss means unschedulable
            if (R_diamond > D_i):
                schedualbe = False

        if schedualbe:
            # no deadline miss means taskset is schedulable
            #print("Schedulable!")
            EO_sched_count = EO_sched_count + 1
        else:
            pass
            #print("Not schedulable!")

        # ---------------------------------------------------------------------
        # R_i_TPDS
        # the second iteration is to work out all the WCRTs
        R_key = "R_i_TPDS"
        schedualbe = True
        for i in Taskset:
            Taskset[i]["R_i"] = Taskset[i][R_key]
            D_i = Taskset[i]["T"]

            # get higher prioirty taskset
            hp = []
            for j in range(i):
                hp.append(j)

            # get the maximum Rj in lp(i)
            max_Rj = 0
            if i < len(Taskset) - 1:
                for j in range(i+1, len(Taskset)):
                    if Taskset[j][R_key] > max_Rj: 
                        max_Rj = Taskset[j][R_key]

            # calculate the response time
            max_Rj = 0
            R_diamond = rta_multi_calc_R_diamond(Taskset, R_i_EO, max_Rj, hp, R_key)
            
            # even one deadline miss means unschedulable
            if (R_diamond > D_i):
                schedualbe = False

        if schedualbe:
            # no deadline miss means taskset is schedulable
            #print("Schedulable!")
            TPDS_sched_count = TPDS_sched_count + 1
        else:
            pass
            #print("Not schedulable!")

    print("Utilization:", round(u/m, 2), 
            "  Random:", round(RND_sched_count/TASKSET_TO_EVALUATE * 100, 1), 
            "  EO:", round(EO_sched_count / TASKSET_TO_EVALUATE * 100, 1), 
            "  TPDS:", round(TPDS_sched_count / TASKSET_TO_EVALUATE * 100, 1))


################################################################################
################################################################################
def rta_np_classic(task_idx, m):
    """ The classical bound
    """
    _, _, _, _, _, L, W = load_task(task_idx)
    makespan = L + math.ceil(1 / m * (W - L) )
    return makespan


################################################################################
################################################################################
def EMOSFT_Ordering_PA(task_list, C_dict):
    ''' C_high first
    task_list <-> c_list maps each by each
    '''
    c_list = []
    for i in task_list:
        c_list.append(C_dict[i])

    max_index, max_value = max(enumerate(c_list), key=itemgetter(1))

    return task_list[max_index]


################################################################################
################################################################################
def TPDS_max_l_max_lb(l, lb, A):
    # l  = {1: 8, 2: 9, 3: 3, 4: 6, 5: 8}
    # lb = {1: 5, 2: 3, 3: 5, 4: 3, 5: 4}
    # A  = [1, 2, 3, 4, 5]

    l_array = []
    lb_array = []
    l_index = []
    for vi in A:
        l_array.append(l[vi])
        lb_array.append(lb[vi])
        l_index.append(vi)

    indices, L_sorted = zip(*sorted(enumerate(l_array), reverse=True, key=itemgetter(1)))

    LB_with_L_sorted = []
    for i in indices:
        LB_with_L_sorted.append(lb_array[i])

    if len(L_sorted) == 1:
        # no need to compare if only one node
        v = l_index[0]
    else:
        for idx, li in enumerate(L_sorted):
            if idx == 0:
                continue
            else:
                if li < L_sorted[idx-1]:
                    #print_debug("found!", idx-1, L_sorted[idx-1])
                    break

        idx = idx - 1

        if idx == 0:
            # no draw case
            v = l_index[indices[idx]]
        else:
            # has draw case
            lb_max = -1
            lb_max_node = -1
            
            for i in range(0, idx+1):
                if LB_with_L_sorted[i] > lb_max:
                    lb_max = LB_with_L_sorted[i]
                    lb_max_node = l_index[indices[i]]
            
            v = lb_max_node

    return v


def TPDS_Compute_Length(G, C):
    lf = {}
    lb = {}
    l = {}

    # topological ordering
    # (skipped as this is guaranteed by the generator)
    G_new = copy.deepcopy(G)
    theta_i = G_new.keys()
    

    for theta_ij in theta_i:
        # calculate the length
        C_i = C[theta_ij]

        # forward searching in G_new
        lf_i = C_i

        pre_ij = find_predecesor(G_new, theta_ij)
        while pre_ij:
            max_c = 0
            max_v = -1
            for idx in pre_ij:
                if C[idx] > max_c:
                    max_c = C[idx]
                    max_v = idx
            
            lf_i = lf_i + max_c
            ve = max_v
            pre_ij = find_predecesor(G_new, ve)

        # backward searching in G_new
        lb_i = C_i

        suc_ij = find_successor(G_new, theta_ij)
        while suc_ij:
            max_c = 0
            max_v = -1
            for idx in suc_ij:
                if C[idx] > max_c:
                    max_c = C[idx]
                    max_v = idx
            
            lb_i = lb_i + max_c
            ve = max_v
            suc_ij = find_successor(G_new, ve)

        # calculate l
        l_i = lf_i + lb_i - C_i
        
        # assign to length
        l[theta_ij] = l_i
        lf[theta_ij] = lf_i
        lb[theta_ij] = lb_i

    return l, lf, lb


def TPDS_Assign_Priority(G, C, l, lf, lb, Prio, p):
    # note: p is assigned as as array to be able to pass by reference! Only p[0] is used.

    V = list(copy.deepcopy(G).keys())
    G_copy = copy.deepcopy(G)

    #print_debug(V)
    #print_debug(G_copy)

    while V:
        # find v in V with no predecesor and maximum l(v)
        l_max = -1
        l_max_node = -1
        for vi in V:
            if not find_predecesor(G_copy, vi):
                if l[vi] > l_max:
                    l_max = l[vi]
                    l_max_node = vi
        v = l_max_node

        # priority assignment
        Prio[v] = p[0]; p[0] = p[0] + 1; A = find_successor(G_copy, v)

        # removing v and its related edges
        remove_nodes_in_graph(G_copy, [v])
        if v in V:
            V.remove(v)
        
        # iterates A
        while A:
            # find v in A with no predecesor and maximum l(v)
            # when ties, compare lb(v) instead!
            v = TPDS_max_l_max_lb(l, lb, A)

            if find_predecesor(G_copy, v):
                G_prime = {}
                ans_v = find_ancestors(G_copy, v, path=[])

                for key, value in copy.deepcopy(G_copy).items():
                    if key in ans_v:
                        for j in value:
                            if j not in ans_v:
                                value.remove(j)
                        
                        G_prime[key] = value

                TPDS_Assign_Priority(G_prime, C, l, lf, lb, Prio, p)
                remove_nodes_in_graph(G_copy, ans_v)

                for vv in ans_v:
                    if vv in V:
                        V.remove(vv)
            
            # removing v and its related edges
            remove_nodes_in_graph(G_copy, [v])
            if v in V:
                V.remove(v)

            # priority assignment
            Prio[v] = p[0]; p[0] = p[0] + 1; A = find_successor(G_copy, v)


def TPDS_Ordering_PA(G, C):
    """ Ordering in: 
    Qingqiang He, et. al, Intra-Task Priority Assignment in Real-Time Scheduling of DAG Tasks on Multi-cores, 2019
    """
    # 1. Procedure compute length
    l, lf, lb = TPDS_Compute_Length(G, C)

    # 2. Procedure assign priority
    prio = {}
    p_next = [0]
    TPDS_Assign_Priority(G, C, l, lf, lb, Prio=prio, p=p_next)

    return prio


def TPDS_rta(task_idx, m):
    """ Response time analysis in: 
    Qingqiang He, et. al, Intra-Task Priority Assignment in Real-Time Scheduling of DAG Tasks on Multi-cores, 2019
    """
    # --------------------------------------------------------------------------
    # I. load the DAG task
    G_dict, C_dict, C_array, lamda, VN_array, L, W = load_task(task_idx)

    # --------------------------------------------------------------------------
    # II. assignment priorities
    Prio = TPDS_Ordering_PA(G_dict, C_dict)

    # --------------------------------------------------------------------------
    # III. calculate finish time
    # topological ordering
    # (skipped as this is guaranteed by the generator)
    f_dict = {}
    I_dict = {}

    for theta_ij in G_dict:
        # start to search interference nodes >>>
        # concurrent nodes of ij. Note this can be empty.
        int_ij = find_concurrent_nodes(G_dict, theta_ij)

        ans_ij = find_ancestors(G_dict, theta_ij, path=[])
        for ij in ans_ij:
            ans_int = I_dict[ij]
            for ijij in ans_int:
                if ijij in int_ij:
                    int_ij.remove(ijij)
        
        # fonly the (m) longest lower priority interference node is kept
        int_ij_EO = []
        int_ij_EO_less_candidates = []
        int_ij_EO_less_candidates_C = []

        if int_ij:
            for int_ij_k in int_ij:
                # lower the better
                if Prio[int_ij_k] < Prio[theta_ij]:
                    # E_k > E_i, add with confidence
                    int_ij_EO.append(int_ij_k)
                else:
                    # E_k < E_i, put into a list and later will only get longest (m)
                    int_ij_EO_less_candidates.append( int_ij_k )
                    int_ij_EO_less_candidates_C.append( C_dict[int_ij_k] )

            # sort nodes by C (if it exists), and append (m-1) longest to int_ij_EO
            if int_ij_EO_less_candidates:
                list_of_less_EO_nodes_C = int_ij_EO_less_candidates_C
                indices, _ = zip(*sorted(enumerate(list_of_less_EO_nodes_C), key=itemgetter(1), reverse=True))
                #indices = [i[0] for i in sorted(enumerate(list_of_less_EO_nodes_C), key=lambda x:x[1])]
                int_ij_EO_less_candidates_sorted = []

                for idx_ in range(len(list_of_less_EO_nodes_C)):
                    int_ij_EO_less_candidates_sorted.append(int_ij_EO_less_candidates[indices[idx_]])

                # adding (m - 1) lower EO nodes
                for xxx in range(1, m):
                    if len(int_ij_EO_less_candidates) >= xxx:
                        int_ij_EO.append( int_ij_EO_less_candidates_sorted[xxx - 1] )
                
                int_ij = int_ij_EO.copy()
        
        I_dict[theta_ij] = int_ij
        # >>> end of searching interference nodes

        int_c_sum = sum(C_dict[ij] for ij in int_ij)
        interference = math.ceil(1.0 / m * int_c_sum)

        # find the max finish time of all its predecences
        f_ij_pre_max = 0

        predecsor_of_ij = find_predecesor(G_dict, theta_ij)
        for pre_i in predecsor_of_ij:
            if f_dict[pre_i] > f_ij_pre_max:
                f_ij_pre_max = f_dict[pre_i]

        # calculate the finish time
        f_ij = C_dict[theta_ij] + f_ij_pre_max + interference
        f_dict[theta_ij] = f_ij 

    # --------------------------------------------------------------------------
    # IV. calculate reponse time
    R0 = max(f_dict[i] for i in f_dict)

    return R0



time_diff = 0

################################################################################
################################################################################
def experiment(exp=1):

    # R0 = rta_np_classic(task_idx, m)

    #R, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True)

    # print_debug("- - - - - - - - - - - - - - - - - - - -")
    # print_debug("R0 = {}".format(R0))
    # print_debug("R1 = {}, alpha = {}, beta = {}".format(R, alpha, beta))
    # print_debug("{:.1f} % improvement".format((R0 - R) / float(R0) * 100.0))


    # with open('result.txt', 'r+') as f:
    #     m = 2

    #     for task_idx in range(0, 100):
    #         print_debug("- - - - - - - - - - - - - - - - - - - -")
    #         print_debug("Tau {}:".format(task_idx))
    #         print_debug("- - - - - - - - - - - - - - - - - - - -")

    #         R0 = rta_np_classic(task_idx, m)
    #         R, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False)
    #         print_debug("\r\n \r\n")
    #         R_EO, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True) 

    #         f.write("- - - - - - - - - - - - - - - - - - - - \r\n")
    #         f.write("Tau {}: \r\n".format(task_idx))

    #         f.write("R0 = {} \r\n".format(R0))

    #         f.write("R1 = {}, alpha = {}, beta = {} \r\n".format(R, alpha, beta))
    #         f.write("{:.1f} % improvement \r\n".format((R0 - R) / float(R0) * 100.0))

    #         f.write("R2 = {}, alpha = {}, beta = {} \r\n".format(R_EO, alpha, beta))
    #         f.write("{:.1f} % improvement \r\n".format((R0 - R_EO) / float(R0) * 100.0))

    #import resource, sys
    #resource.setrlimit(resource.RLIMIT_STACK, (2**29,-1))
    #sys.setrecursionlimit(10**6)

    ##
    #R = rta_alphabeta_new(11, 2, EOPA=True, TPDS=False)
    #exit(0)

    # Experiments for RTSS 2020
    # exp 1: RTA
    # exp 2: scale p
    # exp 3: scale L
    # exp 4: multi-DAG
    # exp 5: time complexitiy (for rebuttal)

    # exp 1 (scale m)
    if exp == 1:
        for m in [2, 3, 4, 5, 6, 7, 8]:
            dag_base_folder = "data/data-generic/"
            L_ratio = -1
            results = []
            for task_idx in tqdm(range(TASKSET_TO_EVALUATE)):
                # run the five methods
                R0 = rta_np_classic(task_idx, m)
                R_AB, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=False)
                R_AB_EO, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True, TPDS=False)
                R_AB_TPDS, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=True)
                R_TPDS = TPDS_rta(task_idx, m)

                #print("{}, {}, {}, {}, {}, {}".format(task_idx, R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS))

                results.append([task_idx, R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS])
            
            pickle.dump(results, open("results/m{}.p".format(m), "wb"))
    # exp 2 (scale p)
    elif exp == 2:
        m = 4
        for p in [4, 5, 6, 7, 8]:
            dag_base_folder = "data/data-p{}/".format(p)
            L_ratio = -1
            results = []
            for task_idx in tqdm(range(TASKSET_TO_EVALUATE)):
                # run the five methods
                R0 = rta_np_classic(task_idx, m)
                R_AB, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=False)
                R_AB_EO, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True, TPDS=False)
                R_AB_TPDS, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=True)
                R_TPDS = TPDS_rta(task_idx, m)

                #print("{}, {}, {}, {}, {}, {}".format(task_idx, R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS))

                results.append([task_idx, R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS])
            
            pickle.dump(results, open("results/m{}-p{}.p".format(m,p), "wb"))
    # exp 3 (Scale L)
    elif exp == 3:
        m = 2
        p = 8
        for L in [0.6, 0.7, 0.8, 0.9]:
            dag_base_folder = "data/data-p{}/".format(p)
            L_ratio = L
            results = []
            for task_idx in tqdm(range(TASKSET_TO_EVALUATE)):
                # run the five methods
                R0 = rta_np_classic(task_idx, m)
                R_AB, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=False)
                R_AB_EO, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True, TPDS=False)
                R_AB_TPDS, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False, TPDS=True)
                R_TPDS = TPDS_rta(task_idx, m)

                #print("{}, {}, {}, {}, {}, {}".format(task_idx, R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS))

                results.append([task_idx, R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS])
            
            pickle.dump(results, open("results/m{}-p{}-L{:.2f}.p".format(m,p,L), "wb"))
    elif exp == 4:
        # exp 4
        # multi-DAG schedulability
        m = 6
        u_list = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
        u_list_new = [round(i * m, 2) for i in u_list]

        for u in u_list_new:
            rta_schedulability_test(m, u)
    elif exp == 5:
        # exp 5
        # run-time overhead
        res = []
        
        for task_id in range(TASKSET_TO_EVALUATE):
            G_dict, C_dict, C_array, lamda, VN_array, L, W = load_task(task_id)
            Eligiblity_Ordering_PA(G_dict, C_dict)
            print(time_diff)

            # to avoid anomalies in the measurements
            if time_diff < 0.05:
                res.append(time_diff)
        
        print("Mean:", sum(res) / len(res))
        print("Min:", min(res))
