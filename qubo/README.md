## QUBO Formulations

Some ideas for QUBO formulations from Justyna.

An example comes from the profiled data of executing Sam$(oa)^{2}$, which is an HPC simulation framework for oceanic problems, such as tsunami, oscillating lake. The logfile shows:

* Number of processes: $8$
* Number of tasks per process: $208$, where this value depends on the scale of simulation scenarios we want to configure. This refers to https://github.com/meistero/Samoa.
* The length of tasks (task execution time) is collected from the logfile after 100 simulation iterations, as follows:
    + Process $P_{0}$: $[15.5, 15.5, ..., 15.5]$
    + Process $P_{1}$: $[38.1, 38.1, ..., 38.1]$
    + $...$
    + Process $P_{7}$: $[8.1, 8.1, ..., 8.1]$

To be simple, the example with the QUBO formulations below is shown with only $4$ processes from $P_{0}$ to $P_{3}$, and so on with their corresponding task length values.

### Formulating as a linear equation

Based on the way of calculating the total load values by the number of tasks and the task lengths, we can formulate as a linear equation
$$
    a_{0} \times y_{0} + b_{0} \times y_{1} + c_{0} \times y_{2} + d_{0} \times y_{3} = L_{0} \\
    a_{1} \times y_{0} + b_{1} \times y_{1} + c_{1} \times y_{2} + d_{1} \times y_{3} = L_{1} \\
    a_{2} \times y_{0} + b_{2} \times y_{1} + c_{2} \times y_{2} + d_{2} \times y_{3} = L_{2} \\
    a_{3} \times y_{0} + b_{3} \times y_{1} + c_{3} \times y_{2} + d_{3} \times y_{3} = L_{3}
$$

Where, $[y_{0}, y_{1}, y_{2}, y_{3}]$ correspond to the length of tasks on each process $[15.5, 38.1, 66.7, 67.4]$; the coeeficients $[a_{0}, a_{1}, a_{2}, a_{3}]$ are associated with the total number of tasks of $P_{0}$ as a given distribution before running. In the case, tasks are migrated around to balance the load, then $b_{0}, c_{0}, ... $ shown in the first row are used to indicate the migrated tasks from the others to $P_{0}$. Following that, $L_{0}$ denotes the total load of $P_{0}$ at the end. The linear equations for $P_{1}$, $P_{2}$, $P_{3}$ are similarly.

According to the example with $4$ processes, $208$ tasks per process, we can propose the following constraints:
* For coefficients $a$, $b$, $c$, $d$:
    
    $a_{0} + a_{1} + a_{2} + a_{3} = 208$

    $b_{0} + b_{1} + b_{2} + b_{3} = 208$

    $c_{0} + c_{1} + c_{2} + c_{3} = 208$

    $d_{0} + d_{1} + d_{2} + d_{3} = 208$

* For the objective function:

    $F_{obj} = (L_{0} - avg)^2 + (L_{1} - avg)^2 + (L_{2} - avg)^2 + (L_{3} - avg)^2$

    Where, the value of $F_{obj}$ closed to $0$ is ideally.

* To transform $a_{0}, a_{1}, ..., d_{3}$ as the binary variables, we can address them as follows:

    $a_{0} = 2^0 \times x_{0} + 2^1 \times x_{1} + 2^2 \times x_{2} + 2^3 \times x_{3} + 2^4 \times x_{4} + 2^5 \times x_{5} + 2^6 \times x_{6} + \alpha \times x_{7}$

    $ = x_{0} + 2 \times x_{1} + 4 \times x_{2} + 8 \times x_{3} + 16 \times x_{4} + 32 \times x_{5} + 64 \times x_{6} + \alpha \times x_{7}$

    + Use 8 bits to represent the value of $a_{0}$
    
    + In this example, the number of tasks per process is 208, therefore, the last variable $x_7$ can be multiplied with $\alpha = 81$

### Formulation as task assignment with one-hot encoding



<!--     
    + Assigned on $m$ processes (processors) $\{P_{0}, P_{1}, ..., P_{m-1}\}$

    + Problem: load imbalance among processes due to performance slowdown, need to relocate tasks or migrate tasks, where we also aim to minimize makespan,
        - $makespan$: the completion time of all processes
        - migration cost: $c_{ij}$ when moving a task from process $i$ to process $j$

* Example: $20$ tasks in total, assigned to $4$ processes, the load values are illustrated as follows.



### A try for QUBO formulation

* Given $n$ tasks with execution time/load: $\{t_{0}, t_{1}, ..., t_{n-1}\}$
* Given a distribution on $m$ processes: $\{P_{0}, P_{1}, ..., P_{m-1}\}$.
* Binary variables following the given tasks: $\{x_{0}, x_{1}, ..., x_{n-1}\}$
* According the given information we know the load imbalance, e.g.,
    + In the above example, $n = 20$ tasks, $m = 4$ processes, tasks are binarized $\{x_{0}, x_{1}, ..., x_{19}\}$.
    + We know that: $P_{0}, P_{2}$ are underloaded processes, $P_{1}, P_{3}$ are overloaded.
    + Assume task migration happens, we have the objective function:

        `minimize` $y = \sum_{i \in n_{0}} t_{i} x_{i} + \sum_{i \in n_{2}} t_{i} x_{i} - (\sum_{i \in n_{1}} t_{i} x_{i} + \sum_{i \in n_{3}} t_{i} x_{i})$

        where, $\{n_{0}, n_{1}, ..., n_{m-1}\}$ is a new subset of tasks on each process.
    
    + The constraints include:

        $n_{0} + n_{1} + n_{2} + n_{3} = n$

        $n_{0} \leq k_{0}$, $n_{1} \leq k_{1}$, $n_{2} \leq k_{2}$, $n_{3} \leq k_{3}$, with $k_{i}$ is the maximun number of tasks that a process $i$ can hold.

### Another way to formulate the problem

* Using one-hot encoding (idea from Justyna):
    + For example, with a given task distribution and load values, we assume, $n=12$ tasks, $\{100, 100, 100, 200, 200, 200, 75, 75, 75, 150, 150, 150\}$.
    + The number of processes is $m=4$, each has $3$ tasks.
    + Using one-hot encoding to represent the tasks assigned in a process

    ![Onehot bitstring](./docs/onehot_bitstring.png)

* Migrating or no migrating tasks
     -->

