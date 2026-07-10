"""
This file contains the implementation of the class Panel: a plain
filled, bordered rectangle, typically used as background chrome
behind other widgets or on its own as a HUD backdrop.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional

import pygame

from .theme import Theme
from .widget import Widget


class Panel(Widget):
    """
    A plain filled, bordered rectangle. Typically used as the
    background chrome behind other widgets (see Container), or on its
    own as a HUD backdrop.

    Usage example:

        panel = Panel(10, 10, 200, 120)
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        theme: Optional[Theme] = None,
        visible: bool = True,
    ) -> None:
        super().__init__(x, y, width, height, theme=theme, visible=visible)

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)

        if self.theme.border_width > 0:
            pygame.draw.rect(
                surface, self.theme.border_color, self.rect, self.theme.border_width
            )
