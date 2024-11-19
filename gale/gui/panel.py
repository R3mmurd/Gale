"""
This file contains the implementation of the class Panel.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame


class Panel:
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(
            surface,
            (255, 255, 255, 255),
            pygame.Rect(self.x, self.y, self.width, self.height),
            3,
            3,
            3,
            3,
        )
        pygame.draw.rect(
            surface,
            (56, 56, 56, 255),
            pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4),
            3,
            3,
            3,
            3,
        )

    def toggle(self) -> None:
        self.visible = not self.visible
