from numpy.lib.npyio import load
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import re
import sys
import os
import csv


"""Read chameleon-stats logs

Retrieve statistic information that profiled by internal chameleon funcs.
The logs are collected by iter over iter.

Args:
    + filename: the log file
Returns:
    + a complex array: stores data by rank, each rank contains iter-based info
"""
def parse_statslog_results(filename):

    # open the logfile
    file = open(filename, 'r')
    num_ranks = 0
    for line in file:
        if "_num_overall_ranks" in line:
            tokens = line.split("\t")
            num_ranks = int(tokens[2])
            break

    # for storing runtime/iter
    ret_data = []
    tw_sum_arr = []
    tw_idle_arr = []
    iter_runtime_arr = []
    iter_loctime_arr = []
    iter_rettime_arr = []
    data_transfer_rate = []
    task_migration_rate = []
    num_local_tasks = []
    num_remot_tasks = []
    num_balan_calls = []
    balancing_cost  = []
    for i in range(num_ranks):
        ret_data.append([])
        tw_sum_arr.append([])
        tw_idle_arr.append([])
        iter_runtime_arr.append([])
        iter_loctime_arr.append([])
        iter_rettime_arr.append([])
        num_local_tasks.append([])
        num_remot_tasks.append([])
        data_transfer_rate.append([])
        task_migration_rate.append([])
        num_balan_calls.append([])
        balancing_cost.append([])

    for line in file:
        # get distributed taskwait sum (correct just for 1 openmp thread/rank)
        if "_time_taskwait_sum" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', ((tokens[0].split(" "))[1]))[0])
            tw_sum = float(tokens[3])
            tw_sum_arr[rank_id].append(tw_sum)
        # get local exe_time:
        if "_time_task_execution_local_sum" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', ((tokens[0].split(" "))[1]))[0])
            local_time_sum = float(tokens[3])
            n_local_tasks = int(tokens[5])
            iter_loctime_arr[rank_id].append(local_time_sum)
            num_local_tasks[rank_id].append(n_local_tasks)
        # get remote exe_time:
        if "_time_task_execution_stolen_sum" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', ((tokens[0].split(" "))[1]))[0])
            remote_time_sum = float(tokens[3])
            n_remote_tasks = int(tokens[5])
            iter_rettime_arr[rank_id].append(remote_time_sum)
            num_remot_tasks[rank_id].append(n_remote_tasks)
        # get real-load time
        if "_time_task_execution_overall_sum" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', ((tokens[0].split(" "))[1]))[0])
            real_load = float(tokens[3])
            iter_runtime_arr[rank_id].append(real_load)
        # get the avg_taskwait time
        if "_time_taskwait_idling_sum" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', tokens[0])[0])
            idle_sum = float(tokens[3])
            count = float(tokens[5])
            avg_idle = idle_sum / count
            tw_idle_arr[rank_id].append(avg_idle)
        # get the throughput of comm_thread
        if "effective throughput" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', tokens[0])[0])
            fvalue = re.findall(r'\d+(?:\.\d*)', tokens[3])
            if fvalue != []:
                throughput = float(fvalue[0])
                data_transfer_rate[rank_id].append(throughput)
            else:
                data_transfer_rate[rank_id].append(0.0)
        # get task migration rate
        if "task_migration_rate" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', tokens[0])[0])
            fvalue = re.findall(r'\d+(?:\.\d*)', tokens[2])
            if fvalue != []:
                mig_rate = float(fvalue[0])
                task_migration_rate[rank_id].append(mig_rate)
            else:
                task_migration_rate[rank_id].append(0.0)
        # get balancing operation cost
        if "_time_balancing_calculation_sum" in line:
            tokens = line.split("\t")
            rank_id = int(re.findall(r'\d+', tokens[0])[0])
            cost_val = float(re.findall(r'\d+(?:\.\d*)', tokens[3])[0])
            count_val = int(tokens[5])
            if cost_val != [] and count_val != []:
                cost = cost_val
                count = count_val
                num_balan_calls[rank_id].append(count)
                balancing_cost[rank_id].append(cost)
            else:
                num_balan_calls[rank_id].append(0)
                balancing_cost[rank_id].append(0.0)

    # calculate avg_mse loss
    num_iters = len(iter_runtime_arr[0])
    for r in range(num_ranks):
        for i in range(num_iters):
            real_val = iter_runtime_arr[r][i]

    # merge the ret_data array
    for i in range(num_ranks):
        avg_tw_idle_value = np.sum(tw_idle_arr[i]) / len(tw_idle_arr[i])
        avg_runtime_value = np.average(iter_runtime_arr[i][3:]) # from the 3rd loop
        sum_runtime_value = np.sum(iter_runtime_arr[i])
        mea_runtime_value = np.mean(iter_runtime_arr[i])
        sum_taskwait_value = np.sum(tw_sum_arr[i])
        ret_data[i].append(i)                       # 0. rank_id
        ret_data[i].append(avg_tw_idle_value)       # 1. avg_tw
        ret_data[i].append(tw_idle_arr[i])          # 2. tw_idle_time array of Rank i
        ret_data[i].append(avg_runtime_value)       # 3. avg_runtime_value of Rank i
        ret_data[i].append(sum_runtime_value)       # 4. sum of iter runtimes / Rank i
        ret_data[i].append(mea_runtime_value)       # 5. mean of iter runtimes / Rank i
        ret_data[i].append(iter_runtime_arr[i])     # 6. iter runtime array of Rank i
        ret_data[i].append(data_transfer_rate[i])   # 7. data transfer rate of Rank i
        ret_data[i].append(task_migration_rate[i])  # 8. task migration rate of Rank i
        ret_data[i].append(iter_loctime_arr[i])     # 9. local exe time arr of Rank i
        ret_data[i].append(num_local_tasks[i])      # 10. arr of # local executed tasks / Rank i
        ret_data[i].append(iter_rettime_arr[i])     # 11. remote exe time arr of Rank i
        ret_data[i].append(num_remot_tasks[i])      # 12. arr of # remote executed tasks / Rank i
        ret_data[i].append(sum_taskwait_value)      # 13. sum of taskwait_time sum by iters / Rank i
        ret_data[i].append(num_balan_calls[i])      # 14. num of balancing calls / Rank i
        ret_data[i].append(balancing_cost[i])       # 15. balancing cost / Rank i

    return ret_data


