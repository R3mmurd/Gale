"""
This file contains the implementation of a mixins for collidable game objects.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any

import pygame


class CollidableMixin:
    """
    This method requires that derivated classes have the following attributes:
        - x: float
        - y: float
        - width: float
        - height: float
    """

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def collides(self, another: pygame.Rect) -> bool:
        return self.get_collision_rect().colliderect(another)
