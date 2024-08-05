import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import re
import sys
import os
import csv

# --------------------------------------------------------------
# Main function
# --------------------------------------------------------------
if __name__ == "__main__":

    # get the chameleon-stat input file
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    list_input_files = os.listdir(input_folder)
    list_output_files = os.listdir(output_folder)

    print(list_input_files)
    print(list_output_files)

    res = [sub for sub in list_output_files if 'kk_*_32' in sub]
    print(res)

    exit(1)

    df_input = pd.read_csv(inputfile)
    df_output = pd.read_csv(outputfile)
    
    arr_total_load_before_rebalancing = df_input['L']
    arr_total_load_after_rebalancing = df_output['L']

    max_input_load = np.max(arr_total_load_before_rebalancing)
    avg_input_load = np.average(arr_total_load_before_rebalancing)

    max_output_load = np.max(arr_total_load_after_rebalancing)
    avg_output_load = np.average(arr_total_load_after_rebalancing)

    Rimb_input = max_input_load / avg_input_load - 1
    Rimb_output = max_output_load / avg_output_load - 1

    Speedup = max_input_load / max_output_load

    print('Rimb after rebalancing: {:.5f}'.format(Rimb_output))
    print('Speedup after rebalancing: {:.5f}'.format(Speedup))

    arr_remote_tasks = df_output['num_remote']
    num_total_mig_tasks = np.sum(arr_remote_tasks)
    num_avg_mig_tasks_per_proc = np.average(arr_remote_tasks)
    print('Num. total migrated tasks: {:.5f}'.format(num_total_mig_tasks))
    print('Num. avg migrated tasks/proc: {:.5f}'.format(num_avg_mig_tasks_per_proc))
