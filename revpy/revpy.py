"""
High-level revenue management functions for calculating booking limits.

Currently includes EMSRb, EMSRb + fare transformation (EMSRb-MR), and a
custom heuristic (EMSRb_MR_step).

"""

import numpy as np

from revpy.helpers import check_fares_decreasing, \
    cumulative_booking_limits, incremental_booking_limits
from revpy.optimizers import calc_EMSRb
from revpy.meta_optimizers import calc_EMSRb_MR


def booking_limits(fares, demands, cap, sigmas=None, method='EMSRb'):
   
    if method == 'EMSRb_MR_step':
        book_lim = iterative_booking_limits(fares, demands, cap, sigmas,
                                            'EMSRb_MR')
    else:
        prot_levels = protection_levels(fares, demands, sigmas, cap, method)
        cum_book_lim = cumulative_booking_limits(prot_levels, cap)
        book_lim = incremental_booking_limits(cum_book_lim)

    return book_lim


def protection_levels(fares, demands, sigmas=None, cap=None, method='EMSRb'):
   
    check_fares_decreasing(fares)

    if method == 'EMSRb':
        return calc_EMSRb(fares, demands, sigmas)

    elif method == 'EMSRb_MR':
        prot_levels = calc_EMSRb_MR(fares, demands, sigmas, cap)
        return prot_levels

    else:
        raise ValueError('method "{}" not supported'.format(method))


def iterative_booking_limits(fares, demands, cap, sigmas=None,
                             method='EMSRb_MR'):
   

    # iterate through all possible capacities (remaining seats) and
    # calculate cheapest open fare class (fc)
    cheapest_open_fc_list = []
    for remaining_cap in range(1, int(cap) + 1):
        temp_book_lims = \
            booking_limits(fares, demands, remaining_cap, sigmas, method)
        cheapest_open_fc = max(np.where(temp_book_lims > 0)[0])
        cheapest_open_fc_list.append(cheapest_open_fc)
    fcs = np.array(range(0, len(fares)))
    book_lims = np.zeros(len(fcs))

    # count the number of times a particular fare class was the cheapest
    # open
    for fc in fcs:
        book_lims[fc] = cheapest_open_fc_list.count(fc)

    return book_lims
