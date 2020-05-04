#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

class Processor:
    def __init__(self):
        self.idle = True
        self.workload = 0
        self.trace = []


    # assign a task
    def assign(self, task):
        pass


    # execute for t time
    def execute(self, t):
        if False:
            self.idle = True
