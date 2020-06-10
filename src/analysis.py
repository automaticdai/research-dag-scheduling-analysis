#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle

import networkx as nx

from graph import find_longest_path_dfs, find_predecesor, find_successor, get_subpath_between

# Bars L: x < y
# Bars EQ: x = y
# Bars G: x > y
# Column: 'WCET-m2','Full-m2','Half-m2','WCET-m4','Full-m4', 'Half-m4'
bars_L = [0, 0, 0, 0, 0, 0]
bars_EQ = [0, 0, 0, 0, 0, 0]
bars_G = [0, 0, 0, 0, 0, 0]

def plot_boxplots_from_trace():
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
            for i in makespans_raw:
                ms = int(i)
                # expand data (simply repeat) for non-randomised result
                # this to make sure each bar chart has the same number of data
                if policy=="eligibility":
                    for _ in range(100):
                        if e_model=="WCET":
                            for _ in range(100):
                                makespans.append(ms)
                        else:
                            makespans.append(ms)
                else:
                    # Random + WCET
                    if e_model=="WCET":
                        makespans.append(ms)
                    else:
                        makespans.append(ms)

            boxplot_data.append(makespans)

            label = policy + "-" + e_model + "-m" + str(m)
            boxplot_label.append(label)

            cnt = cnt + 1

            # every 12 is for one test case
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

                # count the frequency
                
                # Bars L: x < y
                # Bars EQ: x = y
                # Bars G: x > y
                # Column: 'WCET-m2','Full-m2','Half-m2','WCET-m4','Full-m4', 'Half-m4'

                # WCET-m2
                column_idx = [1,3,5,8,10,12]
                for column in range(6):
                    b = np.array(boxplot_data[0 + column_idx[column]]) #random
                    a = np.array(boxplot_data[1 + column_idx[column]]) #EO

                    l = np.count_nonzero(a < b)
                    eq = np.count_nonzero(a == b)
                    g = np.count_nonzero(a > b)

                    bars_L[column] = bars_L[column] + l
                    bars_EQ[column] = bars_EQ[column] + eq
                    bars_G[column] = bars_G[column] + g

                print("One testset done.")

                # clean
                cnt = 0
                boxplot_label = []
                boxplot_data = []

    # plot the frequency table
    for i in range(6):
        bars_L[i] = bars_L[i] / 2000
        bars_EQ[i] = bars_EQ[i] / 2000
        bars_G[i] = bars_G[i] / 2000

    plot_stacked_barchart()


def plot_stacked_barchart():
    # y-axis in bold
    rc('font', weight='bold')

    # bars1 = [12, 28, 1, 8, 8, 22]
    # bars2 = [28, 7, 16, 4, 10, 10]
    # bars3 = [25, 3, 23, 25, 22, 17]

    # Heights of bars1 + bars2
    bars = np.add(bars_L, bars_EQ).tolist()

    # The position of the bars on the x-axis
    r = [0, 1, 2, 4, 5, 6]

    # Names of group and bar width
    names = ['WCET-m2','Full-m2','Half-m2','WCET-m4','Full-m4', 'Half-m4']
    barWidth = 0.8

    # Create brown bars
    plt.bar(r, bars_L, color='#f55442', edgecolor='black', width=barWidth)
    # Create green bars (middle), on top of the firs ones
    plt.bar(r, bars_EQ, bottom=bars_L, color='#5145f7', edgecolor='black', width=barWidth)
    # Create green bars (top)
    plt.bar(r, bars_G, bottom=bars, color='#42eb63', edgecolor='black', width=barWidth)

    # Custom X axis
    plt.xticks(r, names, fontweight='bold')
    #plt.xlabel("Method Group")
    plt.ylabel("Frequency")
    plt.legend(["EO < RND","EO = RND","EO > RND"])

    # Show graphic
    plt.show()


def plot_rta():
    boxplot_data = []

    diff_array = pickle.load(open("m2.p", "rb"))
    boxplot_data.append(diff_array)
    cm2 = (sum(i > 0  for i in diff_array))

    diff_array = pickle.load(open("m4.p", "rb"))
    boxplot_data.append(diff_array)
    cm4 = (sum(i > 0  for i in diff_array))

    diff_array = pickle.load(open("m6.p", "rb"))
    boxplot_data.append(diff_array)
    cm6 = (sum(i > 0  for i in diff_array))

    diff_array = pickle.load(open("m8.p", "rb"))
    boxplot_data.append(diff_array)
    cm8 = (sum(i > 0  for i in diff_array))

    # plot the boxplot
    bp1 = plt.boxplot(boxplot_data,
                        notch=False,  # notch shape
                        vert=True,  # vertical box alignment
                        patch_artist=True,  # fill with color
                        showfliers=True)

    colors = ['lightblue', 'lightgreen', 'pink', 'orange']
    for idx, box in enumerate(bp1['boxes']):
        box.set_facecolor(colors[idx])


    plt.xticks([1,2,3,4], ["m=2", "m=4", "m=6", "m=8"])
    plt.ylabel("Precentage of Improvement (%)")

    plt.show()

    # plot the bar charts
    N = 4
    a_means = (cm2, cm4, cm6, cm8)
    b_means = (10000-cm2, 10000-cm4, 10000-cm6, 10000-cm8)

    ind = np.arange(N) 
    width = 0.35       
    plt.bar(ind, a_means, width, label='RTA_new is better')
    plt.bar(ind + width, b_means, width, label='RTA_new is not better')

    plt.ylabel('# of cases')
    plt.title('RTA_new compared with RTA_traditional')

    plt.xticks(ind + width / 2, ('m = 2', 'm = 4', 'm = 6', 'm = 8'))
    plt.legend(loc='best')
    plt.show()


def exp_rta():
    diff_array = []

    print("{:>12s} {:>12s} {:>12s}".format("Baseline", "RTA_New", "Diff"))
    print("----------------------------------------")
    for tau in range(10000):
        m = 8
        rta_baseline = rta_np(tau, m)
        rta_a, rta_b, rta_c = rta_new(tau, m)
        diff = max((rta_baseline - rta_a), 0) / rta_baseline * 100
        diff_array.append(diff)
        print("{:>12.1f} {:>12.1f} {:>12.1f}".format(rta_baseline, rta_a, diff))
    print("----------------------------------------")
    pickle.dump(diff_array, open("m8.p", "wb"))


if __name__ == "__main__":
    #plot_boxplots_from_trace()

    #exp_rta()
    #plot_rta()