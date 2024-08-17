import pandas as pd
import numpy as np
from typing import Literal
from dimod import ConstrainedQuadraticModel, BinaryArray
from dimod.sym import Sense
from dwave.system import LeapHybridCQMSampler
import csv

def read_input_csv(path: str, index_col : str | Literal[False] | None = None) -> pd.DataFrame:
    return pd.read_csv(path, index_col=index_col)


class LRBData:
    def __init__(self, path: str, index_col: str | Literal[False] | None = None):
        self.path = path
        self.index_col = index_col
        
        self.input_df = self.read_input_csv()
        self.processes = self.input_df.index.tolist()
        self.num_of_processes = len(self.processes)
        self.num_of_tasks = self.input_df.loc[self.processes, self.processes].sum().sum()
        self.num_of_tasks_per_process = self.get_num_of_tasks_per_process()
        self.total_load = self.input_df["L"].sum()
        self.max_load = self.input_df["L"].max()
        self.avg_load = self.input_df["L"].mean() # todo refactor to mean_load 
        self.min_load = self.input_df["L"].min()
        

    def read_input_csv(self) -> pd.DataFrame:
        return pd.read_csv(self.path, index_col=self.index_col)
    
    def get_num_of_tasks_per_process(self) -> int:
        if len(set(self.input_df.loc[self.processes, self.processes].sum(axis=1).tolist()))== 1:
            return self.input_df.loc[self.processes[0],self.processes[0]] # if all are equal, return the first one
        else:
            raise ValueError("Number of tasks per process is not equal for all processes")
        
        
