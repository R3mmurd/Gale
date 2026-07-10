from typing import List, Tuple

import pygame

import settings
from src.Torch import Torch


class Room:
    """
    A single, fixed layout: an outer wall, a handful of interior
    pillars to walk around, two torches to find, and an exit tile
    tucked in the far corner.
    """

    START_POSITION: Tuple[float, float] = (30, 30)

    WALLS: List[pygame.Rect] = [
        # Border.
        pygame.Rect(0, 0, settings.VIRTUAL_WIDTH, settings.WALL_THICKNESS),
        pygame.Rect(
            0,
            settings.VIRTUAL_HEIGHT - settings.WALL_THICKNESS,
            settings.VIRTUAL_WIDTH,
            settings.WALL_THICKNESS,
        ),
        pygame.Rect(0, 0, settings.WALL_THICKNESS, settings.VIRTUAL_HEIGHT),
        pygame.Rect(
            settings.VIRTUAL_WIDTH - settings.WALL_THICKNESS,
            0,
            settings.WALL_THICKNESS,
            settings.VIRTUAL_HEIGHT,
        ),
        # Interior pillars.
        pygame.Rect(90, 40, 16, 110),
        pygame.Rect(170, 130, 150, 16),
        pygame.Rect(280, 40, 16, 100),
        pygame.Rect(320, 150, 16, 78),
    ]

    EXIT_RECT: pygame.Rect = pygame.Rect(
        settings.VIRTUAL_WIDTH - settings.WALL_THICKNESS - settings.EXIT_SIZE - 6,
        settings.VIRTUAL_HEIGHT - settings.WALL_THICKNESS - settings.EXIT_SIZE - 6,
        settings.EXIT_SIZE,
        settings.EXIT_SIZE,
    )

    @classmethod
    def create_torches(cls) -> List[Torch]:
        return [Torch(210, 30), Torch(360, 110)]

    @classmethod
    def render(cls, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_FLOOR)

        for wall in cls.WALLS:
            pygame.draw.rect(surface, settings.COLOR_WALL, wall)

        pygame.draw.rect(surface, settings.COLOR_EXIT, cls.EXIT_RECT)
