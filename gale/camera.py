"""
This module contains a simple camera class.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame

from typing import Any


class Camera:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        """
        Initialize a new Camera.

        :param x: The x component for the position of the camera.
        :param y: The y component for the position of the camera.
        :param width: The width of the camera.
        :param height: The height of the camera.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.collision_boundaries = None
        self.following = None

    def attach_to(self, entity: Any) -> None:
        """
        Attach the camera to an entity.

        :param entity: The entity to follow.
        """
        self.following = entity

    def set_collision_boundaries(self, rect: pygame.Rect) -> None:
        """
        Set the collision boundaries for the camera.

        :param rect: The collision boundaries.
        """
        self.collision_boundaries = rect

    def update(self) -> None:
        """
        Update the camera position.

        This function updates the camera position based on the entity that is following.
        """
        if self.following is not None:
            self.x = self.following.x - self.width // 2
            self.y = self.following.y - self.height // 2

        if self.collision_boundaries is not None:
            self.x = max(
                self.collision_boundaries.x,
                min(
                    self.x,
                    self.collision_boundaries.x
                    + self.collision_boundaries.width
                    - self.width,
                ),
            )
            self.y = max(
                self.collision_boundaries.y,
                min(
                    self.y,
                    self.collision_boundaries.y
                    + self.collision_boundaries.height
                    - self.height,
                ),
            )

    def get_rect(self) -> pygame.Rect:
        """
        Get the camera as a rectangle.

        :returns: A pygame.Rect object representing the camera
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)
