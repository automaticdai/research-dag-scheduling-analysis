#!/usr/bin/python3
# -*- coding: utf-8 -*-

# DAG Scheduling Simulator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pickle

import networkx as nx

from graph import find_longest_path_dfs, find_predecesor, find_successor, get_subpath_between
from rta_alphabeta_new import rta_np_classic, load_task


# return the column of a 2D array
def column(matrix, i):
    return [row[i] for row in matrix]


# ==============================================================================
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
                makespan = rta_np_classic(taskset_idx, 2)
                boxplot_data.insert(0, [makespan])
                boxplot_label.insert(0, "rta-m2")

                makespan = rta_np_classic(taskset_idx, 4)
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
# ==============================================================================


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


def rtss_boxplot_rta():
    # load data
    results = pickle.load(open("r_0627_01/m8.p", "rb"))

    task_idx = column(results, 0)
    R0 = column(results, 1)
    R_AB = column(results, 2)
    R_AB_EO = column(results, 3)
    R_AB_TPDS = column(results, 4)
    R_TPDS = column(results, 5)

    # clean data
    for idx, value in enumerate(R0):
        R_AB[idx] = R_AB[idx] * 1.0 / value 

        if R_AB[idx] > 1:
            #R_AB[idx] = 1
            pass

        R_AB_EO[idx] = R_AB_EO[idx] * 1.0 / value 
        R_AB_TPDS[idx] = R_AB_TPDS[idx] * 1.0 / value 
        R_TPDS[idx] = R_TPDS[idx] * 1.0 / value 

        R0[idx] =  1


    # boxplot 
    boxplot_data = [R0, R_AB, R_AB_EO, R_AB_TPDS, R_TPDS]



    bp1 = plt.boxplot(boxplot_data,
                        notch=False,  # notch shape
                        vert=True,  # vertical box alignment
                        patch_artist=True,  # fill with color
                        showfliers=True)

    colors = ['lightblue', 'lightgreen', 'pink', 'orange', 'red']
    for idx, box in enumerate(bp1['boxes']):
         box.set_facecolor(colors[idx])
    
    plt.title('RTA')
    plt.xticks([1,2,3,4,5], ["R0","R_AB","R_AB_EO","R_AB_TPDS","R_TPDS"])
    plt.show()


def rtss_boxplot_simulation():
    # load data
    results = pickle.load(open("m2-simu.p", "rb"))

    M0 = column(results, 0)
    M_EO = column(results, 1)
    M_TPDS = column(results, 2)
    M_EMSOFT = column(results, 3)

    # clean data
    for idx, value in enumerate(M0):
        M_EO[idx] = M_EO[idx] * 1.0 / value 
        if M_EO[idx] > 1:
            M_EO[idx] = 1

        M_TPDS[idx] = M_TPDS[idx] * 1.0 / value 
        M_EMSOFT[idx] = M_EMSOFT[idx] * 1.0 / value 

        M0[idx] =  1


    # boxplot 
    boxplot_data = [M0, M_EO, M_TPDS, M_EMSOFT]



    bp1 = plt.boxplot(boxplot_data,
                        notch=False,  # notch shape
                        vert=True,  # vertical box alignment
                        patch_artist=True,  # fill with color
                        showfliers=True)

    colors = ['lightblue', 'lightgreen', 'pink', 'orange']
    for idx, box in enumerate(bp1['boxes']):
        box.set_facecolor(colors[idx])
    
    plt.title('Simulation')
    plt.xticks([1,2,3,4], ["M0","M_EO","M_TPDS","M_EMSOFT"])
    plt.show()


def comparison_RTA_Simu():
    # load data (RTA)
    results = pickle.load(open("m2.p", "rb"))

    task_idx = column(results, 0)
    R0 = column(results, 1)
    R_AB = column(results, 2)
    R_AB_EO = column(results, 3)
    R_AB_TPDS = column(results, 4)
    R_TPDS = column(results, 5)

    # load data (simu)
    results = pickle.load(open("m2-simu.p", "rb"))

    M0 = column(results, 0)
    M_EO = column(results, 1)
    M_TPDS = column(results, 2)
    M_EMSOFT = column(results, 3)

    # rta vs simu
    for idx, i in enumerate(task_idx):
        print(M_EO[i], R0[i], R_AB_EO[i], M_EO[i] <= R_AB_EO[i])

    # M_EO vs 








basefolder = "./r_0628_01/"

