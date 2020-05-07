#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

from task import Job, Task

class Processor:
    def __init__(self):
        self.idle = True
        self.idle_cnt = 0
        self.workload = 0
        self.task = -1


    # get workload left
    def get_workload(self):
        return self.workload


    # get the current running task
    def get_running_task(self):
        return self.task


    # assign a task to the processor
    def assign(self, task_):
        self.task = task_.idx
        self.workload = task_.C
        self.idle = False


    # execute for t time
    def execute(self, t):
        finish_flag = False
        if not self.idle:
            self.workload = self.workload - t
            if self.workload == 0:
                self.idle = True
                finish_flag = True
        else:
            self.idle_cnt = self.idle_cnt + t

        return (self.task, finish_flag)


    # migrate a task to another processor
    def migrate(self, _task):
        pass


    # perform a context switch
    def context_switch(self, _task, _task_new):
        pass
