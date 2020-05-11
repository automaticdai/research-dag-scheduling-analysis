#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

from task import Job, Task


class Storage:
    def __init__(self):
        pass


class Memory:
    def __init__(self):
        pass


class Cache(Storage):
    def __init__(self, type_, shared_=False):
        if type_ == "L1":
            self.type = type_
            self.size = 1
            self.miss_penalty = 5
        elif type_ == "L2":
            self.type = type_
            self.size = 10
            self.miss_penalty = 20
        elif type_ == "L3":
            self.type = type_
            self.size = 100
            self.miss_penalty = 200
        else:
            # should have an exception
            raise ValueError("Not supported cache type")


    def is_hit(self):
        pass


class Core:
    """ a core is a hardware entity for executing code. Each core:
    - can execute code
    - optionally has a level 1 cache (I-Cache and D-Cache)
    - optionally has a level 2 cache if level 1 cache is enabled
    """

    def __init__(self):
        self.idle = True
        self.idle_cnt = 0
        self.workload = 0
        self.job_id = -1


    def get_workload(self):
        """ get the workload left
        """
        return self.workload


    def get_running_task(self):
        """ get the current running task
        """
        return self.job_id


    def get_idle_count(self):
        """ get CPU idle count
        """
        return self.idle_cnt
    

    def assign(self, job_):
        """ assign a job to the core
        """
        self.job_id = job_.idx
        self.workload = job_.C
        self.idle = False


    # execute for t time
    def execute(self, t):
        """ execute the current job for time t
        """

        finish_flag = False
        if not self.idle:
            self.workload = self.workload - t
            if self.workload == 0:
                self.idle = True
                finish_flag = True
        else:
            self.idle_cnt = self.idle_cnt + t

        return (self.job_id, finish_flag)


    def abort(self):
        """ abort execution
        """
        pass


    def migrate(self, _task):
        """ migrate a task to another core
        """
        pass


    def context_switch(self, _task, _task_new):
        """ perform a context switch
        """
        pass


class Processor:
    """ a processor has:
    - 1 to n cores
    - cache
    """
    pass