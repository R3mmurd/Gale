"""
This file contains the implementation of the classes Joint,
RevoluteJoint, and WheelJoint.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any


class Joint:
    """
    Base class for a constraint between two bodies. Created through
    World.create_revolute_joint/create_wheel_joint, never directly.
    """

    def __init__(self, b2_joint: Any) -> None:
        self._b2_joint = b2_joint

    def destroy(self, b2_world: Any) -> None:
        """
        Internal — use World.destroy_joint instead.
        """
        b2_world.DestroyJoint(self._b2_joint)


class RevoluteJoint(Joint):
    """
    A pin joint: constrains two bodies to rotate around a shared
    point, optionally motorized and/or limited to an angle range.

    Usage example:

        joint = world.create_revolute_joint(anchor_body, arm, (100, 50))
        joint.enable_motor = True
        joint.motor_speed = 2.0
        joint.max_motor_torque = 500
    """

    @property
    def angle(self) -> float:
        return self._b2_joint.angle

    @property
    def motor_speed(self) -> float:
        return self._b2_joint.motorSpeed

    @motor_speed.setter
    def motor_speed(self, value: float) -> None:
        self._b2_joint.motorSpeed = value

    @property
    def max_motor_torque(self) -> float:
        # b2RevoluteJoint's SWIG binding exposes maxMotorTorque as a
        # write-only property (no getter) — GetMaxMotorTorque() is the
        # equivalent read path.
        return self._b2_joint.GetMaxMotorTorque()

    @max_motor_torque.setter
    def max_motor_torque(self, value: float) -> None:
        self._b2_joint.maxMotorTorque = value

    @property
    def enable_motor(self) -> bool:
        return self._b2_joint.motorEnabled

    @enable_motor.setter
    def enable_motor(self, value: bool) -> None:
        self._b2_joint.motorEnabled = value


class WheelJoint(Joint):
    """
    A wheel with suspension: constrains a body to move along an axis
    relative to another (the suspension), plus an unconstrained
    rotation (the wheel spinning), optionally motorized.

    Usage example:

        joint = world.create_wheel_joint(
            chassis, wheel, wheel.position, frequencyHz=4, dampingRatio=0.7
        )
        joint.enable_motor = True
        joint.motor_speed = -10  # drive forward
        joint.max_motor_torque = 800
    """

    @property
    def motor_speed(self) -> float:
        return self._b2_joint.motorSpeed

    @motor_speed.setter
    def motor_speed(self, value: float) -> None:
        self._b2_joint.motorSpeed = value

    @property
    def max_motor_torque(self) -> float:
        return self._b2_joint.maxMotorTorque

    @max_motor_torque.setter
    def max_motor_torque(self, value: float) -> None:
        self._b2_joint.maxMotorTorque = value

    @property
    def enable_motor(self) -> bool:
        return self._b2_joint.motorEnabled

    @enable_motor.setter
    def enable_motor(self, value: bool) -> None:
        self._b2_joint.motorEnabled = value

    @property
    def frequency(self) -> float:
        return self._b2_joint.springFrequencyHz

    @frequency.setter
    def frequency(self, value: float) -> None:
        self._b2_joint.springFrequencyHz = value

    @property
    def damping_ratio(self) -> float:
        return self._b2_joint.springDampingRatio

    @damping_ratio.setter
    def damping_ratio(self, value: float) -> None:
        self._b2_joint.springDampingRatio = value
