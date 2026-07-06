from typing import List

import pygame

from gale.ai.agent import Agent
from gale.ai.decision_tree import ActionNode, DecisionNode, DecisionTree
from gale.ai.steering import Flee, Kinematic, Wander

import settings
from src import level


class Civilian(Agent):
    """
    A neutral bystander driven by a DecisionTree (instead of a
    BehaviorTree, like Guard) as a second, simpler way of picking a
    steering behavior: flee from the nearest guard if one is close
    enough, wander otherwise. A DecisionTree has no persistent RUNNING
    state, so this test is naturally re-evaluated fresh every tick.
    """

    def __init__(self, x: float, y: float, guards: List[Agent]) -> None:
        super().__init__(
            x=x,
            y=y,
            max_speed=settings.CIVILIAN_FLEE_SPEED,
            max_acceleration=settings.CIVILIAN_FLEE_SPEED * 6,
        )
        self.radius = settings.CIVILIAN_RADIUS
        self.guards = guards

        self.wander = Wander(
            self.kinematic,
            offset=40,
            radius=25,
            max_acceleration=settings.CIVILIAN_SPEED * 4,
        )
        self.flee = Flee(self.kinematic, Kinematic())

        def near_a_guard(agent: Agent) -> bool:
            return any(
                (guard.position - self.position).length()
                < settings.CIVILIAN_FLEE_RADIUS
                for guard in self.guards
            )

        def flee_nearest_guard(agent: Agent) -> None:
            nearest = min(
                self.guards, key=lambda guard: (guard.position - self.position).length()
            )
            self.flee.target = nearest.kinematic
            self.set_steering_behavior(self.flee)

        def wander_around(agent: Agent) -> None:
            self.set_steering_behavior(self.wander)

        self.set_brain(
            DecisionTree(
                DecisionNode(
                    test=near_a_guard,
                    true_branch=ActionNode(flee_nearest_guard),
                    false_branch=ActionNode(wander_around),
                )
            )
        )

    def update(self, dt: float) -> None:
        super().update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            settings.COLOR_CIVILIAN,
            (int(self.position.x), int(self.position.y)),
            self.radius,
        )
