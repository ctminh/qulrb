from dimod import ConstrainedQuadraticModel, Binary, Integer, SampleSet, BinaryArray
from dwave.system import LeapHybridCQMSampler

# init tasks and processors
tasks = [f"task_{i}" for i in range(12)]
processors = [f"processor_{i}" for i in range(4)]
print('----------------------------------------')
print('Tasks: {}'.format(tasks))
print('Processors: {}'.format(processors))
print('----------------------------------------\n')

# init new task asignment array
new_assignment = [[BinaryArray([f"x{4*i + j}" for j in range(len(processors))])] for i in range(len(tasks))]
print('----------------------------------------')
print('Binary variables and Binary array: {}'.format(new_assignment))
print('----------------------------------------\n')

# init a constrained quadratic model
cqm = ConstrainedQuadraticModel()

# init given information about task exe time
original_time = [
    100, 100, 100,  # processor 0 
    200, 200, 200,  # processor 1 
    75, 75, 75,     # processor 2 
    150, 150, 150,  # processor 3
]

original_assignment = [
    [1, 0, 0, 0],
    [1, 0, 0, 0],
    [1, 0, 0, 0],
    
    [0, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 0, 0],
    
    [0, 0, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 0],
    
    [0, 0, 0, 1],
    [0, 0, 0, 1],
    [0, 0, 0, 1],
]

# processor_speeds = [2.0, 1.0, 4.0, 1.0]
processor_speeds = [1.0, 1.0, 1.0, 1.0]
delay_for_moving_task = 20

# ---------------------------------------------
# calculate the penaty cost
# ---------------------------------------------
penalties_for_moving_task = []

for task_id, task_name in enumerate(tasks):
    original_processor_id = 0
    for processor_id, processor_name in enumerate(processor_speeds):
        if original_assignment[task_id][processor_id] == 1:
            original_processor_id = processor_id
            # print('processor_id: {}, processor_name: {}, original_processor_id: {}'.format(processor_id, processor_name, original_processor_id))
    
    penalty_for_change_of_speed_and_delay = []
    for processor_id, new_processor_speed in enumerate(processor_speeds):

        time_in_new_speed = processor_speeds[original_processor_id]/new_processor_speed * original_time[task_id]
        penalty = time_in_new_speed - original_time[task_id]
        # print('processor_id: {}, new_processor_speed: {}, time_in_new_speed: {}, penalty: {}'.format(processor_id, new_processor_speed, 
        #                                                                                     time_in_new_speed, penalty))
        
        if processor_id != original_processor_id:
            penalty += delay_for_moving_task
            
        penalty_for_change_of_speed_and_delay.append(penalty)

    penalties_for_moving_task.append(penalty_for_change_of_speed_and_delay)       

# checking task migration cost plus perf slowdown
print('----------------------------------------')
for row in penalties_for_moving_task:
    print(row)
print('----------------------------------------\n')

# ---------------------------------------------
# calculate objective function
# ---------------------------------------------
avg = sum(original_time)/4 # 393.75
obj_function = 0

for processor_id, processor_name in enumerate(processors):
    
    processor_time = 0
    for task_id, task_name in enumerate(tasks):
        processor_time += (
                        new_assignment[task_id][0][processor_id] * 
                        (original_time[task_id] + penalties_for_moving_task[task_id][processor_id])
                        )
    print(f"Processor {processor_name} time {processor_time}")
    obj_function += (processor_time - avg)**2
    
print(f"Objective function {obj_function/len(processors)}")

# ---------------------------------------------
# try to use dwave solver
# ---------------------------------------------
for task_id, task in enumerate(tasks):
    cqm.add_constraint(new_assignment[task_id][0][0]
                       + new_assignment[task_id][0][1] 
                       + new_assignment[task_id][0][2] 
                       + new_assignment[task_id][0][3] == 1)
    
cqm.set_objective(obj_function/len(processors))
sampler = LeapHybridCQMSampler()
raw_sampleset = sampler.sample_cqm(cqm, time_limit=5)
feasible_sampleset = raw_sampleset.filter(lambda d: d.is_feasible)

# ---------------------------------------------
# parse the result back to check which tasks can be moved
# ---------------------------------------------
amount_of_moved_tasks = 0
for task_id, task_name in enumerate(tasks):
    check_if_moved = 1
    for processor_id, processor_name in enumerate(processors):
        check_if_moved -= (original_assignment[task_id][processor_id]
                           * new_assignment[task_id][0][processor_id])
    if check_if_moved == 1:
        print(f"Task {task_id} migrated")
    amount_of_moved_tasks += check_if_moved
print(f"\nAmount of moved tasks: {amount_of_moved_tasks}")

sample_id = 0
chosen_sample = feasible_sampleset.samples()[sample_id]

for task_id, task in enumerate(tasks):
    print(chosen_sample[f'x{4*task_id}'],
          chosen_sample[f'x{4*task_id + 1}'],
          chosen_sample[f'x{4*task_id + 2}'],
          chosen_sample[f'x{4*task_id + 3}'],
         )