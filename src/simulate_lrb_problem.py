import os
import sys
import math

import numpy as np

# init a set of tasks
T = [15.506, 15.506, 15.506, 38.136, 38.136, 38.136, 66.734, 66.734, 66.734, 67.376, 67.376, 67.376]

# a given distribution of tasks on 4 processes
num_procs = 4
num_tasks_per_proc = int(len(T)/num_procs)
P = []
for i in range (num_procs):
    sub_P = []
    for t in range(num_tasks_per_proc):
        sub_P.append(T[i*num_tasks_per_proc + t])
    P.append(sub_P)
print('A given distribution of tasks on {:2d} processes: '.format(num_procs))
print(P)
print('----------------------------------------\n')

# some statistic information
L = []
for i in range(num_procs):
    L.append(np.sum(P[i]))

L_avg = np.average(L)
P_underload = []
P_overload  = []
L_underload = []
L_overload  = []

for i in range(num_procs):
    if L[i] > L_avg:
        L_overload.append(L[i] - L_avg)
        P_overload.append(i)
    else:
        L_underload.append(L_avg - L[i])
        P_underload.append(i)

print('Average load: {:.3f}'.format(L_avg))
print('Processes underloaded: {} | L_underload={} | Sum={}'.format(P_underload, L_underload, np.sum(L_underload)))
print('Processes overloaded:  {} | L_overload ={} | Sum={}'.format(P_overload, L_overload, np.sum(L_overload)))
print('----------------------------------------\n')

# -----------------------------------------------------
# Util functions
# -----------------------------------------------------

def update_underload(L_underload, P_underload, val, proc):
    if proc in P_underload:
        pidx = P_underload.index(proc)
        L_underload[pidx] = val
    elif proc in P_overload: # remove this process
        pidx = P_overload.index(proc)
        del L_overload[pidx]
        P_overload.remove(proc)

def update_overload(L_overload, P_overload, val, proc):
    if proc in P_overload:
        pidx = P_overload.index(proc)
        L_overload[pidx] = val
    elif proc in P_underload: # remove this process
        pidx = P_underload.index(proc)
        del L_underload[pidx]
        P_underload.remove(proc)

def update_load(P_arr, L_arr, L_overload, L_underload):
    num_processes = len(P_arr)
    for i in range(num_processes):
        num_tasks = len(P_arr[i])
        sum_cur_load = np.sum(P_arr[i])
        L_arr[i] = sum_cur_load
    
    # calculate avg load
    Lavg = np.average(L_arr)

    # TODO: update load overloaded and underloaded
    for i in range(num_procs):
        if L[i] > L_avg:
            overload_val = L[i] - L_avg
            update_overload(L_overload, P_overload, overload_val, i)
            
        elif L[i] < L_avg:
            underload_val = L_avg - L[i]
            update_underload(L_underload, P_underload, underload_val, i)
        else:
            if i in P_underload:
                process_idx = P_underload.index(i)
                P_underload.remove(i)
                del L_underload[process_idx]
            else:
                process_idx = P_overload.index(i)
                P_overload.remove(i)
                del L_overload[process_idx]

    return Lavg

def obj_func(L, L_avg):
    num_procs = len(L)
    obj_val = 0
    for i in range(num_procs):
        obj_val += (L[i] - L_avg)**2

    return obj_val

# -----------------------------------------------------
# Rebalancing Algorithm 1: greedy
# -----------------------------------------------------
penalty_migration_cost = 0
objective_function = 0

for i in P_overload:

    for j in P_underload:

        n_tasks_can_migrate = 0
        n_tasks_can_receive = 0

        if len(L_overload) > 0 and len(L_underload) > 0:
            idx_P_over  = P_overload.index(i)
            idx_P_under = P_underload.index(j)
            n_tasks_can_migrate = math.ceil(L_overload[idx_P_over]  / P[i][0])
            n_tasks_can_receive = math.ceil(L_underload[idx_P_under] / P[j][0])

        print('[P{}/P{}] n_tasks availabel to migrate {}, to receive {}'.format(i, j, 
                n_tasks_can_migrate, n_tasks_can_receive))
        
        # check the remaining tasks
        n_tasks_rem_in_Poverload = len(P[i])
        
        # decide migrating tasks
        if n_tasks_can_migrate > 0 and n_tasks_can_receive > 0 and n_tasks_rem_in_Poverload > 2:
            
            numtask2migrate = min(n_tasks_can_migrate, n_tasks_can_receive)
            cost2migrate = numtask2migrate * 8.725 # temp. set 25 ms for migrating a task at a time

            # update migration cost
            penalty_migration_cost += cost2migrate

            # move tasks around
            for t in range(numtask2migrate):
                task_from_Poverload = P[i].pop()
                # insert this task to Punderload
                P[j].append(task_from_Poverload)
                print('   moved a task from P{} to P{}'.format(i, j))
                print('   current tasks in P{}: {}'.format(i, P[i]))
                print('                 in P{}: {}'.format(j, P[j]))

        # update the load
        L_avg = update_load(P, L, L_overload, L_underload)
        print('-------------------------------')
        print('   + Load array: {}'.format(L))
        print('   + Penalty migration cost: {}'.format(penalty_migration_cost))
        print('   + Objective function: sum(L[i]-Lavg)^2 = {:.2f}'.format(obj_func(L, L_avg)))
        print('   + P_underloaded: {} | L_underload={} | Sum={}'.format(P_underload, L_underload, np.sum(L_underload)))
        print('   + P_overloaded:  {} | L_overload ={} | Sum={}'.format(P_overload, L_overload, np.sum(L_overload)))
        print('-------------------------------')

# -----------------------------------------------------
# Rebalancing Algorithm 1: sorted-base greedy
# -----------------------------------------------------
