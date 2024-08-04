import os
import sys
import math
import heapq

import numpy as np
import pandas as pd

from typing import List, Tuple
from itertools import count


# --------------------------------------------------------
# Load rebalancing algorithm/solver
# --------------------------------------------------------
def karmarkar_karp_rebalancing(arr_num_local_tasks, num_procs, load_per_task_arr):
    arr_load_per_task = load_per_task_arr.to_list()
    partitions: List[Tuple[int, int, List[List[int]], List[int]]] = []
    heap_count = count()

    for i in range(len(arr_num_local_tasks)):
        this_partition: List[List[int]] = []

        for n in range(num_procs - 1):
            this_partition.append([])

        this_partition.append([arr_num_local_tasks[i]])
        this_sizes: List[int] = [0] * (num_procs - 1) + [arr_num_local_tasks[i]]
        heapq.heappush(
            partitions, (-arr_num_local_tasks[i], next(heap_count), this_partition, this_sizes)
        )

    for k in range(len(arr_num_local_tasks) - 1):
        _, _, p1, p1_sum = heapq.heappop(partitions)
        _, _, p2, p2_sum = heapq.heappop(partitions)

        new_sizes: List[int] = [
            p1_sum[j] + p2_sum[num_procs - j - 1] for j in range(num_procs)
        ]

        new_partition: List[List[int]] = [
            p1[j] + p2[num_procs - j - 1] for j in range(num_procs)
        ]

        indices = np.argsort(new_sizes)
        new_sizes = [new_sizes[i] for i in indices]
        new_partition = [new_partition[i] for i in indices]
        diff = new_sizes[-1] - new_sizes[0]
        heapq.heappush(partitions, (-diff, next(heap_count), new_partition, new_sizes))
    
    _, _, final_partition, final_sums = partitions[0]
    migrated_tasks_arr = partitions[0][2]

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
