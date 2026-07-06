"""
This file contains the implementation of the class ListView.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, List, Optional, Sequence, Tuple

import pygame

from gale.input_handler import MouseClickData
from gale.text import Text

from .cursor import Cursor
from .theme import Theme
from .widget import Direction, Widget

Item = Tuple[str, Callable[[], None]]


class ListView(Widget):
    """
    A vertical list of selectable items, each a (label, on_select)
    pair. Supports both keyboard navigation (on_navigate moves the
    selection with wraparound, on_confirm invokes the selected item)
    and mouse interaction (hovering highlights, clicking selects and
    invokes). This is the generalization of gale.ui's "menu": build a
    menu as Container([Panel(...), ListView(...)]).

    Usage example:

        menu = ListView(
            40, 40, 240, 120,
            items=[("Host", start_hosting), ("Join", start_joining), ("Quit", quit_game)],
        )
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        items: Sequence[Item],
        font: Optional[pygame.font.Font] = None,
        cursor: Optional[Cursor] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The list's x position.
        :param y: The list's y position.
        :param width: The list's width.
        :param height: The list's height.
        :param items: The (label, on_select) pairs to show, top to bottom.
        :param font: The font used for each item's label. The default value is None, so theme.font is used.
        :param cursor: A Cursor rendered next to the selected item. The default value is None, so no indicator is drawn (the row highlight alone marks the selection).
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, width, height, theme=theme)
        self.items: List[Item] = list(items)
        self.selected_index: int = 0
        self._font = font
        self.cursor: Optional[Cursor] = cursor
        self.focusable = True

    def row_height(self) -> float:
        return self.height / len(self.items) if self.items else self.height

    def row_rect(self, index: int) -> pygame.Rect:
        row_height = self.row_height()
        return pygame.Rect(
            int(self.x),
            int(self.y + index * row_height),
            int(self.width),
            int(row_height),
        )

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible or not self.items:
            return

        font = self._font if self._font is not None else self.theme.font

        for index, (label, _) in enumerate(self.items):
            row_rect = self.row_rect(index)

            if index == self.selected_index:
                fill_color = (
                    self.theme.focus_color if self.focused else self.theme.hover_color
                )
                pygame.draw.rect(surface, fill_color, row_rect)

            text_obj = Text(
                label,
                font,
                row_rect.centerx,
                row_rect.centery,
                self.theme.text_color,
                center=True,
            )
            text_obj.render(surface)

            if index == self.selected_index and self.cursor is not None:
                self.cursor.render(surface, (row_rect.x - 4, row_rect.centery))

    def on_mouse_motion(self, position: Tuple[float, float]) -> None:
        self.hovered = self.contains(position)

        if self.hovered:
            self.selected_index = self._row_at(position)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released:
            self.selected_index = self._row_at(position)
            self._activate()

        return True

    def on_confirm(self) -> bool:
        if not self.enabled or not self.items:
            return False

        self._activate()
        return True

    def on_navigate(self, direction: Direction) -> bool:
        if not self.enabled or not self.items:
            return False

        _, dy = direction

        if dy == 0:
            return False

        self.selected_index = (self.selected_index + dy) % len(self.items)
        return True

    def _row_at(self, position: Tuple[float, float]) -> int:
        row_height = self.row_height()
        index = int((position[1] - self.y) // row_height) if row_height else 0
        return max(0, min(len(self.items) - 1, index))

    def _activate(self) -> None:
        _, on_select = self.items[self.selected_index]
        on_select()
