"""
This file contains the implementation of some ease functions to
interpolate values.

Author: Alejandro Mujica
"""

import math

from .math_util import real_equal


def ease_linear(t: float) -> float:
    """
    Linear interpolation function.
    This function does not interpolate the value.
    """
    return t


def ease_in_sine(t: float) -> float:
    """
    Ease in function using the sine function.
    This function starts slow and then accelerates.
    """
    return 1 - math.cos((math.pi * t) / 2)


def ease_out_sine(t: float) -> float:
    """
    Ease out function using the sine function.
    This function starts fast and then decelerates.
    """
    return math.sin((math.pi * t) / 2)


def ease_in_out_sine(t: float) -> float:
    """
    Ease in out function using the sine function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    return -(math.cos(math.pi * t) - 1) / 2


def ease_in_quad(t: float) -> float:
    """
    Ease in function using the quadratic function.
    This function starts slow and then accelerates.
    """
    return t * t


def ease_out_quad(t: float) -> float:
    """
    Ease out function using the quadratic function.
    This function starts fast and then decelerates.
    """
    return 1 - (1 - t) * (1 - t)


def ease_in_out_quad(t: float) -> float:
    """
    Ease in out function using the quadratic function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


def ease_in_cubic(t: float) -> float:
    """
    Ease in function using the cubic function.
    This function starts slow and then accelerates.
    """
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """
    Ease out function using the cubic function.
    This function starts fast and then decelerates.
    """
    return 1 - pow(1 - t, 3)


def ease_in_out_cubic(t: float) -> float:
    """
    Ease in out function using the cubic function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def ease_in_quart(t: float) -> float:
    """
    Ease in function using the quartic function.
    This function starts slow and then accelerates.
    """
    return t * t * t * t


def ease_out_quart(t: float) -> float:
    """
    Ease out function using the quartic function.
    This function starts fast and then decelerates.
    """
    return 1 - pow(1 - t, 4)


def ease_in_out_quart(t: float) -> float:
    """
    Ease in out function using the quartic function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    return 8 * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 4) / 2


def ease_in_quint(t: float) -> float:
    """
    Ease in function using the quintic function.
    This function starts slow and then accelerates.
    """
    return t * t * t * t * t


def ease_out_quint(t: float) -> float:
    """
    Ease out function using the quintic function.
    This function starts fast and then decelerates.
    """
    return 1 - pow(1 - t, 5)


def ease_in_out_quint(t: float) -> float:
    """
    Ease in out function using the quintic function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    return 16 * t * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 5) / 2


def ease_in_expo(t: float) -> float:
    """
    Ease in function using the exponential function.
    This function starts slow and then accelerates.
    """
    return 0 if real_equal(t, 0) else pow(2, 10 * t - 10)


def ease_out_expo(t: float) -> float:
    """
    Ease out function using the exponential function.
    This function starts fast and then decelerates.
    """
    return 1 if real_equal(t, 1) else 1 - pow(2, -10 * t)


def ease_in_out_expo(t: float) -> float:
    """
    Ease in out function using the exponential function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    if real_equal(t, 0) or real_equal(t, 1):
        return t

    if t < 0.5:
        return pow(2, 20 * t - 10) / 2
    else:
        return (2 - pow(2, -20 * t + 10)) / 2


def ease_in_circ(t: float) -> float:
    """
    Ease in function using the circular function.
    This function starts slow and then accelerates.
    """
    return 1 - math.sqrt(1 - t * t)


def ease_out_circ(t: float) -> float:
    """
    Ease out function using the circular function.
    This function starts fast and then decelerates.
    """
    return math.sqrt(1 - pow(t - 1, 2))


