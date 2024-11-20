"""
This file contains the implementation of the class Text.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional

import pygame


def render_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    x: float,
    y: float,
    color: pygame.Color,
    bg_color: Optional[pygame.Color] = None,
    center: bool = False,
    shadowed: bool = False,
):
    text_obj: pygame.Surface = font.render(text, True, color, bg_color)
    text_rect: pygame.Rect = text_obj.get_rect()

    if center:
        text_rect.center = (x, y)
    else:
        text_rect.x = x
        text_rect.y = y

    if shadowed:
        shadow_text: pygame.Surface = font.render(text, True, (0, 0, 0))
        shadow_rect: pygame.Rect = shadow_text.get_rect()
        shadow_rect.x = text_rect.x + 1
        shadow_rect.y = text_rect.y + 1
        surface.blit(shadow_text, shadow_rect)

    surface.blit(text_obj, text_rect)


class Text:
    def __init__(
        self,
        text_str: str,
        font: pygame.font.Font,
        x: float,
        y: float,
        color: pygame.Color,
        bg_color: Optional[pygame.Color] = None,
        center: bool = False,
        shadowed: bool = False,
    ):
        self.__text_str = text_str
        self.__font: pygame.font.Font = font
        self.__text: pygame.Surface = font.render(
            self.__text_str, True, color, bg_color
        )
        self.__rect: pygame.Rect = self.__text.get_rect()
        self.__x: float = x
        self.__y: float = y
        self.__center: bool = center
        self.__shadowed: bool = shadowed
        if self.__shadowed:
            self.__shadow_text: pygame.Surface = font.render(
                self.__text_str, True, (0, 0, 0)
            )

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y

    def render(self, surface: pygame.Surface) -> None:
        if self.__center:
            self.__rect.center = (self.__x, self.__y)
        else:
            self.__rect.x = self.__x
            self.__rect.y = self.__y

        if self.__shadowed:
            shadow_rect = self.__shadow_text.get_rect()
            shadow_rect.x = self.__rect.x + 1
            shadow_rect.y = self.__rect.y + 1
            surface.blit(self.__shadow_text, shadow_rect)

        surface.blit(self.__text, self.__rect)
