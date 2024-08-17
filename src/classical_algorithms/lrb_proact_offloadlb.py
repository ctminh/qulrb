import os
import sys
import math

import numpy as np
import pandas as pd

# --------------------------------------------------------
# Load rebalancing function
# --------------------------------------------------------
def proact2_task_rebalancing(arr_tasks, arr_local_load, arr_remote_load, arr_num_local_tasks, arr_num_remote_tasks, load_per_task_arr):
    NUM_PROCS = len(arr_local_load)
    LOAD_PER_TASK_PER_PROC = load_per_task_arr.to_list()

    # check total load info and sort proc ids
    arr_total_load = []
    for i in range(NUM_PROCS):
        arr_total_load.append(arr_local_load[i]+arr_remote_load[i])
    Lmax = np.max(arr_total_load)
    Lavg = np.average(arr_total_load)

    sorted_proc_ids = np.argsort(arr_total_load)

    # create a tracking table for local and remote tasks
    table_locrem_tasks = []
    for i in range(NUM_PROCS):
        table_locrem_tasks.append([])
        for j in range(NUM_PROCS):
            if i == j:
                table_locrem_tasks[i].append(arr_num_local_tasks[j])
            else:
                table_locrem_tasks[i].append(0)

    # main loop for the algorithm
    for i in range(NUM_PROCS):

        # get the most underloaded process | left to right
        victim = sorted_proc_ids[i]
        victim_load = arr_total_load[victim]

        # if the victim load < average
        if victim_load < Lavg:

            underloaded_val = Lavg - victim_load

            # print('-------------------------------------------')
            # print("Checking the underloaded P{}: underloaded_val={:.3f}".format(victim, underloaded_val))
            # print('-------------------------------------------')

            # checking the most overloaded process
            for j in range(NUM_PROCS-1, 0, -1):

                offloader = sorted_proc_ids[j]
                offloader_load = arr_total_load[offloader]
                overloaded_val = offloader_load - Lavg

                if offloader_load > Lavg and overloaded_val >= LOAD_PER_TASK_PER_PROC[offloader]/2:
                    # print(' + Process P{} is overloaded'.format(offloader))
                    
                    # check num tasks for migration
                    numtasks_can_migrate = 0
                    migrated_load = 0.0
                    if overloaded_val >= underloaded_val:
                        numtasks_can_migrate =  round(underloaded_val / LOAD_PER_TASK_PER_PROC[offloader])
                        migrated_load = numtasks_can_migrate * LOAD_PER_TASK_PER_PROC[offloader]
                    else:
                        numtasks_can_migrate = round(overloaded_val / LOAD_PER_TASK_PER_PROC[offloader])
                        migrated_load = numtasks_can_migrate * LOAD_PER_TASK_PER_PROC[offloader]
                    
                    # print(' + Process P{} migrate {} task(s) to P{}, migrated_load={:.3f}'.format(offloader,
                    #                                             numtasks_can_migrate, victim, migrated_load))
                    
                    # update underloaded value, and local load of offloader, remote load of victim
                    underloaded_val = underloaded_val - migrated_load
                    arr_local_load[offloader] -= migrated_load
                    arr_remote_load[victim] += migrated_load
                    # print(' + New underloaded value at P{}: {:.3f}'.format(victim, underloaded_val))
                    
                    # update the number of tasks inc. local tasks for offloader, remote tasks for victim
                    arr_num_local_tasks[offloader] -= numtasks_can_migrate
                    arr_num_remote_tasks[victim] += numtasks_can_migrate
                    # print('-----------------------')
                    # print(' + Updated local  load at victim P{}: {:.3f}'.format(victim, arr_local_load[victim]))
                    # print(' + Updated remote load at victim P{}: {:.3f}'.format(victim, arr_remote_load[victim]))
                    # print(' + Updated local  load at offloader P{}: {:.3f}'.format(offloader, arr_local_load[offloader]))
                    # print(' + Updated remote load at offloader P{}: {:.3f}'.format(offloader, arr_remote_load[offloader]))
                    # print('-----------------------')

                    # update the total load value of both offloader and victim
                    arr_total_load[offloader] = arr_local_load[offloader] + arr_remote_load[offloader]
                    arr_total_load[victim] = arr_local_load[victim] + arr_remote_load[victim]
                    # print(' + Updated total load at victim    P{}: {:.3f}'.format(victim, arr_total_load[victim]))
                    # print(' + Updated total load at offloader P{}: {:.3f}'.format(offloader, arr_total_load[offloader]))
                    # print('-----------------------')

                    # update the tracking table
                    table_locrem_tasks[offloader][offloader] -= numtasks_can_migrate
                    table_locrem_tasks[offloader][victim] += numtasks_can_migrate
                    # print(' + Updated tracking table: {}'.format(table_locrem_tasks))
                    # print('-----------------------')

                    # stop condition
                    abs_value = abs(arr_total_load[victim] - Lavg)
                    # print(' + Abs(victim load P{} - Lavg) = {:.3f}\n'.format(victim, abs_value))

                    if abs_value < LOAD_PER_TASK_PER_PROC[offloader]:
                        break

    # generate a dataframe to record results
    num_migrated_tasks_table = []
    num_migrated_tasks_table_header = ['Process']
    for i in range(NUM_PROCS):
        num_migrated_tasks_table.append([0] * NUM_PROCS)
        num_migrated_tasks_table_header.append('P' + str(i))
    # summarize num. local tasks, remote tasks, and total load values
    num_migrated_tasks_table_header.append('num_total')
    num_migrated_tasks_table_header.append('num_local')
    num_migrated_tasks_table_header.append('num_remote')
    num_migrated_tasks_table_header.append('L')
    for i in range(NUM_PROCS):
        final_arr_of_tasks = table_locrem_tasks[i]
        for j in range(NUM_PROCS):
            if j == i:
                num_migrated_tasks_table[i][i] = final_arr_of_tasks[j]
            else:
                if final_arr_of_tasks[j] != 0:
                    origin_proc_idx = i
                    dest_proc_idx = j
                    num_migrated_tasks_table[dest_proc_idx][origin_proc_idx] = final_arr_of_tasks[j]

    for i in range(NUM_PROCS):
        num_total_tasks = np.sum(num_migrated_tasks_table[i])
        num_locals = num_migrated_tasks_table[i][i]
        num_remotes = num_total_tasks - num_locals
        L = round(np.sum(arr_total_load[i]), 5) 
        # check total load and num of total tasks
        sum_load = round(sum([a*b for a,b in zip(num_migrated_tasks_table[i], LOAD_PER_TASK_PER_PROC)]), 5)
        assert(sum_load==L)
        # append additional info about num total tasks, local, and remote tasks, and total load
        num_migrated_tasks_table[i].append(num_total_tasks)
        num_migrated_tasks_table[i].append(num_locals)
        num_migrated_tasks_table[i].append(num_remotes)
        num_migrated_tasks_table[i].append(L)
        num_migrated_tasks_table[i].insert(0, 'P'+str(i))

    df_mig_tasks = pd.DataFrame(num_migrated_tasks_table, columns=num_migrated_tasks_table_header)

    return df_mig_tasks

