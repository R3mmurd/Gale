"""
This file contains the implementation of the class Window.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, List, Optional, Sequence

import pygame

from .button import Button
from .container import Container
from .label import Label
from .panel import Panel
from .theme import Theme, get_default_theme
from .widget import Widget


class Window(Container):
    """
    A Panel-backed Container with an optional title and an optional
    close ("X") button docked in its top-right corner, the way a
    desktop window or an in-game modal dialog (an inventory, a pause
    menu, a dialogue box the player can dismiss early) is closed.

    Usage example:

        def on_close():
            print("closed")

        window = Window(
            160, 90, 320, 220, title="Inventory", on_close=on_close,
            children=[ListView(...)],
        )
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str = "",
        closable: bool = True,
        on_close: Optional[Callable[[], None]] = None,
        close_button_size: int = 20,
        children: Optional[Sequence[Widget]] = None,
        theme: Optional[Theme] = None,
        visible: bool = True,
    ) -> None:
        """
        :param x: The window's x position.
        :param y: The window's y position.
        :param width: The window's width.
        :param height: The window's height.
        :param title: Optional text shown at the top-left corner. The default value is "" (no title).
        :param closable: Whether a close ("X") button is docked at the top-right corner. The default value is True.
        :param on_close: Called with no arguments after the window is closed, either through the close button or a direct call to close(). The default value is None.
        :param close_button_size: Width/height, in pixels, of the close button. The default value is 20.
        :param children: Extra widgets placed on top of the background panel/title/close button, in the given order (so later ones draw on top and are hit-tested first). The default value is None.
        :param theme: This widget's own theme, also handed down to the background panel, title label, and close button unless they're given their own. The default value is None.
        :param visible: Whether the window (and everything in it) is drawn/updated/reachable by input. The default value is True.
        """
        self.on_close: Optional[Callable[[], None]] = on_close
        self.close_button: Optional[Button] = None

        theme_obj = theme if theme is not None else get_default_theme()
        padding = theme_obj.padding

        widgets: List[Widget] = [Panel(x, y, width, height, theme=theme)]

        if title:
            widgets.append(Label(x + padding, y + padding, title, theme=theme))

        if closable:
            self.close_button = Button(
                x + width - close_button_size - padding,
                y + padding,
                close_button_size,
                close_button_size,
                "X",
                on_click=self.close,
                theme=theme,
            )
            widgets.append(self.close_button)

        widgets.extend(children or [])

        super().__init__(
            x, y, width, height, children=widgets, theme=theme, visible=visible
        )

    def close(self) -> None:
        """
        Hide the window and invoke on_close, if any. Safe to call
        directly (e.g. bound to a keyboard shortcut or another
        widget's on_click) even when closable is False.
        """
        self.visible = False

        if self.on_close is not None:
            self.on_close()