def comparison_A_B_counting(A, B):
    # rta vs simu
    count_less = 0
    count_equal = 0
    count_larger = 0

    advantage_cases = []

    for i in range(1000):
        a = A[i]
        b = B[i]

        #print(A[i] < B[i])
        
        if a < b:
            count_less = count_less + 1
            diff_percentage = (b-a) * 1.0 / b * 100
            advantage_cases.append(diff_percentage)
            #print(diff_percentage)
    
        if a == b:
            count_equal = count_equal + 1
        
        if a > b:
            count_larger = count_larger + 1
    
    #print(count_less, count_equal, count_larger)
    print(sum(advantage_cases) / len(advantage_cases), max(advantage_cases), min(advantage_cases))

    return count_less, count_equal, count_larger


def set_box_color(bp, color):
    plt.setp(bp['boxes'], color=color)
    plt.setp(bp['whiskers'], color=color)
    plt.setp(bp['caps'], color=color)
    plt.setp(bp['medians'], color=color)


def boxplot_rta_grouped_scale_m():
    data_a = []
    data_b = []
    data_c = []
    data_d = []

    for m in [2, 4, 6, 7, 8]:
        results = pickle.load(open(basefolder + "m{}.p".format(m), "rb"))

        task_idx = column(results, 0)
        R0 = column(results, 1)
        R_AB = column(results, 2)
        R_AB_EO = column(results, 3)
        R_AB_TPDS = column(results, 4)
        R_TPDS = column(results, 5)

        # R(AB) is bounded to R0
        max_R0 = 0
        for i, value in enumerate(R0):
            if R_AB[i] > value:  R_AB[i] = value

            if value > max_R0:  max_R0 = value

        # R_AB_EO is bounded to R_TPDS
        for i, value in enumerate(R_TPDS):
            if R_AB_EO[i] > value:
                R_AB_EO[i] = value

        # normalise
        for i, _ in enumerate(R0):
            scale_value = 7140
            R0[i] = R0[i] * 1.0 / scale_value
            R_AB[i] = R_AB[i] * 1.0 / scale_value
            R_AB_EO[i] = R_AB_EO[i] * 1.0 / scale_value
            R_TPDS[i] = R_TPDS[i] * 1.0 / scale_value
            
        data_a.append(R0)
        data_b.append(R_AB)
        data_c.append(R_TPDS)
        data_d.append(R_AB_EO)


    ticks = ['m=2', 'm=4', 'm=6', 'm=7', 'm=8']

    plt.figure()

    bp1 = plt.boxplot(data_a, positions=np.array(range(len(data_a)))*4.0-1.2, sym='', widths=0.6) # patch_artist=True
    bp2 = plt.boxplot(data_b, positions=np.array(range(len(data_b)))*4.0-0.4, sym='', widths=0.6)
    bp3 = plt.boxplot(data_c, positions=np.array(range(len(data_c)))*4.0+0.4, sym='', widths=0.6)
    bp4 = plt.boxplot(data_d, positions=np.array(range(len(data_d)))*4.0+1.2, sym='', widths=0.6)

    set_box_color(bp1, '#e6550d') # colors are from http://colorbrewer2.org/
    set_box_color(bp2, '#2C7BB6')
    set_box_color(bp3, '#427526')
    set_box_color(bp4, '#fdae6b')

    # fill with colors
    # colors = ['pink', 'lightblue', 'lightgreen']
    # for bplot in (bp1, bp2, bp3, bp4):
    #     for patch, color in zip(bplot['boxes'], colors):
    #         patch.set_facecolor(color)
            
    # draw temporary red and blue lines and use them to create a legend
    plt.plot([], c='#e6550d', label='classic')
    plt.plot([], c='#2C7BB6', label='rta-cfp')
    plt.plot([], c='#427526', label='he2019')
    plt.plot([], c='#fdae6b', label='rta-cfp-eo')
    plt.legend()

    plt.xticks(range(0, len(ticks) * 4, 4), ticks)
    #plt.xlim(-2, len(ticks) * 2)
    #plt.ylim(0, 8)
    plt.tight_layout()
    plt.grid(which='major', linestyle=':', linewidth='0.5')
    plt.show()


