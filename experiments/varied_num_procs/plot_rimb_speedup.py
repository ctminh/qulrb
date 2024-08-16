import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import imageio
import sys
import os
import csv
import re

# --------------------------------------------------------------
# Main function
# --------------------------------------------------------------
if __name__ == "__main__":

    # extract data
    imb_file = sys.argv[1]
    speedup_file = sys.argv[2]
    df_imb_ratios = pd.read_csv(imb_file)
    df_speedup = pd.read_csv(speedup_file)

    # create figure and axis objects with subplots()
    # set the size, 13 is width, 12 is height
    gs = gridspec.GridSpec(1,2)
    fig = plt.figure(figsize=(10,4))
    ax1 = plt.subplot(gs[0,0])
    ax2 = plt.subplot(gs[0,1])
    
    # ---------------------------------------------------------
    # Line styles
    # ---------------------------------------------------------
    lstyles = ['dashed', 'dashed', 'dashed', 'solid', 'solid','solid','solid','solid']
    ldashstyles = ['dashed', 'dashed', 'dashed', 'dashed', 'dashed', 'dashed', 'dashed', 'dashed']
    lcolors = ['black', 'blue', 'darkgreen', 'red', 'darkorange', 'purple', 'teal', 'brown']
    lmarkers = ['*', '^', 'o', 's', 'P', 'p', 'd', 'x']
    alphas = [0.3, 1.0, 1.0, 0.3, 1.0, 1.0, 1.0, 1.0]
    legend_size = 9
    ticklabel_size = 10
    legend_labels = ['Greedy', 'KK', 'ProactLB', 'Q_CQM1_k1', 'Q_CQM1_k2', 'Q_CQM2_k1', 'Q_CQM2_k2']

    # ---------------------------------------------------------
    # 1. The imb-ratio chart
    # ---------------------------------------------------------
    ax1.set_title('Imbalance ratio after rebalancing')
    ax1_ticks = ['4', '8', '16', '32', '64']
    ax1_indices = np.arange(len(ax1_ticks))
    ax1.plot(ax1_indices, df_imb_ratios['greedy'], label=legend_labels[0], linestyle=lstyles[0], marker=lmarkers[0], color=lcolors[0])
    ax1.plot(ax1_indices, df_imb_ratios['kk'], label=legend_labels[1], linestyle=lstyles[1], marker=lmarkers[1], color=lcolors[1])
    ax1.plot(ax1_indices, df_imb_ratios['proactlb'], label=legend_labels[2], linestyle=lstyles[2], marker=lmarkers[2], color=lcolors[2])
    # ax1.plot(ax1_indices, df_imb_ratios['gurobi'], label=legend_labels[3], linestyle=lstyles[3], marker=lmarkers[3], color=lcolors[3])
    ax1.plot(ax1_indices, df_imb_ratios['qubo1_cqm_k1'], label=legend_labels[3], linestyle=lstyles[4], marker=lmarkers[4], color=lcolors[4])
    ax1.plot(ax1_indices, df_imb_ratios['qubo1_cqm_k2'], label=legend_labels[4], linestyle=lstyles[5], marker=lmarkers[5], color=lcolors[5])
    ax1.plot(ax1_indices, df_imb_ratios['qubo2_cqm_k1'], label=legend_labels[5], linestyle=lstyles[6], marker=lmarkers[6], color=lcolors[6])
    ax1.plot(ax1_indices, df_imb_ratios['qubo2_cqm_k2'], label=legend_labels[6], linestyle=lstyles[7], marker=lmarkers[7], color=lcolors[7])
    ax1.set_xticks(ax1_indices)
    ax1.set_xticklabels(ax1_ticks, fontsize=ticklabel_size)
    # ax1.set_ylim(-0.5, 0.5)
    ax1.set_yscale('log')
    ax1.set_xlabel("# compute nodes")
    ax1.set_ylabel("Imbalance")
    ax1.legend(fontsize=legend_size, loc='upper left')
    ax1.grid()

    # ---------------------------------------------------------
    # 2. The speedup chart
    # ---------------------------------------------------------
    ax2.set_title('Speedup')
    ax2_ticks = ['4', '8', '16', '32', '64']
    ax2_indices = np.arange(len(ax2_ticks))
    ax2.plot(ax2_indices, df_speedup['greedy'], label=legend_labels[0], linestyle=lstyles[0], marker=lmarkers[0], color=lcolors[0])
    ax2.plot(ax2_indices, df_speedup['kk'], label=legend_labels[1], linestyle=lstyles[1], marker=lmarkers[1], color=lcolors[1])
    ax2.plot(ax2_indices, df_speedup['proactlb'], label=legend_labels[2], linestyle=lstyles[2], marker=lmarkers[2], color=lcolors[2])
    # ax2.plot(ax2_indices, df_speedup['gurobi'], label=legend_labels[3], linestyle=lstyles[3], marker=lmarkers[3], color=lcolors[3])
    ax2.plot(ax2_indices, df_speedup['qubo1_cqm_k1'], label=legend_labels[3], linestyle=lstyles[4], marker=lmarkers[4], color=lcolors[4])
    ax2.plot(ax2_indices, df_speedup['qubo1_cqm_k2'], label=legend_labels[4], linestyle=lstyles[5], marker=lmarkers[5], color=lcolors[5])
    ax2.plot(ax2_indices, df_speedup['qubo2_cqm_k1'], label=legend_labels[5], linestyle=lstyles[6], marker=lmarkers[6], color=lcolors[6])
    ax2.plot(ax2_indices, df_speedup['qubo2_cqm_k2'], label=legend_labels[6], linestyle=lstyles[7], marker=lmarkers[7], color=lcolors[7])
    ax2.set_xticks(ax2_indices)
    ax2.set_xticklabels(ax2_ticks, fontsize=ticklabel_size)
    ax2.set_ylim(0.0, 6.0)
    ax2.set_xlabel("# compute nodes")
    ax2.set_ylabel("Speedup")
    ax2.legend(fontsize=legend_size, loc='upper left')
    ax2.grid()

    # save the figure
    print("--------------------------------------------------------------------")
    fig_filename = "./varied_numprocs_imbs_speedup.pdf"
    print("Write file to: " + fig_filename)
    plt.savefig(os.path.join("./", fig_filename), bbox_inches='tight')
    print("--------------------------------------------------------------------")
