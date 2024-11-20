"""
This file contains the implementation of the class Menu.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional, Sequence

import pygame

from .panel import Panel
from .selection import Selection, SelectionItem


class Menu:
    """
    This class represents a GUI menu.
    """

    def __init__(
        self,
        items: Sequence[str],
        x: float,
        y: float,
        width: float,
        height: float,
        main_color: tuple[int, int, int, int] | tuple[int, int, int],
        back_color: tuple[int, int, int, int] | tuple[int, int, int],
        text_color: tuple[int, int, int, int] | tuple[int, int, int],
        font: pygame.font.Font,
        cursor: Optional[pygame.Surface] = None,
    ):
        """
        Create a new Menu object.

        :param items: The items of the menu.
        :param x: The x position of the menu.
        :param y: The y position of the menu.
        :param width: The width of the menu.
        :param height: The height of the menu.
        :param main_color: The main color of the menu.
        :param back_color: The background color of the menu.
        :param text_color: The color of the text.
        :param font: The font of the text.
        :param cursor: The cursor to show when an item is selected.
        """
        panel_x = x - 10
        panel_width = 0

        for item in items:
            width = font.size("A")[0] * len(item.text)
            if width > panel_width:
                panel_width = width

        panel_width += 8

        if cursor is not None:
            panel_x -= cursor.get_width()
            panel_width += cursor.get_width()

        self.panel = Panel(panel_x, y, panel_width, height + 8, main_color, back_color)

        self.selection = Selection(
            items, x, y + 6, width, height, text_color, font, cursor
        )

    def move_up(self) -> None:
        """
        Move the selection up circularly.
        """
        self.selection.move_up()

    def move_down(self) -> None:
        """
        Move the selection down circularly.
        """
        self.selection.move_down()

    def select(self) -> None:
        """
        Call the on_select function of the current item
        """
        self.selection.select()

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the menu.
        """
        self.panel.render(surface)
        self.selection.render(surface)
