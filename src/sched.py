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
from pprint import pprint

from task import DAGTask
from processor import Processor


def random_np():
    t = 0
    T_MAX = 100000

    core_1 = Processor()
    core_2 = Processor()

    # load taskset
    task = DAGTask()

    pprint(task._V)
    pprint(task._E)
    pprint(task._pre)

    # update ready queue


    # randomally pick the next task


    # execute for time t

    # check the next scheduling point


def eligibility_np():
    # assign elibility to tasks

    # I. find critical
    # II. find associative tasks
    # III. find non-critical

    # fetch a task

    # assign to a queue
    
    # execution model

    # decide the next scheduling point

    # log result

    pass


if __name__ == "__main__":
    random_np()
    #eligibility_np()