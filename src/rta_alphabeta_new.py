import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle
from operator import itemgetter

import networkx as nx

from graph import find_longest_path_dfs, find_predecesor, find_successor, find_ancestors, find_descendants, get_subpath_between


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

    # start to iterative delta
    delta = 0
    node_left = node.copy()

    while node_left:
        # this search is limited to node, 
        # so all keys and values that do not contain node_left will be removed
        G_new = G.copy()

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
            #print("PARALLISM: False")
            return False

        finished = False
        while not finished:
            node_copy = node_left.copy()
            for ve in node_copy:
                if find_predecesor(G_new, ve) == []:
                    node_left.remove(ve)
                    finished = True

        suc_ve = find_successor(G_new, ve)
        while suc_ve:
            suc_ve_first = suc_ve[0]
            if suc_ve_first in node_left:
                node_left.remove(suc_ve_first)
            suc_ve = find_successor(G_new, ve)

    #print("PARALLISM: True")
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

    return providers, consumers


def rta_alphabeta_new(task_idx, m, EOPA=False):
    """ Response time analysis using alpha_beta
    """
    # --------------------------------------------------------------------------
    # I. load the DAG task
    G_dict, C_dict, lamda, VN_array, L, W = load_task(task_idx)

    # --------------------------------------------------------------------------
    # II. providers and consumers
    # iterative all critical nodes
    # after this, all provides and consumers will be collected
    providers, consumers = find_providers_consumers(G_dict, lamda, VN_array)
    print("Providers:", providers)
    print("Consumers:", consumers)

    # --------------------------------------------------------------------------
    # III. calculate the finish times of each provider, and the consumers within
    f_dict = {}        # the set of all finish times
    I_dict = {}        # interference workload
    R_i_minus_one = 0  # the response time of the previous provider theta^*_(i - 1)

    alpha_arr = []
    beta_arr = []

    if EOPA:
        Prio_EO = Eligiblity_Ordering_PA(task_idx)

    # ==========================================================================
    # iteratives all providers (first time, to get all finish times)
    for i, theta_i_star in enumerate(providers):
        print("- - - - - - - - - - - - - - - - - - - -")
        print("theta(*)", i, ":", theta_i_star)
        print("theta", i, ":", consumers[i])  

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
            else:
                # not enough cores
                # start to search interference nodes >>>
                # concurrent nodes of ij. Can be empty.
                con_ij = find_concurrent_nodes(G_dict, theta_ij)
                #print("Con nodes:", con_ij)

                int_ij = con_ij.copy()
                remove_nodes_in_list(int_ij, lamda)

                ans_ij = find_ancestors(G_dict, theta_ij, path=[])
                remove_nodes_in_list(ans_ij, lamda)
                #print("Ans nodes:", ans_ij)

                for ij in ans_ij:
                    ans_int = I_dict[ij]
                    for ijij in ans_int:
                        if ijij in int_ij:
                            int_ij.remove(ijij)
                #print("Int nodes:", int_ij)
                
                if EOPA:
                    # for EOPA, only the (m - 1) longest lower priority interference node is kept
                    int_ij_EO = []
                    int_ij_EO_less_candidates = []
                    int_ij_EO_less_candidates_C = []

                    if int_ij:
                        for int_ij_k in int_ij:
                            if Prio_EO[int_ij_k] > Prio_EO[theta_ij]:
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
                
                I_dict[theta_ij] = int_ij
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
            print("f_theta({}) : {}".format(theta_ij, f_dict[theta_ij]))



    # ==========================================================================
    # iteratives all providers (2nd time)
    # the finish times of provider nodes have to be calculated again to get f_theta_i_star
    # the finish times of consumer nodes have to be calculated again to get lambda_ve
    for i, theta_i_star in enumerate(providers):
        print("- - - - - - - - - - - - - - - - - - - -")
        print("theta(*)", i, ":", theta_i_star)
        print("theta", i, ":", consumers[i])  

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
        
        print("finish time of theta(*)", f_theta_i_star)

        # iteratives all consumers
        # (skipped) topoligical order, skipped because guaranteed by the generator
        # note: consumer can be empty
        theta_i = consumers[i]
        f_v_j_max = 0; f_v_j_max_idx = -1
        for _, theta_ij in enumerate(theta_i):
            print(theta_ij, ":", C_dict[theta_ij])
            
            # the interference term
            con_nc_ij = find_concurrent_nodes(G_dict, theta_ij)
            remove_nodes_in_list(con_nc_ij, lamda)
            if test_parallelism(G_dict, con_nc_ij, m - 1):
                # sufficient parallism
                interference = 0
                I_dict[theta_ij] = []
            else:
                # not enough cores
                # start to search interference nodes >>>
                # concurrent nodes of ij. Can be empty.
                con_ij = find_concurrent_nodes(G_dict, theta_ij)
                #print("Con nodes:", con_ij)

                int_ij = con_ij.copy()
                remove_nodes_in_list(int_ij, lamda)

                ans_ij = find_ancestors(G_dict, theta_ij, path=[])
                remove_nodes_in_list(ans_ij, lamda)
                #print("Ans nodes:", ans_ij)

                for ij in ans_ij:
                    ans_int = I_dict[ij]
                    for ijij in ans_int:
                        if ijij in int_ij:
                            int_ij.remove(ijij)
                #print("Int nodes:", int_ij)
                
                if EOPA:
                    # for EOPA, only the (m - 1) longest lower priority interference node is kept
                    int_ij_EO = []
                    int_ij_EO_less_candidates = []
                    int_ij_EO_less_candidates_C = []

                    if int_ij:
                        for int_ij_k in int_ij:
                            if Prio_EO[int_ij_k] > Prio_EO[theta_ij]:
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
                
                I_dict[theta_ij] = int_ij
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
            print("f_theta({}) : {}".format(theta_ij, f_dict[theta_ij]))

            # find max(f_vj)
            if f_ij > f_v_j_max:
                f_v_j_max = f_ij
                f_v_j_max_idx = theta_ij
        
        # (!) R_i_m_minus_one is no longer needed
        #R_i_m_minus_one = f_v_j_max

        # start to calculate the response time of provider i
        Wi_nc = sum(C_dict[ij] for ij in theta_i)
        Li = sum(C_dict[ij] for ij in theta_i_star)
        Wi = Wi_nc + Li 

        # --------------------------------------------------------------------------
        # IV. bound alpha and beta
        # For Case A (has no delay to the critical path):
        if (f_theta_i_star >= f_v_j_max):
            print("** Case A **")
            alpha_i = Wi_nc
            beta_i = 0
        # For Case B (has delay to the critical path):
        else:
            print("** Case B **")
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
            
            print("lamda_ve:", lamda_ve, "len:", len_lamda_ve)

            # beta_i
            beta_i = len_lamda_ve

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
            theta_i_llen = theta_i.copy()
            llen_i = {}
            len_llen_i = {}

            # find the m - 1 longest path and their finish times within the provider
            # n = 1, m - 1
            for n in range(1, m):
                # no more candidates, searching is finished
                if theta_i_llen == []:
                    llen_i[n] = []
                    len_llen_i[n] = 0
                    continue

                f_theta_i_llen = []

                for ij in theta_i_llen:
                    f_theta_i_llen.append(f_dict[ij])

                max_value = max(f_theta_i_llen)
                max_index = f_theta_i_llen.index(max_value)
                ve = theta_i_llen[max_index]

                # find the path (backward search)
                llen_ij = [ve]
                len_llen_ij = C_dict[ve]

                while(True):
                    pre_of_ij = find_predecesor(G_dict, ve)
                    for ij in pre_of_ij:
                        if ij not in theta_i:
                            pre_of_ij.remove(ij)

                    if pre_of_ij:
                        # find the maximum finish time, within the provider
                        f_pre_of_ij = []
                        for ij in pre_of_ij:
                            f_pre_of_ij.append(f_dict[ij])

                        max_value = max(f_pre_of_ij)
                        max_index = f_pre_of_ij.index(max_value)

                        if max_value > f_theta_i_star:
                            ve = pre_of_ij[max_index]
                            llen_ij.append(ve)
                            len_llen_ij = len_llen_ij + C_dict[ve]
                        else:
                            break
                    else:
                        break

                # remove the nodes in the path from theta_i_llen
                for ij in llen_ij:
                    if ij in theta_i_llen:
                        theta_i_llen.remove(ij)
                
                # save the llen_ij
                llen_i[n] = llen_ij
                len_llen_i[n] = len_llen_ij

            # update the finish time of nodes in len_i
            U_llen = []
            for key in llen_i:
                if llen_i[key]:
                    # topological sort, to ensure finish time is calculated in the right order
                    llen_i[key].sort()

                    # update the UNION(llen(k))
                    for theta_ij in llen_i[key]:
                        U_llen.append(theta_ij)

                    # iterative all nodes in the (key)th longest path
                    for theta_ij in llen_i[key]:
                        # the interference term
                        con_nc_ij = find_concurrent_nodes(G_dict, theta_ij)
                        remove_nodes_in_list(con_nc_ij, lamda)
                        if test_parallelism(G_dict, con_nc_ij, m - 1):
                            # sufficient parallism
                            interference = 0
                        else:
                            # not enough cores
                            # start to search interference nodes >>>
                            # concurrent nodes of ij. Can be empty.
                            con_ij = find_concurrent_nodes(G_dict, theta_ij)
                            #print("Con nodes:", con_ij)

                            int_ij = con_ij.copy()
                            remove_nodes_in_list(int_ij, lamda)

                            ans_ij = find_ancestors(G_dict, theta_ij, path=[])
                            remove_nodes_in_list(ans_ij, lamda)
                            #print("Ans nodes:", ans_ij)

                            for ij in ans_ij:
                                ans_int = I_dict[ij]
                                for ijij in ans_int:
                                    if ijij in int_ij:
                                        int_ij.remove(ijij)
                            #print("Int nodes:", int_ij)

                            I_dict[theta_ij] = int_ij
                            # >>> end of searching interference nodes

                            # one more step: remove all Union(llen(k))
                            for ij in U_llen:
                                if ij in int_ij:
                                    int_ij.remove(ij)

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

                        print("Finish time of {:} updated from {:} to {:}".format(theta_ij, f_dict[theta_ij], f_ij))
                        f_dict[theta_ij] = f_ij

            # calculate f_delta = sum[(f_ve - f_theta_i_star)]0
            f_delta_sum = 0
            for iii_f in range(1, m):
                if llen_i[iii_f]:
                    llen_i_ve = llen_i[iii_f][-1]
                    f_delta = max(f_dict[llen_i_ve] - f_theta_i_star, 0)
                    f_delta_sum = f_delta_sum + f_delta
                else:
                    pass

            # approxiation of alpha
            # (!) note: alpha_i_new is removed as it is unsafe
            #alpha_i_new = Wi - Li - f_delta_sum
            alpha_i_new = 0

            # alpha_i is the max of the two
            alpha_i = max(alpha_i_hat, alpha_i_new)
        
        if not EOPA:
            # RTA-CFP
            # calculate the response time based on alpha_i and beta_i
            #Ri = Li + beta_i + math.ceil(1.0 / m * (Wi - Li - alpha_i - beta_i))
            # this improved is to bound Ri to be better than classic bound
            Ri = Li + math.ceil(1.0 / m * (Wi - Li - max(alpha_i - (m-1) * beta_i, 0)))
        else:
            # RTA-CFP + EOPA
            if beta_i == 0:
                Ri = Li
            else:
                I_lambda_ve = []

                # I_lambda_ve calculation
                for v_kk in lamda_ve:
                    v_jj = I_dict[v_kk]

                    for v_jjj in v_jj:
                        if f_dict[v_jjj] > f_theta_i_star:
                            I_lambda_ve.append(v_jjj)

                I_lambda_ve = []

                # test parallelism of I_lambda_ve
                if test_parallelism(G_dict, I_lambda_ve, m):
                    I_term_for_EO = 0
                else:
                    # calculate I_ve
                    I_ve = 0

                    for v_kk in I_lambda_ve:
                        if f_dict[v_kk] - C_dict[v_kk] >= f_theta_i_star:
                            I_ve = I_ve + C_dict[v_kk]
                        else:
                            I_ve = I_ve + (f_dict[v_kk] - f_theta_i_star)

                    I_term_for_EO = math.ceil(1.0 / m * I_ve)

                    # check: I_ve should <= (Wi - Li - alpha_i - beta_i)
                    print("(DEBUG) Wi - Li - alpha_i - beta_i: {}".format( Wi - Li - alpha_i - beta_i ))
                    print("(DEBUG) I_ve: {}".format( I_ve ))

                Ri = Li + beta_i + I_term_for_EO

        print("R_i:", Ri)

        R_i_minus_one = R_i_minus_one + Ri
        print("R_sum: ", R_i_minus_one)

        alpha_arr.append(alpha_i)
        beta_arr.append(beta_i)

    R = R_i_minus_one

    return R, alpha_arr, beta_arr


