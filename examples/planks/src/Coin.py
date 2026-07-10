import pygame

import settings


class Coin:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = 6
        self.collected: bool = False

    def touches(self, rect: pygame.Rect) -> bool:
        return rect.collidepoint(self.x, self.y) or pygame.Rect(
            self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2
        ).colliderect(rect)

    def render(self, surface: pygame.Surface, camera) -> None:
        if self.collected:
            return

        screen_x, screen_y = camera.world_to_screen((self.x, self.y))
        pygame.draw.circle(
            surface,
            settings.COLOR_COIN,
            (round(screen_x), round(screen_y)),
            round(self.radius * camera.zoom),
        )
