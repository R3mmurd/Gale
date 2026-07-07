"""
This file contains the implementation of the classes CircleShape,
BoxShape, and PolygonShape: plain descriptors for a Body's fixtures.
None of them ever touch Box2D directly — Body translates them into
Box2D fixtures, in pixel units converted to meters internally.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import List, Tuple


class CircleShape:
    """
    A circular fixture.

    Usage example:

        body.add_circle(CircleShape(radius=8, friction=0.4, restitution=0.6))
    """

    def __init__(
        self,
        radius: float,
        density: float = 1.0,
        friction: float = 0.3,
        restitution: float = 0.0,
        is_sensor: bool = False,
        offset: Tuple[float, float] = (0, 0),
    ) -> None:
        """
        :param radius: The circle's radius, in pixels.
        :param density: Mass per unit area, used to compute the body's total mass. The default value is 1.0.
        :param friction: How much this fixture resists sliding against another, from 0 (frictionless) to 1 (high friction) and beyond. The default value is 0.3.
        :param restitution: Bounciness, from 0 (no bounce) to 1 (perfectly elastic) and beyond. The default value is 0.0.
        :param is_sensor: Whether this fixture detects overlaps (for on_collision_begin/on_collision_end and touching_bodies) without ever producing a physical collision response. The default value is False.
        :param offset: This fixture's center, relative to its body's position, in pixels. The default value is (0, 0).
        """
        self.radius: float = radius
        self.density: float = density
        self.friction: float = friction
        self.restitution: float = restitution
        self.is_sensor: bool = is_sensor
        self.offset: Tuple[float, float] = offset


class BoxShape:
    """
    A rectangular fixture.

    Usage example:

        body.add_box(BoxShape(width=32, height=32))
    """

    def __init__(
        self,
        width: float,
        height: float,
        density: float = 1.0,
        friction: float = 0.3,
        restitution: float = 0.0,
        is_sensor: bool = False,
        offset: Tuple[float, float] = (0, 0),
    ) -> None:
        """
        :param width: The box's width, in pixels.
        :param height: The box's height, in pixels.
        :param density: Mass per unit area, used to compute the body's total mass. The default value is 1.0.
        :param friction: How much this fixture resists sliding against another, from 0 (frictionless) to 1 (high friction) and beyond. The default value is 0.3.
        :param restitution: Bounciness, from 0 (no bounce) to 1 (perfectly elastic) and beyond. The default value is 0.0.
        :param is_sensor: Whether this fixture detects overlaps (for on_collision_begin/on_collision_end and touching_bodies) without ever producing a physical collision response. The default value is False.
        :param offset: This fixture's center, relative to its body's position, in pixels. The default value is (0, 0).
        """
        self.width: float = width
        self.height: float = height
        self.density: float = density
        self.friction: float = friction
        self.restitution: float = restitution
        self.is_sensor: bool = is_sensor
        self.offset: Tuple[float, float] = offset


class PolygonShape:
    """
    An arbitrary convex polygon fixture (at most 8 vertices, Box2D's
    own limit).

    Usage example:

        body.add_polygon(PolygonShape([(0, -10), (10, 10), (-10, 10)]))
    """

    def __init__(
        self,
        points: List[Tuple[float, float]],
        density: float = 1.0,
        friction: float = 0.3,
        restitution: float = 0.0,
        is_sensor: bool = False,
    ) -> None:
        """
        :param points: The polygon's vertices, in pixels, relative to its body's position, in either winding order (Box2D normalizes it). Must describe a convex polygon.
        :param density: Mass per unit area, used to compute the body's total mass. The default value is 1.0.
        :param friction: How much this fixture resists sliding against another, from 0 (frictionless) to 1 (high friction) and beyond. The default value is 0.3.
        :param restitution: Bounciness, from 0 (no bounce) to 1 (perfectly elastic) and beyond. The default value is 0.0.
        :param is_sensor: Whether this fixture detects overlaps (for on_collision_begin/on_collision_end and touching_bodies) without ever producing a physical collision response. The default value is False.
        """
        self.points: List[Tuple[float, float]] = list(points)
        self.density: float = density
        self.friction: float = friction
        self.restitution: float = restitution
        self.is_sensor: bool = is_sensor
