"""
This file contains the implementation of the class Panel.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame


class Panel:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        main_color: tuple[int, int, int, int] | tuple[int, int, int],
        back_color: tuple[int, int, int, int] | tuple[int, int, int],
    ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.main_color = main_color
        self.back_color = back_color
        self.visible = True

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(
            surface,
            self.back_color,
            pygame.Rect(self.x, self.y, self.width, self.height),
            0,
            3,
            3,
            3,
            3,
        )
        pygame.draw.rect(
            surface,
            self.main_color,
            pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4),
            0,
            3,
            3,
            3,
            3,
        )

    def toggle(self) -> None:
        self.visible = not self.visible
