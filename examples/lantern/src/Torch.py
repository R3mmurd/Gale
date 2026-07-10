import pygame

import settings


class Torch:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = settings.TORCH_RADIUS
        self.collected: bool = False

    def touches(self, x: float, y: float, radius: float) -> bool:
        dx = self.x - x
        dy = self.y - y
        return (dx * dx + dy * dy) ** 0.5 <= self.radius + radius

    def render(self, surface: pygame.Surface) -> None:
        if self.collected:
            return

        pygame.draw.circle(
            surface,
            settings.COLOR_TORCH,
            (round(self.x), round(self.y)),
            self.radius,
        )