def boxplot_rta_grouped_scale_p():
    data_a = []
    data_b = []
    data_c = []
    data_d = []

    m = 4
    for p in [4, 5, 6, 7, 8]:
        results = pickle.load(open(basefolder + "exp2/m{}-p{}.p".format(m, p), "rb"))

        task_idx = column(results, 0)
        R0 = column(results, 1)
        R_AB = column(results, 2)
        R_AB_EO = column(results, 3)
        R_AB_TPDS = column(results, 4)
        R_TPDS = column(results, 5)

        # R(AB) is bounded to R0
        max_R0 = 0
        for i, value in enumerate(R0):
            if R_AB[i] > value:  R_AB[i] = value

            if value > max_R0:  max_R0 = value

        # R_AB_EO is bounded to R_TPDS
        for i, value in enumerate(R_TPDS):
            if R_AB_EO[i] > value:
                R_AB_EO[i] = value

        # normalise
        for i, _ in enumerate(R0):
            scale_value = 7340
            R0[i] = R0[i] * 1.0 / scale_value
            R_AB[i] = R_AB[i] * 1.0 / scale_value
            R_AB_EO[i] = R_AB_EO[i] * 1.0 / scale_value
            R_TPDS[i] = R_TPDS[i] * 1.0 / scale_value
            
        data_a.append(R0)
        data_b.append(R_AB)
        data_c.append(R_TPDS)
        data_d.append(R_AB_EO)


    ticks = ['p=4', 'p=5', 'p=6', 'p=7', 'p=8']

    plt.figure()

    bp1 = plt.boxplot(data_a, positions=np.array(range(len(data_a)))*4.0-1.2, sym='', widths=0.6) # patch_artist=True
    bp2 = plt.boxplot(data_b, positions=np.array(range(len(data_b)))*4.0-0.4, sym='', widths=0.6)
    bp3 = plt.boxplot(data_c, positions=np.array(range(len(data_c)))*4.0+0.4, sym='', widths=0.6)
    bp4 = plt.boxplot(data_d, positions=np.array(range(len(data_d)))*4.0+1.2, sym='', widths=0.6)

    set_box_color(bp1, '#e6550d') # colors are from http://colorbrewer2.org/
    set_box_color(bp2, '#2C7BB6')
    set_box_color(bp3, '#427526')
    set_box_color(bp4, '#fdae6b')

    # fill with colors
    # colors = ['pink', 'lightblue', 'lightgreen']
    # for bplot in (bp1, bp2, bp3, bp4):
    #     for patch, color in zip(bplot['boxes'], colors):
    #         patch.set_facecolor(color)
            
    # draw temporary red and blue lines and use them to create a legend
    plt.plot([], c='#e6550d', label='classic')
    plt.plot([], c='#2C7BB6', label='rta-cfp')
    plt.plot([], c='#427526', label='he2019')
    plt.plot([], c='#fdae6b', label='rta-cfp-eo')
    plt.legend()

    plt.xticks(range(0, len(ticks) * 4, 4), ticks)
    #plt.xlim(-2, len(ticks) * 2)
    #plt.ylim(0, 8)
    plt.tight_layout()
    plt.grid(which='major', linestyle=':', linewidth='0.5')
    plt.show()


def boxplot_rta_grouped_scale_L():
    data_a = []
    data_b = []
    data_c = []
    data_d = []

    m = 4
    p = 8
    for L in [0.5, 0.6, 0.7, 0.8, 0.9]:
        results = pickle.load(open(basefolder + "exp3/m{}-p{}-L{:.2f}.p".format(m, p, L), "rb"))

        task_idx = column(results, 0)
        R0 = column(results, 1)
        R_AB = column(results, 2)
        R_AB_EO = column(results, 3)
        R_AB_TPDS = column(results, 4)
        R_TPDS = column(results, 5)

        # R(AB) is bounded to R0
        max_R0 = 0
        for i, value in enumerate(R0):
            if R_AB[i] > value:  R_AB[i] = value

            if value > max_R0:  max_R0 = value

        # R_AB_EO is bounded to R_TPDS
        for i, value in enumerate(R_TPDS):
            if R_AB_EO[i] > value:
                R_AB_EO[i] = value

        # normalise
        for i, _ in enumerate(R0):
            scale_value = 7340
            R0[i] = R0[i] * 1.0 / scale_value
            R_AB[i] = R_AB[i] * 1.0 / scale_value
            R_AB_EO[i] = R_AB_EO[i] * 1.0 / scale_value
            R_TPDS[i] = R_TPDS[i] * 1.0 / scale_value
            
        data_a.append(R0)
        data_b.append(R_AB)
        data_c.append(R_TPDS)
        data_d.append(R_AB_EO)


    ticks = ['p=0.5', 'p=0.6', 'p=0.7', 'p=0.8', 'p=0.9']

    plt.figure()

    bp1 = plt.boxplot(data_a, positions=np.array(range(len(data_a)))*4.0-1.2, sym='', widths=0.6) # patch_artist=True
    bp2 = plt.boxplot(data_b, positions=np.array(range(len(data_b)))*4.0-0.4, sym='', widths=0.6)
    bp3 = plt.boxplot(data_c, positions=np.array(range(len(data_c)))*4.0+0.4, sym='', widths=0.6)
    bp4 = plt.boxplot(data_d, positions=np.array(range(len(data_d)))*4.0+1.2, sym='', widths=0.6)

    set_box_color(bp1, '#e6550d') # colors are from http://colorbrewer2.org/
    set_box_color(bp2, '#2C7BB6')
    set_box_color(bp3, '#427526')
    set_box_color(bp4, '#fdae6b')

    # fill with colors
    # colors = ['pink', 'lightblue', 'lightgreen']
    # for bplot in (bp1, bp2, bp3, bp4):
    #     for patch, color in zip(bplot['boxes'], colors):
    #         patch.set_facecolor(color)
            
    # draw temporary red and blue lines and use them to create a legend
    plt.plot([], c='#e6550d', label='classic')
    plt.plot([], c='#2C7BB6', label='rta-cfp')
    plt.plot([], c='#427526', label='he2019')
    plt.plot([], c='#fdae6b', label='rta-cfp-eo')
    plt.legend()

    plt.xticks(range(0, len(ticks) * 4, 4), ticks)
    #plt.xlim(-2, len(ticks) * 2)
    #plt.ylim(0, 8)
    plt.tight_layout()
    plt.grid(which='major', linestyle=':', linewidth='0.5')
    plt.show()


