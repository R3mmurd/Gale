"""
This file contains Joint, RevoluteJoint, and WheelJoint: constraints
between two Bodies (a hinge, and a wheel-on-a-suspension-spring,
respectively), wrapping one or more pymunk constraints without ever
exposing pymunk itself. Created through
World.create_revolute_joint/create_wheel_joint.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math
from typing import Any, List


class Joint:
    """
    Base class for a constraint between two bodies. Created through
    World.create_revolute_joint/create_wheel_joint, never directly.
    """

    def __init__(self, pm_constraints: List[Any]) -> None:
        self._pm_constraints = pm_constraints

    def destroy(self, pm_space: Any) -> None:
        """
        Internal — use World.destroy_joint instead.
        """
        for constraint in self._pm_constraints:
            pm_space.remove(constraint)


class RevoluteJoint(Joint):
    """
    A pin joint: constrains two bodies to rotate around a shared
    point, optionally motorized and/or limited to an angle range.

    Usage example:

        joint = world.create_revolute_joint(anchor_body, arm, (100, 50))
        joint.enable_motor = True
        joint.motor_speed = 2.0
        joint.max_motor_torque = 500

        joint.enable_limit = True
        joint.lower_angle = -0.5
        joint.upper_angle = 0.5
    """

    def __init__(
        self, pivot: Any, motor: Any, limit: Any, body_a: Any, body_b: Any
    ) -> None:
        super().__init__([pivot, motor, limit])
        self._pivot = pivot
        self._motor = motor
        self._limit = limit
        self._body_a = body_a
        self._body_b = body_b
        self._motor_enabled = False
        self._max_motor_torque = 0.0
        self._limit_enabled = False

    @property
    def angle(self) -> float:
        return self._body_b.angle - self._body_a.angle

    @property
    def motor_speed(self) -> float:
        # pymunk's SimpleMotor.rate drives body_b's angular velocity in
        # the opposite direction of its sign, the reverse of the
        # convention this API documents (positive motor_speed spins
        # body_b positively, relative to body_a) — negate at the
        # boundary so callers never see pymunk's convention.
        return -self._motor.rate

    @motor_speed.setter
    def motor_speed(self, value: float) -> None:
        self._motor.rate = -value

    @property
    def max_motor_torque(self) -> float:
        return self._max_motor_torque

    @max_motor_torque.setter
    def max_motor_torque(self, value: float) -> None:
        self._max_motor_torque = value

        if self._motor_enabled:
            self._motor.max_force = value

    @property
    def enable_motor(self) -> bool:
        return self._motor_enabled

    @enable_motor.setter
    def enable_motor(self, value: bool) -> None:
        self._motor_enabled = value
        self._motor.max_force = self._max_motor_torque if value else 0.0

    @property
    def enable_limit(self) -> bool:
        return self._limit_enabled

    @enable_limit.setter
    def enable_limit(self, value: bool) -> None:
        self._limit_enabled = value
        self._limit.max_force = float("inf") if value else 0.0

    @property
    def lower_angle(self) -> float:
        return self._limit.min

    @lower_angle.setter
    def lower_angle(self, value: float) -> None:
        self._limit.min = value

    @property
    def upper_angle(self) -> float:
        return self._limit.max

    @upper_angle.setter
    def upper_angle(self, value: float) -> None:
        self._limit.max = value


class WheelJoint(Joint):
    """
    A wheel with suspension: constrains a body to slide along an axis
    relative to another (the suspension, via a groove joint plus a
    damped spring), plus an unconstrained rotation (the wheel
    spinning), optionally motorized.

    Usage example:

        joint = world.create_wheel_joint(
            chassis, wheel, wheel.position, frequencyHz=4, dampingRatio=0.7
        )
        joint.enable_motor = True
        joint.motor_speed = -10  # drive forward
        joint.max_motor_torque = 800
    """

    def __init__(
        self,
        groove: Any,
        spring: Any,
        motor: Any,
        mass: float,
        frequency: float,
        damping_ratio: float,
    ) -> None:
        super().__init__([groove, spring, motor])
        self._spring = spring
        self._motor = motor
        self._mass = mass if mass > 0 else 1.0
        self._frequency = frequency
        self._damping_ratio = damping_ratio
        self._motor_enabled = False
        self._max_motor_torque = 0.0
        self._apply_spring_constants()

    def _apply_spring_constants(self) -> None:
        omega = 2 * math.pi * self._frequency
        self._spring.stiffness = self._mass * omega**2
        self._spring.damping = 2 * self._mass * self._damping_ratio * omega

    @property
    def motor_speed(self) -> float:
        # See RevoluteJoint.motor_speed: pymunk's SimpleMotor.rate sign
        # is inverted relative to the resulting angular velocity.
        return -self._motor.rate

    @motor_speed.setter
    def motor_speed(self, value: float) -> None:
        self._motor.rate = -value

    @property
    def max_motor_torque(self) -> float:
        return self._max_motor_torque

    @max_motor_torque.setter
    def max_motor_torque(self, value: float) -> None:
        self._max_motor_torque = value

        if self._motor_enabled:
            self._motor.max_force = value

    @property
    def enable_motor(self) -> bool:
        return self._motor_enabled

    @enable_motor.setter
    def enable_motor(self, value: bool) -> None:
        self._motor_enabled = value
        self._motor.max_force = self._max_motor_torque if value else 0.0

    @property
    def frequency(self) -> float:
        return self._frequency

    @frequency.setter
    def frequency(self, value: float) -> None:
        self._frequency = value
        self._apply_spring_constants()

    @property
    def damping_ratio(self) -> float:
        return self._damping_ratio

    @damping_ratio.setter
    def damping_ratio(self, value: float) -> None:
        self._damping_ratio = value
        self._apply_spring_constants()
