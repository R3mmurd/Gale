from typing import List, Optional, Tuple

import pygame

from gale.ai.agent import Agent
from gale.ai.behavior_tree import BehaviorTree, Status
from gale.ai.blackboard import Blackboard
from gale.ai.fuzzy import (
    FuzzyRule,
    FuzzyRuleSet,
    FuzzyVariable,
    LeftShoulderSet,
    RightShoulderSet,
    fuzzy_and,
    fuzzy_or,
)
from gale.ai.graph import NavGraph
from gale.ai.markov import MarkovChain, MarkovState, MarkovStateMachine
from gale.ai.scripting import Registry, build_behavior_tree
from gale.ai.steering import (
    CollisionAvoidance,
    Kinematic,
    PathFollow,
    PrioritySteering,
    SteeringBehavior,
    SteeringOutput,
    Wall,
    WallAvoidance,
)
from gale.ai.tactical import InfluenceMap, best_position
from gale.ai.targeting import predict_intercept_time

import settings
from src import level

Point = Tuple[float, float]

_SIGHT = settings.GUARD_SIGHT_RADIUS
DISTANCE_VAR = FuzzyVariable(
    "distance",
    domain=(0, _SIGHT * 1.5),
    sets={
        "near": LeftShoulderSet(_SIGHT * 0.3, _SIGHT * 0.75),
        "far": RightShoulderSet(_SIGHT * 0.5, _SIGHT),
    },
)
VISIBLE_VAR = FuzzyVariable(
    "visible", domain=(0, 1), sets={"yes": RightShoulderSet(0, 1)}
)
ALERTNESS_VAR = FuzzyVariable(
    "alertness",
    domain=(0, 1),
    sets={"low": LeftShoulderSet(0.3, 0.6), "high": RightShoulderSet(0.4, 0.7)},
)
ALERT_RULES = FuzzyRuleSet(
    [
        FuzzyRule(
            lambda d: fuzzy_and(d["distance"]["near"], d["visible"]["yes"]),
            "alertness",
            "high",
        ),
        FuzzyRule(
            lambda d: fuzzy_or(d["distance"]["far"], 1 - d["visible"]["yes"]),
            "alertness",
            "low",
        ),
    ]
)
ALERT_THRESHOLD = 0.55
INVESTIGATE_TIMEOUT = 3.0


class _LiveKinematics:
    """
    A read-only, always-current view of every guard's Kinematic,
    suitable for CollisionAvoidance's targets: iterating it later
    (once every guard has been constructed) always reflects the full
    roster, instead of a snapshot taken before it was complete.
    """

    def __init__(self, guards: List["Guard"]) -> None:
        self.guards = guards

    def __iter__(self):
        return (guard.kinematic for guard in self.guards)


class _DynamicSteering(SteeringBehavior):
    """
    Delegates to whatever steering behavior the behavior tree most
    recently decided on (guard.movement_behavior), so PrioritySteering
    can wrap wall/collision avoidance around a movement choice that
    changes every tick without rebuilding the whole pipeline.
    """

    def __init__(self, guard: "Guard") -> None:
        self.guard = guard

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        if self.guard.movement_behavior is None:
            return SteeringOutput()

        return self.guard.movement_behavior.get_steering(dt)


class _PatrolLegState(MarkovState):
    """
    Walks a straight leg between two patrol points, completing once
    close enough to the far end.
    """

    def __init__(self, name: str, guard: "Guard", path: Tuple[Point, Point]) -> None:
        super().__init__(name)
        self.guard = guard
        self.path = path

    def enter(self, *args, **kwargs) -> None:
        super().enter(*args, **kwargs)
        self.guard.movement_behavior = PathFollow(
            self.guard.kinematic, self.path, path_offset=20
        )

    def is_complete(self) -> bool:
        final = pygame.Vector2(self.path[-1])
        return (self.guard.position - final).length() < 14


class _IdleState(MarkovState):
    """
    Stands still for a fixed duration -- patrol variety, via
    MarkovStateMachine, instead of an unbroken back-and-forth.
    """

    def __init__(self, name: str, guard: "Guard", duration: float) -> None:
        super().__init__(name, duration=duration)
        self.guard = guard

    def enter(self, *args, **kwargs) -> None:
        super().enter(*args, **kwargs)
        self.guard.movement_behavior = None


