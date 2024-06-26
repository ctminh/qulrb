import os
import sys
import math
import heapq

import numpy as np

from typing import List, Tuple
from itertools import count

# --------------------------------------------------------
# Task and load configuration
# --------------------------------------------------------
NUM_PROCS = 8
NUM_TASKS_PER_PROC = 10
TASK_MIGRATION_DELAY = 4 # in ms
LOAD_PER_TASK_PER_PROC = [15.506, 38.136, 66.734, 67.376, 38.305, 15.768, 8.134, 8.141] # in ms per task per process

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
            sum_load += arr_tasks[i*(num_procs-1) + j]
        load_arr.append(sum_load)

    max_load = np.max(load_arr)
    min_load = np.min(load_arr)
    avg_load = np.average(load_arr)
    print('-------------------------------------------')
    print('Total load per process: {}'.format(load_arr))
    print('   + Max: {:.3f}'.format(max_load))
    print('   + Min: {:.3f}'.format(min_load))
    print('   + Avg: {:.3f}'.format(avg_load))
    print('   + Imb: {:.3f}'.format(max_load/avg_load - 1))
    print('-------------------------------------------\n')
    
    return load_arr

# --------------------------------------------------------
# Load rebalancing algorithm/solver
# --------------------------------------------------------
def karmarkar_karp_rebalancing(arr_num_local_tasks, num_procs):
    
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
    
    print('final_partition: {}'.format(final_partition))
    print('final_sums: {}'.format(final_sums))
    
    return partitions


# --------------------------------------------------------
# Main function
# --------------------------------------------------------

if __name__ == "__main__":

    # init an array of given tasks
    ARRAY_TASKS = given_task_distribution(NUM_PROCS, NUM_TASKS_PER_PROC, LOAD_PER_TASK_PER_PROC)
    print('Array of given tasks:')
    print(ARRAY_TASKS)
    print('-------------------------------------------\n')

    # show load information
    ARRAY_LOCAL_LOAD = statistics_summary(ARRAY_TASKS, NUM_PROCS, NUM_TASKS_PER_PROC)

    # load rebalancing algorithm
    ARRAY_REMOTE_LOAD = []
    ARRAY_NUM_LOCAL_TASKS = []
    ARRAY_NUM_REMOTE_TASKS = []
    for i in range(NUM_PROCS):
        ARRAY_REMOTE_LOAD.append(0.0)
        ARRAY_NUM_LOCAL_TASKS.append(NUM_TASKS_PER_PROC)
        ARRAY_NUM_REMOTE_TASKS.append(0)

    table_task_migration = karmarkar_karp_rebalancing(ARRAY_TASKS, NUM_PROCS)
    # print('-------------------------------------------')
    # print('Guide task migration: ')
    # for i in range(NUM_PROCS):
    #     for j in range(NUM_PROCS):
    #         if  i != j and table_task_migration[i][j] > 0:
    #             print('  + P{}: migrates {} tasks to P{}'.format(i, table_task_migration[i][j], j))
    # print('-------------------------------------------\n')

