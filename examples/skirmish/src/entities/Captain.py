import math
from typing import Dict, List, Optional, Tuple

import pygame

from gale.ai.agent import Agent
from gale.ai.blackboard import Blackboard
from gale.ai.goap import GoapAction, plan
from gale.ai.graph import NavGraph
from gale.ai.learning import NGramPredictor
from gale.ai.rules import Rule, RuleEngine
from gale.ai.steering import PathFollow
from gale.ai.tactical import InfluenceMap, best_position
from gale.ai.targeting import iterative_targeting_angle

import settings
from src import level

Point = Tuple[float, float]

# The 8 compass directions the leader's movement is quantized into for
# the NGramPredictor -- fine enough to be useful, coarse enough that
# the same direction repeats long enough to actually learn a pattern.
_DIRECTIONS: List[Point] = [
    (math.cos(i * math.pi / 4), math.sin(i * math.pi / 4)) for i in range(8)
]

_GOAP_ACTIONS = [
    GoapAction("call_alarm", preconditions={}, effects={"alarm_called": True}, cost=1),
    GoapAction(
        "take_position",
        preconditions={"alarm_called": True},
        effects={"in_position": True},
        cost=2,
    ),
    GoapAction(
        "throw_grenade",
        preconditions={"in_position": True},
        effects={"grenade_thrown": True},
        cost=1,
    ),
]


def _quantize_direction(velocity: pygame.Vector2) -> Optional[int]:
    if velocity.length_squared() < 1:
        return None

    heading = velocity.normalize()
    return max(
        range(8),
        key=lambda i: heading.dot(pygame.Vector2(_DIRECTIONS[i])),
    )


class Captain(Agent):
    """
    The squad's opposing number: a RuleEngine decides the guard force's
    overall stance from a shared working memory (how many guards are
    currently alert, how close the squad is to extraction), and, once
    engaged, a GOAP plan (call the alarm, take up a tactical position,
    lob a grenade) is executed one action at a time. An NGramPredictor
    learns the squad leader's recent movement pattern to bias where
    the grenade leads them.
    """

    def __init__(
        self,
        x: float,
        y: float,
        squad,
        nav_graph: NavGraph,
        influence_map: InfluenceMap,
        blackboard: Blackboard,
        fire_callback,
    ) -> None:
        super().__init__(
            x=x, y=y, max_speed=settings.GUARD_SPEED * 0.8, blackboard=blackboard
        )
        self.radius = settings.CAPTAIN_RADIUS
        self.squad = squad
        self.nav_graph = nav_graph
        self.influence_map = influence_map
        self.fire_callback = fire_callback

        self.stance: str = "calm"
        self._rule_engine = RuleEngine(
            [
                Rule(
                    "desperate",
                    lambda m: m["distance_to_extraction"] < 150,
                    lambda m: m.update(stance="desperate"),
                    priority=10,
                ),
                Rule(
                    "engage",
                    lambda m: m["alert_count"] > 0,
                    lambda m: m.update(stance="engage"),
                    priority=5,
                ),
                Rule(
                    "calm",
                    lambda m: True,
                    lambda m: m.update(stance="calm"),
                    priority=0,
                ),
            ]
        )

        self._world_state: Dict[str, bool] = {
            "alarm_called": False,
            "in_position": False,
            "grenade_thrown": False,
        }
        self._plan: List[GoapAction] = []
        self._cooldown_timer: float = 0.0
        self._position_target: Optional[Point] = None

        self._direction_predictor = NGramPredictor(n=3)
        self._last_direction: Optional[int] = None

    def _update_stance(self, alert_count: int) -> None:
        memory = self._rule_engine.working_memory
        memory["alert_count"] = alert_count
        memory["distance_to_extraction"] = pygame.Vector2(
            level.EXTRACTION_RECT.center
        ).distance_to(self.squad.position)
        self._rule_engine.run()
        self.stance = memory.get("stance", "calm")

    def _observe_leader_direction(self) -> None:
        direction = _quantize_direction(self.squad.leader.velocity)

        if direction is not None and direction != self._last_direction:
            self._direction_predictor.observe(direction)
            self._last_direction = direction

    def _run_goap(self, dt: float) -> None:
        if self.stance == "calm":
            return

        if self._world_state["grenade_thrown"]:
            self._cooldown_timer -= dt

            if self._cooldown_timer <= 0:
                self._world_state = {
                    "alarm_called": False,
                    "in_position": False,
                    "grenade_thrown": False,
                }
                self._position_target = None

            return

        if not self._plan:
            self._plan = (
                plan(self._world_state, {"grenade_thrown": True}, _GOAP_ACTIONS) or []
            )

        if not self._plan:
            return

        action = self._plan[0]
        done = self._execute(action, dt)

        if done:
            self._world_state.update(action.effects)
            self._plan.pop(0)

            if self._world_state["grenade_thrown"]:
                self._cooldown_timer = settings.GOAP_COOLDOWN

    def _execute(self, action: GoapAction, dt: float) -> bool:
        if action.name == "call_alarm":
            self.blackboard.set(
                "alert_position", (self.squad.position.x, self.squad.position.y)
            )
            self.blackboard.set("is_alerted", True)
            return True

        if action.name == "take_position":
            if self._position_target is None:
                self._position_target = best_position(
                    level.COVER_POINTS,
                    score=lambda p: self.influence_map.dominance_at(pygame.Vector2(p)),
                )
                path = level.find_path(
                    self.nav_graph, tuple(self.position), self._position_target
                )
                self.set_steering_behavior(
                    PathFollow(self.kinematic, path or [self._position_target])
                )

            arrived = (
                self.position - pygame.Vector2(self._position_target)
            ).length() < 16

            if arrived:
                self.set_steering_behavior(None)

            return arrived

        if action.name == "throw_grenade":
            self._throw_grenade()
            return True

        return True

    def _throw_grenade(self) -> None:
        predicted_direction = self._direction_predictor.predict_next()
        aim_point = pygame.Vector2(self.squad.position)

        if predicted_direction is not None:
            aim_point += pygame.Vector2(_DIRECTIONS[predicted_direction]) * 40

        angle = iterative_targeting_angle(
            self.position, aim_point, settings.GRENADE_SPEED, settings.GRENADE_GRAVITY
        )

        if angle is None:
            return

        to_target = aim_point - self.position
        base_orientation = math.atan2(to_target.y, to_target.x)
        world_angle = base_orientation + angle
        velocity = (
            pygame.Vector2(math.cos(world_angle), math.sin(world_angle))
            * settings.GRENADE_SPEED
        )
        self.fire_callback("grenade", pygame.Vector2(self.position), velocity)

    def update(self, dt: float, alert_count: int) -> None:
        self._update_stance(alert_count)
        self._observe_leader_direction()
        self._run_goap(dt)
        super().update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        center = (int(self.position.x), int(self.position.y))
        pygame.draw.circle(surface, settings.COLOR_CAPTAIN, center, self.radius)
