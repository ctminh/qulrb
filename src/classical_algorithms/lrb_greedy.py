import os
import sys
import math

import numpy as np

# --------------------------------------------------------
# Load rebalancing algorithm/solver
# --------------------------------------------------------
def greedy_rebalancing(arr_num_local_tasks, num_procs):
    
    sorted_numbers = sorted(enumerate(arr_num_local_tasks), key=lambda x: x[1], reverse=True)
    sums = [0] * num_procs

    # print('Tasks sorted by load value:')
    # print(sorted_numbers)
    # print('')

    partitions = []
    for i in range(num_procs):
        partitions.append([])

    for index, number in sorted_numbers:
        smallest = min(range(len(sums)), key=sums.__getitem__)
        sums[smallest] += number
        partitions[smallest].append(number)
    
    # print('Total load and re-distributed tasks/process:')
    # for i in range(num_procs):
    #     print('  + P{}, sum={:.3f}, num_tasks={}: {}'.format(i, sums[i], len(partitions[i]), partitions[i]))
    
    return partitions


