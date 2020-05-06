#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

class Task:
    def __init__(self, _idx=0, _c=0):
        self.idx = _idx
        self.c = _c


class DAGTask():
    def __init__(self):
        """
        assumptions:
        - the first node is the source node
        - the last node is the sink node
        """
        
        self._G = {1:[2,3,4], 2:[5,6], 3:[7,8], 4:[11], 5:[9], 6:[9], 7:[10], 8:[10], 9:[11], 10:[11], 11:[]}
        self._C = [1, 5, 6, 7, 3, 6, 4, 2, 9, 8, 1]
        self._V = sorted(self._G.keys())

        # pre- constraint list (reverse E and accumulate)
        self._pre = {}
        for _key,_item in self._G.items():
            for i in _item:
                if i in self._pre:
                    self._pre[i].append(_key)
                else:
                    self._pre[i] = [_key]
