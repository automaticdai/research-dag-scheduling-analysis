#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

class Job:
    """ a job has:
    - an id (may inheritate from the task that releases it)
    - a computational time
    - a deadline
    """ 
    def __init__(self, idx_=0, C_=0, D_=0):
        self.idx = idx_
        self.C = C_
        self.D = D_


class Task(Job):
    """ in additional to a jobm a task has:
    - a period, and 
    - a release offset 
    """
    def __init__(self, T_=0, r_=0):
        super().__init__(self)
        self.T = T_
        self.r = r_


class DAGTask(Task):
    def __init__(self):
        """ a DAG task is a task with directed graph dependencies
        - G is the graph
        - pre is the precondition that describes the dependability
        - the computational time of a DAG is an array contains all C of its nodes
        
        assumptions:
        - the first node is the source node, with C = 1
        - the last node is the sink node, with C = 1
        """
        
        super().__init__(self)

        self.G = {1:[2,3,4], 2:[5,6], 3:[7,8], 4:[11], 5:[9], 6:[9], 7:[10], 8:[10], 9:[11], 10:[11], 11:[]}
        self.C = [1, 5, 6, 7, 3, 6, 4, 2, 9, 8, 1]
        self.V = sorted(self.G.keys())

        # pre- constraint list (reverse E and accumulate)
        self.pre = {}
        for key, item in self.G.items():
            for i in item:
                if i in self.pre:
                    self.pre[i].append(key)
                else:
                    self.pre[i] = [key]
