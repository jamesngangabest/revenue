import numpy as np
import pandas as pd
import pulp
from itertools import product
from functools import wraps


def solve_network_lp(fares, demands, capacities, A, class_names=None,
                     trip_names=None, leg_names=None):
   
    optimal revenue: number
            the optimal revenue achieved with the optimal allocation
    trip_names, constraint_ 

    n_classes, n_trips = fares.shape
    n_legs = len(capacities)

    null_fares = pd.isnull(fares)
    null_demands = pd.isnull((demands))
    null_A = pd.isnull(A)
    demands[null_fares | null_demands] = 0
    fares[null_fares] = 0
    A[null_A] = 0

    if class_names is None:
        class_names = ['class{}'.format(i) for i in np.arange(n_classes) + 1]

    if trip_names is None:
        trip_names = ['trip{}'.format(i) for i in np.arange(n_trips) + 1]

    if leg_names is None:
        leg_names = ['leg{}'.format(i) for i in np.arange(n_legs) + 1]

    product_names = ['{}_{}'.format(trip, cls)
                       for cls, trip
                       in product(class_names, trip_names)]

    prob, x = define_lp(fares, product_names)
    add_demand_constraints(x, demands, product_names)
    capacity_constraints = add_capacity_constraints(prob, x, A, product_names,
                                                    capacities, leg_names)

    optimal_revenue = solve_lp(prob)

    allocations = get_allocations(x, product_names, fares.shape)
    bid_prices, constraint_names = get_shadow_prices(capacity_constraints)

    return allocations, bid_prices, optimal_revenue, trip_names, \
           constraint_names, class_names, leg_names


def define_lp(fares, product_names):
   
    prob = pulp.LpProblem('network_RM', pulp.LpMaximize)

    # decision variables: available seats per product
    x = pulp.LpVariable.dicts('x', product_names, lowBound=0)

    # objective function
    revenue = pulp.lpSum([x[it]*fares.ravel()[i] for i, it in
                          enumerate(product_names)])
    prob += revenue

    return prob, x


def add_demand_constraints(x, demands, product_names):
    """Add demands as upper bound to possible seat availability on products."""
    for i, it in enumerate(product_names):
        x[it].upBound = demands.ravel()[i]


def add_capacity_constraints(prob, x, A, product_names, capacities,
                             leg_names=None):
    
    n_trips, n_legs = A.shape
    n_classes = int(len(product_names) / n_trips)
    A_ = np.tile(A, (n_classes, 1))

    capacity_constraints = []
    for leg, leg_name in enumerate(leg_names):
        leg_load = pulp.lpSum([x[it]*A_[i, leg] for i, it
                               in enumerate(product_names)])
        capacity_constraint = (leg_load <= capacities[leg],
                               "cap_{}".format(leg_name))
        prob += capacity_constraint
        capacity_constraints.append(capacity_constraint)

    return capacity_constraints


def get_allocations(x, product_names, out_shape):
    """Return allocations after solving of LP and reshape them."""
    allocations = [x[it].value() for it in product_names]
    return np.array(allocations).reshape(out_shape)


def get_shadow_prices(constraints):
    """Extract shadow prices for the capacity contraints -> bid prices."""
    shadow_prices = [var[0].pi for var in constraints]
    constraint_names = [var[1] for var in constraints]
    return shadow_prices, constraint_names


def solve_lp(prob):
    """Solve LP, return min/max."""
    optimization_result = prob.solve()
    assert optimization_result == pulp.LpStatusOptimal
    optimal_value = pulp.value(prob.objective)

    return optimal_value


def wrap_df(func):
    """Make `solve_network_lp` accepting pandas data frames."""
    @wraps(func)
    def solve_network_lp(fares, demands, capacities, A, class_names=None,
                         trip_names=None, leg_names=None):

        if isinstance(fares, pd.DataFrame):
            trip_names = fares.columns
            fares = fares.values
        if isinstance(demands, pd.DataFrame):
            class_names = demands.index
            demands = demands.values
        if isinstance(A, pd.DataFrame):
            leg_names = A.columns
            A = A.values

        (allocations, bid_prices, optimal_revenue,
         trip_names, constraint_names, class_names,
         leg_names) = func(fares, demands, capacities, A,
                           class_names, trip_names, leg_names)

        allocations_df = pd.DataFrame(allocations.T,
                                      columns=class_names,
                                      index=trip_names)

        bid_prices_df = pd.DataFrame(bid_prices,
                                     columns=['bid_price'],
                                     index=leg_names)

        return allocations_df, bid_prices_df

    return solve_network_lp


solve_network_lp_df = wrap_df(solve_network_lp)