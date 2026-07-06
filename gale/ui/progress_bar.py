"""
This file contains the implementation of the class ProgressBar.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional

import pygame

from .theme import Theme
from .widget import Widget


class ProgressBar(Widget):
    """
    A filled bar showing value out of max_value. value and max_value
    are plain public attributes (no set_value/set_max methods) so they
    can be driven directly by gale.timer.Timer.tween, e.g.:

        Timer.tween(0.5, [(health_bar, {"value": new_hp})])
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        value: float = 0,
        max_value: float = 100,
        color: Optional[pygame.Color] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The bar's x position.
        :param y: The bar's y position.
        :param width: The bar's width.
        :param height: The bar's height.
        :param value: The current value. The default value is 0.
        :param max_value: The value that fills the bar completely. The default value is 100.
        :param color: The fill color. The default value is None, so theme.accent_color is used.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, width, height, theme=theme)
        self.value: float = value
        self.max_value: float = max_value
        self._color = color

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)

        ratio = (
            0.0
            if self.max_value <= 0
            else max(0.0, min(1.0, self.value / self.max_value))
        )
        fill_width = int(self.width * ratio)

        if fill_width > 0:
            fill_color = (
                self._color if self._color is not None else self.theme.accent_color
            )
            fill_rect = pygame.Rect(
                int(self.x), int(self.y), fill_width, int(self.height)
            )
            pygame.draw.rect(surface, fill_color, fill_rect)

        if self.theme.border_width > 0:
            pygame.draw.rect(
                surface, self.theme.border_color, self.rect, self.theme.border_width
            )
