import sys
import math
import random
import logging

from collections import defaultdict
from itertools import combinations

import gurobipy as gp
from gurobipy import GRB

def solve_tsp(nodes, distances):
    """
    Solve a dense symmetric TSP using the following base formulation:

    min  sum_ij d_ij x_ij
    s.t. sum_j x_ij == 2   forall i in V
         x_ij binary       forall (i,j) in E

    and subtours eliminated using lazy constraints.
    """

    with gp.Env() as env, gp.Model(env=env) as m:
        # Create variables, and add symmetric keys to the resulting dictionary
        # 'x', such that (i, j) and (j, i) refer to the same variable.
        x = m.addVars(distances.keys(), obj=distances, vtype=GRB.BINARY, name="e")
        x.update({(j, i): v for (i, j), v in x.items()})

        # Create degree 2 constraints
        for i in nodes:
            m.addConstr(gp.quicksum(x[i, j] for j in nodes if i != j) == 2)

        # Optimize model using lazy constraints to eliminate subtours
        m.Params.LazyConstraints = 1
        # cb = TSPCallback(nodes, x)
        # m.optimize(cb)

        # Extract the solution as a tour
        edges = [(i, j) for (i, j), v in x.items() if v.X > 0.5]
        # tour = shortest_subtour(edges)
        # assert set(tour) == set(nodes)

        # return tour, m.ObjVal
        return m.ObjVal


if __name__ == "__main__":

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: tsp.py npoints <seed>")
        sys.exit(0)
    npoints = int(sys.argv[1])
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    # Create n random points in 2D
    random.seed(seed)
    nodes = list(range(npoints))
    points = [(random.randint(0, 100), random.randint(0, 100)) for i in nodes]

    # Dictionary of Euclidean distance between each pair of points
    distances = {
        (i, j): math.sqrt(sum((points[i][k] - points[j][k]) ** 2 for k in range(2)))
        for i, j in combinations(nodes, 2)
    }

    print("-------------------------------------------------------")
    print("Points: {}".format(points))
    print("Distances: {}".format(distances))
    print("-------------------------------------------------------")

    # tour, cost = solve_tsp(nodes, distances)

    # print("")
    # print(f"Optimal tour: {tour}")
    # print(f"Optimal cost: {cost:g}")
    # print("")