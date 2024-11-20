"""
This file contains the implementation of the class ProgressBar.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame


class ProgressBar:
    """
    This class represents a GUI progress bar.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: tuple[int, int, int, int] | tuple[int, int, int],
        back_color: tuple[int, int, int, int] | tuple[int, int, int],
        max_value: int,
        value: int,
    ) -> None:
        """
        Create a new ProgressBar object.

        :param x: The x position of the progress bar.
        :param y: The y position of the progress bar.
        :param width: The width of the progress bar.
        :param height: The height of the progress bar.
        :param color: The color of the progress bar.
        :param max_value: The maximum value of the progress bar.
        :param value: The current value of the progress bar.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.back_color = back_color
        self.__max_value = max_value
        self.__value = value

    def get_value(self) -> int:
        return self.__value

    def set_value(self, value: int) -> None:
        self.__value = max(0, min(value, self.__max_value))

    def add_value(self, value: int) -> None:
        self.__value = max(0, min(self.__value + value, self.__max_value))

    def get_max_value(self) -> int:
        return self.__max_value

    def render(self, screen: pygame.Surface) -> None:
        """
        Render the progress bar.

        :param screen: The surface to render the progress bar.
        """
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(
            screen,
            self.back_color,
            (self.x, self.y, self.width * self.__value / self.__max_value, self.height),
        )
