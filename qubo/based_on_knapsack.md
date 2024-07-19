# LITERATURE
[SPAA-03] Gagan Aggarwal, Rajeev Motwani, and An Zhu. 2003. The load rebalancing problem. In Proceedings of the fifteenth annual ACM symposium on Parallel algorithms and architectures (SPAA '03). Association for Computing Machinery, New York, NY, USA, 258–265, https://doi.org/10.1145/777412.777460. [Formal NP-hard definition of the problem.]

[TPDS-13] Hung-Chang Hsiao, Hsueh-Yi Chung, Haiying Shen, and Yu-Chang Chao. 2013. Load Rebalancing for Distributed File Systems in Clouds. In IEEE Transactions on Parallel and Distributed Systems, vol. 24, no. 5, pp. 951-962, https://doi.org/10.1109/TPDS.2012.196. [Confirmation that the metric used for the objective function could be the "distance" from the average load value]

[SAI-23] Abhishek Awasthi, et al. 2023. Quantum Computing Techniques for Multi-knapsack Problems. In Arai, K. (eds) Intelligent Computing. SAI 2023. Lecture Notes in Networks and Systems, vol 739. Springer, Cham. https://doi.org/10.1007/978-3-031-37963-5_19. [In TPDS-13 it is mentioned that the LRB problem is similar to the knapsack problem. We use a similar QUBO formulation. However, we also have the initial assignment of tasks, and the constraint that we cannot move more than $k$ tasks. GitHub repository: https://github.com/QutacQuantum/Knapsack/blob/main/Knapsack_Full_Notebook.ipynb]

-----------------
# QUBO FORMULATION

"Given a possibly suboptimal assignemnt of jobs to processors, reassign jobs to different processors so as to minimize the makespan, by moving as few jobs as possible. More specifically, we look at the problem of minimizing the makespan, while migrating no more than $k$ jobs." [SPAA-03]

$N$ - number of tasks

$M$ - number of processes

$t_j$ - time of the execution of task $j$ (does not depend on the process)


$$ \begin{equation}
         x_{i,j}= 
\begin{cases}
    1,  & \text{task } j \text{ is assigned to processor } i,\\
    0,              & \text{otherwise}.
\end{cases}
 \end{equation}$$

### Objective function 

min $\sum_{i=0}^{M-1} (avg - \sum_{j=0}^{N-1} t_j \cdot x_{i,j})^2 $, where $ avg = \frac{\sum_{j} t_j}{N}$

The closer the objective function to 0, the better the more equally distributed the tasks.


### Constraints
- Migrate no more than $k$ jobs

$ \sum_{j=0}^{N-1} (1 - \sum_{i=0}^{M-1} (\hat{x}_{i,j} \cdot x_{i,j})^2) \leq k$, where $\hat{x}_{i,j}$ is the original assignment

- The assignment cannot be worse than the original one

$ \sum_{j=0}^{N-1} t_j \cdot x_{i,j} \leq c \text{, } \forall_{i} \in {0, \dots, M-1} $, where $c$ is the makespan

- Each task has to be assigned to exactly one processor (it depends on the encoding of the problem)
 
 $ \sum_{i=0}^{M-1} x_{i,j} = 1 \forall_{j} \in {0, \dots, N-1}$ 

RELATED WORK:
[Rathore-Load-2024] Omer Rathore, Alastair Basden, Nicholas Chancellor and Halim Kusumaatmaja. 2024. Load Balancing For High Performance Computing Using Quantum Annealing. In arXiv preprint.  https://doi.org/10.48550/arXiv.2403.05278. [It is not strictly related but presents a different quantum annealing approach to the similar problem. What it indicates is that there is some interest in this topic.]