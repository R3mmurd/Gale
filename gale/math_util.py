"""
This file contains some math utilities.
"""

EPSILON = 10e-6


def real_equal(x: float, y: float) -> bool:
    """
    Compare two real numbers with a small epsilon.
    """
    return abs(x - y) <= EPSILON
