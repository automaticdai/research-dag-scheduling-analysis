#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import os
import logging
import pickle
import json
import random
import math
import operator
from pprint import pprint

from task import DAGTask, Job
from processor import Core
from graph import find_longest_path_dfs, find_associative_nodes


EXECUTION_MODEL = ["WCET", "HALF_RANDOM", "HALF_RANDOM_NORM", "FULL_RANDOM", "FULL_RANDOM_NORM", "BCET"]
PREEMPTION_COST = 0
MIGRATION_COST = 0

PATH_OF_SRC = os.path.dirname(os.path.abspath(__file__))
LOG_TO_FILE_LOCATION = PATH_OF_SRC + "/../results/log.txt"


def trace_init(log_to_file):
    LOG_FORMAT = '[%(asctime)s-%(levelname)s: %(message)s]'
    LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
    if log_to_file == True:
        logging.basicConfig(filename='log.txt', filemode='a', level=logging.INFO,
                            format=LOG_FORMAT, datefmt=LOG_DATEFMT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATEFMT)


def trace(msglevel, timestamp, message):
    if msglevel == 0: logging.debug("t = " + str(timestamp) + ": " +  message)
    elif msglevel == 1: logging.info("t = " + str(timestamp) + ": " +  message)
    elif msglevel == 2: logging.warning("t = " + str(timestamp) + ": " + message)
    elif msglevel == 3: logging.error("t = " + str(timestamp) + ": " + message)
    else: pass


