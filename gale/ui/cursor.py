"""
This file contains the implementation of the class Cursor.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Tuple

import pygame


class Cursor:
    """
    A custom cursor image, usable two ways:

    - As the OS mouse pointer: call set_as_system_cursor() once (a
      state's enter() is a good place) to swap pygame's own cursor for
      this image.
    - As a keyboard-navigation indicator: pass it to ListView(cursor=...)
      so it is rendered next to the currently selected item.

    A game configures the cursors it needs through its own settings.py,
    the same way it already does for TEXTURES/FONTS/SOUNDS:

        CURSORS = {
            "pointer": Cursor(pygame.image.load(BASE_DIR / "assets" / "graphics" / "cursor_pointer.png"), hotspot=(2, 2)),
        }
    """

    def __init__(
        self, image: pygame.Surface, hotspot: Tuple[int, int] = (0, 0)
    ) -> None:
        """
        :param image: The cursor's image.
        :param hotspot: The pixel within image that marks the actual pointer position. The default value is (0, 0), the image's top-left corner.
        """
        self.image: pygame.Surface = image
        self.hotspot: Tuple[int, int] = hotspot
        self.visible: bool = True

    def set_as_system_cursor(self) -> None:
        """
        Replace the OS mouse pointer with this cursor's image.
        """
        pygame.mouse.set_cursor(pygame.cursors.Cursor(self.hotspot, self.image))

    def show(self) -> None:
        self.visible = True
        pygame.mouse.set_visible(True)

    def hide(self) -> None:
        self.visible = False
        pygame.mouse.set_visible(False)

    def render(self, surface: pygame.Surface, position: Tuple[float, float]) -> None:
        """
        Draw this cursor's image at position, used for the
        keyboard-navigation indicator use case (the OS pointer use
        case never calls this: pygame already draws the real cursor).

        :param surface: The surface to draw on.
        :param position: Where the hotspot should land.
        """
        if not self.visible:
            return

        surface.blit(
            self.image, (position[0] - self.hotspot[0], position[1] - self.hotspot[1])
        )
