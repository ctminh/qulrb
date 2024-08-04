import os
import sys
import math
import argparse
import pandas as pd
import numpy as np

import datetime
from timeit import default_timer as timer

from lrb_greedy import greedy_rebalancing
from lrb_karmarkar_karp import karmarkar_karp_rebalancing
from lrb_proact_offload1 import proact1_task_rebalancing
from lrb_proact_offload2 import proact2_task_rebalancing

# --------------------------------------------------------
# Task and load configuration
# --------------------------------------------------------
# NUM_PROCS = 8
# NUM_TASKS_PER_PROC = 10
# TASK_MIGRATION_DELAY = 4 # in ms
# LOAD_PER_TASK_PER_PROC = [15.506, 38.136, 66.734, 67.376, 38.305, 15.768, 8.134, 8.141] # in ms per task per process

# --------------------------------------------------------
# Util functions
# --------------------------------------------------------
def given_task_distribution(num_procs, num_tasks_per_proc, load_per_task_arr):
    arr_given_tasks = []
    for i in range(num_procs):
        for j in range(num_tasks_per_proc):
            arr_given_tasks.append(load_per_task_arr[i])
    return arr_given_tasks

def statistics_summary(arr_tasks, num_procs, num_tasks_per_proc):
    load_arr = []
    for i in range(num_procs):
        sum_load = 0.0
        for j in range(num_tasks_per_proc):
            sum_load += arr_tasks[i*num_tasks_per_proc + j]
        load_arr.append(sum_load)

    max_load = np.max(load_arr)
    min_load = np.min(load_arr)
    avg_load = np.average(load_arr)
    Rimb = max_load/avg_load -1

    formatted_load_arr = ["%.3f" % l for l in load_arr]

    print('-------------------------------------------')
    print('Total load per process: {}'.format(formatted_load_arr))
    print('   + Max: {:.3f}'.format(max_load))
    print('   + Min: {:.3f}'.format(min_load))
    print('   + Avg: {:.3f}'.format(avg_load))
    print('   + Imb: {:.3f}'.format(Rimb))
    print('-------------------------------------------\n')
    
    return load_arr, Rimb

def check_imb_ratio(df_migration_task_table):
    num_procs = len(df_migration_task_table['Process'])
    total_load_arr = df_migration_task_table['L'].to_list()
    max_load = np.max(total_load_arr)
    min_load = np.min(total_load_arr)
    avg_load = np.average(total_load_arr)
    Rimb = max_load/avg_load - 1
    return Rimb, max_load, min_load