def Eligiblity_Ordering_PA(task_idx):
    """ The Eligibility Ordering priority assignment
    """
    Prio = {}
    E_MAX = 2000

    # --------------------------------------------------------------------------
    # I. load the DAG task
    G_dict, C_dict, lamda, VN_array, _, _ = load_task(task_idx)

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
        G_new = G_dict.copy()

        for key, value in G_new.copy().items():
            if key not in theta_i:
                del G_new[key]
            else:
                value_new = value.copy()
                for j in value:
                    if j not in theta_i:
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
            indices, L_sorted = zip(*sorted(enumerate(list_of_li), key=itemgetter(1)))
            theta_i_sorted = []
            for idx_ in range(len(list_of_li)):
                theta_i_sorted.append(theta_i[indices[idx_]])

            # 3. assign priorities according to l(i)
            for j in theta_i_sorted:
                Prio[j] = E_next
                E_next = E_next - 1

        E_next = E_next - 100
        iter_idx = iter_idx + 1

    return Prio


def rta_alphabeta_new_multi():
    """ rta for multi-DAGs
    """
    pass


def rta_np_classic(task_idx, m):
    """ The classical bound
    """
    _, _, _, _, L, W = load_task(task_idx)
    makespan = math.ceil( L + 1 / m * (W - L) )
    return makespan


