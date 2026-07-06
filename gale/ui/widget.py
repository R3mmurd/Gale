"""
This file contains the implementation of the class Widget, the base
every gale.ui widget (Panel, Button, Container, ...) derives from.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional, Tuple

import pygame

from gale.input_handler import MouseClickData

from .theme import Theme, get_default_theme

Direction = Tuple[int, int]


class Widget:
    """
    Base class for anything gale.ui can render and route input to.

    A subclass overrides update/render to draw itself, and whichever
    of on_mouse_motion/on_mouse_click/on_confirm/on_navigate it reacts
    to. on_mouse_click, on_confirm, and on_navigate return a bool
    meaning "did I consume this?", so a Container knows whether to
    keep forwarding the same input to something else (a click behind a
    focused widget should not also reach whatever is under it).
    """

    # Class-level default: purely decorative widgets (Panel, Label)
    # never take keyboard focus, so a Container skips them when picking
    # what to focus first or where Tab/arrow navigation should land.
    # Interactive subclasses (Button, Checkbox, ListView, TextInput)
    # set self.focusable = True in their own __init__. Container
    # overrides this as a property instead (focusable if any child is).
    focusable: bool = False

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        theme: Optional[Theme] = None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        """
        :param x: The widget's x position.
        :param y: The widget's y position.
        :param width: The widget's width.
        :param height: The widget's height.
        :param theme: This widget's own theme. The default value is None, so it always uses gale.ui.theme.get_default_theme() (kept live: changing the default with set_default_theme affects this widget immediately).
        :param visible: Whether the widget is drawn/updated/reachable by input. The default value is True.
        :param enabled: Whether the widget reacts to input. A disabled widget is still drawn (typically with theme.disabled_color) and updated. The default value is True.
        """
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self._theme: Optional[Theme] = theme
        self.visible: bool = visible
        self.enabled: bool = enabled
        self.focused: bool = False
        self.hovered: bool = False
        self.parent: Optional["Widget"] = None
        self.wants_raw_keyboard: bool = False

    @property
    def theme(self) -> Theme:
        return self._theme if self._theme is not None else get_default_theme()

    @theme.setter
    def theme(self, value: Optional[Theme]) -> None:
        self._theme = value

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def contains(self, position: Tuple[float, float]) -> bool:
        """
        :param position: A point, in the same coordinate space as x/y.
        :returns: Whether position is inside this widget's rect.
        """
        return self.rect.collidepoint(position)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass

    def on_mouse_motion(self, position: Tuple[float, float]) -> None:
        self.hovered = self.contains(position)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        return False

    def on_confirm(self) -> bool:
        return False

    def on_navigate(self, direction: Direction) -> bool:
        return False
