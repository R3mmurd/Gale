"""
This file contains the implementation of the class World.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, List, Optional, Tuple

import Box2D
import pygame

from .body import Body
from .body_type import BodyType
from .joint import Joint, RevoluteJoint, WheelJoint
from .shapes import BoxShape, CircleShape, PolygonShape

OnCollision = Callable[[Body, Body], None]

# Box2D's own recommended values, unrelated to pixels_per_meter.
VELOCITY_ITERATIONS: int = 8
POSITION_ITERATIONS: int = 3


class _ContactListener(Box2D.b2ContactListener):
    def __init__(self, world: "World") -> None:
        super().__init__()
        self._world = world

    def BeginContact(self, contact) -> None:
        self._world._dispatch_contact(contact, self._world._begin_callbacks)

    def EndContact(self, contact) -> None:
        self._world._dispatch_contact(contact, self._world._end_callbacks)


class World:
    """
    A physics simulation, in pixel units. Wraps a Box2D world (never
    exposed) and every Body/Joint created in it.

    Follows the same update/fixed_update split Unity uses to decouple
    the game loop's real, variable dt from the fixed timestep Box2D's
    solver needs for stable results: call update(dt) once a frame,
    same as everything else in gale; it accumulates dt and calls
    fixed_update() (a real Box2D step) as many times as needed to
    consume it. fixed_update() is itself a public method, useful for
    tests (or the rare game) that want to drive the simulation one
    fixed step at a time directly.

    Usage example:

        world = World(gravity=(0, 900))
        ground = world.create_static_body(200, 280, BoxShape(400, 20))
        ball = world.create_dynamic_body(200, 50, CircleShape(radius=10))

        # In your state:
        def update(self, dt: float) -> None:
            self.world.update(dt)
    """

    def __init__(
        self,
        gravity: Tuple[float, float] = (0, 900),
        pixels_per_meter: float = 30.0,
        fixed_timestep: float = 1 / 60,
    ) -> None:
        """
        :param gravity: Acceleration applied to every dynamic body, in pixels per second squared. Positive y points down the screen (gale's usual convention), so the default value, (0, 900), is a normal-feeling "downward" gravity. The default value is (0, 900).
        :param pixels_per_meter: Conversion factor between this World's public pixel units and the meters Box2D's solver expects internally (Box2D is tuned for body sizes of roughly 0.1 to 10 meters; too small or too large is numerically unstable). The default value is 30.0, meaning a 30-pixel-wide object is treated as 1 meter wide.
        :param fixed_timestep: The fixed timestep fixed_update() advances the simulation by, in seconds. The default value is 1 / 60.
        """
        self.pixels_per_meter: float = pixels_per_meter
        self.fixed_timestep: float = fixed_timestep
        self._accumulator: float = 0.0

        self._b2_world = Box2D.b2World(
            gravity=(gravity[0] / pixels_per_meter, gravity[1] / pixels_per_meter)
        )
        self._listener = _ContactListener(self)
        self._b2_world.contactListener = self._listener

        self._begin_callbacks: List[OnCollision] = []
        self._end_callbacks: List[OnCollision] = []

    def create_static_body(
        self, x: float, y: float, shape: Optional[Any] = None
    ) -> Body:
        """
        :param x: Initial x position, in pixels.
        :param y: Initial y position, in pixels.
        :param shape: A CircleShape/BoxShape/PolygonShape to attach immediately. The default value is None, so fixtures can be added later via Body.add_circle/add_box/add_polygon.
        :returns: The new Body.
        """
        return self._create_body(BodyType.STATIC, x, y, shape)

    def create_dynamic_body(
        self, x: float, y: float, shape: Optional[Any] = None
    ) -> Body:
        """
        :param x: Initial x position, in pixels.
        :param y: Initial y position, in pixels.
        :param shape: A CircleShape/BoxShape/PolygonShape to attach immediately. The default value is None, so fixtures can be added later via Body.add_circle/add_box/add_polygon.
        :returns: The new Body.
        """
        return self._create_body(BodyType.DYNAMIC, x, y, shape)

    def create_kinematic_body(
        self, x: float, y: float, shape: Optional[Any] = None
    ) -> Body:
        """
        :param x: Initial x position, in pixels.
        :param y: Initial y position, in pixels.
        :param shape: A CircleShape/BoxShape/PolygonShape to attach immediately. The default value is None, so fixtures can be added later via Body.add_circle/add_box/add_polygon.
        :returns: The new Body.
        """
        return self._create_body(BodyType.KINEMATIC, x, y, shape)

    def _create_body(
        self, body_type: int, x: float, y: float, shape: Optional[Any]
    ) -> Body:
        position = (x / self.pixels_per_meter, y / self.pixels_per_meter)

        if body_type == BodyType.STATIC:
            b2_body = self._b2_world.CreateStaticBody(position=position)
        elif body_type == BodyType.KINEMATIC:
            b2_body = self._b2_world.CreateKinematicBody(position=position)
        else:
            b2_body = self._b2_world.CreateDynamicBody(position=position)

        body = Body(b2_body, body_type, self.pixels_per_meter)

        if isinstance(shape, CircleShape):
            body.add_circle(shape)
        elif isinstance(shape, BoxShape):
            body.add_box(shape)
        elif isinstance(shape, PolygonShape):
            body.add_polygon(shape)

        return body

    def destroy_body(self, body: Body) -> None:
        """
        :param body: The Body to remove from this World.
        """
        body.destroy()

    def create_revolute_joint(
        self, body_a: Body, body_b: Body, anchor: Tuple[float, float], **options: Any
    ) -> RevoluteJoint:
        """
        :param body_a: The first body.
        :param body_b: The second body.
        :param anchor: The pivot point, in pixels, in world coordinates.
        :param options: Forwarded to Box2D's revolute joint definition (e.g. enableLimit, lowerAngle, upperAngle).
        :returns: The new RevoluteJoint.
        """
        ppm = self.pixels_per_meter
        b2_joint = self._b2_world.CreateRevoluteJoint(
            bodyA=body_a._b2_body,
            bodyB=body_b._b2_body,
            anchor=(anchor[0] / ppm, anchor[1] / ppm),
            **options,
        )
        return RevoluteJoint(b2_joint)

    def create_wheel_joint(
        self,
        body_a: Body,
        body_b: Body,
        anchor: Tuple[float, float],
        axis: Tuple[float, float] = (0, 1),
        **options: Any,
    ) -> WheelJoint:
        """
        :param body_a: The chassis (or other body the wheel is attached to).
        :param body_b: The wheel.
        :param anchor: The suspension's attachment point, in pixels, in world coordinates.
        :param axis: The suspension's movement axis, in body_a's local frame. The default value is (0, 1) (straight up/down).
        :param options: Forwarded to Box2D's wheel joint definition (e.g. frequencyHz, dampingRatio, maxMotorTorque, motorSpeed, enableMotor).
        :returns: The new WheelJoint.
        """
        ppm = self.pixels_per_meter
        b2_joint = self._b2_world.CreateWheelJoint(
            bodyA=body_a._b2_body,
            bodyB=body_b._b2_body,
            anchor=(anchor[0] / ppm, anchor[1] / ppm),
            axis=axis,
            **options,
        )
        return WheelJoint(b2_joint)

    def destroy_joint(self, joint: Joint) -> None:
        """
        :param joint: The Joint to remove from this World.
        """
        joint.destroy(self._b2_world)

    def on_collision_begin(self, callback: OnCollision) -> None:
        """
        :param callback: Called with (body_a, body_b) when two fixtures start touching. At least one of the two must not be a sensor for physical collision response; either or both may be sensors for overlap-only detection.
        """
        self._begin_callbacks.append(callback)

    def on_collision_end(self, callback: OnCollision) -> None:
        """
        :param callback: Called with (body_a, body_b) when two fixtures that were touching stop touching.
        """
        self._end_callbacks.append(callback)

    def _dispatch_contact(self, contact, callbacks: List[OnCollision]) -> None:
        body_a = contact.fixtureA.body.userData
        body_b = contact.fixtureB.body.userData

        if not isinstance(body_a, Body) or not isinstance(body_b, Body):
            return

        for callback in callbacks:
            callback(body_a, body_b)

    def update(self, dt: float) -> None:
        """
        Call once a frame with the real, variable elapsed time. Steps
        the simulation forward by calling fixed_update() as many
        times as the accumulated time covers.

        :param dt: Time elapsed, in seconds, since the last call.
        """
        self._accumulator += dt

        while self._accumulator >= self.fixed_timestep:
            self.fixed_update()
            self._accumulator -= self.fixed_timestep

    def fixed_update(self) -> None:
        """
        Advance the simulation by exactly one fixed_timestep.
        """
        self._b2_world.Step(
            self.fixed_timestep, VELOCITY_ITERATIONS, POSITION_ITERATIONS
        )
        self._b2_world.ClearForces()

    def render_debug(self, surface: pygame.Surface, color=(0, 255, 0)) -> None:
        """
        Draw every fixture's outline directly onto surface, with no
        assets — a debugging aid for building a level.

        :param surface: The surface to draw on.
        :param color: The outline color. The default value is (0, 255, 0).
        """
        ppm = self.pixels_per_meter

        for b2_body in self._b2_world.bodies:
            for fixture in b2_body.fixtures:
                shape = fixture.shape

                if isinstance(shape, Box2D.b2CircleShape):
                    center = b2_body.transform * shape.pos
                    pygame.draw.circle(
                        surface, color, (center * ppm), shape.radius * ppm, 1
                    )
                elif isinstance(shape, Box2D.b2PolygonShape):
                    points = [
                        (b2_body.transform * vertex) * ppm for vertex in shape.vertices
                    ]
                    pygame.draw.polygon(surface, color, points, 1)
