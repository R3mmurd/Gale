from typing import List, Tuple

import pygame

from gale.ai.agent import Agent
from gale.ai.formation import FormationManager, WedgeFormation
from gale.ai.steering import Arrive

import settings
from src import level

Point = Tuple[float, float]


class SquadMember(Agent):
    """
    A follower in the player's squad: steered by Arrive towards
    whatever slot FormationManager currently assigns it, so it tags
    along with the leader's formation without needing to know where
    the squad as a whole is headed.
    """

    def __init__(self, x: float, y: float) -> None:
        super().__init__(
            x=x,
            y=y,
            max_speed=settings.SQUAD_LEADER_SPEED,
            max_acceleration=settings.SQUAD_LEADER_SPEED * 8,
        )
        self.radius = settings.SQUAD_MEMBER_RADIUS

    def update(self, dt: float) -> None:
        super().update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            settings.COLOR_MEMBER,
            (int(self.position.x), int(self.position.y)),
            self.radius,
        )


class Squad:
    """
    The player's squad: a leader directly driven by input (see
    set_input_direction) and two SquadMember followers, arranged in a
    WedgeFormation behind it via FormationManager -- "two-level"
    steering, since a member only ever follows its own slot, never the
    squad's overall plan.
    """

    def __init__(self, start: Point) -> None:
        self.leader = Agent(
            x=start[0],
            y=start[1],
            max_speed=settings.SQUAD_LEADER_SPEED,
            face_movement_direction=False,
        )
        self.radius = settings.SQUAD_MEMBER_RADIUS
        self.members: List[SquadMember] = [
            SquadMember(start[0] - 20, start[1] - 15),
            SquadMember(start[0] - 20, start[1] + 15),
        ]

        self.formation = FormationManager(
            self.leader.kinematic, WedgeFormation(spacing=30, depth=26)
        )
        for member in self.members:
            self.formation.add_member(member.kinematic)

        self.formation.update()

        for member in self.members:
            member.set_steering_behavior(
                Arrive(
                    member.kinematic,
                    self.formation.slot_kinematic(member.kinematic),
                    target_radius=4,
                    slow_radius=50,
                )
            )

        self.hits_taken = 0

    @property
    def position(self) -> pygame.Vector2:
        return self.leader.position

    def all_positions(self) -> List[pygame.Vector2]:
        return [self.leader.position] + [member.position for member in self.members]

    def set_input_direction(self, dx: float, dy: float) -> None:
        direction = pygame.Vector2(dx, dy)
        self.leader.kinematic.velocity = (
            direction.normalize() * settings.SQUAD_LEADER_SPEED
            if direction.length_squared() > 0
            else pygame.Vector2()
        )

    def register_hit(self) -> None:
        self.hits_taken += 1

    def update(self, dt: float) -> None:
        self.leader.update(dt)
        self.leader.kinematic.position = level.resolve_circle_vs_obstacles(
            self.leader.kinematic.position, self.radius
        )
        self.formation.update()

        for member in self.members:
            member.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        for member in self.members:
            member.render(surface)

        pygame.draw.circle(
            surface,
            settings.COLOR_LEADER,
            (int(self.leader.position.x), int(self.leader.position.y)),
            self.radius + 1,
        )
