import networkx as nx
from graph import find_longest_path_dfs, find_predecesor, find_successor, get_subpath_between

def rta_np(task_idx, m):
    """ Classical RTA approach for non-preemptive scheduling
    """
    # load the DAG task
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

    # formulate the c list
    C_exp = []
    for key in sorted(C_dict):
        C_exp.append(C_dict[key])

    C_exp.append(1)

    V_array.sort()
    Li, _ = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_exp)
    Wi = sum(C_exp)
    # end of load DAG task

    makespan = Li + 1 / m * (Wi - Li)

    return makespan
