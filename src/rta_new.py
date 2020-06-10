import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle

import networkx as nx

from graph import find_longest_path_dfs, find_predecesor, find_successor, get_subpath_between


def gen_node_pairs_from_path(path):
    pairs = []

    for i in path:
        for j in path:
            if j > i:
                pairs.append((i,j))

    return pairs


def find_providers_consumers_new(G, lamda, VN):
    """ Find provides and consumers by decompose the DAG graph
    """
    # Exception handling: 
    # - VN = []

    theta = []         # consumers list
    theta_p = []       # providers list
    theta_p_super = [] # super provider list

    cp_mapping = {}    
    pc_mapping = {}    # mapping between consumers and providers
    pc_mapping_super = {}

    legal_spans = []   # legal spans


    # Step I. get consumers
    n_s = lamda[0]
    n_e = lamda[-1]

    node_pairs = gen_node_pairs_from_path(lamda)

    for node_pair in node_pairs:
        n_a, n_b = node_pair

        for path in nx.all_simple_paths(G, n_a, n_b):
            #print(path)
            path.remove(n_a)
            path.remove(n_b)

            #if path is not []:
            found_c_nodes = False
            for i in lamda:
                if i in path and i is not n_a and i is not n_b:
                    found_c_nodes = True

            if not found_c_nodes:
                #print("Match")
                if path:
                    theta.append(path)

    # merge consumers
    # H = nx.DiGraph()
    # for p in theta_t:
    #     edeges = zip(p[0:-2], p[1:-1])
    #     H.add_edges_from(edeges)
    # print(H.edges())


    # Step II. get providers
    #print("cp_mapping:")
    for idx, theta_i in enumerate(theta):
        for t in G.predecessors(theta_i[0]):
            if t in lamda:
                c_a = t
         
        for t in G.successors(theta_i[-1]):
            if t in lamda:
                c_b = t

        theta_p_i = get_subpath_between(lamda, c_a, c_b)

        duplicated = False
        for idx_pp, pp in enumerate(theta_p):
            if pp == theta_p_i:
                duplicated = True
                pc_mapping[idx_pp].append(idx)
                cp_mapping[idx] = idx_pp

        if not duplicated:
            theta_p.append(theta_p_i)
            pc_mapping[len(theta_p)-1] = [idx]
            cp_mapping[idx] = len(theta_p)-1
        #print(theta_i, "-->", theta_p_i)


    # Step III. merge the super provider (greeding)
    ppp = []
    for v_i in lamda:
        match = False
        
        for k, p_i in enumerate(theta_p):
            if v_i in p_i:
                match = True
                break
        
        if not match:
            if ppp:
                theta_p_super.append(ppp)
            else:
                theta_p_super.append([v_i])
            ppp = []
        else:
            ppp.append(v_i)
    theta_p_super.append([v_i])


    # Step IV. get the legal length & the new cp mapping
    #print("----------")
    #print("cp_mapping_super:")
    for i, v in enumerate(theta):
        p_i = cp_mapping[i]
        p = theta_p[p_i]     # provider p_i of consumer i

        for k, super_p in enumerate(theta_p_super):
            if set(p).issubset(set(super_p)):
                if k in pc_mapping_super:
                    pc_mapping_super[k].append(i)
                else:
                    pc_mapping_super[k] = [i]
                break

        #print(v, "-->", theta_p_super[k]) 


    # unfinished!
    # calculate the relative legal starting time and end time within a provider
    C = {}
    for u, _, weight in G.edges(data='label'):
        C[u] = weight
    C[u+1] = 1

    legal_t_s = 0 
    legal_t_e = 0
    span = [legal_t_s, legal_t_e]
    legal_spans.append(span)


    return (theta_p_super, theta, pc_mapping_super, legal_spans)