def ease_in_out_circ(t: float) -> float:
    """
    Ease in out function using the circular function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    return (
        (1 - math.sqrt(1 - 4 * t * t)) / 2
        if t < 0.5
        else (math.sqrt(1 - pow(-2 * t + 2, 2)) + 1) / 2
    )


def ease_in_back(t: float) -> float:
    """
    Ease in function using the back function.
    This function starts slow and then accelerates.
    """
    C1 = 1.70158
    C3 = C1 + 1
    return C3 * t * t * t - C1 * t * t


def ease_out_back(t: float) -> float:
    """
    Ease out function using the back function.
    This function starts fast and then decelerates.
    """
    C1 = 1.70158
    C3 = C1 + 1
    return 1 + C3 * pow(t - 1, 3) + C1 * pow(t - 1, 2)


def ease_in_out_back(t: float) -> float:
    """
    Ease in out function using the back function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    C1 = 1.70158
    C2 = C1 * 1.525

    return (
        (4 * t * t * ((C2 + 1) * 2 * t - C2)) / 2
        if t < 0.5
        else (pow(2 * t - 2, 2) * ((C2 + 1) * (t * 2 - 2) + C2) + 2) / 2
    )


def ease_in_elastic(t: float) -> float:
    """
    Ease in function using the elastic function.
    This function starts slow and then accelerates.
    """
    if real_equal(t, 0) or real_equal(t, 1):
        return t

    C4 = (2 * math.pi) / 3

    return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * C4)


def ease_out_elastic(t: float) -> float:
    """
    Ease out function using the elastic function.
    This function starts fast and then decelerates.
    """
    if real_equal(t, 0) or real_equal(t, 1):
        return t

    C4 = (2 * math.pi) / 3

    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * C4) + 1


def ease_in_out_elastic(t: float) -> float:
    """
    Ease in out function using the elastic function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    if real_equal(t, 0) or real_equal(t, 1):
        return t

    C5 = (2 * math.pi) / 4.5

    if t < 0.5:
        return -0.5 * pow(2, 20 * t - 10) * math.sin((20 * t - 11.125) * C5)
    else:
        return pow(2, -20 * t + 10) * math.sin((20 * t - 11.125) * C5) * 0.5 + 1


def ease_in_bounce(t: float) -> float:
    """
    Ease in function using the bounce function.
    This function starts slow and then accelerates.
    """
    return 1 - ease_out_bounce(1 - t)


def ease_out_bounce(t: float) -> float:
    """
    Ease out function using the bounce function.
    This function starts fast and then decelerates.
    """
    n1 = 7.5625
    d1 = 2.75

    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def ease_in_out_bounce(t: float) -> float:
    """
    Ease in out function using the bounce function.
    This function starts slow, then accelerates, and finally decelerates.
    """
    if t < 0.5:
        return (1 - ease_out_bounce(1 - 2 * t)) / 2
    else:
        return (1 + ease_out_bounce(2 * t - 1)) / 2


EASE_FUNCTIONS = {
    "linear": ease_linear,
    "in_sine": ease_in_sine,
    "out_sine": ease_out_sine,
    "in_out_sine": ease_in_out_sine,
    "in_quad": ease_in_quad,
    "out_quad": ease_out_quad,
    "in_out_quad": ease_in_out_quad,
    "in_cubic": ease_in_cubic,
    "out_cubic": ease_out_cubic,
    "in_out_cubic": ease_in_out_cubic,
    "in_quart": ease_in_quart,
    "out_quart": ease_out_quart,
    "in_out_quart": ease_in_out_quart,
    "in_quint": ease_in_quint,
    "out_quint": ease_out_quint,
    "in_out_quint": ease_in_out_quint,
    "in_expo": ease_in_expo,
    "out_expo": ease_out_expo,
    "in_out_expo": ease_in_out_expo,
    "in_circ": ease_in_circ,
    "out_circ": ease_out_circ,
    "in_out_circ": ease_in_out_circ,
    "in_back": ease_in_back,
    "out_back": ease_out_back,
    "in_out_back": ease_in_out_back,
    "in_elastic": ease_in_elastic,
    "out_elastic": ease_out_elastic,
    "in_out_elastic": ease_in_out_elastic,
    "in_bounce": ease_in_bounce,
    "out_bounce": ease_out_bounce,
    "in_out_bounce": ease_in_out_bounce,
}