# --------------------------------------------------------
# Main function
# --------------------------------------------------------
if __name__ == "__main__":

    # argument declaration
    parser = argparse.ArgumentParser()

    parser.add_argument("-alg", "--algorithm", type=str,
                        default="kk",
                        help="Algorithm for rebalancing the load")
    parser.add_argument("-inp", "--inputfile", type=str,
                        help="Input file for the rebalancing algorithm")
    parser.add_argument("-out", "--outputdir", type=str,
                        help="Output directory")
    parser.add_argument("-imb", "--imbcase", type=int,
                        default=1,
                        help="Imbalance ratio testcase")
    args = vars(parser.parse_args())
    algorithm = args["algorithm"]
    input_file = args["inputfile"]
    output_dir = args["outputdir"]
    imb_case = args["imbcase"]

    # read input file
    df_input = pd.read_csv(input_file)
    print('-------------------------------------------')
    print(df_input)
    NUM_PROCS = len(df_input['Process'])
    NUM_TASKS_PER_PROC = df_input['P0'][0]
    LOAD_PER_TASK_PER_PROC = df_input['w']

    # init an array of given tasks
    ARRAY_TASKS = given_task_distribution(NUM_PROCS, NUM_TASKS_PER_PROC, LOAD_PER_TASK_PER_PROC)
    # print('A given distribution of tasks:')
    # print(ARRAY_TASKS)
    # print('-------------------------------------------\n')

    # show load information
    ARRAY_LOCAL_LOAD, R_IMB = statistics_summary(ARRAY_TASKS, NUM_PROCS, NUM_TASKS_PER_PROC)

    # load rebalancing algorithm
    ARRAY_REMOTE_LOAD = []
    ARRAY_NUM_LOCAL_TASKS = []
    ARRAY_NUM_REMOTE_TASKS = []
    for i in range(NUM_PROCS):
        ARRAY_REMOTE_LOAD.append(0.0)
        ARRAY_NUM_LOCAL_TASKS.append(NUM_TASKS_PER_PROC)
        ARRAY_NUM_REMOTE_TASKS.append(0)

    # check applying different rebalancing method
    t1 = datetime.datetime.now()
    if algorithm == "greedy":
        print('Running algorithm: greedy')
        table_task_migration = greedy_rebalancing(ARRAY_TASKS, NUM_PROCS, LOAD_PER_TASK_PER_PROC)
    elif algorithm == "kk":
        print('Running algorithm: kk')
        table_task_migration = karmarkar_karp_rebalancing(ARRAY_TASKS, NUM_PROCS, LOAD_PER_TASK_PER_PROC)
    elif algorithm == "proact1":
        print('Running algorithm: proact1')
        table_task_migration = proact1_task_rebalancing(ARRAY_TASKS, ARRAY_LOCAL_LOAD, ARRAY_REMOTE_LOAD, ARRAY_NUM_LOCAL_TASKS, ARRAY_NUM_REMOTE_TASKS, LOAD_PER_TASK_PER_PROC)
    elif algorithm == "proact2":
        print('Running algorithm: proact2')
        table_task_migration = proact2_task_rebalancing(ARRAY_TASKS, ARRAY_LOCAL_LOAD, ARRAY_REMOTE_LOAD, ARRAY_NUM_LOCAL_TASKS, ARRAY_NUM_REMOTE_TASKS, LOAD_PER_TASK_PER_PROC)
    t2 = datetime.datetime.now()

    elapsed_time = (t2-t1).microseconds

    R_NEW_IMB, max_exe, min_exe = check_imb_ratio(table_task_migration)

    print('\n-------------------------------------------')
    print('Elapsed time: {:.5f}us'.format(elapsed_time))
    print('  + New Rimb: {:.5f}'.format(R_NEW_IMB))
    print('  + Max: {:.3f}'.format(max_exe))
    print('  + Min: {:.3f}'.format(min_exe))
    print('-------------------------------------------\n')
    
    output_filename = output_dir + 'output_' + algorithm + '_lrp_imb_case' + str(imb_case) + '.csv'
    table_task_migration.to_csv(output_filename, index=False)
    print('Write output to file: ', output_filename)
    print('-------------------------------------------\n')

    # check algorithms
    # algorithms = ["greedy", "kk", "proact1", "proact2"]
    # makespan = []
    # min_exetime = []
    # rimb = []
    # overhead = []

    # for i in range(len(algorithms)):
    #     t1 = datetime.datetime.now()
    #     if algorithms[i] == "greedy":
    #         print('Running algorithm: greedy')
    #         table_task_migration = greedy_rebalancing(ARRAY_TASKS, NUM_PROCS, LOAD_PER_TASK_PER_PROC.to_list())
    #     elif algorithms[i] == "kk":
    #         print('Running algorithm: kk')
    #         table_task_migration = karmarkar_karp_rebalancing(ARRAY_TASKS, NUM_PROCS)
    #     elif algorithms[i] == "proact1":
    #         print('Running algorithm: proact1')
    #         table_task_migration = proact1_task_rebalancing(ARRAY_TASKS, ARRAY_LOCAL_LOAD, ARRAY_REMOTE_LOAD, ARRAY_NUM_LOCAL_TASKS, ARRAY_NUM_REMOTE_TASKS)
    #     elif algorithms[i] == "proact2":
    #         print('Running algorithm: proact2')
    #         table_task_migration = proact2_task_rebalancing(ARRAY_TASKS, ARRAY_LOCAL_LOAD, ARRAY_REMOTE_LOAD, ARRAY_NUM_LOCAL_TASKS, ARRAY_NUM_REMOTE_TASKS)
    #     t2 = datetime.datetime.now()
    #     overhead.append((t2-t1).microseconds)

    #     R_NEW_IMB, max_exe, min_exe = check_imb_ratio(table_task_migration)
    #     rimb.append(R_NEW_IMB)
    #     makespan.append(max_exe)
    #     min_exetime.append(min_exe)

    # create a dataframe
    # list_of_tuples = list(zip(algorithms, makespan, min_exetime, rimb, overhead))
    # df = pd.DataFrame(list_of_tuples, columns=['Algorithm', 'Makespan', 'Min_Exetime', 'Rimb', 'Overhead'])

    # print('\n-------------------------------------------')
    # print(df)

    # print('Elapsed time: {:.3f}us'.format((t2-t1).microseconds))
    # print('Rimb: ')

    # print('Guide task migration: ')
    # for i in range(NUM_PROCS):
    #     for j in range(NUM_PROCS):
    #         if  i != j and table_task_migration[i][j] > 0:
    #             print('  + P{}: migrates {} tasks to P{}'.format(i, table_task_migration[i][j], j))
    # print('-------------------------------------------\n')
