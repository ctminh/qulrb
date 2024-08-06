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
    # algorithm = sys.argv[3]

    list_input_files = os.listdir(input_folder)
    list_output_files = os.listdir(output_folder)

    list_algorithms = ['greedy', 'kk', 'proact2', 'gurobi', 'qubo_cqm_k1', 'qubo_cqm_k2']
    num_procs = 8
    num_tasks = [8, 16, 32, 64, 128, 256, 512, 1024, 2048]

    data_balanced_imbs = {'num_tasks': num_tasks}
    data_balanced_speedups = {'num_tasks': num_tasks}
    data_total_num_mig_tasks = {'num_tasks': num_tasks}
    data_avg_num_mig_tasks_per_proc = {'num_tasks': num_tasks}

    for algorithm in list_algorithms:
        arr_balanced_rimbs = []
        arr_speedups = []
        arr_total_mig_tasks = []
        arr_avg_mig_tasks_per_proc = []

        for nt in num_tasks:
            # identify the input and output files
            input = input_folder + 'input_table_' + str(num_procs) + 'nodes_' + str(nt) + 'tasks.csv'
            output = output_folder + 'output_' + algorithm + '_lrp_' + str(num_procs) + 'nodes_' + str(nt) + 'tasks.csv'

            if os.path.isfile(input) and os.path.isfile(output):
                # read the input and output files
                df_input = pd.read_csv(input)
                df_output = pd.read_csv(output)

                # get the load information
                arr_total_load_before_rebalancing = df_input['L']
                arr_total_load_after_rebalancing = df_output['L']
                max_input_load = np.max(arr_total_load_before_rebalancing)
                avg_input_load = np.average(arr_total_load_before_rebalancing)
                max_output_load = np.max(arr_total_load_after_rebalancing)
                avg_output_load = np.average(arr_total_load_after_rebalancing)
                Rimb_input = max_input_load / avg_input_load - 1
                Rimb_output = max_output_load / avg_output_load - 1
                Speedup = max_input_load / max_output_load

                # get the number of tasks information
                arr_remote_tasks = df_output['num_remote']
                num_total_mig_tasks = np.sum(arr_remote_tasks)
                num_avg_mig_tasks_per_proc = np.average(arr_remote_tasks)

                # collect results
                arr_balanced_rimbs.append(round(Rimb_output, 5))
                arr_speedups.append(round(Speedup, 5))

                arr_total_mig_tasks.append(num_total_mig_tasks)
                arr_avg_mig_tasks_per_proc.append(num_avg_mig_tasks_per_proc)
            
            else:
                arr_balanced_rimbs.append(0.0)
                arr_speedups.append(0.0)
                arr_total_mig_tasks.append(0.0)
                arr_avg_mig_tasks_per_proc.append(0.0)
        
        data_balanced_imbs[algorithm] = arr_balanced_rimbs
        data_balanced_speedups[algorithm] = arr_speedups
        data_total_num_mig_tasks[algorithm] = arr_total_mig_tasks
        data_avg_num_mig_tasks_per_proc[algorithm] = arr_avg_mig_tasks_per_proc

    # create dataframes
    df_imb_ratios = pd.DataFrame(data_balanced_imbs)
    df_speedups = pd.DataFrame(data_balanced_speedups)
    df_total_num_mig_tasks = pd.DataFrame(data_total_num_mig_tasks)
    df_avg_num_mig_tasks_per_proc = pd.DataFrame(data_avg_num_mig_tasks_per_proc)

    print("-------------------------------------------")
    print("Write the table of imb ratios after rebalancing to csv: ./data_varied_numtasks_imb_ratios.csv")
    df_imb_ratios.to_csv('./data_varied_numtasks_imb_ratios.csv', index=False)
    print("-------------------------------------------\n")

    print("Write the table of speedup after rebalancing to csv: ./data_varied_numtasks_speedups.csv")
    df_speedups.to_csv('./data_varied_numtasks_speedups.csv', index=False)
    print("-------------------------------------------\n")

    print("Summary: the average of total tasks migrated: ")
    print(df_total_num_mig_tasks)
    print("-------------------------------------------\n")

    print("Summary: the average of tasks migrated per process: ")
    print(df_avg_num_mig_tasks_per_proc)
    print("-------------------------------------------\n")

