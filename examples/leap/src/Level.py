import pygame

from gale.physics.shapes import BoxShape, CircleShape
from gale.physics.world import World

import settings


class Level:
    """
    Two ground segments with a gap between them, a kinematic platform
    that oscillates back and forth to ferry the player across the
    gap, and a goal sensor on the far side.
    """

    def __init__(self, world: World) -> None:
        ground_y = settings.VIRTUAL_HEIGHT - settings.GROUND_HEIGHT / 2

        self.ground_left = world.create_static_body(
            settings.GROUND_LEFT_WIDTH / 2,
            ground_y,
            BoxShape(settings.GROUND_LEFT_WIDTH, settings.GROUND_HEIGHT),
        )
        self.ground_left.user_data = "ground"

        self.ground_right = world.create_static_body(
            settings.VIRTUAL_WIDTH - settings.GROUND_RIGHT_WIDTH / 2,
            ground_y,
            BoxShape(settings.GROUND_RIGHT_WIDTH, settings.GROUND_HEIGHT),
        )
        self.ground_right.user_data = "ground"

        wall_height = settings.VIRTUAL_HEIGHT
        self.wall_left = world.create_static_body(
            -5, wall_height / 2, BoxShape(10, wall_height)
        )
        self.wall_right = world.create_static_body(
            settings.VIRTUAL_WIDTH + 5, wall_height / 2, BoxShape(10, wall_height)
        )

        platform_y = (
            ground_y - settings.GROUND_HEIGHT / 2 - settings.PLATFORM_HEIGHT / 2
        )
        self.platform = world.create_kinematic_body(
            settings.PLATFORM_MIN_X,
            platform_y,
            BoxShape(settings.PLATFORM_WIDTH, settings.PLATFORM_HEIGHT),
        )
        self.platform.user_data = "ground"
        self.platform.set_velocity(settings.PLATFORM_SPEED, 0)

        self.goal = world.create_static_body(
            settings.VIRTUAL_WIDTH - settings.GROUND_RIGHT_WIDTH / 2,
            ground_y - settings.GROUND_HEIGHT / 2 - settings.GOAL_RADIUS,
            CircleShape(settings.GOAL_RADIUS, is_sensor=True),
        )
        self.goal.user_data = "goal"

    def update(self, dt: float) -> None:
        x = self.platform.position.x

        if x <= settings.PLATFORM_MIN_X and self.platform.velocity.x < 0:
            self.platform.set_velocity(settings.PLATFORM_SPEED, 0)
        elif x >= settings.PLATFORM_MAX_X and self.platform.velocity.x > 0:
            self.platform.set_velocity(-settings.PLATFORM_SPEED, 0)

    def render(self, surface: pygame.Surface) -> None:
        for ground in (self.ground_left, self.ground_right):
            self._render_box(
                surface,
                ground,
                settings.GROUND_LEFT_WIDTH,
                settings.GROUND_HEIGHT,
                settings.COLOR_GROUND,
            )

        self._render_box(
            surface,
            self.platform,
            settings.PLATFORM_WIDTH,
            settings.PLATFORM_HEIGHT,
            settings.COLOR_PLATFORM,
        )

        pygame.draw.circle(
            surface, settings.COLOR_GOAL, self.goal.position, settings.GOAL_RADIUS
        )

    def _render_box(self, surface, body, width, height, color) -> None:
        position = body.position
        rect = pygame.Rect(
            int(position.x - width / 2),
            int(position.y - height / 2),
            int(width),
            int(height),
        )
        pygame.draw.rect(surface, color, rect)
