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

from rta_alphabeta_new import Eligiblity_Ordering_PA, TPDS_Ordering_PA, EMOSFT_Ordering_PA
from rta_alphabeta_new import load_task

EXECUTION_MODEL = ["WCET", "HALF_RANDOM", "HALF_RANDOM_NORM", "FULL_RANDOM", "FULL_RANDOM_NORM", "BCET"]
PREEMPTION_COST = 0
MIGRATION_COST = 0

PATH_OF_SRC = os.path.dirname(os.path.abspath(__file__))
LOG_TO_FILE_LOCATION = PATH_OF_SRC + "/../results/log.txt"


def trace_init(log_to_file = False, debug = False):
    LOG_FORMAT = '[%(asctime)s-%(levelname)s: %(message)s]'
    LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'

    if debug: log_mode = logging.DEBUG
    else: log_mode = logging.INFO

    if log_to_file == True:
        logging.basicConfig(filename='log.txt', filemode='a', level=log_mode,
                            format=LOG_FORMAT, datefmt=LOG_DATEFMT)
    else:
        logging.basicConfig(level=log_mode, format=LOG_FORMAT, datefmt=LOG_DATEFMT)


def trace(msglevel, timestamp, message):
    if msglevel == 0: logging.debug("t = " + str(timestamp) + ": " +  message)
    elif msglevel == 1: logging.info("t = " + str(timestamp) + ": " +  message)
    elif msglevel == 2: logging.warning("t = " + str(timestamp) + ": " + message)
    elif msglevel == 3: logging.error("t = " + str(timestamp) + ": " + message)
    else: pass


def EO_v1():
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
    
    Prio = {}

    # I. Critical
    offset = EO_ELIG_BASE_C
    sorted_x = sorted({k: EO_WCET[k] for k in EO_V_C}.items(), key=operator.itemgetter(1), reverse=False)
    
    for i in sorted_x:
        Prio[i[0]] = offset
        offset = offset + 1
    
    # II. Associate
    # order by WCET (longest first)
    offset = EO_ELIG_BASE_A
    sorted_x = sorted({k: EO_WCET[k] for k in EO_V_A}.items(), key=operator.itemgetter(1), reverse=False)
    for i in sorted_x:
        Prio[i[0]] = offset
        offset = offset + 1

    # III. Non-Critical
    offset = EO_ELIG_BASE_NC
    sorted_x = sorted({k: EO_WCET[k] for k in EO_V_NC}.items(), key=operator.itemgetter(1), reverse=False)
    for i in sorted_x:
        Prio[i[0]] = offset
        offset = offset + 1
    
    #pprint(Prio)


def sched(dag, number_of_cores, algorithm = "random", execution_model = "WCET", T_MAX = 1000000000):
    """
    Policies:
    - random (dynamic)
    - eligibility
    - TPDS2019
    - EMSOFT2019 (dynamic)
    
    Execution models:
    - WCET
    - half_random
    - full_random
    """

    t = 0

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
        Prio = Eligiblity_Ordering_PA(dag.G, dag.C_dict)
    elif algorithm == "TPDS2019":
        Prio = TPDS_Ordering_PA(dag.G, dag.C_dict)
    #pprint(Prio)

    # start scheduling
    trace(0, t, "Algorithm = {:s}, Exe_Model = {:s}, #Cores = {:d}".format(algorithm, execution_model, number_of_cores))

    # add the source node to the ready queue
    r_queue.append(1)
    w_queue.remove(1)

    while t < T_MAX and not finished:
        trace(0, t, "Scheduling point reached!")

        # update the ready queue (by iterative all left nodes)
        w_queue_c = w_queue.copy()
        f_queue_c = f_queue.copy()

        for i in w_queue_c:
            all_matched = True
            for elem in dag.pre[i]:
                if elem not in f_queue_c:
                    all_matched = False

            if all_matched:
                r_queue.append(i)
                w_queue.remove(i)
        
        # iterates all cores
        for m in range(number_of_cores):
            if cores[m].idle:
                # if anything is in the ready queue
                if r_queue:
                    # pick the next task
                    if algorithm == "random":
                        # dynamic priority
                        task_idx = random.choice(r_queue)
                    elif algorithm == "EMSOFT2019":
                        # dynamic priority
                        task_idx = EMOSFT_Ordering_PA(r_queue, dag.C_dict)
                    elif algorithm == "eligibility":
                        # static priority
                        # find the task with highest eligibities
                        E_MAX = 0
                        task_idx = r_queue[0]
                        for i in r_queue:
                            if Prio[i] > E_MAX:
                                task_idx = i
                                E_MAX = Prio[i]
                    elif algorithm == "TPDS2019":
                        # static priority
                        # find the task with highest eligibities
                        E_MIN = 1000000
                        task_idx = r_queue[0]
                        for i in r_queue:
                            if Prio[i] < E_MIN:
                                task_idx = i
                                E_MIN = Prio[i]
                    else:
                        task_idx = r_queue[0]

                    # get the task execution time
                    task_wcet = dag.C[task_idx - 1]
                    
                    # assign task to core
                    tau = Job(idx_ = task_idx, C_ = task_wcet)
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
    # test code::
    # enable logger
    trace_init(log_to_file = False)
    
    for m in [2, 4, 8, 16]:
        R_all = []

        for idx in range(1000):
            G_dict, C_dict, C_array, lamda, VN_array, L, W = load_task(idx)
            dag = DAGTask(G_dict, C_array)

            # find the high watermark of random
            R0 = 0
            for i in range(100):
                r = sched(dag, number_of_cores = m, algorithm = "random", execution_model = "WCET")
                if r > R0:
                    R0 = r

            R1 = sched(dag, number_of_cores = m, algorithm = "eligibility", execution_model = "WCET")
            R2 = sched(dag, number_of_cores = m, algorithm = "TPDS2019", execution_model = "WCET")
            R3 = sched(dag, number_of_cores = m, algorithm = "EMSOFT2019", execution_model = "WCET")

            R_all.append([R0, R1, R2, R3])

            print("{}, {}, {}, {}, {}".format(idx, R0, R1, R2, R3))

        pickle.dump(R_all, open("m{}-simu.p".format(m), "wb"))
    
    print("Experiment finished!")
