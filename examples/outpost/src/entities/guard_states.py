"""
The Guard's hierarchical state machine (HFSM), built with
gale.state.HierarchicalState/StateMachine: a top-level state machine
with "patrol" / "search" / "alert" states, where "patrol" is itself a
HierarchicalState made of two finer-grained substates, "walking" (follow
the patrol path) and "looking_around" (pause and slowly scan). The
top-level transitions are driven by the guard's gale.ai.perception
AlertLevel (see Guard.update): UNAWARE -> patrol, SUSPICIOUS -> search,
ALERTED -> alert.
"""

import math
from typing import Optional, Tuple

import pygame

from gale.state import BaseState, HierarchicalState, StateMachine

import settings
from src import level
from src.path_follower import PathFollower

Point = Tuple[float, float]


def _face_and_step(guard, target: pygame.Vector2, speed: float, dt: float) -> None:
    direction = target - guard.kinematic.position
    distance_squared = direction.length_squared()

    if distance_squared == 0:
        return

    guard.kinematic.orientation = math.atan2(direction.y, direction.x)
    step = direction.normalize() * speed * dt

    if step.length_squared() > distance_squared:
        step = direction

    guard.kinematic.position += step


class Walking(BaseState):
    def __init__(self, state_machine: StateMachine, guard) -> None:
        super().__init__(state_machine)
        self.guard = guard

    def update(self, dt: float) -> None:
        guard = self.guard
        follower = guard.patrol_follower
        follower.update(guard.position)

        if follower.finished:
            guard.patrol_points.reverse()
            follower.set_path(guard.patrol_points)
            self.state_machine.change("looking_around")
            return

        _face_and_step(guard, follower.target.position, settings.GUARD_PATROL_SPEED, dt)


class LookingAround(BaseState):
    def __init__(self, state_machine: StateMachine, guard) -> None:
        super().__init__(state_machine)
        self.guard = guard

    def enter(self) -> None:
        self.timer = settings.LOOK_AROUND_DURATION
        self.base_orientation = self.guard.kinematic.orientation
        self.spin = 1

    def update(self, dt: float) -> None:
        self.timer -= dt
        self.guard.kinematic.orientation += (
            settings.LOOK_AROUND_ROTATION_SPEED * dt * self.spin
        )

        if abs(self.guard.kinematic.orientation - self.base_orientation) > math.pi / 3:
            self.spin *= -1

        if self.timer <= 0:
            self.state_machine.change("walking")


class Patrol(HierarchicalState):
    """
    The top-level "patrol" state: a HierarchicalState made of the
    "walking"/"looking_around" substates above. See
    gale.state.HierarchicalState and docs/examples/state.rst for the
    general pattern this follows.
    """

    def __init__(self, state_machine: StateMachine, guard) -> None:
        self.guard = guard
        super().__init__(
            state_machine,
            substates={
                "walking": lambda sm: Walking(sm, guard),
                "looking_around": lambda sm: LookingAround(sm, guard),
            },
            initial_substate="walking",
        )


class Search(BaseState):
    """
    The guard grew suspicious: path (via A* over the level's NavGraph)
    towards the target's last known position, re-planning whenever that
    position changes.
    """

    def __init__(self, state_machine: StateMachine, guard) -> None:
        super().__init__(state_machine)
        self.guard = guard
        self.follower = PathFollower(arrival_radius=10)
        self._known_target: Optional[Point] = None

    def enter(self) -> None:
        self._known_target = None

    def update(self, dt: float) -> None:
        guard = self.guard
        target = guard.blackboard.get("last_known_target_position")

        if target is None:
            return

        target_point: Point = (target.x, target.y)

        if target_point != self._known_target:
            self._known_target = target_point
            path = level.find_path(guard.nav_graph, tuple(guard.position), target_point)
            self.follower.set_path(path if path else [target_point])

        self.follower.update(guard.position)
        _face_and_step(
            guard, self.follower.target.position, settings.GUARD_SEARCH_SPEED, dt
        )


class Alert(BaseState):
    """
    The guard has spotted the target: charge straight at its current
    (live) position -- no need to path around walls carefully, the
    target is right there.
    """

    def __init__(self, state_machine: StateMachine, guard) -> None:
        super().__init__(state_machine)
        self.guard = guard

    def update(self, dt: float) -> None:
        guard = self.guard
        _face_and_step(
            guard,
            guard.player.kinematic.position,
            settings.GUARD_SEARCH_SPEED * 1.15,
            dt,
        )
