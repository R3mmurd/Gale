"""
This file contains the implementation of the class Label.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional

import pygame

from gale.text import Text

from .theme import Theme
from .widget import Widget


class Label(Widget):
    """
    A piece of static (or programmatically updatable, via set_text)
    text, drawn with gale.text.Text.

    Usage example:

        label = Label(320, 40, "Rally", center=True)
        label.set_text("Rally: 3 - 2")
    """

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        font: Optional[pygame.font.Font] = None,
        color: Optional[pygame.Color] = None,
        center: bool = False,
        shadowed: bool = False,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The label's x position.
        :param y: The label's y position.
        :param text: The text to render.
        :param font: The font to use. The default value is None, so theme.font is used.
        :param color: The text color. The default value is None, so theme.text_color is used.
        :param center: Whether (x, y) is the text's center rather than its top-left corner. The default value is False.
        :param shadowed: Whether to draw a 1px drop shadow behind the text. The default value is False.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, 0, 0, theme=theme)
        self._font = font
        self._color = color
        self._center = center
        self._shadowed = shadowed
        self._text_obj: Text = self._build_text(text)

    def _build_text(self, text: str) -> Text:
        font = self._font if self._font is not None else self.theme.font
        color = self._color if self._color is not None else self.theme.text_color
        text_obj = Text(
            text,
            font,
            self.x,
            self.y,
            color,
            center=self._center,
            shadowed=self._shadowed,
        )
        self.width = text_obj.rect.width
        self.height = text_obj.rect.height
        return text_obj

    def set_text(self, text: str) -> None:
        """
        :param text: The new text to display.
        """
        self._text_obj = self._build_text(text)

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        self._text_obj.x = self.x
        self._text_obj.y = self.y
        self._text_obj.render(surface)
