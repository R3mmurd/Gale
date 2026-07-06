"""
gale.physics: 2D physics for gale games, backed by Box2D (never
exposed in the public API — everything here works in plain pixel
units and gale's own vocabulary) plus a lightweight scene graph for
organizing physics entities.

See docs/examples/physics.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .body import Body
from .body_type import BodyType
from .joint import Joint, RevoluteJoint, WheelJoint
from .node import Node
from .shapes import BoxShape, CircleShape, PolygonShape
from .world import World

__all__ = [
    "Body",
    "BodyType",
    "BoxShape",
    "CircleShape",
    "Joint",
    "Node",
    "PolygonShape",
    "RevoluteJoint",
    "WheelJoint",
    "World",
]