def EMOSFT_Ordering_PA(task_idx):
    pass


def TPDS_Ordering_PA(task_idx):
    """ Ordering in: 
    Qingqiang He, et. al, Intra-Task Priority Assignment in Real-Time Scheduling of DAG Tasks on Multi-cores, 2019
    """
    Prio = {}


    return Prio


def rta_TPDS(task_idx, m):
    """ Response time analysis in: 
    Qingqiang He, et. al, Intra-Task Priority Assignment in Real-Time Scheduling of DAG Tasks on Multi-cores, 2019
    """
    # --------------------------------------------------------------------------
    # I. load the DAG task
    G_dict, C_dict, lamda, VN_array, L, W = load_task(task_idx)

    # --------------------------------------------------------------------------
    # II. sort into topological order (skipped)

    # --------------------------------------------------------------------------
    # III. assignment priorities
    Prio = TPDS_Ordering(task_idx)


def rta_TPDS_multi():
    pass


if __name__ == "__main__":
    task_idx = 7; m = 2 # (2, 4, 8, 16)

    # R0 = rta_np_classic(task_idx, m)
    # R, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False)
    #R, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True)

    # print("- - - - - - - - - - - - - - - - - - - -")
    # print("R0 = {}".format(R0))
    # print("R1 = {}, alpha = {}, beta = {}".format(R, alpha, beta))
    # print("{:.1f} % improvement".format((R0 - R) / float(R0) * 100.0))


    with open('result.txt', 'r+') as f:
        m = 2

        for task_idx in range(3, 4):
            print("- - - - - - - - - - - - - - - - - - - -")
            print("Tau {}:".format(task_idx))
            print("- - - - - - - - - - - - - - - - - - - -")

            R0 = rta_np_classic(task_idx, m)
            R, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=False)
            print("\r\n \r\n")
            R_EO, alpha, beta = rta_alphabeta_new(task_idx, m, EOPA=True) 

            f.write("- - - - - - - - - - - - - - - - - - - - \r\n")
            f.write("Tau {}: \r\n".format(task_idx))

            f.write("R0 = {} \r\n".format(R0))

            f.write("R1 = {}, alpha = {}, beta = {} \r\n".format(R, alpha, beta))
            f.write("{:.1f} % improvement \r\n".format((R0 - R) / float(R0) * 100.0))

            f.write("R2 = {}, alpha = {}, beta = {} \r\n".format(R_EO, alpha, beta))
            f.write("{:.1f} % improvement \r\n".format((R0 - R_EO) / float(R0) * 100.0))


    #TPDS_Ordering(task_idx)
    #rta_TPDS(task_idx, m)
