## Experiment setup

1. Varied Imbalance Ratios
- Num. Procs: 8						
- Num. Tasks/proc: 50						
- Matrix sizes: 128, 192, 256, 320, 384, 448, 512

|           | P0  | P1  | P2  | P3  | P4  | P5  | P6  | P7  | Rimb       |
|-----------|-----|-----|-----|-----|-----|-----|-----|-----|------------|
|Testcase 1 | 384 | 384 | 384 | 384 | 384 | 384 | 384 | 384 | 0          |
|Testcase 2	| 448 | 384	| 256 | 320	| 128 | 192	| 128 | 512	| 0,72972973 |
|Testcase 3	| 512 | 192	| 128 | 192	| 128 | 128	| 128 | 512	| 1,13333333 |
|Testcase 4	| 128 | 192	| 128 | 256	| 128 | 320	| 192 | 512	| 1,20689655 |
|Testcase 5	| 128 | 128	| 512 | 128	| 128 | 128	| 448 | 128	| 1,37037037 |

2. Varied Numbers of Partitions/Processes

3. Varied Numbers of Tasks

