#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

def find_all_paths(G_, start_vertex, end_vertex, path=[]):
    """ find all paths from start_vertex to end_vertex in graph """
    graph = G_
    path = path + [start_vertex]
    
    if start_vertex == end_vertex:
        return [path]
    
    if start_vertex not in graph:
        return []
    
    paths = []
    for vertex in graph[start_vertex]:
        if vertex not in path:
            # solve this in a recursive way
            extended_paths = find_all_paths(G_,
                                            vertex, 
                                            end_vertex, 
                                            path)
            for p in extended_paths:
                paths.append(p)
    
    return paths


def find_longest_path_dfs(G_, start_vertex, end_vertex, weights):
    """ find the longest path with depth first search """

    # find all paths
    paths = find_all_paths(G_, start_vertex, end_vertex)
    
    # search for the critical path
    costs = []
    for path in paths:
        cost = 0
        for v in path:
            cost = cost + weights[v - 1]
        costs.append(cost)

    (m, i) = max((v,i) for i,v in enumerate(costs))

    return (m, paths[i])


def find_associative_nodes(G_, candidate_nodes, critical_path):
    # find associative nodes that could block the critical path

    associated_nodes = []

    # if there is any route from A -> B, then B is associated with A
    for S in candidate_nodes:
        for E in critical_path:
            if find_all_paths(G_, S, E):
                if S not in associated_nodes:  associated_nodes.append(S)

    return associated_nodes


if __name__ == "__main__":
    G = {1:[2,3,4], 2:[5,6], 3:[7,8], 4:[11], 5:[9], 6:[9], 7:[10], 8:[10], 9:[11], 10:[11], 11:[]}
    C = [1, 5, 6, 7, 3, 6, 4, 2, 9, 8, 1]

    print(find_all_paths(G, 1, 11))
    print(find_longest_path_dfs(G, 1, 11, C))
