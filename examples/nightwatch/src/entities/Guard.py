from typing import List, Optional, Tuple

import pygame

from gale.ai.agent import Agent
from gale.ai.behavior_tree import (
    Action,
    BehaviorTree,
    Condition,
    Selector,
    Sequence,
    Status,
)
from gale.ai.blackboard import Blackboard
from gale.ai.graph import NavGraph
from gale.ai.steering import Pursue, Seek

import settings
from src import level
from src.path_follower import PathFollower

Point = Tuple[float, float]


class Guard(Agent):
    """
    Patrols back and forth between two points. When it sees the player
    (within sight radius and with a clear line of sight), it chases
    them directly and posts the sighting on the shared squad
    Blackboard, so every other Guard sharing it learns where to
    investigate even without seeing the player themselves. If it loses
    the player, it keeps investigating the last known position (path
    found with A* over the level's NavGraph, since it has to walk
    around walls) for a while before giving up and returning to patrol.

    The whole decision is re-evaluated fresh every tick: every Action
    below returns Status.SUCCESS (never RUNNING), which is what makes
    the root Selector reset itself and re-check from the top (starting
    with "do I currently see the player?") on every single tick,
    instead of latching onto whichever branch ran last.
    """

    def __init__(
        self,
        x: float,
        y: float,
        patrol_points: Tuple[Point, Point],
        player: Agent,
        nav_graph: NavGraph,
        blackboard: Blackboard,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            max_speed=settings.GUARD_CHASE_SPEED,
            max_acceleration=settings.GUARD_CHASE_SPEED * 6,
            blackboard=blackboard,
        )
        self.radius = settings.GUARD_RADIUS
        self.player = player
        self.nav_graph = nav_graph

        self._patrol_points: List[Point] = list(patrol_points)
        self.patrol_follower = PathFollower()
        self.patrol_follower.set_path(self._patrol_points)
        self.patrol_seek = Seek(self.kinematic, self.patrol_follower.target)

        self.investigate_follower = PathFollower()
        self.investigate_seek = Seek(self.kinematic, self.investigate_follower.target)
        self._known_alert_position: Optional[Point] = None
        self._investigate_timer: float = 0.0

        self.chase_pursue = Pursue(self.kinematic, player.kinematic)

        self.set_brain(
            BehaviorTree(
                Selector(
                    [
                        Sequence(
                            [Condition(self._sees_player), Action(self._spot_player)]
                        ),
                        Sequence(
                            [
                                Condition(self._is_investigating),
                                Action(self._investigate_step),
                            ]
                        ),
                        Action(self._patrol_step),
                    ]
                )
            )
        )

    def _sees_player(self, agent: Agent) -> bool:
        distance = (self.player.position - self.position).length()
        return distance <= settings.GUARD_SIGHT_RADIUS and level.has_line_of_sight(
            tuple(self.position), tuple(self.player.position)
        )

    def _spot_player(self, agent: Agent, dt: float) -> Status:
        alert_position = (self.player.position.x, self.player.position.y)
        self._known_alert_position = alert_position
        self._investigate_timer = settings.GUARD_LOSE_INTEREST_TIME
        self.blackboard.set("alert_position", alert_position)
        self.blackboard.set("is_alerted", True)
        self.set_steering_behavior(self.chase_pursue)
        return Status.SUCCESS

    def _is_investigating(self, agent: Agent) -> bool:
        alert_position = self.blackboard.get("alert_position")
        return self._investigate_timer > 0 or (
            alert_position is not None and alert_position != self._known_alert_position
        )

    def _investigate_step(self, agent: Agent, dt: float) -> Status:
        alert_position = self.blackboard.get("alert_position")

        if alert_position != self._known_alert_position:
            self._known_alert_position = alert_position
            self._investigate_timer = settings.GUARD_LOSE_INTEREST_TIME
            path = level.find_path(self.nav_graph, tuple(self.position), alert_position)
            self.investigate_follower.set_path(path if path else [alert_position])

        self._investigate_timer -= dt

        if self._investigate_timer <= 0:
            return Status.FAILURE

        self.investigate_follower.update(self.position)
        self.set_steering_behavior(self.investigate_seek)
        return Status.SUCCESS

    def _patrol_step(self, agent: Agent, dt: float) -> Status:
        self.patrol_follower.update(self.position)

        if self.patrol_follower.finished:
            self._patrol_points.reverse()
            self.patrol_follower.set_path(self._patrol_points)

        self.set_steering_behavior(self.patrol_seek)
        return Status.SUCCESS

    def update(self, dt: float) -> None:
        super().update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        is_alert = self.steering_behavior is not self.patrol_seek
        color = settings.COLOR_GUARD_ALERT if is_alert else settings.COLOR_GUARD_PATROL
        center = (int(self.position.x), int(self.position.y))
        pygame.draw.circle(surface, color, center, self.radius)

        if self.velocity.length_squared() > 1:
            tip = self.position + self.velocity.normalize() * (self.radius + 6)
            pygame.draw.line(surface, color, center, tip, 2)

        if is_alert:
            pygame.draw.circle(
                surface, color, (center[0], center[1] - self.radius - 8), 3
            )
