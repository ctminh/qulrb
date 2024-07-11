import os
import sys
import math

import numpy as np

# --------------------------------------------------------
# Load rebalancing function
# --------------------------------------------------------
def proact1_task_rebalancing(arr_tasks, arr_local_load, arr_remote_load, arr_num_local_tasks, arr_num_remote_tasks):
    NUM_PROCS = len(arr_local_load)
    LOAD_PER_TASK_PER_PROC = []
    for i in range(NUM_PROCS):
        LOAD_PER_TASK_PER_PROC.append(arr_tasks[i*NUM_PROCS])
        
    # check total load info and sort proc ids
    arr_total_load = []
    for i in range(NUM_PROCS):
        total_load_val = arr_local_load[i]+arr_remote_load[i]
        arr_total_load.append(total_load_val)
    Lavg = np.average(arr_total_load)

    sorted_proc_ids = np.argsort(arr_total_load)

    # extract overloaded and underloaded process ids
    NUM_OVERLOAD_PROCS = []
    NUM_UNDERLOAD_PROCS = []
    for i in sorted_proc_ids:
        L = arr_total_load[i]
        if L < Lavg:
            NUM_UNDERLOAD_PROCS.append(i)
        elif L > Lavg:
            NUM_OVERLOAD_PROCS.append(i)

    print('-------------------------------------------')
    print('Total load array: {}'.format(arr_local_load))
    print('Sorted process indices: {}'.format(sorted_proc_ids))
    print('  + Overloaded processes: {}'.format(NUM_OVERLOAD_PROCS))
    print('  + Underloaded processes: {}'.format(NUM_UNDERLOAD_PROCS))
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

    for i in NUM_UNDERLOAD_PROCS:

        # get the most underloaded process | left to right
        victim = i
        victim_load = arr_total_load[victim]

        # if the victim load < average
        if victim_load < Lavg:

            underloaded_val = Lavg - victim_load

            print('-------------------------------------------')
            print("Checking the underloaded P{}: underloaded_val={:.3f}".format(victim, underloaded_val))
            print('-------------------------------------------')

            # checking the most overloaded process
            for j in range(len(NUM_OVERLOAD_PROCS)-1, 0, -1):

                offloader = NUM_OVERLOAD_PROCS[j]
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
