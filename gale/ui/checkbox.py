"""
This file contains the implementation of the class Checkbox.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, Optional, Tuple

import pygame

from gale.input_handler import MouseClickData

from .theme import Theme
from .widget import Widget


class Checkbox(Widget):
    """
    A square toggle. Fires on_change(checked) whenever its state
    flips, either by a mouse click or by on_confirm while focused.
    """

    def __init__(
        self,
        x: float,
        y: float,
        size: float,
        checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The checkbox's x position.
        :param y: The checkbox's y position.
        :param size: The checkbox's width and height.
        :param checked: The initial state. The default value is False.
        :param on_change: Called with the new state whenever it changes. The default value is None.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, size, size, theme=theme)
        self.checked: bool = checked
        self.on_change: Optional[Callable[[bool], None]] = on_change
        self.focusable = True

    def toggle(self) -> None:
        self.checked = not self.checked

        if self.on_change is not None:
            self.on_change(self.checked)

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)

        border_color = (
            self.theme.focus_color if self.focused else self.theme.border_color
        )
        pygame.draw.rect(
            surface, border_color, self.rect, max(1, self.theme.border_width)
        )

        if self.checked:
            inset = self.rect.inflate(-int(self.width * 0.4), -int(self.height * 0.4))
            pygame.draw.rect(surface, self.theme.accent_color, inset)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released:
            self.toggle()

        return True

    def on_confirm(self) -> bool:
        if not self.enabled:
            return False

        self.toggle()
        return True
