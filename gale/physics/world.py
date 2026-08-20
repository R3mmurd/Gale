"""
This file contains the implementation of the class World: a physics
simulation, in pixel units, wrapping a pymunk space without ever
exposing pymunk itself — creates every Body/Joint, steps the
simulation, and dispatches collision callbacks.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame
import pymunk

from .body import Body
from .body_type import BodyType
from .joint import Joint, RevoluteJoint, WheelJoint
from .shapes import BoxShape, CircleShape, PolygonShape

OnCollision = Callable[[Body, Body], None]

# Box2D-era defaults (frequency/damping of a wheel joint's suspension)
# kept as this World's own defaults so existing games that don't pass
# frequencyHz/dampingRatio explicitly still get a reasonable suspension.
DEFAULT_SUSPENSION_FREQUENCY: float = 2.0
DEFAULT_SUSPENSION_DAMPING: float = 0.7

# pymunk's GrooveJoint (used to build a wheel joint's suspension slide)
# needs a finite groove, unlike Box2D's wheel joint, whose translation
# is unbounded unless enableLimit/lowerTranslation/upperTranslation say
# otherwise. This is the unbounded case's stand-in: far enough, in
# pixels, that no realistic suspension ever reaches it.
_WHEEL_JOINT_DEFAULT_TRAVEL: float = 2000.0

_BODY_TYPE_TO_PYMUNK = {
    BodyType.STATIC: pymunk.Body.STATIC,
    BodyType.DYNAMIC: pymunk.Body.DYNAMIC,
    BodyType.KINEMATIC: pymunk.Body.KINEMATIC,
}


def _option(
    options: Dict[str, Any], camel_key: str, snake_key: str, default: Any
) -> Any:
    """
    Every joint option here accepts both Box2D's own camelCase name
    (matching every gale release before pymunk) and gale's usual
    snake_case, so **options straight from an old project keeps working
    verbatim.
    """
    return options.get(camel_key, options.get(snake_key, default))


class World:
    """
    A physics simulation, in pixel units. Wraps a pymunk space (never
    exposed) and every Body/Joint created in it.

    Follows the same update/fixed_update split Unity uses to decouple
    the game loop's real, variable dt from the fixed timestep the
    solver needs for stable results: call update(dt) once a frame,
    same as everything else in gale; it accumulates dt and calls
    fixed_update() (a real simulation step) as many times as needed to
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
        :param pixels_per_meter: Conversion factor between this World's public pixel units and the meters the solver expects internally (tuned for body sizes of roughly 0.1 to 10 meters; too small or too large is numerically unstable). The default value is 30.0, meaning a 30-pixel-wide object is treated as 1 meter wide.
        :param fixed_timestep: The fixed timestep fixed_update() advances the simulation by, in seconds. The default value is 1 / 60.
        """
        self.pixels_per_meter: float = pixels_per_meter
        self.fixed_timestep: float = fixed_timestep
        self._accumulator: float = 0.0

        self._space = pymunk.Space()
        self._space.gravity = (
            gravity[0] / pixels_per_meter,
            gravity[1] / pixels_per_meter,
        )

        self._begin_callbacks: List[OnCollision] = []
        self._end_callbacks: List[OnCollision] = []
        # Body.touching_bodies is driven by this, not pymunk's
        # each_arbiter: Chipmunk never keeps a persistent arbiter for a
        # sensor shape (only these begin/separate events fire for one),
        # so each_arbiter alone would make touching_bodies blind to
        # anything sensor-based — e.g. a wind zone's is_sensor=True
        # BoxShape never showing the bodies inside it. Reference-counted
        # per-pair so two bodies with multiple overlapping fixtures
        # don't drop out on the first fixture pair to separate.
        self._touching: Dict[Body, Dict[Body, int]] = {}
        self._space.on_collision(
            begin=self._on_begin_contact, separate=self._on_end_contact
        )

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
        pm_body = pymunk.Body(body_type=_BODY_TYPE_TO_PYMUNK[body_type])
        pm_body.position = (x / self.pixels_per_meter, y / self.pixels_per_meter)
        self._space.add(pm_body)

        body = Body(pm_body, self, body_type, self.pixels_per_meter)

        if isinstance(shape, CircleShape):
            body.add_circle(shape)
        elif isinstance(shape, BoxShape):
            body.add_box(shape)
        elif isinstance(shape, PolygonShape):
            body.add_polygon(shape)

        return body

    def _apply_motor_options(self, joint: Any, options: Dict[str, Any]) -> None:
        # max_motor_torque before enable_motor: enable_motor's setter
        # reads the already-stored torque cap to arm the motor.
        joint.max_motor_torque = _option(
            options, "maxMotorTorque", "max_motor_torque", 0.0
        )
        joint.motor_speed = _option(options, "motorSpeed", "motor_speed", 0.0)
        joint.enable_motor = _option(options, "enableMotor", "enable_motor", False)

    def destroy_body(self, body: Body) -> None:
        """
        :param body: The Body to remove from this World.
        """
        body.destroy()

    def _forget_touching(self, body: Body) -> None:
        for other in self._touching.pop(body, {}):
            self._touching.get(other, {}).pop(body, None)

    def create_revolute_joint(
        self, body_a: Body, body_b: Body, anchor: Tuple[float, float], **options: Any
    ) -> RevoluteJoint:
        """
        :param body_a: The first body.
        :param body_b: The second body.
        :param anchor: The pivot point, in pixels, in world coordinates.
        :param options: enableMotor/motorSpeed/maxMotorTorque and enableLimit/lowerAngle/upperAngle (or their snake_case equivalents) — same meaning as Box2D's revolute joint, applied at creation. Every one of them is also a settable property on the returned RevoluteJoint for changing later.
        :returns: The new RevoluteJoint.
        """
        ppm = self.pixels_per_meter
        world_anchor = (anchor[0] / ppm, anchor[1] / ppm)

        pivot = pymunk.PivotJoint(body_a._pm_body, body_b._pm_body, world_anchor)
        motor = pymunk.SimpleMotor(body_a._pm_body, body_b._pm_body, 0.0)
        motor.max_force = 0.0
        limit = pymunk.RotaryLimitJoint(body_a._pm_body, body_b._pm_body, 0.0, 0.0)
        limit.max_force = 0.0

        # Match Box2D's joint default (collideConnected=False): two
        # bodies pinned together by a joint shouldn't also push each
        # other apart through fixture collision — pymunk's constraints
        # collide their bodies by default, Box2D's don't.
        pivot.collide_bodies = False
        motor.collide_bodies = False
        limit.collide_bodies = False

        self._space.add(pivot, motor, limit)

        joint = RevoluteJoint(pivot, motor, limit, body_a._pm_body, body_b._pm_body)
        self._apply_motor_options(joint, options)

        joint.lower_angle = _option(options, "lowerAngle", "lower_angle", 0.0)
        joint.upper_angle = _option(options, "upperAngle", "upper_angle", 0.0)
        joint.enable_limit = _option(options, "enableLimit", "enable_limit", False)

        return joint

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
        :param options: frequencyHz/dampingRatio (suspension spring tuning), enableMotor/motorSpeed/maxMotorTorque, and enableLimit/lowerTranslation/upperTranslation (suspension travel bounds, in pixels along axis; unbounded unless enableLimit is set) — same meaning as Box2D's wheel joint, applied at creation. The motor options are also settable properties on the returned WheelJoint for changing later; the translation limit is creation-only.
        :returns: The new WheelJoint.
        """
        ppm = self.pixels_per_meter
        frequency = _option(
            options, "frequencyHz", "frequency_hz", DEFAULT_SUSPENSION_FREQUENCY
        )
        damping_ratio = _option(
            options, "dampingRatio", "damping_ratio", DEFAULT_SUSPENSION_DAMPING
        )
        default_travel = _WHEEL_JOINT_DEFAULT_TRAVEL / ppm
        enable_limit = _option(options, "enableLimit", "enable_limit", False)
        lower_translation = (
            _option(options, "lowerTranslation", "lower_translation", -60.0) / ppm
            if enable_limit
            else -default_travel
        )
        upper_translation = (
            _option(options, "upperTranslation", "upper_translation", 60.0) / ppm
            if enable_limit
            else default_travel
        )

        pm_body_a = body_a._pm_body
        pm_body_b = body_b._pm_body

        world_anchor = pymunk.Vec2d(anchor[0] / ppm, anchor[1] / ppm)
        local_anchor_a = pm_body_a.world_to_local(world_anchor)
        local_anchor_b = pm_body_b.world_to_local(world_anchor)

        axis_local = pymunk.Vec2d(*axis)
        if axis_local.length > 0:
            axis_local = axis_local.normalized()

        groove_a = local_anchor_a + axis_local * lower_translation
        groove_b = local_anchor_a + axis_local * upper_translation

        groove = pymunk.GrooveJoint(
            pm_body_a, pm_body_b, groove_a, groove_b, local_anchor_b
        )

        world_a = pm_body_a.local_to_world(local_anchor_a)
        world_b = pm_body_b.local_to_world(local_anchor_b)
        rest_length = (world_a - world_b).length

        spring = pymunk.DampedSpring(
            pm_body_a,
            pm_body_b,
            local_anchor_a,
            local_anchor_b,
            rest_length,
            1.0,
            1.0,
        )

        motor = pymunk.SimpleMotor(pm_body_a, pm_body_b, 0.0)
        motor.max_force = 0.0

        # See the same collide_bodies note in create_revolute_joint.
        groove.collide_bodies = False
        spring.collide_bodies = False
        motor.collide_bodies = False

        self._space.add(groove, spring, motor)

        joint = WheelJoint(
            groove, spring, motor, pm_body_b.mass, frequency, damping_ratio
        )
        self._apply_motor_options(joint, options)

        return joint

    def destroy_joint(self, joint: Joint) -> None:
        """
        :param joint: The Joint to remove from this World.
        """
        joint.destroy(self._space)

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

    def _on_begin_contact(self, arbiter: Any, space: Any, data: Any) -> bool:
        bodies = self._arbiter_bodies(arbiter)

        if bodies is not None:
            self._track_touching(*bodies, 1)
            self._dispatch_contact(bodies, self._begin_callbacks)

        return True

    def _on_end_contact(self, arbiter: Any, space: Any, data: Any) -> None:
        bodies = self._arbiter_bodies(arbiter)

        if bodies is not None:
            self._track_touching(*bodies, -1)
            self._dispatch_contact(bodies, self._end_callbacks)

    def _arbiter_bodies(self, arbiter: Any) -> Optional[Tuple[Body, Body]]:
        shape_a, shape_b = arbiter.shapes
        body_a = getattr(shape_a.body, "gale_body", None)
        body_b = getattr(shape_b.body, "gale_body", None)

        if not isinstance(body_a, Body) or not isinstance(body_b, Body):
            return None

        return body_a, body_b

    def _track_touching(self, body_a: Body, body_b: Body, delta: int) -> None:
        count = self._touching.setdefault(body_a, {}).get(body_b, 0) + delta

        if count <= 0:
            self._touching[body_a].pop(body_b, None)
            self._touching.get(body_b, {}).pop(body_a, None)
        else:
            self._touching[body_a][body_b] = count
            self._touching.setdefault(body_b, {})[body_a] = count

    def _dispatch_contact(
        self, bodies: Tuple[Body, Body], callbacks: List[OnCollision]
    ) -> None:
        for callback in callbacks:
            callback(*bodies)

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
        self._space.step(self.fixed_timestep)

    def render_debug(self, surface: pygame.Surface, color=(0, 255, 0)) -> None:
        """
        Draw every fixture's outline directly onto surface, with no
        assets — a debugging aid for building a level.

        :param surface: The surface to draw on.
        :param color: The outline color. The default value is (0, 255, 0).
        """
        ppm = self.pixels_per_meter

        for pm_shape in self._space.shapes:
            if isinstance(pm_shape, pymunk.Circle):
                center = pm_shape.body.local_to_world(pm_shape.offset)
                pygame.draw.circle(
                    surface, color, (center * ppm), pm_shape.radius * ppm, 1
                )
            elif isinstance(pm_shape, pymunk.Poly):
                points = [
                    pm_shape.body.local_to_world(vertex) * ppm
                    for vertex in pm_shape.get_vertices()
                ]
                pygame.draw.polygon(surface, color, points, 1)
