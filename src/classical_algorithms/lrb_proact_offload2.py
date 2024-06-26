import os
import sys
import math

import numpy as np

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
# Load rebalancing function
# --------------------------------------------------------
def proact_task_rebalancing(arr_local_load, arr_remote_load, arr_num_local_tasks, arr_num_remote_tasks):
    
    # check total load info and sort proc ids
    arr_total_load = []
    for i in range(NUM_PROCS):
        arr_total_load.append(arr_local_load[i]+arr_remote_load[i])
    Lmax = np.max(arr_total_load)
    Lavg = np.average(arr_total_load)

    sorted_proc_ids = np.argsort(arr_total_load)
    print('-------------------------------------------')
    print('Total load array: {}'.format(arr_local_load))
    print('Sorted process indices: {}'.format(sorted_proc_ids))
    print('-------------------------------------------\n')

    # create a tracking table for local and remote tasks
    table_locrem_tasks = []
    for i in range(NUM_PROCS):
        table_locrem_tasks.append([])
        for j in range(NUM_PROCS):
            if i == j:
                table_locrem_tasks[i].append(arr_num_local_tasks[j])
            else:
                table_locrem_tasks[i].append(0)
                
    print('Local-remote-tasks tracking table:')
    print(table_locrem_tasks)
    print('-------------------------------------------\n')

    # main loop for the algorithm
    print('-------------------------------------------')
    print('Rebalancing the load: ')

    for i in range(NUM_PROCS):

        # get the most underloaded process | left to right
        victim = sorted_proc_ids[i]
        victim_load = arr_total_load[victim]

        # if the victim load < average
        if victim_load < Lavg:

            underloaded_val = Lavg - victim_load

            print('-------------------------------------------')
            print("Checking the underloaded P{}: underloaded_val={:.3f}".format(victim, underloaded_val))
            print('-------------------------------------------')

            # checking the most overloaded process
            for j in range(NUM_PROCS-1, 0, -1):

                offloader = sorted_proc_ids[j]
                offloader_load = arr_total_load[offloader]
                overloaded_val = offloader_load - Lavg

                # print("---> Checking the overloaded P{}: overloaded_val={:.3f}".format(offloader, overloaded_val))

                if offloader_load > Lavg and overloaded_val >= LOAD_PER_TASK_PER_PROC[offloader]/2:
                    print('      + Process P{} is overloaded'.format(offloader))
                    
                    # check num tasks for migration
                    numtasks_can_migrate = 0
                    migrated_load = 0.0
                    if overloaded_val >= underloaded_val:
                        numtasks_can_migrate =  round(underloaded_val / LOAD_PER_TASK_PER_PROC[offloader])
                        migrated_load = numtasks_can_migrate * LOAD_PER_TASK_PER_PROC[offloader]
                    else:
                        numtasks_can_migrate = round(overloaded_val / LOAD_PER_TASK_PER_PROC[offloader])
                        migrated_load = numtasks_can_migrate * LOAD_PER_TASK_PER_PROC[offloader]
                    
                    print('      + Process P{} migrate {} task(s) to P{}, migrated_load={:.3f}'.format(offloader,
                                                                numtasks_can_migrate, victim, migrated_load))
                    
                    # update underloaded value, and local load of offloader, remote load of victim
                    underloaded_val = underloaded_val - migrated_load
                    arr_local_load[offloader] -= migrated_load
                    arr_remote_load[victim] += migrated_load
                    print('      + New underloaded value at P{}: {:.3f}'.format(victim, underloaded_val))
                    
                    # update the number of tasks inc. local tasks for offloader, remote tasks for victim
                    arr_num_local_tasks[offloader] -= numtasks_can_migrate
                    arr_num_remote_tasks[victim] += numtasks_can_migrate
                    print('      -----------------------')
                    print('      + Updated local  load at victim P{}: {:.3f}'.format(victim, arr_local_load[victim]))
                    print('      + Updated remote load at victim P{}: {:.3f}'.format(victim, arr_remote_load[victim]))
                    print('      + Updated local  load at offloader P{}: {:.3f}'.format(offloader, arr_local_load[offloader]))
                    print('      + Updated remote load at offloader P{}: {:.3f}'.format(offloader, arr_remote_load[offloader]))
                    print('      -----------------------')

                    # update the total load value of both offloader and victim
                    arr_total_load[offloader] = arr_local_load[offloader] + arr_remote_load[offloader]
                    arr_total_load[victim] = arr_local_load[victim] + arr_remote_load[victim]
                    print('      + Updated total load at victim    P{}: {:.3f}'.format(victim, arr_total_load[victim]))
                    print('      + Updated total load at offloader P{}: {:.3f}'.format(offloader, arr_total_load[offloader]))
                    print('      -----------------------')

                    # update the tracking table
                    table_locrem_tasks[offloader][offloader] -= numtasks_can_migrate
                    table_locrem_tasks[offloader][victim] += numtasks_can_migrate
                    print('      + Updated tracking table: {}'.format(table_locrem_tasks))
                    print('      -----------------------')

                    # stop condition
                    abs_value = abs(arr_total_load[victim] - Lavg)
                    print('      + Abs(victim load P{} - Lavg) = {:.3f}\n'.format(victim, abs_value))

                    if abs_value < LOAD_PER_TASK_PER_PROC[offloader]:
                        break

    print('-------------------------------------------')
    print('Total load after rebalancing: ')
    for i in range(NUM_PROCS):
        print('  + P{}: {:.4f}ms | Local load: {:7.3f}, Remote load: {:7.3f}'.format(i, arr_total_load[i], arr_local_load[i], arr_remote_load[i]))
    print('-------------------------------------------\n')

    return table_locrem_tasks


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

    table_task_migration = proact_task_rebalancing(ARRAY_LOCAL_LOAD, ARRAY_REMOTE_LOAD, ARRAY_NUM_LOCAL_TASKS, ARRAY_NUM_REMOTE_TASKS)
    print('-------------------------------------------')
    print('Guide task migration: ')
    for i in range(NUM_PROCS):
        for j in range(NUM_PROCS):
            if  i != j and table_task_migration[i][j] > 0:
                print('  + P{}: migrates {} tasks to P{}'.format(i, table_task_migration[i][j], j))
    print('-------------------------------------------\n')

