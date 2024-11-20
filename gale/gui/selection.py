"""
This file contains the implementation of the classes SelectionItem and Selection.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Sequence, Optional, Callable

import pygame

from ..text import render_text


class SelectionItem:
    """
    This class represents an item in a Selection object.
    """

    def __init__(self, text: str, on_select: Callable) -> None:
        """
        Create a new SelectionItem object.

        :param text: The text of the item.
        :param on_select: The function to call when the item is selected.
        """
        self.text = text
        self.on_select = on_select


class Selection:
    """
    This class represents a GUI selection.
    """

    def __init__(
        self,
        items: Sequence[SelectionItem],
        x: float,
        y: float,
        width: float,
        height: float,
        text_color: tuple[int, int, int, int] | tuple[int, int, int],
        font: pygame.font.Font,
        cursor: Optional[pygame.Surface] = None,
    ) -> None:
        """
        Create a new Selection object.

        :param items: The items of the selection.
        :param x: The x position of the selection.
        :param y: The y position of the selection.
        :param width: The width of the selection.
        :param height: The height of the selection.
        :param text_color: The color of the text.
        :param font: The font of the text.
        :param cursor: The cursor to show when an item is selected.
        """
        self.items = items
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text_color = text_color
        self.font = font
        self.cursor = cursor
        self.gap_height = self.height // len(self.items)
        self.current_selection = 0

    def move_up(self) -> None:
        """
        Move the selection up circularly.
        """
        if self.current_selection == 0:
            self.current_selection = len(self.items) - 1
        else:
            self.current_selection -= 1

    def move_down(self) -> None:
        """
        Move the selection down circularly.
        """
        if self.current_selection == len(self.items) - 1:
            self.current_selection = 0
        else:
            self.current_selection += 1

    def select(self) -> None:
        """
        Call the on_select function of the current item
        """
        if self.items[self.current_selection].on_select is not None:
            self.items[self.current_selection].on_select()

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the selection.
        """
        current_y = self.y

        for i in range(len(self.items)):
            padded_y = (
                current_y + (self.gap_height // 2) - (self.font.size("A")[1] // 2)
            )

            if i == self.current_selection and self.cursor is not None:
                surface.blit(
                    self.cursor,
                    (self.x - self.cursor.get_width() - 4, padded_y),
                )

            render_text(
                surface,
                self.items[i].text,
                self.font,
                self.x,
                padded_y,
                self.text_color,
            )
            current_y = current_y + self.gap_height
