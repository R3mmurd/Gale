"""
This file contains the implementation of the class Body.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, List, Optional

import pygame

from .body_type import BodyType
from .shapes import BoxShape, CircleShape, PolygonShape


class Body:
    """
    A physics body, in pixel units. Wraps a single Box2D body (never
    exposed) plus its fixtures. Created through World.create_static_body/
    create_dynamic_body/create_kinematic_body, never directly.

    Usage example:

        player = world.create_dynamic_body(100, 50, CircleShape(radius=10))
        player.apply_impulse(0, -400)  # jump

        # Every frame, after world.update(dt):
        pygame.draw.circle(surface, "white", player.position, 10)
    """

    def __init__(self, b2_body: Any, body_type: int, pixels_per_meter: float) -> None:
        """
        :param b2_body: The underlying Box2D body. Internal — build a Body through one of World's create_*_body methods instead.
        :param body_type: One of the BodyType constants.
        :param pixels_per_meter: The conversion factor this body's owning World uses.
        """
        self._b2_body = b2_body
        self._b2_body.userData = self
        self.body_type: int = body_type
        self._ppm: float = pixels_per_meter
        self.user_data: Any = None

    @property
    def position(self) -> pygame.Vector2:
        return pygame.Vector2(self._b2_body.position) * self._ppm

    @position.setter
    def position(self, value) -> None:
        x, y = value
        self._b2_body.position = (x / self._ppm, y / self._ppm)

    @property
    def angle(self) -> float:
        return self._b2_body.angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._b2_body.angle = value

    @property
    def velocity(self) -> pygame.Vector2:
        return pygame.Vector2(self._b2_body.linearVelocity) * self._ppm

    @velocity.setter
    def velocity(self, value) -> None:
        self.set_velocity(*value)

    @property
    def angular_velocity(self) -> float:
        return self._b2_body.angularVelocity

    @angular_velocity.setter
    def angular_velocity(self, value: float) -> None:
        self._b2_body.angularVelocity = value

    def set_velocity(self, vx: float, vy: float) -> None:
        """
        :param vx: Horizontal velocity, in pixels per second.
        :param vy: Vertical velocity, in pixels per second.
        """
        self._b2_body.linearVelocity = (vx / self._ppm, vy / self._ppm)

    def apply_force(self, fx: float, fy: float) -> None:
        """
        Apply a continuous force at this body's center of mass (call
        every frame while the force should be acting, such as a
        thruster).

        :param fx: Horizontal force.
        :param fy: Vertical force.
        """
        self._b2_body.ApplyForceToCenter((fx / self._ppm, fy / self._ppm), wake=True)

    def apply_torque(self, torque: float) -> None:
        """
        :param torque: The torque to apply this step.
        """
        self._b2_body.ApplyTorque(torque, wake=True)

    def apply_impulse(self, ix: float, iy: float) -> None:
        """
        Apply an instantaneous change in momentum at this body's
        center of mass (a one-off "kick", such as a jump).

        :param ix: Horizontal impulse.
        :param iy: Vertical impulse.
        """
        self._b2_body.ApplyLinearImpulse(
            (ix / self._ppm, iy / self._ppm), self._b2_body.worldCenter, wake=True
        )

    def add_circle(self, shape: CircleShape) -> None:
        """
        :param shape: The circle fixture to attach to this body.
        """
        self._b2_body.CreateCircleFixture(
            radius=shape.radius / self._ppm,
            pos=(shape.offset[0] / self._ppm, shape.offset[1] / self._ppm),
            density=shape.density,
            friction=shape.friction,
            restitution=shape.restitution,
            isSensor=shape.is_sensor,
        )

    def add_box(self, shape: BoxShape) -> None:
        """
        :param shape: The box fixture to attach to this body.
        """
        self._b2_body.CreatePolygonFixture(
            box=(
                shape.width / 2 / self._ppm,
                shape.height / 2 / self._ppm,
                (shape.offset[0] / self._ppm, shape.offset[1] / self._ppm),
                0,
            ),
            density=shape.density,
            friction=shape.friction,
            restitution=shape.restitution,
            isSensor=shape.is_sensor,
        )

    def add_polygon(self, shape: PolygonShape) -> None:
        """
        :param shape: The polygon fixture to attach to this body.
        """
        vertices = [(x / self._ppm, y / self._ppm) for x, y in shape.points]
        self._b2_body.CreatePolygonFixture(
            vertices=vertices,
            density=shape.density,
            friction=shape.friction,
            restitution=shape.restitution,
            isSensor=shape.is_sensor,
        )

    @property
    def touching_bodies(self) -> List["Body"]:
        """
        :returns: Every other Body currently in contact with this one (a cheap way to answer "is this body resting on something," with no event bookkeeping needed).
        """
        bodies = []

        for contact_edge in self._b2_body.contacts:
            contact = contact_edge.contact

            if contact.touching:
                other = contact_edge.other.userData

                if isinstance(other, Body):
                    bodies.append(other)

        return bodies

    def destroy(self) -> None:
        """
        Remove this body (and its fixtures) from its World. Do not
        use this Body afterwards.
        """
        self._b2_body.userData = None
        self._b2_body.world.DestroyBody(self._b2_body)
