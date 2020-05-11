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
import math
import copy
import networkx as nx
from pprint import pprint

from task import DAGTask, Job
from sched import trace_init, sched
from pathlib import Path

class Simulator:
    def __init__(self):
        self.taskset_size = 20
        self.randomization_times = 200


    def config(self):
        pass


    def run(self):
        # enable logger
        trace_init(log_to_file = False)
        
        # # # # # # # # # #
        # start simulation
        n = 0
        random.seed(0)

        # iteratives tasksets
        for task_idx in range(self.taskset_size):
            # generate random seeds, each seed produce a different set of WCETs
            random_seeds = random.sample(range(self.randomization_times * 100), self.randomization_times)

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
            C_exp.append(1)
            dag = DAGTask(G_dict, C_exp)
            dag_C_origin = dag.C.copy()  # make a copy if dag

            # # # # # # # # # #
            # iteratives algorithms
            for algorithm_name in ("random", "eligibility"):
                for m in (2, 4):
                    for e_model in ("WCET", "full_random", "half_random"):
                        makespans = []
                        makespan = -1
                        if algorithm_name == "random" or e_model is not "WCET":
                            # repeat multiple times if randomization is involved
                            for repeat_i in range(self.randomization_times):
                                # recovery to the original DAG as WCET might be changed
                                dag.C = dag_C_origin.copy()
                                # overide WCETs using random_seeds, if execution time model is not WCET
                                random.seed(random_seeds[repeat_i])
                                for _idx, _c in enumerate(dag.C):
                                    if e_model == "half_random":
                                        dag.C[_idx] = random.randint(math.ceil(_c/2), _c)
                                    elif e_model == "full_random":
                                        dag.C[_idx] = random.randint(1, _c)
                                    else:
                                        pass

                                if algorithm_name == "random":
                                    for _ in range(self.randomization_times):
                                        makespan = sched(dag, number_of_cores = m, algorithm = algorithm_name, execution_model = e_model)
                                        makespans.append(makespan)
                                        n = n + 1
                                else:
                                    makespan = sched(dag, number_of_cores = m, algorithm = algorithm_name, execution_model = e_model)
                                    makespans.append(makespan)
                                    n = n + 1
                        else:
                            # if no randomization is involved, i.e., eligibility + WCET
                            dag.C = dag_C_origin.copy()
                            makespan = sched(dag, number_of_cores = m, algorithm = algorithm_name, execution_model = e_model)
                            makespans.append(makespan)
                            n = n + 1
                        
                        message = "{:d};{:s};{:d};{:s};{:s}".format(task_idx, algorithm_name, m, e_model, str(makespans).replace(" ",""))
                        print(message)
                        #print(task_idx, ";", algorithm_name, ";", m, ";", e_model, ";", makespans)
            
            #print(n)


if __name__ == "__main__":
    sim = Simulator()
    sim.run()
