#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

class DAGTask:
    def __init__(self):
        self._T = 50
        self._D = 50
        self._W = 100
        self._L = 50
        
        self._V = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        self._C = [1, 5, 6, 7, 3, 6, 4, 2, 9, 8, 1]
        self._E = {1:[2,3,4], 2:[5,6], 3:[7,8], 4:[11], 5:[9], 6:[9], 7:[10], 8:[10], 9:[11], 10:[11]}

        # pre- constraint list (reverse E and accumulate)
        self._pre = {}
        for _key,_item in self._E.items():
            for i in _item:
                if i in self._pre:
                    self._pre[i].append(_key)
                else:
                    self._pre[i] = [_key]

        # search for the critical path
        

        # find the critical nodes


        # find the associative nodes


        # find the non-critical nodes

