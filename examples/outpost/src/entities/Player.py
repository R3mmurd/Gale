import pygame

from gale.ai.agent import Agent

import settings
from src import level


class Player(Agent):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x=x, y=y, max_speed=settings.PLAYER_SPEED)
        self.radius = settings.PLAYER_RADIUS

    def set_input_direction(self, dx: float, dy: float) -> None:
        """
        :param dx: Horizontal component of the currently-held movement keys, in [-1, 1].
        :param dy: Vertical component of the currently-held movement keys, in [-1, 1].
        """
        direction = pygame.Vector2(dx, dy)
        self.kinematic.velocity = (
            direction.normalize() * settings.PLAYER_SPEED
            if direction.length_squared() > 0
            else pygame.Vector2()
        )

    def update(self, dt: float) -> None:
        super().update(dt)
        self.kinematic.position = level.resolve_circle_vs_obstacles(
            self.kinematic.position, self.radius
        )

    def render(self, surface: pygame.Surface) -> None:
        screen_x, screen_y = level.to_screen(self.position.x, self.position.y)
        pygame.draw.circle(
            surface, settings.COLOR_PLAYER, (int(screen_x), int(screen_y)), 7
        )
        pygame.draw.circle(
            surface, settings.COLOR_PLAYER, (int(screen_x), int(screen_y)), 7, 1
        )