def find_providers_consumers(G, lamda, VN):
    """ Find provides and consumers by decompose the DAG graph
    """
    # Exception handling: 
    # - VN = []

    theta = []         # consumers list
    theta_p = []       # providers list
    theta_p_super = [] # super provider list

    cp_mapping = {}    
    pc_mapping = {}    # mapping between consumers and providers
    pc_mapping_super = {}

    legal_spans = []   # legal spans


    # Step I. get consumers
    n_s = lamda[0]
    n_e = lamda[-1]

    node_pairs = gen_node_pairs_from_path(lamda)

    for node_pair in node_pairs:
        n_a, n_b = node_pair

        for path in nx.all_simple_paths(G, n_a, n_b):
            #print(path)
            path.remove(n_a)
            path.remove(n_b)

            #if path is not []:
            found_c_nodes = False
            for i in lamda:
                if i in path and i is not n_a and i is not n_b:
                    found_c_nodes = True

            if not found_c_nodes:
                #print("Match")
                if path:
                    theta.append(path)

    # merge consumers
    # H = nx.DiGraph()
    # for p in theta_t:
    #     edeges = zip(p[0:-2], p[1:-1])
    #     H.add_edges_from(edeges)
    # print(H.edges())


    # Step II. get providers
    #print("cp_mapping:")
    for idx, theta_i in enumerate(theta):
        for t in G.predecessors(theta_i[0]):
            if t in lamda:
                c_a = t
         
        for t in G.successors(theta_i[-1]):
            if t in lamda:
                c_b = t

        theta_p_i = get_subpath_between(lamda, c_a, c_b)

        duplicated = False
        for idx_pp, pp in enumerate(theta_p):
            if pp == theta_p_i:
                duplicated = True
                pc_mapping[idx_pp].append(idx)
                cp_mapping[idx] = idx_pp

        if not duplicated:
            theta_p.append(theta_p_i)
            pc_mapping[len(theta_p)-1] = [idx]
            cp_mapping[idx] = len(theta_p)-1
        #print(theta_i, "-->", theta_p_i)


    # Step III. merge the super provider (greeding)
    ppp = []
    for v_i in lamda:
        match = False
        
        for k, p_i in enumerate(theta_p):
            if v_i in p_i:
                match = True
                break
        
        if not match:
            if ppp:
                theta_p_super.append(ppp)
            else:
                theta_p_super.append([v_i])
            ppp = []
        else:
            ppp.append(v_i)
    theta_p_super.append([v_i])


    # Step IV. get the legal length & the new cp mapping
    #print("----------")
    #print("cp_mapping_super:")
    for i, v in enumerate(theta):
        p_i = cp_mapping[i]
        p = theta_p[p_i]     # provider p_i of consumer i

        for k, super_p in enumerate(theta_p_super):
            if set(p).issubset(set(super_p)):
                if k in pc_mapping_super:
                    pc_mapping_super[k].append(i)
                else:
                    pc_mapping_super[k] = [i]
                break

        

        #print(v, "-->", theta_p_super[k]) 


    # unfinished!
    # calculate the relative legal starting time and end time within a provider
    C = {}
    for u, _, weight in G.edges(data='label'):
        C[u] = weight
    C[u+1] = 1

    legal_t_s = 0 
    legal_t_e = 0
    span = [legal_t_s, legal_t_e]
    legal_spans.append(span)


    return (theta_p_super, theta, pc_mapping_super, legal_spans)


def rta_new(task_idx, m):
    """ Proposed new RTA
    """

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
    G_dict[max_key] = []

    # formulate the c list (c[0] is c for v1!!)
    C_exp = []
    for key in sorted(C_dict):
        C_exp.append(C_dict[key])

    C_exp.append(1)

    V_array.sort()
    Li, lamda = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_exp)
    Wi = sum(C_exp)

    VN_array = V_array.copy()

    for i in lamda:
        if i in VN_array:
            VN_array.remove(i)

    # >> end of load DAG task >>

    providers, consumers, pc_mapping, legal_span = find_providers_consumers(G, lamda, VN_array)

    # A. Analysis-based
    llens = {}
    for idx, provider in enumerate(providers):
        # for each provider, find the longest theta
        #print(provider)
        if (idx == 0) or (idx == len(providers) - 1):
            # skip the source and sink nodes
            continue

        if idx in pc_mapping:
            max_llens = 0
            for i in pc_mapping[idx]:
                llen = 0
                for v in consumers[i]:
                    llen = llen + C_exp[v-1]
                
                llens[i] = llen
                #print("C(", consumers[i], ") = ", llen)

                if llen > max_llens:
                    max_llens = llen

        # [TODO] be careful there could be more than one super provider
        if idx == 2:
            raise Exception("Not support yet!")
        
        Wi_p = Wi
        Li_p = Li
        Ri_m = max_llens + 1.0 / (m - 1) * (Wi_p - Li_p - max_llens)

        if Li_p >= Ri_m:
            # case 1
            alpha_i = Wi_p - Li_p
            beta_i = 0
        else:
            # case 2
            # calculate beta
            beta_i = min((Ri_m - Li_p), max_llens)

            # sort llens
            llens_sorted_array = []
            for key in llens:
                value = llens[key]
                llens_sorted_array.append(value) 
            llens_sorted_array.sort(reverse=True)

            x = {}
            for k in range(m):
                if k < len(llens_sorted_array):
                    llen_k = llens_sorted_array[k]
                else:
                    llen_k = 0
                
                a = 0
                for i in provider:
                    a = a + C_exp[i-1]
                
                b = 0
                for i in range(k):
                    if i < len(llens_sorted_array):
                        b = b + llens_sorted_array[i]
                    else:
                        b = b + 0
                
                x[k] = llen_k + 1.0 / (m - 1) * (a - b)

            # calculate alpha
            w_not_accomodated = 0
            for i in range(m-1):
                w_not_accomodated = w_not_accomodated + max(x[i] - Li_p, 0)
            alpha_i = a - w_not_accomodated
        
        # calculate the response time bound
        rt_new = Li_p + (1.0 / m) * (Wi_p - Li_p - alpha_i - beta_i) + beta_i


    rt_baseline = rta_np(task_idx,m)
    #print(rta_baseline)

    return rt_new