def hist_sensitivity_L():
    data_a = []
    data_b = []
    data_c = []
    data_d = []

    x = []
    y = []
    z = []

    # # p = 8 by default
    # for m in [4]:
    #     results = pickle.load(open(basefolder + "exp1/m{}.p".format(m), "rb"))

    #     task_idx = column(results, 0)
    #     R0 = column(results, 1)
    #     R_AB = column(results, 2)
    #     R_AB_EO = column(results, 3)
    #     R_AB_TPDS = column(results, 4)
    #     R_TPDS = column(results, 5)

    #     for i, value in enumerate(R_TPDS):
    #         a = R_AB_EO[i]
    #         b = R_TPDS[i] 
    #         #if a < b:
    #         # load task & get L%
    #         G_dict, C_dict, C_array, lamda, VN_array, L, W = load_task(task_idx[i])
    #         L_ratio = L * 1.0 / W

    #         diff_percentage = (b - a) * 1.0 / b * 100
    #         x.append(L_ratio)
    #         y.append(diff_percentage)

    # results = {}
    # results["x"] = x
    # results["y"] = y
    # pickle.dump(results, open("s-l-m{}.p".format(m), "wb"))

    m = 4
    results = pickle.load(open(basefolder + "s-l-m{}.p".format(m), "rb"))

    x = results["x"]
    y = results["y"]

    x_new = []
    y_new = []
    for i, j in zip(x,y):
        if j > 0 and i <= 0.5:
            x_new.append(i)
            y_new.append(j)

    plt.figure()
    #plt.scatter(x, y, marker='o');
    plt.hist2d(x_new, y_new)
    plt.xlabel("% of L in W")
    plt.ylabel("% of improvement")
    plt.show()
    
    return



def barchart_simu_grouped():
    # y-axis in bold
    rc('font', weight='bold')

    bars_L = []
    bars_EQ = []
    bars_G = []

    for m in [2, 4, 6, 8]:
        # load data (simu)
        results = pickle.load(open(basefolder + "exp1/m{}.p".format(m), "rb")) # 
        RTA_EO = column(results, 3)
        RTA_TPDS = column(results, 4)

        L, EQ, G = comparison_A_B_counting(RTA_EO, RTA_TPDS)
        bars_L.append(L)
        bars_EQ.append(EQ)
        bars_G.append(G)

    # Heights of bars1 + bars2
    bars = np.add(bars_L, bars_EQ).tolist()

    # The position of the bars on the x-axis
    r = [0, 1, 2, 3]

    # Names of group and bar width
    names = ['m=2', 'm=4', 'm=6', 'm=8']

    # Create brown bars
    barWidth = 0.6
    plt.bar(r, bars_L, color='#f55442', edgecolor='black', width=barWidth)
    # Create green bars (middle), on top of the firs ones
    #plt.bar(r, bars_EQ, bottom=bars_L, color='#5145f7', edgecolor='black', width=barWidth)
    # Create green bars (top)
    plt.bar(r, bars_G, bottom=bars_L, color='#5145f7', edgecolor='black', width=barWidth)

    # Custom X axis
    plt.xticks(r, names, fontweight='bold')
    #plt.xlabel("Method Group")
    plt.ylabel("Frequency")
    plt.legend(["EO < He2019", "EO > He2019"])

    plt.grid(which='major', linestyle=':', linewidth='0.5')

    # Show graphic
    plt.show()


if __name__ == "__main__":
    #rtss_boxplot_rta()
    #rtss_boxplot_simulation()
    #comparison_EO_TPDS()
    
    #boxplot_rta_grouped_scale_m()
    #barchart_simu_grouped()
    #boxplot_rta_grouped_scale_p()
    boxplot_rta_grouped_scale_L()
    #hist_sensitivity_L()

    