import pygame

import settings


class Player:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = settings.PLAYER_RADIUS
        self.vx: float = 0.0
        self.vy: float = 0.0

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x = max(self.radius, min(settings.WORLD_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(settings.WORLD_HEIGHT - self.radius, self.y))

    def render(self, surface: pygame.Surface, camera) -> None:
        screen_x, screen_y = camera.world_to_screen((self.x, self.y))
        radius = round(self.radius * camera.zoom)
        pygame.draw.circle(
            surface, settings.COLOR_PLAYER, (round(screen_x), round(screen_y)), radius
        )
