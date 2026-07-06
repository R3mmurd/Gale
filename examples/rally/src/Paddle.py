import pygame

import settings


class Paddle:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.width: float = settings.PADDLE_WIDTH
        self.height: float = settings.PADDLE_HEIGHT
        self.vy: float = 0.0

    def update(self, dt: float) -> None:
        self.y += self.vy * dt
        self.y = max(0, min(settings.VIRTUAL_HEIGHT - self.height, self.y))

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, settings.COLOR_PADDLE, self.get_rect())
