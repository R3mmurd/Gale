"""
This file contains the implementation of the class Button: a
clickable, labeled rectangle, activated by a mouse click or by
on_confirm while focused.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, Optional, Tuple

import pygame

from gale.input_handler import MouseClickData
from gale.text import Text

from .theme import Theme
from .widget import Widget


class Button(Widget):
    """
    A clickable rectangle with a centered label. Fires on_click both
    when clicked with the mouse and when it is the focused widget and
    on_confirm is triggered (typically bound to Enter/a controller's
    "confirm" button through gale.input_handler).

    Usage example:

        def start_game():
            ...

        button = Button(220, 200, 200, 48, "Start", on_click=start_game)
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        font: Optional[pygame.font.Font] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The button's x position.
        :param y: The button's y position.
        :param width: The button's width.
        :param height: The button's height.
        :param text: The button's label.
        :param on_click: Called with no arguments when the button is activated. The default value is None.
        :param font: The font used for the label. The default value is None, so theme.font is used.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, width, height, theme=theme)
        self.text: str = text
        self.on_click: Optional[Callable[[], None]] = on_click
        self._font = font
        self.focusable = True

    def _label_color(self) -> pygame.Color:
        if not self.enabled:
            return self.theme.disabled_color

        return self.theme.text_color

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        if self.focused:
            fill_color = self.theme.focus_color
        elif self.hovered and self.enabled:
            fill_color = self.theme.hover_color
        else:
            fill_color = self.theme.background_color

        pygame.draw.rect(surface, fill_color, self.rect)

        if self.theme.border_width > 0:
            pygame.draw.rect(
                surface, self.theme.border_color, self.rect, self.theme.border_width
            )

        font = self._font if self._font is not None else self.theme.font
        text_obj = Text(
            self.text,
            font,
            self.rect.centerx,
            self.rect.centery,
            self._label_color(),
            center=True,
        )
        text_obj.render(surface)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released:
            self._activate()

        return True

    def on_confirm(self) -> bool:
        if not self.enabled:
            return False

        self._activate()
        return True

    def _activate(self) -> None:
        if self.on_click is not None:
            self.on_click()
