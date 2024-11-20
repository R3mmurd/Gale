"""
This file contains the implementation of the class Panel.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import textwrap

import pygame

from .panel import Panel
from ..text import render_text


class TextBox:
    """
    This class represents a GUI text box that computes dynamically how many
    characters could be rendered into it and how many lines are needed to
    display the text. It also has a method to display the text in chunks.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        font: pygame.font.Font,
        main_color: tuple[int, int, int, int] | tuple[int, int, int],
        back_color: tuple[int, int, int, int] | tuple[int, int, int],
        text_color: tuple[int, int, int, int] | tuple[int, int, int],
    ) -> None:
        """
        Create a new TextBox object.

        :param x: The x position of the text box.
        :param y: The y position of the text box.
        :param width: The width of the text box.
        :param height: The height of the text box.
        :param text: The text to display.
        :param font: The font of the text.
        :param main_color: The main color of the text box.
        :param back_color: The background color of the text box.
        :param text_color: The color of the text.
        """
        self.panel = Panel(x, y, width, height, main_color, back_color)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = font
        self.text_color = text_color
        self.text_chunks = textwrap.wrap(
            self.text, (self.width - 12) // self.font.size("A")[0]
        )
        self.chunk_counter = 0
        self.end_of_text = False
        self.closed = False
        self.displaying_chunks = []
        self.next()

    def __next_chunks(self) -> list[str]:
        chunks = []
        num_chunks = len(self.text_chunks)
        max_rows = int(self.height / (3 + self.font.size("A")[1] * 1.5))

        for i in range(self.chunk_counter, self.chunk_counter + max_rows):
            chunks.append(self.text_chunks[i])

            if i == num_chunks - 1:
                self.end_of_text = True
                return chunks

        self.chunk_counter += max_rows

        return chunks

    def next(self) -> str:
        """
        Display the next chunk of text.
        """
        if self.closed:
            return

        if self.end_of_text:
            self.displaying_chunks = []
            self.panel.toggle()
            self.closed = True
        else:
            self.displaying_chunks = self.__next_chunks()

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the text box on the given surface.
        """
        self.panel.render(surface)

        for i in range(len(self.displaying_chunks)):
            render_text(
                surface,
                self.displaying_chunks[i],
                self.font,
                self.x + 6,
                self.y + 6 + i * self.font.size("A")[1] * 1.5,
                self.text_color,
            )
