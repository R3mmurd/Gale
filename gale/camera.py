"""
This module contains a simple camera class.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame


class Camera:

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        """
        Initialize a new Camera.

        :param x: The x component for the position of the camera.
        :param y: The y component for the position of the camera.
        :param width: The width of the camera.
        :param height: The height of the camera.
        """
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height
        self.__collision_boundaries = None
        self.__following = None

    @property
    def x(self) -> float:
        """
        Get the x component of the camera position.

        :returns: The x component of the camera position.
        """
        return self.__x

    @property
    def y(self) -> float:
        """
        Get the y component of the camera position.

        :returns: The y component of the camera position.
        """
        return self.__y

    @property
    def width(self) -> float:
        """
        Get the width of the camera.

        :returns: The width of the camera.
        """
        return self.__width

    @property
    def height(self) -> float:
        """
        Get the height of the camera.

        :returns: The height of the camera.
        """
        return self.__height

    def attach_to(self, entity: any) -> None:
        """
        Attach the camera to an entity.

        :param entity: The entity to follow.
        """
        self.__following = entity

    def set_collision_boundaries(self, rect: pygame.Rect) -> None:
        """
        Set the collision boundaries for the camera.

        :param rect: The collision boundaries.
        """
        self.__collision_boundaries = rect

    def update(self) -> None:
        """
        Update the camera position.

        This function updates the camera position based on the entity that is following.
        """
        if self.__following is not None:
            self.__x = self.__following.x - self.__width / 2
            self.__y = self.__following.y - self.__height / 2

        if self.__collision_boundaries is not None:
            self.__x = max(
                self.__collision_boundaries.x,
                min(
                    self.__x,
                    self.__collision_boundaries.x
                    + self.__collision_boundaries.width
                    - self.__width,
                ),
            )
            self.__y = max(
                self.__collision_boundaries.y,
                min(
                    self.__y,
                    self.__collision_boundaries.y
                    + self.__collision_boundaries.height
                    - self.__height,
                ),
            )

    def get_rect(self) -> pygame.Rect:
        """
        Get the camera as a rectangle.

        :returns: A pygame.Rect object representing the camera
        """
        return pygame.Rect(self.__x, self.__y, self.__width, self.__height)