class LoadRebalancingProblem:
    
    def __init__(self, data: LRBData, max_num_migrated_tasks: int, output_path: str, experiment_id: int):
        self.data = data
        self.max_num_migrated_tasks = max_num_migrated_tasks
        self.coefficients = self.calc_coefficients(self.data.num_of_tasks_per_process)
        self.variable_names = self.get_variable_names()
        self.variable_mapping = self.get_variable_mapping()
        self.variables = self.get_variables()
        self.output_path = output_path
        self.experiment_id = experiment_id
        
    @staticmethod
    def calc_coefficients(constant: int) -> list[int]:
        num_coeffs = int(np.floor(np.log2(constant)))
        coeffs = [2 ** j for j in range(num_coeffs)]
        if constant - 2 ** num_coeffs >= 0:
            coeffs.append(constant - 2 ** num_coeffs + 1)
        return coeffs #[::-1]
    
    def get_variable_names(self):
        return [(p_to, p_from, coef_id)
                        for p_to_id, p_to in enumerate(self.data.processes)
                        for p_from_id, p_from in enumerate(self.data.processes)
                        for coef_id, coef in enumerate(self.coefficients)
                        if p_from_id != p_to_id
                    ]
        
    def get_variable_mapping(self):
        return dict(zip(self.variable_names, range(len(self.variable_names))))
    
    def get_variables(self):
        return BinaryArray(self.variable_mapping.keys())
    
    
    def create_cqm_model(self):
        # 1. Create the model
        self.model = ConstrainedQuadraticModel()
        
        # 2. Add the variables TODO - is this step necessary?
        self.model.add_variables('BINARY', self.variable_mapping.keys())
        
        # 3. Create the objective function        
        # 3.1. Add the first term
        bqm_by_process = {process_id: [] for process_id, _ in enumerate(self.data.processes)}
        for p_to_id, p_to in enumerate(self.data.processes):
            relocated_terms = 0
            for p_from_id, p_from in enumerate(self.data.processes):
                for coefficient_id, coefficient in enumerate(self.coefficients):
                    if p_to!=p_from:
                        relocated_terms += (self.variables[self.variable_mapping[(p_to, p_from, coefficient_id)]]  
                                            * coefficient
                                            * self.data.input_df.loc[p_from, "w"])
            bqm_by_process[p_to_id] = relocated_terms
        
        # 3.2. Add the second term
        # now we want to have the remainder of the jobs to be subtracted for the same variable
        for p_to_id, p_to in enumerate(self.data.processes):
            not_relocated_terms = self.data.num_of_tasks_per_process
            for p_from_id, p_from in enumerate(self.data.processes):
                for coefficient_id, coefficient in enumerate(self.coefficients):
                    if p_to_id != p_from_id:
                        not_relocated_terms -= (coefficient 
                                                * self.variables[self.variable_mapping[p_from, p_to, coefficient_id]]) # this is dangerous, from->to
            not_relocated_terms *= self.data.input_df.loc[p_to, "w"]
            
            bqm_by_process[p_to_id] += not_relocated_terms
        
        # TODO merge steps 3.1 and 3.2
        
        # Finally here, we create the objective function
        # now we want to have the remainder of the jobs to be subtracted for the same variable
        objective_function = 0
        for _, entry in bqm_by_process.items():
            objective_function += (entry - self.data.avg_load)**2
                
        # 3.3. Add the objective function to the model
        self.model.set_objective(objective_function)
        
        # 4. Create the constraints
        # 4.1. The number of tasks migrated should not exceed the total amount of tasks
        constraint_all_tasks_assigned = [0] * self.data.num_of_processes
        for p_to_id, p_to in enumerate(self.data.processes):
            for p_from_id, p_from in enumerate(self.data.processes):
                for coefficient_id, coefficient in enumerate(self.coefficients):
                    if p_to != p_from:
                        constraint_all_tasks_assigned[p_to_id] += (coefficient 
                                                                   * self.variables[self.variable_mapping[p_from, p_to, coefficient_id]])
                        
        for constraint in constraint_all_tasks_assigned:
            self.model.add_constraint(constraint, "<=", self.data.num_of_tasks_per_process)
            
        # 4.2. New load of each process should not exceed the maximum load before rebalancing
        for _, entry in bqm_by_process.items():
            self.model.add_constraint(entry, "<=", self.data.max_load)
        
        # 4.3
        self.model.add_constraint(sum(constraint_all_tasks_assigned), "<=", self.max_num_migrated_tasks)
        
    # TODO - this is a bit of a mess, refactor later
    def solve_and_save(self):
        my_time_limit = 5.0
        sampler = LeapHybridCQMSampler()

        raw_sampleset = sampler.sample_cqm(self.model, time_limit=my_time_limit)
        
        # raw_sampleset = sampler.sample_cqm(self.model)
                
        aggregated_results = raw_sampleset.aggregate()
        
        feasible_sampleset = aggregated_results.filter(lambda d: d.is_feasible)
        
        solutions = feasible_sampleset.lowest()
        solutions_df = solutions.to_pandas_dataframe(sample_column=True) # TODO this for sure can be made more efficient
        
        solutions_df.to_csv(f'new_outputs/raw_cqm_correct/{self.output_path}_experimentid_{self.experiment_id}.csv')
        
        result_id = 0
        for _, row in solutions_df.iterrows():
            results = row["sample"]
            
            row_labels = self.data.processes
            column_labels = self.data.processes + ["num_total", "num_local", "num_remote", "L"]
            output_df = pd.DataFrame(np.zeros((len(row_labels), len(column_labels))), columns=column_labels, index=row_labels)
            output_df.index.name = 'Process'
            
            for result, value in results.items():
                p_to, p_from, p_id = result
                output_df.loc[p_to, p_from] += value * self.coefficients[int(p_id)]
                
            output_df["num_remote"] = output_df.loc[self.data.processes, self.data.processes].sum(axis=1)
            
            sum_per_column = output_df.loc[self.data.processes, self.data.processes].sum(axis=0)
            for process in self.data.processes: # TODO this for sure can be simplified in Pandas
                output_df.loc[process, process] = self.data.num_of_tasks_per_process - sum_per_column[process]
                output_df.loc[process, "num_local"] = self.data.num_of_tasks_per_process - sum_per_column[process]
        
            output_df["num_total"] = output_df["num_local"] + output_df["num_remote"]
        
            assert output_df["num_remote"].sum() <= self.max_num_migrated_tasks # this is a sanity check
            assert output_df['num_total'].sum() == self.data.num_of_tasks
            
            for p_from in self.data.processes: # TODO this for sure can be simplified in Pandas
                for p_to in self.data.processes:
                    output_df.loc[p_to, "L"] += output_df.loc[p_to, p_from] * self.data.input_df.loc[p_from, "w"]
                    
            output_df = output_df.astype({column: int for column in output_df.columns[:-1]})
                        
            output_path = f"new_outputs/{self.output_path}_resultid_{result_id}_experimentid_{self.experiment_id}.csv"
            output_df.to_csv(output_path)
            
            solution_metadata = {
                'input_file': self.data.path,
                'output_file': output_path,
                'max_num_migrated_tasks': self.max_num_migrated_tasks,
                'solutions_found': solutions_df.shape[0],
                'result_id': result_id,
                'num_of_processes': self.data.num_of_processes,
                'num_of_tasks': self.data.num_of_tasks,
                'imbalance_ratio': (output_df["L"].max() - output_df["L"].mean())/output_df["L"].mean(),
                'speedup': self.data.max_load/ output_df["L"].max(),
                'num_migrated_tasks': output_df['num_remote'].sum(),
                'total_load' : output_df["L"].sum(),
                'max_load' : output_df["L"].max(),
                'avg_load' : output_df["L"].mean(),
                'min_load': output_df["L"].min(),
                'max_load_before_rebalancing' : self.data.max_load,
                'avg_load_before_rebalancing' : self.data.avg_load,
                'min_load_before_rebalancing': self.data.min_load,
                'num_binary_variables': len(self.model.variables),
                'num_constraints': len(self.model.constraints),
                'num_inequality_constraints': sum(constraint.sense in (Sense.Le, Sense.Ge) for constraint in self.model.constraints.values()),
                'qpu_access_time': raw_sampleset.info['qpu_access_time'],
                'run_time': raw_sampleset.info['run_time'],
                'charge_time': raw_sampleset.info['charge_time'],
                'problem_id': raw_sampleset.info['problem_id'],
                'experiment_id': self.experiment_id,
                'max_time': 20.0,
            }
        
            result_id += 1
            
            output_csv = 'new_outputs/all_experiments.csv'

            # Open the CSV file for appending
            with open(output_csv, mode='a', newline='') as file:
                writer = csv.writer(file)

                # Write the row of values
                writer.writerow(solution_metadata.values())

            print("Finished")


