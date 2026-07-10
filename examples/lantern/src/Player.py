from typing import List, Optional

import pygame

import settings


class Player:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = settings.PLAYER_RADIUS
        self.vx: float = 0.0
        self.vy: float = 0.0

    def get_rect(
        self, x: Optional[float] = None, y: Optional[float] = None
    ) -> pygame.Rect:
        x = self.x if x is None else x
        y = self.y if y is None else y
        return pygame.Rect(
            round(x - self.radius),
            round(y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def update(self, dt: float, walls: List[pygame.Rect]) -> None:
        new_x = self.x + self.vx * dt

        if not self._collides(new_x, self.y, walls):
            self.x = new_x

        new_y = self.y + self.vy * dt

        if not self._collides(self.x, new_y, walls):
            self.y = new_y

    def _collides(self, x: float, y: float, walls: List[pygame.Rect]) -> bool:
        rect = self.get_rect(x, y)
        return any(rect.colliderect(wall) for wall in walls)

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(
            surface,
            settings.COLOR_PLAYER,
            (round(self.x), round(self.y)),
            self.radius,
        )
