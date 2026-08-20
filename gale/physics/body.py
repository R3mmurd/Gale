"""
This file contains the implementation of the class Body: a physics
body and its fixtures, in pixel units, wrapping a single pymunk body
without ever exposing pymunk itself. Created through
World.create_static_body/create_dynamic_body/create_kinematic_body.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, List, Optional

import pygame
import pymunk

from .body_type import BodyType
from .shapes import BoxShape, CircleShape, PolygonShape


class Body:
    """
    A physics body, in pixel units. Wraps a single pymunk body (never
    exposed) plus its fixtures. Created through World.create_static_body/
    create_dynamic_body/create_kinematic_body, never directly.

    Usage example:

        player = world.create_dynamic_body(100, 50, CircleShape(radius=10))
        player.apply_impulse(0, -400)  # jump

        # Every frame, after world.update(dt):
        pygame.draw.circle(surface, "white", player.position, 10)
    """

    def __init__(
        self,
        pm_body: Any,
        world: Any,
        body_type: int,
        pixels_per_meter: float,
    ) -> None:
        """
        :param pm_body: The underlying pymunk body. Internal — build a Body through one of World's create_*_body methods instead.
        :param world: The World pm_body lives in. Internal — needed so add_circle/add_box/add_polygon/destroy/touching_bodies can reach its pymunk space and contact-tracking.
        :param body_type: One of the BodyType constants.
        :param pixels_per_meter: The conversion factor this body's owning World uses.
        """
        self._pm_body = pm_body
        self._pm_body.gale_body = self
        self._world = world
        self.body_type: int = body_type
        self._ppm: float = pixels_per_meter
        self.user_data: Any = None
        self._linear_damping: float = 0.0
        self._angular_damping: float = 0.0

    @property
    def _pm_space(self) -> Any:
        return self._world._space

    @property
    def position(self) -> pygame.Vector2:
        return pygame.Vector2(*self._pm_body.position) * self._ppm

    @position.setter
    def position(self, value) -> None:
        x, y = value
        self._pm_body.position = (x / self._ppm, y / self._ppm)

    @property
    def angle(self) -> float:
        return self._pm_body.angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._pm_body.angle = value

    @property
    def velocity(self) -> pygame.Vector2:
        return pygame.Vector2(*self._pm_body.velocity) * self._ppm

    @velocity.setter
    def velocity(self, value) -> None:
        self.set_velocity(*value)

    @property
    def angular_velocity(self) -> float:
        return self._pm_body.angular_velocity

    @angular_velocity.setter
    def angular_velocity(self, value: float) -> None:
        self._pm_body.angular_velocity = value

    def set_velocity(self, vx: float, vy: float) -> None:
        """
        :param vx: Horizontal velocity, in pixels per second.
        :param vy: Vertical velocity, in pixels per second.
        """
        self._pm_body.velocity = (vx / self._ppm, vy / self._ppm)

    def apply_force(self, fx: float, fy: float) -> None:
        """
        Apply a continuous force at this body's center of mass (call
        every frame while the force should be acting, such as a
        thruster).

        :param fx: Horizontal force.
        :param fy: Vertical force.
        """
        self._pm_body.apply_force_at_local_point(
            (fx / self._ppm, fy / self._ppm), (0, 0)
        )

    def apply_torque(self, torque: float) -> None:
        """
        :param torque: The torque to apply this step.
        """
        self._pm_body.torque += torque

    def apply_impulse(self, ix: float, iy: float) -> None:
        """
        Apply an instantaneous change in momentum at this body's
        center of mass (a one-off "kick", such as a jump).

        :param ix: Horizontal impulse.
        :param iy: Vertical impulse.
        """
        self._pm_body.apply_impulse_at_local_point(
            (ix / self._ppm, iy / self._ppm), (0, 0)
        )

    def add_circle(self, shape: CircleShape) -> None:
        """
        :param shape: The circle fixture to attach to this body.
        """
        ppm = self._ppm
        pm_shape = pymunk.Circle(
            self._pm_body,
            radius=shape.radius / ppm,
            offset=(shape.offset[0] / ppm, shape.offset[1] / ppm),
        )
        self._configure_shape(pm_shape, shape)

    def add_box(self, shape: BoxShape) -> None:
        """
        :param shape: The box fixture to attach to this body.
        """
        ppm = self._ppm
        half_width = shape.width / 2 / ppm
        half_height = shape.height / 2 / ppm
        ox = shape.offset[0] / ppm
        oy = shape.offset[1] / ppm
        vertices = [
            (-half_width + ox, -half_height + oy),
            (half_width + ox, -half_height + oy),
            (half_width + ox, half_height + oy),
            (-half_width + ox, half_height + oy),
        ]
        pm_shape = pymunk.Poly(self._pm_body, vertices)
        self._configure_shape(pm_shape, shape)

    def add_polygon(self, shape: PolygonShape) -> None:
        """
        :param shape: The polygon fixture to attach to this body.
        """
        ppm = self._ppm
        vertices = [(x / ppm, y / ppm) for x, y in shape.points]
        pm_shape = pymunk.Poly(self._pm_body, vertices)
        self._configure_shape(pm_shape, shape)

    def _configure_shape(self, pm_shape: Any, shape: Any) -> None:
        pm_shape.density = shape.density
        pm_shape.friction = shape.friction
        pm_shape.elasticity = shape.restitution
        pm_shape.sensor = shape.is_sensor
        self._pm_space.add(pm_shape)

    @property
    def touching_bodies(self) -> List["Body"]:
        """
        :returns: Every other Body currently in contact with this one (a cheap way to answer "is this body resting on something," with no event bookkeeping needed). Includes sensor overlaps, same as on_collision_begin/on_collision_end.
        """
        return list(self._world._touching.get(self, {}).keys())

    def set_damping(
        self, linear_damping: float = 0.0, angular_damping: float = 0.0
    ) -> None:
        """
        Slow this body's linear/angular velocity down over time, e.g.
        to approximate air resistance — every fixed_update(), velocity
        is scaled by 1 / (1 + fixed_timestep * damping). 0 (the
        default for every new Body) means no damping at all.

        :param linear_damping: Damping applied to velocity. The default value is 0.0.
        :param angular_damping: Damping applied to angular_velocity. The default value is 0.0.
        """
        self._linear_damping = linear_damping
        self._angular_damping = angular_damping
        self._pm_body.velocity_func = self._apply_velocity_and_damping

    def _apply_velocity_and_damping(
        self, pm_body: Any, gravity: Any, damping: float, dt: float
    ) -> None:
        pymunk.Body.update_velocity(pm_body, gravity, damping, dt)
        pm_body.velocity = pm_body.velocity / (1 + dt * self._linear_damping)
        pm_body.angular_velocity = pm_body.angular_velocity / (
            1 + dt * self._angular_damping
        )

    def destroy(self) -> None:
        """
        Remove this body (and its fixtures) from its World. Do not
        use this Body afterwards.
        """
        self._pm_body.gale_body = None
        self._world._forget_touching(self)

        for pm_shape in list(self._pm_body.shapes):
            self._pm_space.remove(pm_shape)

        self._pm_space.remove(self._pm_body)
