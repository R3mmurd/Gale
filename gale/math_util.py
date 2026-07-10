"""
This file contains small math utilities shared by other gale modules
— currently just a tolerance-based float equality check, used by
gale.ease_functions to detect t=0/t=1 exactly despite floating-point
drift.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

EPSILON = 10e-6


def real_equal(x: float, y: float) -> bool:
    return abs(x - y) <= EPSILON