def sched(dag, number_of_cores, algorithm = "random", execution_model = "WCET"):
    """
    Policies:
    - random
    - eligibility
    
    Execution models:
    - WCET
    - half_random
    - full_random
    """

    t = 0
    T_MAX = 100000

    # initialize cores
    cores = []
    for m in range(number_of_cores):
        core = Core()
        cores.append(core)

    # variables
    finished = False

    w_queue = dag.V.copy() # waitting queue (not released due to constraints)
    r_queue = []            # ready nodes queue
    f_queue = []            # finished nodes queue

    if algorithm == "eligibility":
        EO_G = dag.G.copy()
        EO_V = dag.V.copy()
        wcet = dag.C.copy()

        EO_WCET = {}
        for i in EO_V:
            EO_WCET[i] = wcet[i - 1]

        # [Classify nodes]
        # I. find critical nodes
        _, EO_V_C = find_longest_path_dfs(EO_G, EO_V[0], EO_V[-1], wcet)
        
        # II. find associative nodes
        candidate = EO_V.copy()
        for i in EO_V_C:  candidate.remove(i)

        critical_nodes = EO_V_C.copy()
        critical_nodes.remove(EO_V_C[0])
        critical_nodes.remove(EO_V_C[-1]) # the source and the sink node is ignored

        EO_V_A = find_associative_nodes(EO_G, candidate, critical_nodes)

        # III. find non-critical nodes (V_NC = V \ V_C \ V_A)
        EO_V_NC = EO_V.copy()
        for i in EO_V_C:  EO_V_NC.remove(i)
        for i in EO_V_A:  EO_V_NC.remove(i)

        # [Assign eligibilities]
        EO_ELIG_BASE_C = 1000
        EO_ELIG_BASE_A = 100
        EO_ELIG_BASE_NC = 1
        
        EO_eligibility = {}

        # I. C
        offset = EO_ELIG_BASE_C
        sorted_x = sorted({k: EO_WCET[k] for k in EO_V_C}.items(), key=operator.itemgetter(1), reverse=False)
        
        for i in sorted_x:
            EO_eligibility[i[0]] = offset
            offset = offset + 1
        
        # II. A
        # order by WCET (longest first)
        offset = EO_ELIG_BASE_A
        sorted_x = sorted({k: EO_WCET[k] for k in EO_V_A}.items(), key=operator.itemgetter(1), reverse=False)
        for i in sorted_x:
            EO_eligibility[i[0]] = offset
            offset = offset + 1

        # III. NC
        offset = EO_ELIG_BASE_NC
        sorted_x = sorted({k: EO_WCET[k] for k in EO_V_NC}.items(), key=operator.itemgetter(1), reverse=False)
        for i in sorted_x:
            EO_eligibility[i[0]] = offset
            offset = offset + 1
        
        #pprint(EO_eligibility)


    # start scheduling
    trace(0, t, "Algorithm = {:s}, Exe_Model = {:s}, #Cores = {:d}".format(algorithm, execution_model, number_of_cores))

    # add the source node to the ready queue
    r_queue.append(1)
    w_queue.remove(1)

    while t < T_MAX and not finished:
        trace(0, t, "Scheduling point reached!")

        # update the ready queue (by iterative all left nodes)
        for i in w_queue:
            if all(elem in f_queue  for elem in dag.pre[i]):
                r_queue.append(i)
                w_queue.remove(i)
        
        # iterates all cores
        for m in range(number_of_cores):
            if cores[m].idle:
                # if anything is in the ready queue
                if r_queue:
                    # pick the next task
                    if algorithm == "random":
                        task_idx = random.choice(r_queue)
                    elif algorithm == "eligibility":
                        # find the task with highest eligibities
                        E_MAX = 0
                        task_idx = r_queue[0]
                        for i in r_queue:
                            if EO_eligibility[i] > E_MAX:
                                task_idx = i
                                E_MAX = EO_eligibility[i]
                    else:
                        task_idx = r_queue[0]

                    # get the task execution time
                    task_wcet = dag.C[task_idx - 1]
                    if execution_model == "half_random":
                        c_this = random.randint(math.floor(task_wcet/2), task_wcet)
                    elif execution_model == "full_random":
                        c_this = random.randint(1, task_wcet)
                    else:
                        c_this = task_wcet
                    
                    # assign task to core
                    tau = Job(idx_ = task_idx, C_ = c_this)
                    cores[m].assign(tau)
                    r_queue.remove(task_idx)
                    trace(0, t, "Job {:d} assgined to Core {:d}".format(task_idx, m))

        # check the next scheduling point (the shortest workload time)
        A_LARGE_NUMBER = float("inf")
        sp = A_LARGE_NUMBER
        for core in cores:
            if core.get_workload() != 0:
                if core.get_workload() < sp:
                    sp = core.get_workload()
        # (the default scheduling point is 1, i.e., check on each tick)
        if sp == A_LARGE_NUMBER:
            sp = 1

        # execute for time sp
        t = t + sp  # these two statement happens at the same time!
        for m in range(number_of_cores):
            (tau_idx, tau_finished) = cores[m].execute(sp)

            # check finished task and put into the finished queue
            if tau_finished:
                f_queue.append(tau_idx)
                trace(0, t, "Job {:d} finished on Core {:d}".format(tau_idx, m))

        # exit loop if all nodes are finished
        f_queue.sort()
        dag.V.sort()
        if f_queue == dag.V:
            finished = True
    
    makespan = t

    if t < T_MAX:
        trace(0, t, "Finished: Makespan is {:d}".format(makespan))
    else:
        trace(3, t, "Simulation Overrun!")

    return makespan


if __name__ == "__main__":
    # enable logger
    trace_init(log_to_file = False)
    
    # example taskset
    G_exp = {1:[2,3,4], 2:[5,6], 3:[7,8], 4:[11], 5:[9], 6:[9], 7:[10], 8:[10], 9:[11], 10:[11], 11:[]}
    C_exp = [1, 5, 6, 7, 3, 6, 4, 2, 9, 8, 1]
    dag = DAGTask(G_exp, C_exp)

    pprint(("V:", dag.V))
    pprint(("C:", dag.C))
    pprint(("Pre:", dag.pre))

    print(" ")
    sched(dag, number_of_cores = 2, algorithm = "random", execution_model = "WCET")
    
    print(" ")
    sched(dag, number_of_cores = 2, algorithm = "eligibility", execution_model = "WCET")
    
    print(" ")
