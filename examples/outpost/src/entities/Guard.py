import math
from typing import List, Tuple

import pygame

from gale.ai.agent import Agent
from gale.ai.graph import NavGraph
from gale.ai.perception import AlertLevel, Perception, VisionCone
from gale.state import StateMachine

import settings
from src import level
from src.entities.guard_states import Alert, Patrol, Search
from src.path_follower import PathFollower

Point = Tuple[float, float]


class Guard(Agent):
    """
    A guard whose decision making is a hierarchical state machine (see
    src/entities/guard_states.py): "patrol" (itself made of "walking"
    and "looking_around" substates) / "search" / "alert", switched
    between based on the AlertLevel a gale.ai.perception.Perception
    (fed by a single VisionCone) computes every tick from the player's
    position, blocked by the level's wall obstacles just like a real
    line of sight would be.
    """

    def __init__(
        self,
        x: float,
        y: float,
        patrol_points: Tuple[Point, Point],
        player: Agent,
        nav_graph: NavGraph,
    ) -> None:
        super().__init__(x=x, y=y, max_speed=settings.GUARD_SEARCH_SPEED, orientation=0)
        self.radius = settings.GUARD_RADIUS
        self.player = player
        self.nav_graph = nav_graph

        self.patrol_points: List[Point] = list(patrol_points)
        self.patrol_follower = PathFollower()
        self.patrol_follower.set_path(self.patrol_points)

        self.vision_cone = VisionCone(
            self.kinematic,
            range_near=settings.VISION_RANGE_NEAR,
            range_far=settings.VISION_RANGE_FAR,
            half_angle=settings.VISION_HALF_ANGLE,
        )
        self.perception = Perception(
            [self.vision_cone],
            blackboard=self.blackboard,
            decay_rate=settings.PERCEPTION_DECAY_RATE,
            suspicious_threshold=settings.PERCEPTION_SUSPICIOUS_THRESHOLD,
            alerted_threshold=settings.PERCEPTION_ALERTED_THRESHOLD,
        )

        self.fsm = StateMachine(
            {
                "patrol": lambda sm: Patrol(sm, self),
                "search": lambda sm: Search(sm, self),
                "alert": lambda sm: Alert(sm, self),
            }
        )
        self._state_name = "patrol"
        self.fsm.change("patrol")

        # Face the first patrol point right away, instead of an
        # arbitrary orientation of 0.
        initial_direction = pygame.Vector2(self.patrol_points[0]) - self.position
        if initial_direction.length_squared() > 0:
            self.kinematic.orientation = math.atan2(
                initial_direction.y, initial_direction.x
            )

    def _change_state(self, name: str) -> None:
        if self._state_name == name:
            return

        self._state_name = name
        self.fsm.change(name)

    @property
    def alert_level(self) -> AlertLevel:
        return self.blackboard.get("alert_level", AlertLevel.UNAWARE)

    def update(self, dt: float) -> None:
        alert_level = self.perception.update(
            dt, self.player.position, obstacles=level.OBSTACLES
        )

        if alert_level == AlertLevel.ALERTED:
            self._change_state("alert")
        elif alert_level == AlertLevel.SUSPICIOUS:
            self._change_state("search")
        else:
            self._change_state("patrol")

        self.fsm.update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        self._render_vision_cone(surface)

        if self.alert_level == AlertLevel.ALERTED:
            color = settings.COLOR_GUARD_ALERTED
        elif self.alert_level == AlertLevel.SUSPICIOUS:
            color = settings.COLOR_GUARD_SUSPICIOUS
        else:
            color = settings.COLOR_GUARD_PATROL

        screen_x, screen_y = level.to_screen(self.position.x, self.position.y)
        pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), 7)
        pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), 7, 1)

    def _render_vision_cone(self, surface: pygame.Surface) -> None:
        segments = 10
        orientation = self.kinematic.orientation
        half_angle = self.vision_cone.half_angle
        far = self.vision_cone.range_far

        points = [level.to_screen(self.position.x, self.position.y)]

        for i in range(segments + 1):
            angle = orientation - half_angle + (2 * half_angle) * i / segments
            world_point = (
                self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * far
            )
            points.append(level.to_screen(world_point.x, world_point.y))

        cone_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surface, (*settings.COLOR_VISION_CONE, 30), points)
        surface.blit(cone_surface, (0, 0))
