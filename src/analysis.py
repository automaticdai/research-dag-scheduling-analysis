#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from graph import find_longest_path_dfs


def rta_np(task_idx, m):
    # load the DAG task
    dag_task_file = "./data/Tau_{:d}.gpickle".format(task_idx)
    G = nx.read_gpickle(dag_task_file)

    # formulate the graph list
    G_dict = {}
    C_dict = {}
    V_array = []
    max_key = 0
    for u, v, weight in G.edges(data='label'):
        if u not in G_dict:
            G_dict[u] = [v]
        else:
            G_dict[u].append(v)

        if v > max_key:
            max_key = v
        
        if u not in V_array:
            V_array.append(u)
        if v not in V_array:
            V_array.append(v)
        
        C_dict[u] = weight
    G_dict[max_key] = []

    # formulate the c list
    C_exp = []
    for key in sorted(C_dict):
        C_exp.append(C_dict[key])

    C_exp.append(1)

    V_array.sort()
    Li, _ = find_longest_path_dfs(G_dict, V_array[0], V_array[-1], C_exp)
    Wi = sum(C_exp)

    makespan = Li + 1 / m * (Wi - Li)

    return makespan


# df = pd.DataFrame(index = [x for x in range(0,10)])
# for col in range(1,5):
#     df[col] = df.index * col/10

# fig, ax = plt.subplots()
# bp = df.plot.box(
#             ax=ax,
#             whis=[5, 95],
#             showcaps=True,
#             showfliers=False,
#             whiskerprops = {'color':'k','linewidth':0.5,'linestyle':'solid'},
#             capprops={'color': 'k', 'linewidth': 0.5, 'linestyle': 'solid'},
#             medianprops = {'color':'k','linewidth': 0.5, 'linestyle': 'solid'}
#             )

#result_path = "./results/{:d}/{:d}/{:s}/{:s}".format(task_idx, m, algorithm_name, e_model)
#Path(result_path).mkdir(parents=True, exist_ok=True)


def plot():
    result_dict = {}
    boxplot_data = []
    boxplot_label = []
    cnt = 0

    with open('./results/results.log', 'r') as f:
        for line in f:
            cc = line.strip().split(";")
            
            taskset_idx = int(cc[0])
            policy = cc[1]
            m = int(cc[2])
            e_model = cc[3]

            makespans_raw = cc[4].lstrip("[").rstrip("]").split(",")
            makespans = []
            for i in makespans_raw:  makespans.append(int(i))
            result_dict[taskset_idx] = makespans
            boxplot_data.append(makespans)

            label = policy + "-" + e_model + "-m" + str(m)
            boxplot_label.append(label)

            cnt = cnt + 1

            if cnt == 12:
                # reorder the sequence
                i = boxplot_data
                j = boxplot_label
                i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11] = i[0], i[6], i[1], i[7], i[2], i[8], i[3], i[9], i[4], i[10], i[5], i[11]
                j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9], j[10], j[11] = j[0], j[6], j[1], j[7], j[2], j[8], j[3], j[9], j[4], j[10], j[5], j[11]

                # use RTA to get makespan
                makespan = rta_np(taskset_idx, 2)
                boxplot_data.insert(0, [makespan])
                boxplot_label.insert(0, "rta-m2")

                makespan = rta_np(taskset_idx, 4)
                boxplot_data.insert(7, [makespan])
                boxplot_label.insert(7, "rta-m4")

                fig, ax1 = plt.subplots(figsize=(10, 6))
                fig.canvas.set_window_title('MOCHA Analysis Toolbox')
                plt.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.35)

                bp1 = plt.boxplot(boxplot_data,
                                    notch=False,  # notch shape
                                    vert=True,  # vertical box alignment
                                    patch_artist=True,  # fill with color
                                    showfliers=True)

                colors = ['red', 'pink', 'pink', 'lightblue', 'lightblue', 'lightgreen', 'lightgreen', 'red', 'pink', 'pink', 'lightblue', 'lightblue', 'lightgreen', 'lightgreen']
                for idx, box in enumerate(bp1['boxes']):
                    box.set_facecolor(colors[idx])
                    #box.set(color=colors[idx], linewidth=1)

                xtickNames = plt.setp(ax1, xticklabels=boxplot_label)
                plt.setp(xtickNames, rotation=85, fontsize=10)
                
                ax1.set_title('Comparison of Eligibility and Random (Tau {:d})'.format(taskset_idx))
                ax1.set_ylabel('Makespan')

                # plot and save
                #plt.show()
                fig.savefig('./results/boxplot_{:d}.png'.format(taskset_idx))

                plt.close(fig)

                # clean
                cnt = 0
                boxplot_label = []
                boxplot_data = []


#print(rta_np(18, 4))
plot()