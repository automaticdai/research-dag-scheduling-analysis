#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame(index = [x for x in range(0,10)])
for col in range(1,5):
    df[col] = df.index * col/10

fig, ax = plt.subplots()
bp = df.plot.box(
            ax=ax,
            whis=[5, 95],
            showcaps=True,
            showfliers=False,
            whiskerprops = {'color':'k','linewidth':0.5,'linestyle':'solid'},
            capprops={'color': 'k', 'linewidth': 0.5, 'linestyle': 'solid'},
            medianprops = {'color':'k','linewidth': 0.5, 'linestyle': 'solid'}
            )

def RTA_NP_Classic(m, Wi, Li):
    makespan = Li + 1 / m (Wi - Li)
    return makespan
