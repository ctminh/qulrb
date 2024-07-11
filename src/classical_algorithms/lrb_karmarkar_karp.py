import os
import sys
import math
import heapq

import numpy as np

from typing import List, Tuple
from itertools import count


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
    
    # print('final_partition: {}'.format(final_partition))
    # print('final_sums: {}'.format(final_sums))
    # print(partitions[0][2])
    
    return partitions[0][2]
