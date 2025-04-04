"""
This module implements the raycasting algorithm for games.

Author: Alejandro Mujica
"""

from typing import Optional

import pygame


class Segment:
    """
    Represents a segment of a line.
    """

    def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class Ray:
    """
    Represents a ray.
    """

    def __init__(
        self,
        position: pygame.Vector2,
        direction: pygame.Vector2,
        length: Optional[float] = None,
    ) -> None:
        self.position = position
        self.direction = direction
        self.length = length

    def cast(self, segment: Segment) -> Optional[pygame.Vector2]:
        """
        Cast the ray against a segment.
        """
        x1, y1, x2, y2 = segment.x1, segment.y1, segment.x2, segment.y2
        x3, y3, x4, y4 = (
            self.position.x,
            self.position.y,
            self.position.x + self.direction.x,
            self.position.y + self.direction.y,
        )

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if den == 0:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 <= t <= 1 and 0 <= u <= 1:
            intersection_point = pygame.Vector2(x1 + t * (x2 - x1), y1 + t * (y2 - y1))

            if (
                self.length is None
                or intersection_point.distance_to(pygame.Vector2(self.x, self.y))
                <= self.length
            ):
                return intersection_point

        return None

    def draw(self, surface: pygame.Surface, color: pygame.Color) -> None:
        """
        Draw the ray as an arrow.
        """
        pygame.draw.line(
            surface, color, self.position, self.position + self.direction * self.length
        )
        pygame.draw.circle(
            surface,
            color,
            (
                int(self.position.x + self.direction.x * self.length),
                int(self.position.y + self.direction.y * self.length),
            ),
            5,
        )
        pygame.draw.polygon(
            surface,
            color,
            [
                (
                    self.position.x + self.direction.x * self.length,
                    self.position.y + self.direction.y * self.length,
                ),
                (
                    self.position.x + self.direction.x * self.length - 10,
                    self.position.y + self.direction.y * self.length + 10,
                ),
                (
                    self.position.x + self.direction.x * self.length - 10,
                    self.position.y + self.direction.y * self.length - 10,
                ),
            ],
        )


class Raycasting:

    @staticmethod
    def cast_segments(
        segments: list[Segment],
        ray_position: pygame.Vector2,
        ray_direction: pygame.Vector2,
        ray_length: Optional[float] = None,
    ) -> pygame.Vector2:
        ray = Ray(ray_position, ray_direction, ray_length)

        closest_intersection_point = None
        closest_distance = float("inf")

        for segment in segments:
            intersection_point = ray.cast(segment)

            if intersection_point is not None:
                distance = ray.position.distance_to(intersection_point)

                if distance < closest_distance:
                    closest_distance = distance
                    closest_intersection_point = intersection_point

        return closest_intersection_point

    @staticmethod
    def cast_tiles(
        tiles: list[list[pygame.Rect]],
        ray_position: pygame.Vector2,
        ray_direction: pygame.Vector2,
        ray_length: Optional[float] = None,
    ) -> pygame.Vector2:
        segments = []

        for row in range(len(tiles)):
            for col in range(len(tiles[row])):
                if tiles[row][col] is not None:
                    tile = tiles[row][col]

                    x1, y1 = tile.topleft
                    x2, y2 = tile.topright
                    x3, y3 = tile.bottomright
                    x4, y4 = tile.bottomleft

                    segments.append(Segment(x1, y1, x2, y2))
                    segments.append(Segment(x2, y2, x3, y3))
                    segments.append(Segment(x3, y3, x4, y4))
                    segments.append(Segment(x4, y4, x1, y1))

        return Raycasting.cast_segments(
            segments, ray_position, ray_direction, ray_length
        )

    @staticmethod
    def draw_ray(
        surface: pygame.Surface,
        position: pygame.Vector2,
        direction: pygame.Vector2,
        length: float,
        color: pygame.Color,
    ) -> None:
        ray = Ray(position, direction, length)
        ray.draw(surface, color)
