"""
gale.stencil: cut an arbitrary shape (drawn however you like: circles,
polygons, another sprite, text...) out of a surface's alpha channel.

Pygame has no GPU stencil buffer to piggyback on, so this masks on the
CPU instead: draw the shape you want visible into a Stencil's own
mask surface, then apply() it to any other surface — every pixel
outside the shape has its alpha zeroed out (or, with invert=True,
every pixel inside it does). That's the classic building block for
top-down games: a circular torch/vision reveal over a dark overlay, a
minimap cropped to a circle, an item silhouette showing only through
a doorway, and so on.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, Tuple

import pygame

# The convention this module relies on: draw stencil shapes as
# opaque white (any alpha) onto the mask surface. BLEND_RGBA_MULT
# then leaves a masked-in pixel's own color/alpha untouched (channel
# * 255 / 255) and zeroes out a masked-out one (channel * 0 / 255).
_OPAQUE_WHITE: pygame.Color = pygame.Color(255, 255, 255, 255)
_TRANSPARENT: pygame.Color = pygame.Color(0, 0, 0, 0)

DrawFunction = Callable[[pygame.Surface], None]


class Stencil:
    """
    Usage example (a circular torch reveal over a dark overlay):

        stencil = Stencil((width, height))
        stencil.draw(lambda mask: pygame.draw.circle(mask, "white", light_pos, radius))

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        stencil.apply(overlay, invert=True)  # punch the circle out of the dark overlay
        screen.blit(overlay, (0, 0))

    The shape is redrawn every frame you want it to move/change: call
    clear() first, then draw() again (or build a fresh Stencil if you
    prefer). A single Stencil can be applied to as many surfaces as
    you like, with or without invert, once its shape is drawn.
    """

    def __init__(self, size: Tuple[int, int]) -> None:
        """
        :param size: The (width, height) of the surfaces this stencil will be applied to.
        """
        self.size: Tuple[int, int] = size
        self._mask: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        self._mask.fill(_TRANSPARENT)

    def clear(self) -> None:
        """
        Erase whatever shape was previously drawn, so this Stencil can be reused for a new one.
        """
        self._mask.fill(_TRANSPARENT)

    def draw(self, draw_function: DrawFunction) -> None:
        """
        :param draw_function: Called with this stencil's internal mask surface — draw the shape that should be "visible" onto it (e.g. with pygame.draw.circle/polygon or a blit), in opaque white.
        """
        draw_function(self._mask)

    def apply(self, surface: pygame.Surface, invert: bool = False) -> None:
        """
        Zero out the alpha of every pixel of surface that falls
        outside the shape previously passed to draw() (or, with
        invert=True, every pixel inside it). surface must have
        per-pixel alpha (created with pygame.SRCALPHA, or via
        convert_alpha()) for this to have a visible effect once it's
        later blit somewhere else.

        :param surface: The surface to mask, in place. Must be the same size this Stencil was created with.
        :param invert: Whether to keep the outside of the shape instead of the inside. The default value is False.
        """
        mask = self._mask

        if invert:
            mask = pygame.Surface(self.size, pygame.SRCALPHA)
            mask.fill(_OPAQUE_WHITE)
            mask.blit(self._mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
