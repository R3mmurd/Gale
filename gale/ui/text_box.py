"""
This file contains the implementation of the class TextBox.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, List, Optional, Tuple

import pygame

from gale.input_handler import MouseClickData
from gale.text import Text

from .theme import Theme
from .widget import Widget


class TextBox(Widget):
    """
    A paginated block of text, such as dialogue or an in-game hint.
    advance() moves to the next page (on a mouse click or on_confirm),
    or, on the last page, hides the box and calls on_close.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        font: Optional[pygame.font.Font] = None,
        lines_per_page: int = 3,
        on_close: Optional[Callable[[], None]] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The box's x position.
        :param y: The box's y position.
        :param width: The box's width, used to word-wrap the text.
        :param height: The box's height.
        :param text: The full text to page through.
        :param font: The font used to render and measure the text. The default value is None, so theme.font is used.
        :param lines_per_page: How many wrapped lines are shown per page. The default value is 3.
        :param on_close: Called with no arguments once the last page is advanced past. The default value is None.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, width, height, theme=theme)
        self._font = font
        self.lines_per_page: int = lines_per_page
        self.on_close: Optional[Callable[[], None]] = on_close
        self._pages: List[List[str]] = self._paginate(text)
        self.page_index: int = 0

    def _paginate(self, text: str) -> List[List[str]]:
        font = self._font if self._font is not None else self.theme.font
        wrapped = self._wrap(text, font)
        pages = [
            wrapped[i : i + self.lines_per_page]
            for i in range(0, len(wrapped), self.lines_per_page)
        ]
        return pages or [[]]

    def _wrap(self, text: str, font: pygame.font.Font) -> List[str]:
        max_width = self.width - 2 * self.theme.padding
        lines: List[str] = []

        for paragraph in text.split("\n"):
            current = ""

            for word in paragraph.split(" "):
                candidate = f"{current} {word}".strip()

                if current and font.size(candidate)[0] > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate

            lines.append(current)

        return lines

    @property
    def finished(self) -> bool:
        return self.page_index >= len(self._pages) - 1

    def advance(self) -> None:
        if self.finished:
            self.visible = False

            if self.on_close is not None:
                self.on_close()

            return

        self.page_index += 1

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)

        if self.theme.border_width > 0:
            pygame.draw.rect(
                surface, self.theme.border_color, self.rect, self.theme.border_width
            )

        font = self._font if self._font is not None else self.theme.font
        line_height = font.get_linesize()

        for i, line in enumerate(self._pages[self.page_index]):
            text_obj = Text(
                line,
                font,
                self.x + self.theme.padding,
                self.y + self.theme.padding + i * line_height,
                self.theme.text_color,
            )
            text_obj.render(surface)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released:
            self.advance()

        return True

    def on_confirm(self) -> bool:
        if not self.enabled:
            return False

        self.advance()
        return True
