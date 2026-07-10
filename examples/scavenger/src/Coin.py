import pygame

import settings


class Coin:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = settings.COIN_RADIUS
        self.collected: bool = False

    def touches(self, x: float, y: float, radius: float) -> bool:
        dx = self.x - x
        dy = self.y - y
        return (dx * dx + dy * dy) ** 0.5 <= self.radius + radius

    def render(self, surface: pygame.Surface, camera) -> None:
        if self.collected:
            return

        screen_x, screen_y = camera.world_to_screen((self.x, self.y))
        radius = round(self.radius * camera.zoom)
        pygame.draw.circle(
            surface, settings.COLOR_COIN, (round(screen_x), round(screen_y)), radius
        )
