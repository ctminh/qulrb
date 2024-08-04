import os
import sys
import math

import numpy as np
import pandas as pd

# --------------------------------------------------------
# Load rebalancing algorithm/solver
# --------------------------------------------------------
def greedy_rebalancing(arr_num_local_tasks, num_procs, load_per_task_arr):
    arr_load_per_task = load_per_task_arr.to_list()
    sorted_numbers = sorted(enumerate(arr_num_local_tasks), key=lambda x: x[1], reverse=True)
    sums = [0] * num_procs

    partitions = []
    num_migrated_tasks_table = []
    num_migrated_tasks_table_header = ['Process']
    for i in range(num_procs):
        partitions.append([])
        num_migrated_tasks_table.append([0] * num_procs)
        num_migrated_tasks_table_header.append('P' + str(i))

    for index, number in sorted_numbers:
        smallest = min(range(len(sums)), key=sums.__getitem__)
        sums[smallest] += number
        partitions[smallest].append(number)

    migrated_tasks_arr = partitions

    # generate a dataframe to record results
    num_migrated_tasks_table = []
    num_migrated_tasks_table_header = ['Process']
    for i in range(num_procs):
        num_migrated_tasks_table.append([0] * num_procs)
        num_migrated_tasks_table_header.append('P' + str(i))
    # summarize num. local tasks, remote tasks, and total load values
    num_migrated_tasks_table_header.append('num_total')
    num_migrated_tasks_table_header.append('num_local')
    num_migrated_tasks_table_header.append('num_remote')
    num_migrated_tasks_table_header.append('L')
    for i in range(num_procs):
        final_arr_of_tasks = migrated_tasks_arr[i]
        for j in range(len(final_arr_of_tasks)):
            task = final_arr_of_tasks[j]
            origin_proc_idx = arr_load_per_task.index(task)
            if origin_proc_idx == i:
                num_migrated_tasks_table[i][i] += 1
            else:
                dest_proc_idx = i
                num_migrated_tasks_table[dest_proc_idx][origin_proc_idx] += 1
                
    for i in range(num_procs):
        num_total_tasks = np.sum(num_migrated_tasks_table[i])
        num_locals = num_migrated_tasks_table[i][i]
        num_remotes = num_total_tasks - num_locals
        L = round(np.sum(migrated_tasks_arr[i]), 5) 
        # check total load and num of total tasks
        sum_load = round(sum([a*b for a,b in zip(num_migrated_tasks_table[i], arr_load_per_task)]), 5)
        assert(sum_load==L)
        # append additional info about num total tasks, local, and remote tasks, and total load
        num_migrated_tasks_table[i].append(num_total_tasks)
        num_migrated_tasks_table[i].append(num_locals)
        num_migrated_tasks_table[i].append(num_remotes)
        num_migrated_tasks_table[i].append(L)
        num_migrated_tasks_table[i].insert(0, 'P'+str(i))

    df_mig_tasks = pd.DataFrame(num_migrated_tasks_table, columns=num_migrated_tasks_table_header)

    return df_mig_tasks


