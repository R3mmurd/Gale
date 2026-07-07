import pygame

from gale.physics.shapes import BoxShape
from gale.physics.world import World

import settings


class Player:
    def __init__(self, world: World, x: float, y: float) -> None:
        self.body = world.create_dynamic_body(
            x, y, BoxShape(settings.PLAYER_SIZE, settings.PLAYER_SIZE, friction=0.5)
        )
        self.body.user_data = "player"

    @property
    def position(self) -> pygame.Vector2:
        return self.body.position

    def _grounded_body(self):
        """The specific body currently supporting the player, if any.
        Used both for is_grounded() and to carry the player along with
        a moving platform (see move()) - relying on friction alone to
        keep a rigid body glued to a fast platform is unreliable in a
        physics engine, so its velocity is added directly instead."""
        for body in self.body.touching_bodies:
            if body.user_data == "ground":
                return body
        return None

    def is_grounded(self) -> bool:
        return self._grounded_body() is not None

    def move(self, direction: int) -> None:
        """
        :param direction: -1 to move left, 0 to stop, 1 to move right.
        """
        ground = self._grounded_body()
        carry_vx = ground.velocity.x if ground is not None else 0
        self.body.set_velocity(direction * settings.PLAYER_SPEED + carry_vx, self.body.velocity.y)

    def jump(self) -> None:
        if self.is_grounded():
            self.body.apply_impulse(0, -settings.PLAYER_JUMP_IMPULSE)

    def render(self, surface: pygame.Surface) -> None:
        half = settings.PLAYER_SIZE / 2
        rect = pygame.Rect(
            int(self.position.x - half),
            int(self.position.y - half),
            settings.PLAYER_SIZE,
            settings.PLAYER_SIZE,
        )
        pygame.draw.rect(surface, settings.COLOR_PLAYER, rect)
