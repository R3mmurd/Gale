import pygame

import settings


class Wolf:
    """
    A stationary wolf: the point of this example is showing the game
    reporting quest progress, not enemy AI depth, so it is kept as
    simple as possible (see the README for the same note).
    """

    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)
        self.radius = settings.WOLF_RADIUS
        self.defeated = False

    def is_adjacent_to(self, position: pygame.Vector2, radius: float) -> bool:
        return self.position.distance_to(position) <= radius + self.radius

    def render(self, surface: pygame.Surface) -> None:
        if self.defeated:
            return

        pygame.draw.circle(
            surface,
            settings.COLOR_WOLF,
            (round(self.position.x), round(self.position.y)),
            self.radius,
        )
