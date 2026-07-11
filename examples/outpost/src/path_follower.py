"""
A small helper that advances through a list of waypoints, exposing a
Kinematic target whose position marks the current waypoint to move
towards. Identical in spirit to examples/nightwatch/src/path_follower.py.
"""

from typing import List, Sequence, Tuple

import pygame

from gale.ai.steering import Kinematic

Point = Tuple[float, float]


class PathFollower:
    def __init__(self, arrival_radius: float = 12) -> None:
        """
        :param arrival_radius: Distance to a waypoint below which it counts as reached and the follower advances to the next one.
        """
        self.waypoints: List[Point] = []
        self.index: int = 0
        self.arrival_radius: float = arrival_radius
        self.target: Kinematic = Kinematic()

    def set_path(self, waypoints: Sequence[Point]) -> None:
        """
        :param waypoints: The new sequence of points to follow, in order.
        """
        self.waypoints = list(waypoints)
        self.index = 0

        if self.waypoints:
            self.target.position = pygame.Vector2(self.waypoints[0])

    @property
    def finished(self) -> bool:
        """
        :returns: Whether every waypoint has been reached.
        """
        return self.index >= len(self.waypoints)

    def update(self, position: pygame.Vector2) -> None:
        """
        Advance to the next waypoint if position is already close enough
        to the current one.

        :param position: The current position of whoever is following this path.
        """
        if self.finished:
            return

        if (self.target.position - position).length() <= self.arrival_radius:
            self.index += 1

            if not self.finished:
                self.target.position = pygame.Vector2(self.waypoints[self.index])