class Guard(Agent):
    """
    A calm guard patrols (via a MarkovStateMachine picking between two
    patrol legs and standing idle for variety) until its fuzzy
    alertness -- driven by distance to the squad and line of sight --
    crosses a threshold. From then on a data-driven behavior tree (see
    gale.ai.scripting), rebuilt from a plain dict spec, decides between
    fighting from a tactically-chosen position (gale.ai.tactical) or
    investigating the squad's last reported position (shared with
    every other guard through the Blackboard) before giving up and
    returning to patrol.
    """

    def __init__(
        self,
        x: float,
        y: float,
        patrol_points: Tuple[Point, Point],
        squad,
        guards: List["Guard"],
        walls: List[Wall],
        nav_graph: NavGraph,
        influence_map: InfluenceMap,
        blackboard: Blackboard,
        fire_callback,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            max_speed=settings.GUARD_SPEED,
            max_acceleration=settings.GUARD_SPEED * 8,
            blackboard=blackboard,
        )
        self.radius = settings.GUARD_RADIUS
        self.squad = squad
        self.nav_graph = nav_graph
        self.influence_map = influence_map
        self.fire_callback = fire_callback

        self.alertness: float = 0.0
        self.movement_behavior: Optional[SteeringBehavior] = None
        self._fire_cooldown: float = 0.0
        self._investigate_target: Optional[Point] = None
        self._investigate_timer: float = 0.0
        self._cover_target: Optional[Point] = None

        self.set_steering_behavior(
            PrioritySteering(
                self.kinematic,
                [
                    [(WallAvoidance(self.kinematic, walls), 1.0)],
                    [
                        (
                            CollisionAvoidance(self.kinematic, _LiveKinematics(guards)),
                            1.0,
                        )
                    ],
                    [(_DynamicSteering(self), 1.0)],
                ],
            )
        )

        point_a, point_b = patrol_points
        chain = MarkovChain()
        chain.add_transition("to_b", "idle", 0.3)
        chain.add_transition("to_b", "to_a", 0.7)
        chain.add_transition("to_a", "idle", 0.3)
        chain.add_transition("to_a", "to_b", 0.7)
        chain.add_transition("idle", "to_a", 0.5)
        chain.add_transition("idle", "to_b", 0.5)
        self.markov = MarkovStateMachine(
            chain,
            {
                "to_b": _PatrolLegState("to_b", self, (point_a, point_b)),
                "to_a": _PatrolLegState("to_a", self, (point_b, point_a)),
                "idle": _IdleState("idle", self, duration=1.5),
            },
            start="to_b",
        )

        registry = Registry()
        registry.register_condition(
            "is_alert", lambda agent: agent.alertness > ALERT_THRESHOLD
        )
        registry.register_condition(
            "team_alerted",
            lambda agent: agent.blackboard.get("is_alerted", False),
        )
        registry.register_action("combat", lambda agent, dt: agent._combat_step(dt))
        registry.register_action(
            "investigate", lambda agent, dt: agent._investigate_step(dt)
        )
        registry.register_action("patrol", lambda agent, dt: agent._patrol_step(dt))
        spec = {
            "type": "selector",
            "children": [
                {
                    "type": "sequence",
                    "children": [
                        {"type": "condition", "name": "is_alert"},
                        {"type": "action", "name": "combat"},
                    ],
                },
                {
                    "type": "sequence",
                    "children": [
                        {"type": "condition", "name": "team_alerted"},
                        {"type": "action", "name": "investigate"},
                    ],
                },
                {"type": "action", "name": "patrol"},
            ],
        }
        self.set_brain(BehaviorTree(build_behavior_tree(spec, registry)))

    def _update_alertness(self) -> None:
        distance = (self.squad.position - self.position).length()
        visible = level.has_line_of_sight(
            tuple(self.position), tuple(self.squad.position)
        )
        fuzzified = {
            "distance": DISTANCE_VAR.fuzzify(distance),
            "visible": VISIBLE_VAR.fuzzify(1.0 if visible else 0.0),
        }
        output = ALERT_RULES.evaluate(fuzzified)
        self.alertness = ALERTNESS_VAR.defuzzify(output.get("alertness", {}))

    def _combat_step(self, dt: float) -> Status:
        self.blackboard.set(
            "alert_position", (self.squad.position.x, self.squad.position.y)
        )
        self.blackboard.set("is_alerted", True)
        self._investigate_target = None

        if self._cover_target is None:
            self._cover_target = best_position(
                level.COVER_POINTS,
                score=lambda p: self.influence_map.dominance_at(pygame.Vector2(p))
                - pygame.Vector2(p).distance_to(self.squad.position) * 0.01,
            )

        path = level.find_path(self.nav_graph, tuple(self.position), self._cover_target)
        self.movement_behavior = PathFollow(
            self.kinematic, path or [self._cover_target], path_offset=16
        )

        self._fire_cooldown -= dt
        distance = (self.squad.position - self.position).length()

        if (
            self._fire_cooldown <= 0
            and distance <= settings.GUARD_FIRE_RANGE
            and level.has_line_of_sight(
                tuple(self.position), tuple(self.squad.position)
            )
        ):
            self._fire_cooldown = settings.GUARD_FIRE_COOLDOWN
            self._fire_at(self.squad.leader.kinematic)

        return Status.SUCCESS

    def _fire_at(self, target: Kinematic) -> None:
        t = predict_intercept_time(
            self.position, target.position, target.velocity, settings.BULLET_SPEED
        )
        predicted = (
            target.position + target.velocity * t if t is not None else target.position
        )
        direction = predicted - self.position

        if direction.length_squared() == 0:
            return

        velocity = direction.normalize() * settings.BULLET_SPEED
        self.fire_callback("bullet", pygame.Vector2(self.position), velocity)

    def _investigate_step(self, dt: float) -> Status:
        self._cover_target = None
        alert_position = self.blackboard.get("alert_position")

        if alert_position != self._investigate_target:
            self._investigate_target = alert_position
            self._investigate_timer = INVESTIGATE_TIMEOUT
            path = level.find_path(self.nav_graph, tuple(self.position), alert_position)
            self.movement_behavior = PathFollow(
                self.kinematic, path or [alert_position], path_offset=16
            )

        self._investigate_timer -= dt

        if self._investigate_timer <= 0:
            self.blackboard.set("is_alerted", False)
            return Status.FAILURE

        return Status.SUCCESS

    def _patrol_step(self, dt: float) -> Status:
        self._cover_target = None
        self.markov.update(dt)
        return Status.SUCCESS

    @property
    def is_alert(self) -> bool:
        return self.alertness > ALERT_THRESHOLD

    def update(self, dt: float) -> None:
        self._update_alertness()
        super().update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        color = (
            settings.COLOR_GUARD_ALERT if self.is_alert else settings.COLOR_GUARD_CALM
        )
        center = (int(self.position.x), int(self.position.y))
        pygame.draw.circle(surface, color, center, self.radius)

        if self.velocity.length_squared() > 1:
            tip = self.position + self.velocity.normalize() * (self.radius + 6)
            pygame.draw.line(surface, color, center, tip, 2)
