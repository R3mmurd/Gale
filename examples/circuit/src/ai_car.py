"""
The AI racer: a gale.ai.steering.Kinematic driven around the track by
Arrive steering towards successive waypoints of a path computed with
gale.ai.search.a_star over the track's gale.ai.graph.NavGraph (see
src/track.py's build_nav_graph/WAYPOINTS). Once the path is exhausted
(a full lap), a_star is asked for a fresh lap around the same one-way
loop, so the AI keeps circling for as long as the race runs.

Simulated only on the host (it is authoritative for every entity in
this example, human or not); its resulting position/heading/speed are
mirrored into the same plain state dict shape as the human cars (see
src/car.py) so it can be broadcast and, on the clients, buffered and
smoothed through gale.net.SnapshotInterpolator exactly like a remote
player's car.
"""

import math

from gale.ai.search import a_star
from gale.ai.steering import Arrive, Kinematic

import settings
from src import track
from src.path_follower import PathFollower


def _distance(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


class AICar:
    def __init__(self, x: float, y: float, heading: float) -> None:
        self.kinematic = Kinematic(
            x,
            y,
            orientation=heading,
            max_speed=settings.AI_MAX_SPEED,
            max_acceleration=settings.AI_MAX_ACCELERATION,
        )
        self.nav_graph = track.build_nav_graph()
        self.follower = PathFollower(arrival_radius=settings.AI_ARRIVAL_RADIUS)
        self._queue_next_lap()
        self.laps = 0
        self._previous_position = (x, y)

    def _queue_next_lap(self) -> None:
        start_index = track.nearest_waypoint_index(
            self.kinematic.position.x, self.kinematic.position.y
        )
        waypoints = track.WAYPOINTS
        count = len(waypoints)
        start = waypoints[start_index]
        goal = waypoints[(start_index - 1) % count]
        path = a_star(start, goal, self.nav_graph, heuristic=_distance)
        self.follower.set_path(path if path else waypoints)

    def update(self, dt: float) -> None:
        previous_position = (self.kinematic.position.x, self.kinematic.position.y)

        self.follower.update(self.kinematic.position)

        if self.follower.finished:
            self._queue_next_lap()

        steering = Arrive(self.kinematic, self.follower.target).get_steering(dt)
        self.kinematic.update(steering, dt)

        if self.kinematic.velocity.length_squared() > 1.0:
            self.kinematic.orientation = math.atan2(
                self.kinematic.velocity.y, self.kinematic.velocity.x
            )

        current_position = (self.kinematic.position.x, self.kinematic.position.y)

        if track.crosses_finish_line(previous_position, current_position):
            self.laps += 1

        self._previous_position = current_position

    def to_state(self) -> dict:
        """
        :returns: The AI car mirrored into the same {"x", "y", "heading", "speed"} shape src/car.py uses, so PlayState can broadcast/render it identically to the human cars.
        """
        return {
            "x": self.kinematic.position.x,
            "y": self.kinematic.position.y,
            "heading": self.kinematic.orientation,
            "speed": self.kinematic.velocity.length(),
        }
