"""
This file contains some math utilities.
"""

EPSILON = 10e-6


def real_equal(x: float, y: float) -> bool:
    return abs(x - y) <= EPSILON
