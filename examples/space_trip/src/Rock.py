import pygame

import settings


class Rock:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.in_play = True

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, settings.ROCK_WIDTH, settings.ROCK_HEIGHT)

    def update(self, dt: float) -> None:
        self.x -= settings.ROCK_SPEED * dt
        if self.x < -settings.ROCK_WIDTH:
            self.in_play = False

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["rock"], (self.x, self.y))