if __name__ == "__main__":
  
    test_cases = []
      
    experiment_id = 12 #TODO remember to check the experiment_id
    for i, test_case in enumerate(test_cases):
        print(i)
        input_file, k, case = test_case

        # output_file = f"1_varied_imbs_speedup/case_{case}_k_{k}" # TODO
        # output_file = f"2_varied_num_procs/nodes_{case}_k_{k}" # TODO
        # output_file = f"3_varied_num_tasks/tasks_{case}_k_{k}" # TODO
        # output_file = f"samoa/case_{case}_k_{k}" # TODO

        data = LRBData(input_file, index_col="Process")
        lrp = LoadRebalancingProblem(data, k, output_file, experiment_id) #experiment_id
        lrp.create_cqm_model()
        lrp.solve_and_save()
        
        print("Less qubits finished")
    
    # test_cases = [
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case0.csv", 2, 0), #0
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case0.csv", 347, 0), #1
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case1.csv", 73, 1), #2
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case1.csv", 354, 1), #3
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case2.csv", 107, 2), #4
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case2.csv", 352, 2), #5
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case3.csv", 49, 3), #6
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case3.csv", 348, 3), #7
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case4.csv", 71, 4), #8
    #     ("../experiments/varied_imb_ratios/input_lrp/input_table_varied_imbs_case4.csv", 353, 4), #9
    # ]
    
    
    
    # test_cases = [
        # ("../experiments/varied_num_procs/input_lrp/input_table_4nodes.csv", 90,4), #0
    #     ("../experiments/varied_num_procs/input_lrp/input_table_4nodes.csv", 300,4), #1
    #     ("../experiments/varied_num_procs/input_lrp/input_table_8nodes.csv", 163,8), #2
    #     ("../experiments/varied_num_procs/input_lrp/input_table_8nodes.csv", 700,8), #3
    #     ("../experiments/varied_num_procs/input_lrp/input_table_16nodes.csv", 350,16), #4
    #     ("../experiments/varied_num_procs/input_lrp/input_table_16nodes.csv", 1499,16), #5
    #     ("../experiments/varied_num_procs/input_lrp/input_table_32nodes.csv", 644,32),#heavy #6
    #     ("../experiments/varied_num_procs/input_lrp/input_table_32nodes.csv", 3098,32), #heavy #7
    #     ("../experiments/varied_num_procs/input_lrp/input_table_64nodes.csv", 2353,64), #heavy #8
    #     ("../experiments/varied_num_procs/input_lrp/input_table_64nodes.csv", 6302,64), #heavy #9 
    # ]
       
    
    #  test_cases = [
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_8tasks.csv", 11, 8), #0
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_8tasks.csv", 56, 8), #1
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_16tasks.csv", 53, 16), #2
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_16tasks.csv", 112, 16), #3
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_32tasks.csv", 43, 32), #4
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_32tasks.csv", 224, 32), #5
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_64tasks.csv", 87, 64), #6
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_64tasks.csv", 448, 64), #7
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_128tasks.csv", 196, 128), #8
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_128tasks.csv", 896, 128), #9
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_256tasks.csv", 349, 256), #10
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_256tasks.csv", 1792, 256), #11
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_512tasks.csv", 696, 512), #12
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_512tasks.csv", 3584, 512), #13
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_1024tasks.csv", 1407, 1024), #14
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_1024tasks.csv", 7168, 1024), #15
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_2048tasks.csv", 2800, 2048), #16 
    #     ("../experiments/varied_num_tasks/input_lrp/input_table_8nodes_2048tasks.csv", 14336, 2048), #17 
    # ]
        
    # test_cases = [
        # ("../experiments/real_usecase_samoa/input_lrp/samoa_osc_case_32procs.csv", 1568, 32),
        # ("../experiments/real_usecase_samoa/input_lrp/samoa_osc_case_32procs.csv", 6447, 32)
    # ]
   

        
    