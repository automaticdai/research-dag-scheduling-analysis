#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

from task import Task

class Processor:
    def __init__(self):
        self.idle = True
        self.workload = 0
        self.task = -1


    # get workload left
    def get_workload(self):
        return self.workload


    # get the current running task
    def get_running_task(self):
        return self.task


    # assign a task to the processor
    def assign(self, _task):
        self.task = _task.idx
        self.workload = _task.c
        self.idle = False


    # execute for t time
    def execute(self, t):
        finish_flag = False
        if not self.idle:
            self.workload = self.workload - t
            if self.workload == 0:
                self.idle = True
                finish_flag = True

        return (self.task, finish_flag)


    # migrate a task to another processor
    def migrate(self, _task):
        pass


    # perform a context switch
    def context_switch(self, _task, _task_new):
        pass
