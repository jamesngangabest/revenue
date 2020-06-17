


import numpy as np

from revpy.helpers import check_fares_decreasing, fill_nan


def calc_fare_transformation(fares, demands, cap=None,
                             fare_structure='undifferentiated',
                             return_all=False):

    

    if fare_structure != 'undifferentiated':
        raise ValueError('dare structure "{}" not supported'
                         ''.format(fare_structure))

    check_fares_decreasing(fares)

    # cumulative demand
    Q = demands.cumsum()

    # shrink Q when it exceeds capacity
    if cap is not None:
        Q[Q > cap] = cap

    # total revenue
    TR = fares*Q

    # calculate fare adjustment, remove inefficient strategies
    adjusted_fares_temp, adjusted_demand_temp, Q_eff_temp, \
        TR_eff_temp, eff_indices = efficient_strategies(Q, TR, fares[0])

    # ensure that adjusted fares and demands have the same shape as `fares` by
    # filling indices corresponding to inefficient strategies with NaNs.
    size = fares.shape
    adjusted_fares = fill_nan(size, eff_indices, adjusted_fares_temp)
    adjusted_demand = fill_nan(size, eff_indices, adjusted_demand_temp)

    if not return_all:

        return adjusted_fares, adjusted_demand
    else:
        Q_eff = fill_nan(size, eff_indices, Q_eff_temp)
        TR_eff = fill_nan(size, eff_indices, TR_eff_temp)

        return adjusted_fares, adjusted_demand, Q_eff, TR_eff


def efficient_strategies(Q, TR, highest_fare, indices=None):
    

    adjusted_demand = Q - np.hstack((0, Q[:-1]))
    adjusted_fares = (TR - np.hstack((0, TR[:-1]))) / adjusted_demand

   
    if adjusted_demand[0] == 0 or np.isnan(adjusted_demand[0]):
        adjusted_fares[0] = highest_fare

    
    adjusted_fares[np.isnan(adjusted_fares)] = -1

    # initialize indices
    if indices is None:
        indices = np.arange(0, len(Q))

    # base case
    if all(adjusted_fares >= 0):

        return adjusted_fares, adjusted_demand, Q, TR, indices
    # recursively remove inefficient strategies
    else:
        inefficient = adjusted_fares < 0
        Q = Q[~inefficient]
        TR = TR[~inefficient]
        indices = indices[~inefficient]

        return efficient_strategies(Q, TR, highest_fare, indices)


def fare_trafo_decorator(optimizer):
    """Decorator that wraps the fare trafo around an optimizer."""

    def wrapper(fares, demands, sigmas=None, cap=None):
        if sigmas is None:
            sigmas = np.zeros(fares.shape)

        adjusted_fares, adjusted_demand = \
            calc_fare_transformation(fares, demands, cap=cap)

        # inefficient strategies correspond NaN adjusted fares
        efficient_indices = np.where(~np.isnan(adjusted_fares))[0]
        # calculate protection levels with `optimizer` using efficient
        # strategies only
        if adjusted_fares[efficient_indices].size:
            protection_levels_temp = optimizer(
                adjusted_fares[efficient_indices],
                adjusted_demand[efficient_indices],
                sigmas[efficient_indices])
            protection_levels = fill_nan(fares.shape, efficient_indices,
                                         protection_levels_temp)
        else:
            # if there is no efficient strategy, return zeros as  protection
            #  levels
            protection_levels = np.zeros(fares.shape)

        return protection_levels

    return wrapper
