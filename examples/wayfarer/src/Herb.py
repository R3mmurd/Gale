import pygame

import settings


class Herb:
    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)
        self.radius = 6
        self.collected = False

    def touches(self, position: pygame.Vector2, radius: float) -> bool:
        return self.position.distance_to(position) <= self.radius + radius

    def render(self, surface: pygame.Surface) -> None:
        if self.collected:
            return

        pygame.draw.circle(
            surface,
            settings.COLOR_HERB,
            (round(self.position.x), round(self.position.y)),
            self.radius,
        )