"""Generate pandas dataframe through iters

Create dataframe for each type of log information that
can be used to plot charts.

Args:
    + df_header: headers of the dataframe
    + dat_src: data logs
    + dat_idx: index of data
    + num_iters: num of iterations
Returns:
    + dataframe: columns by rank idx, rows by iteration
"""
def generate_df_by_iter(df_header, dat_src, dat_idx, num_iters):
    df_data = []
    for i in range(num_iters):
        datarow = []
        datarow.append(i)   # 1st column: iter index
        for r in range(num_ranks):
            num_balancing_cal_arr = dat_src[r][dat_idx]
            datarow.append(num_balancing_cal_arr[i])
        df_data.append(datarow)
    df_out = pd.DataFrame(df_data, columns=df_header)
    return df_out

# --------------------------------------------------------------
# Main function
# --------------------------------------------------------------
if __name__ == "__main__":

    # get the chameleon-stat input file
    inputfile = sys.argv[1]

    # read the inputfile
    dataset = parse_statslog_results(inputfile)
    num_ranks = len(dataset)
    num_iters = len(dataset[0][6])

    df_header = ['Iter']
    df_data   = []
    for r in range(num_ranks):
        df_header.append('R' + str(r))

    print("-----------------------------------------------------")
    print("Dataframe for runtime/iteration")
    print("-----------------------------------------------------")
    df_runtime = generate_df_by_iter(df_header, dataset, 6, num_iters)
    print(df_runtime)
    print("---------------------------")
    print(" + Sum of runtime over iters: ")
    print("---------------------------")
    df_sum_runtime = df_runtime[df_header[1:]].sum()
    print(df_sum_runtime)
    print("---------------------------")
    print(" + Statistics: max, min, avg = {}, {}, {}".format(df_sum_runtime.max(), df_sum_runtime.min(), df_sum_runtime.mean()))
    print("---------------------------")
    print(" + Rimb: {}".format(df_sum_runtime.max()/df_sum_runtime.mean() - 1))
    print("---------------------------")


    print("\n-----------------------------------------------------")
    print("Dataframe for load values and num. executed tasks")
    print("-----------------------------------------------------")

    print("---------------------------")
    print(" + Num. local tasks:")
    print("---------------------------")
    df_num_local_tasks = generate_df_by_iter(df_header, dataset, 10, num_iters)
    print(df_num_local_tasks)
    print(" + Write dataframe num.local.tasks to csv: ./df_num_local_tasks.csv")
    # df_num_local_tasks.to_csv('./df_num_local_tasks.csv', index=False)
    print("---------------------------\n")

    print("---------------------------")
    print(" + Num. remote tasks:")
    print("---------------------------")
    df_num_remote_tasks = generate_df_by_iter(df_header, dataset, 12, num_iters)
    print(df_num_remote_tasks)
    print(" + Write dataframe num.remote.tasks to csv: ./df_num_remote_tasks.csv")
    # df_num_remote_tasks.to_csv('./df_num_remote_tasks.csv', index=False)
    print("---------------------------\n")

    print("---------------------------")
    print(" + Num. local load:")
    print("---------------------------")
    df_num_local_load = generate_df_by_iter(df_header, dataset, 9, num_iters)
    print(df_num_local_load)
    print(" + Write dataframe num.local.load to csv: ./df_local_load.csv")
    # df_num_local_load.to_csv('./df_local_load.csv', index=False)
    print("---------------------------\n")

    print("---------------------------")
    print(" + Num. remote load:")
    print("---------------------------")
    df_num_remote_load = generate_df_by_iter(df_header, dataset, 11, num_iters)
    print(df_num_remote_load)
    print(" + Write dataframe num.remote.load to csv: ./df_remote_load.csv")
    # df_num_remote_load.to_csv('./df_remote_load.csv', index=False)
    print("---------------------------\n")

    print("\n--------------------------------------------------------")
    print("Dataframe for transfer throughput (MB/s)")
    print("--------------------------------------------------------")
    df_avg_transfer_rate = generate_df_by_iter(df_header, dataset, 7, num_iters)
    print(df_avg_transfer_rate)
    
    print("\n--------------------------------------------------------")
    print("Task migration throughput (task/s)")
    print("--------------------------------------------------------")
    df_avg_migration_throughput = generate_df_by_iter(df_header, dataset, 8, num_iters)
    print(df_avg_migration_throughput)
    print(" + Write dataframe task.migrate.thoughput to csv: ./df_task_migration_throughput.csv")
    df_avg_migration_throughput.to_csv('./df_task_migration_throughput.csv', index=False)
    print("---------------------------\n")
