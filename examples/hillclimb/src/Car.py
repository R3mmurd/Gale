import math

import pygame

from gale.physics.shapes import BoxShape, CircleShape
from gale.physics.world import World

import settings


class Car:
    """
    A chassis and two wheels connected by motorized wheel joints
    (spring/damper suspension via frequency/damping_ratio) — the
    classic Box2D joints showcase.
    """

    def __init__(self, world: World, x: float, y: float) -> None:
        self.chassis = world.create_dynamic_body(
            x, y, BoxShape(settings.CHASSIS_WIDTH, settings.CHASSIS_HEIGHT, density=1.2)
        )
        self.chassis.user_data = "chassis"

        wheel_y = y + settings.WHEEL_OFFSET_Y
        self.rear_wheel = world.create_dynamic_body(
            x - settings.WHEEL_OFFSET_X,
            wheel_y,
            CircleShape(radius=settings.WHEEL_RADIUS, friction=settings.WHEEL_FRICTION),
        )
        self.front_wheel = world.create_dynamic_body(
            x + settings.WHEEL_OFFSET_X,
            wheel_y,
            CircleShape(radius=settings.WHEEL_RADIUS, friction=settings.WHEEL_FRICTION),
        )

        self.rear_joint = world.create_wheel_joint(
            self.chassis,
            self.rear_wheel,
            self.rear_wheel.position,
            axis=(0, 1),
            frequencyHz=settings.SUSPENSION_FREQUENCY,
            dampingRatio=settings.SUSPENSION_DAMPING,
        )
        self.front_joint = world.create_wheel_joint(
            self.chassis,
            self.front_wheel,
            self.front_wheel.position,
            axis=(0, 1),
            frequencyHz=settings.SUSPENSION_FREQUENCY,
            dampingRatio=settings.SUSPENSION_DAMPING,
        )

        for joint in (self.rear_joint, self.front_joint):
            joint.enable_motor = True
            joint.max_motor_torque = settings.MOTOR_TORQUE
            joint.motor_speed = 0

    def drive(self, direction: int) -> None:
        """
        :param direction: 1 to accelerate forward, -1 to reverse, 0 to coast.
        """
        speed = direction * settings.MOTOR_SPEED
        self.rear_joint.motor_speed = speed
        self.front_joint.motor_speed = speed

    def has_flipped(self) -> bool:
        return abs(self.chassis.angle) > settings.FLIP_ANGLE

    def render(self, surface: pygame.Surface) -> None:
        self._render_chassis(surface)

        for wheel in (self.rear_wheel, self.front_wheel):
            self._render_wheel(surface, wheel)

    def _render_chassis(self, surface: pygame.Surface) -> None:
        half_width = settings.CHASSIS_WIDTH / 2
        half_height = settings.CHASSIS_HEIGHT / 2
        corners = [
            (-half_width, -half_height),
            (half_width, -half_height),
            (half_width, half_height),
            (-half_width, half_height),
        ]
        position = self.chassis.position
        angle = self.chassis.angle
        points = [_rotate_and_translate(x, y, angle, position) for x, y in corners]
        pygame.draw.polygon(surface, settings.COLOR_CHASSIS, points)

    def _render_wheel(self, surface: pygame.Surface, wheel) -> None:
        position = wheel.position
        pygame.draw.circle(
            surface, settings.COLOR_WHEEL, position, settings.WHEEL_RADIUS
        )
        mark = _rotate_and_translate(
            settings.WHEEL_RADIUS - 3, 0, wheel.angle, position
        )
        pygame.draw.line(surface, settings.COLOR_WHEEL_MARK, position, mark, 2)


def _rotate_and_translate(x, y, angle, position):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return (
        position.x + x * cos_a - y * sin_a,
        position.y + x * sin_a + y * cos_a,
    )
