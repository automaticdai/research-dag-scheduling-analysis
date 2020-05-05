#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import os
import pickle
import tqdm

from taskset import *
from sched import *


def run_eligibility():
    eligibility_np()


def run_random():
    random_np()


def run_rta():
    # run analysis
    # rta_eligibility(tasks)
    pass


if __name__ == "__main__":
    run_eligibility()
    run_random()
    run_rta()
