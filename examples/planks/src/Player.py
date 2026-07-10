import pygame

from gale.tilemap import move_and_collide

import settings


class Player:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = settings.PLAYER_WIDTH
        self.height: int = settings.PLAYER_HEIGHT
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.on_ground: bool = False

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def jump(self) -> None:
        if self.on_ground:
            self.vy = settings.JUMP_SPEED
            self.on_ground = False

    def update(self, dt: float, tilemap, layer_name: str) -> None:
        self.vy = min(self.vy + settings.GRAVITY * dt, settings.MAX_FALL_SPEED)

        new_rect, hit_x, hit_y = move_and_collide(
            tilemap, layer_name, self.get_rect(), self.vx * dt, self.vy * dt
        )
        self.x, self.y = new_rect.x, new_rect.y

        if hit_y:
            if self.vy > 0:
                self.on_ground = True

            self.vy = 0
        else:
            self.on_ground = False

    def render(self, surface: pygame.Surface, camera) -> None:
        dest = camera.apply(self.get_rect())
        pygame.draw.rect(surface, settings.COLOR_PLAYER, dest)
