import pygame

from gale.physics.shapes import PolygonShape
from gale.physics.world import World

import settings


class Terrain:
    """
    A chain of static polygon segments following settings.terrain_height,
    each a small convex quad down to a common baseline.
    """

    def __init__(self, world: World) -> None:
        self.segments = []
        baseline = settings.VIRTUAL_HEIGHT + 20
        x = 0.0

        while x < settings.VIRTUAL_WIDTH:
            x0 = x
            x1 = min(x + settings.TERRAIN_STEP, settings.VIRTUAL_WIDTH)
            y0 = settings.terrain_height(x0)
            y1 = settings.terrain_height(x1)
            points = [(x0, y0), (x1, y1), (x1, baseline), (x0, baseline)]

            body = world.create_static_body(
                0, 0, PolygonShape(points, friction=settings.TERRAIN_FRICTION)
            )
            body.user_data = "terrain"

            self.segments.append(points)
            x = x1

    def render(self, surface: pygame.Surface) -> None:
        for points in self.segments:
            pygame.draw.polygon(surface, settings.COLOR_TERRAIN, points)
