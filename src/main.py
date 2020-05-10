#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import os
import logging
import pickle
import tqdm
import random
import networkx as nx
from pprint import pprint

from task import DAGTask, Job
from sched import trace_init, sched
from pathlib import Path

class Simulator:
    def __init__(self):
        random.seed(0)


    def config(self):
        pass


    def run(self):
        # enable logger
        trace_init(log_to_file = False)
        
        # # # # # # # # # #
        # start simulation
        n = 0
        # iteratives tasksets
        for task_idx in range(20):
            # load the DAG task
            dag_task_file = "./data/Tau_{:d}.gpickle".format(task_idx)
            G = nx.read_gpickle(dag_task_file)
            
            # formulate the graph list
            G_dict = {}
            C_dict = {}
            max_key = 0
            for u, v, weight in G.edges(data='label'):
                if u not in G_dict:
                    G_dict[u] = [v]
                else:
                    G_dict[u].append(v)

                if v > max_key:
                    max_key = v
                
                C_dict[u] = weight
            G_dict[max_key] = []

            # formulate the c list
            C_exp = []
            for key in sorted(C_dict):
                C_exp.append(C_dict[key])
            dag = DAGTask(G_dict, C_exp)
            C_exp.append(1)

            # # # # # # # # # #
            # iteratives algorithms
            for algorithm_name in ("random", "eligibility"):
                for m in (2, 4):
                    for e_model in ("WCET", "full_random", "half_random"):
                        makespans = []
                        if algorithm_name == "random" or e_model is not "WCET":
                            for _ in range(100):
                                makespan = sched(dag, number_of_cores = m, algorithm = algorithm_name, execution_model = e_model)
                                makespans.append(makespan)
                                n = n + 1
                        else:
                            makespan = sched(dag, number_of_cores = m, algorithm = algorithm_name, execution_model = e_model)
                            makespans.append(makespan)
                            n = n + 1
                        
                        print(task_idx, ";", algorithm_name, ";", m, ";", e_model, ";", makespans)


if __name__ == "__main__":
    sim = Simulator()
    sim.run()
