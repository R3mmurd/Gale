"""
This file contains the implementation of a mixins for renderizable game objects.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame


class RenderizableMixin:
    def render(self, surface: pygame.Surface) -> None:
        image = pygame.Surface(
            (self.frame.__width, self.frame.__height), pygame.SRCALPHA
        )
        image.fill((0, 0, 0, 0))
        image.blit(self.texture, (0, 0), self.frame)

        h_flipped = self.h_flipped or False
        v_flipped = self.v_flipped or False

        if h_flipped or v_flipped:
            image = pygame.transform.flip(image, h_flipped, v_flipped)

        surface.blit(image, (self.x, self.y))
