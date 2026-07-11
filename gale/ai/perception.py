"""
This file contains a perception/vision-cone system for stealth-style
games: a guard's cone of vision, split into a near zone (instant
detection) and a far zone (slower, partial detection), together with a
simple line-of-sight check against rectangular obstacles and a
Perception class that turns sightings into an alert level posted on a
Blackboard for a behavior tree to react to.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math

from enum import Enum
from typing import Any, Optional, Sequence, Union

import pygame

from .blackboard import Blackboard


def has_line_of_sight(
    origin: pygame.Vector2,
    target: pygame.Vector2,
    obstacles: Optional[Sequence[pygame.Rect]] = None,
) -> bool:
    """
    Check whether the straight segment from origin to target is not
    blocked by any of the given obstacles.

    :param origin: Point the sight line starts from.
    :param target: Point the sight line is aimed at.
    :param obstacles: Axis-aligned rectangles that block vision. The default value is None, meaning nothing blocks vision.
    :returns: Whether target is visible from origin, i.e. the segment does not cross any obstacle.
    """
    if not obstacles:
        return True

    start = (int(origin.x), int(origin.y))
    end = (int(target.x), int(target.y))

    for obstacle in obstacles:
        if obstacle.clipline(start, end):
            return False

    return True


class VisionCone:
    """
    Models a guard's field of view as a cone: an origin, a facing
    direction (orientation, in radians), and a half_angle spreading on
    both sides of that direction. Detection is split into two zones:
    range_near, within which a visible target is spotted right away,
    and range_far, up to which a visible target is only partially
    noticed (see awareness_gain), building up over time instead of
    being instant.

    The cone's pose can be given either as a plain (position,
    orientation) pair or as an object exposing .position/.orientation
    (such as a Kinematic), and it is re-read on every call so the cone
    always follows its owner as it moves and turns.

    Usage example:

        guard = Kinematic(x=100, y=100, orientation=0)
        cone = VisionCone(guard, range_near=80, range_far=250, half_angle=math.radians(30))
        if cone.can_see_point(player.position, obstacles=walls):
            ...
    """

    def __init__(
        self,
        origin: Union[Any, pygame.Vector2],
        range_near: float = 100,
        range_far: float = 300,
        half_angle: float = math.pi / 6,
        orientation: float = 0,
    ) -> None:
        """
        :param origin: A Kinematic-like object exposing .position/.orientation, or a plain pygame.Vector2 position (in which case orientation is taken from the orientation parameter).
        :param range_near: Distance within which a visible target is detected instantly.
        :param range_far: Distance up to which a visible target can be partially detected. Beyond it nothing is seen.
        :param half_angle: Half of the total field of view, in radians, measured from the facing direction.
        :param orientation: Facing direction, in radians, used only when origin is a plain position instead of a Kinematic-like object.
        """
        self.origin: Any = origin
        self.range_near: float = range_near
        self.range_far: float = range_far
        self.half_angle: float = half_angle
        self._fixed_orientation: float = orientation

    def _pose(self) -> "tuple[pygame.Vector2, float]":
        if hasattr(self.origin, "position") and hasattr(self.origin, "orientation"):
            return pygame.Vector2(self.origin.position), self.origin.orientation

        return pygame.Vector2(self.origin), self._fixed_orientation

    def can_see_point(
        self,
        point: pygame.Vector2,
        obstacles: Optional[Sequence[pygame.Rect]] = None,
    ) -> bool:
        """
        :param point: The point to test.
        :param obstacles: Axis-aligned rectangles that block vision. The default value is None, meaning nothing blocks vision.
        :returns: Whether point lies within range_far, within half_angle of the facing direction, and (if obstacles are given) has a clear line of sight.
        """
        position, orientation = self._pose()
        offset = pygame.Vector2(point) - position
        distance = offset.length()

        if distance == 0:
            return True

        if distance > self.range_far:
            return False

        facing = pygame.Vector2(math.cos(orientation), math.sin(orientation))
        cos_angle = max(-1.0, min(1.0, facing.dot(offset) / distance))
        angle = math.acos(cos_angle)

        if angle > self.half_angle:
            return False

        return has_line_of_sight(position, pygame.Vector2(point), obstacles)

    def awareness_gain(
        self,
        point: pygame.Vector2,
        dt: float,
        obstacles: Optional[Sequence[pygame.Rect]] = None,
    ) -> float:
        """
        Compute how much awareness should build up this tick for a
        target at point: full speed (dt per second, i.e. 1.0 * dt)
        within range_near, a fraction of that scaled by how far into
        the near..far band the target is when beyond range_near but
        still within range_far, and zero if point is not visible at
        all.

        :param point: Position of the potential target.
        :param dt: Time elapsed (in seconds) since the last update.
        :param obstacles: Axis-aligned rectangles that block vision. The default value is None, meaning nothing blocks vision.
        :returns: The amount of awareness (in the same 0..1 scale used by Perception) to accumulate for this tick.
        """
        if not self.can_see_point(point, obstacles):
            return 0.0

        position, _ = self._pose()
        distance = (pygame.Vector2(point) - position).length()

        if distance <= self.range_near:
            return dt

        far_band = self.range_far - self.range_near

        if far_band <= 0:
            return 0.0

        fraction = 1 - (distance - self.range_near) / far_band
        return dt * fraction


class AlertLevel(Enum):
    """
    How aware a guard currently is of a target.
    """

    UNAWARE = "unaware"
    SUSPICIOUS = "suspicious"
    ALERTED = "alerted"


class Perception:
    """
    Layers an alert-level state machine on top of one or more
    VisionCones, turning raw sightings into a 0..1 "awareness" value
    for a single tracked target (a stealth guard tracking the player
    being the primary use case) and posting the resulting AlertLevel,
    together with the last known target position, onto a Blackboard so
    a behavior tree's Condition/Action nodes can react to it without
    knowing anything about vision cones.

    Blackboard keys written by update():

    - "alert_level": the current AlertLevel.
    - "last_known_target_position": the target's position the last
      time it was seen (kept while SUSPICIOUS or ALERTED, untouched
      once the guard goes back to UNAWARE).
    - "awareness": the raw 0..1 awareness float.

    Usage example:

        blackboard = Blackboard()
        cone = VisionCone(guard, range_near=80, range_far=250, half_angle=math.radians(30))
        perception = Perception([cone], blackboard)

        # In the game loop:
        perception.update(dt, player.position, obstacles=walls)
        if blackboard.get("alert_level") == AlertLevel.ALERTED:
            ...
    """

    def __init__(
        self,
        vision_cones: Sequence[VisionCone],
        blackboard: Optional[Blackboard] = None,
        decay_rate: float = 0.2,
        suspicious_threshold: float = 0.3,
        alerted_threshold: float = 1.0,
    ) -> None:
        """
        :param vision_cones: The vision cones used to look for the target. A target seen by any of them contributes awareness.
        :param blackboard: The blackboard to post the alert level and last known target position to. The default value is None, so a fresh, empty Blackboard is created.
        :param decay_rate: Awareness lost per second while the target is not visible by any cone.
        :param suspicious_threshold: Awareness value at or above which the alert level becomes SUSPICIOUS.
        :param alerted_threshold: Awareness value at or above which the alert level becomes ALERTED.
        """
        self.vision_cones: Sequence[VisionCone] = vision_cones
        self.blackboard: Blackboard = (
            blackboard if blackboard is not None else Blackboard()
        )
        self.decay_rate: float = decay_rate
        self.suspicious_threshold: float = suspicious_threshold
        self.alerted_threshold: float = alerted_threshold
        self.awareness: float = 0.0

    def _alert_level(self) -> AlertLevel:
        if self.awareness >= self.alerted_threshold:
            return AlertLevel.ALERTED

        if self.awareness >= self.suspicious_threshold:
            return AlertLevel.SUSPICIOUS

        return AlertLevel.UNAWARE

    def update(
        self,
        dt: float,
        target_point: pygame.Vector2,
        obstacles: Optional[Sequence[pygame.Rect]] = None,
    ) -> AlertLevel:
        """
        Look for target_point through every vision cone, accumulate or
        decay awareness accordingly, and post the resulting state onto
        the blackboard.

        :param dt: Time elapsed (in seconds) since the last update.
        :param target_point: Current position of the tracked target.
        :param obstacles: Axis-aligned rectangles that block vision. The default value is None, meaning nothing blocks vision.
        :returns: The alert level after this update.
        """
        gain = max(
            (
                cone.awareness_gain(target_point, dt, obstacles)
                for cone in self.vision_cones
            ),
            default=0.0,
        )

        if gain > 0:
            self.awareness = min(1.0, self.awareness + gain)
        else:
            self.awareness = max(0.0, self.awareness - self.decay_rate * dt)

        level = self._alert_level()
        self.blackboard.set("awareness", self.awareness)
        self.blackboard.set("alert_level", level)

        if level != AlertLevel.UNAWARE:
            self.blackboard.set(
                "last_known_target_position", pygame.Vector2(target_point)
            )

        return level
