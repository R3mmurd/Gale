"""
This file contains the implementation of the class Theme, the shared
set of colors/fonts/spacing every widget falls back to unless given
its own.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional

import pygame


class Theme:
    """
    A bundle of style values every widget reads from, either its own
    (passed to its constructor) or a shared default one.

    Usage example:

        pygame.font.init()
        dark_theme = Theme(font=pygame.font.Font(None, 20))
        panel = Panel(10, 10, 200, 100, theme=dark_theme)
    """

    def __init__(
        self,
        font: Optional[pygame.font.Font] = None,
        text_color: pygame.Color = pygame.Color(235, 235, 235),
        background_color: pygame.Color = pygame.Color(30, 30, 34),
        border_color: pygame.Color = pygame.Color(235, 235, 235),
        border_width: int = 1,
        accent_color: pygame.Color = pygame.Color(90, 200, 255),
        hover_color: pygame.Color = pygame.Color(55, 60, 75),
        focus_color: pygame.Color = pygame.Color(255, 210, 60),
        disabled_color: pygame.Color = pygame.Color(120, 120, 120),
        padding: int = 4,
    ) -> None:
        """
        :param font: The font widgets use to render their text. The default value is None, so pygame's built-in default font is created and used.
        :param text_color: Default text color.
        :param background_color: Default fill color for panels/containers.
        :param border_color: Default border/outline color.
        :param border_width: Default border thickness, in pixels.
        :param accent_color: Color used for filled indicators, such as a ProgressBar's fill or a checked Checkbox.
        :param hover_color: Color used to highlight a widget the mouse is over.
        :param focus_color: Color used to highlight the currently focused widget.
        :param disabled_color: Color used to draw a widget with enabled set to False.
        :param padding: Default inner spacing, in pixels.
        """
        if font is None:
            pygame.font.init()
            font = pygame.font.Font(None, 20)

        self.font: pygame.font.Font = font
        self.text_color: pygame.Color = text_color
        self.background_color: pygame.Color = background_color
        self.border_color: pygame.Color = border_color
        self.border_width: int = border_width
        self.accent_color: pygame.Color = accent_color
        self.hover_color: pygame.Color = hover_color
        self.focus_color: pygame.Color = focus_color
        self.disabled_color: pygame.Color = disabled_color
        self.padding: int = padding


_default_theme: Optional[Theme] = None


def get_default_theme() -> Theme:
    """
    :returns: The current default theme, creating one with every value defaulted the first time this is called.
    """
    global _default_theme

    if _default_theme is None:
        _default_theme = Theme()

    return _default_theme


def set_default_theme(theme: Theme) -> None:
    """
    Replace the default theme every widget created without an explicit
    theme falls back to. Existing widgets read gale.ui.theme.get_default_theme()
    fresh on every render, so this takes effect immediately, without
    having to recreate them.

    :param theme: The new default theme.
    """
    global _default_theme
    _default_theme = theme
