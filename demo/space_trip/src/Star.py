import pygame

import settings


class Star:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.in_play = True
    
    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, settings.STAR_WIDTH, settings.STAR_HEIGHT)
    
    def update(self, dt: float) -> None:
        self.x -= settings.STAR_SPEED * dt
        if self.x < -settings.STAR_WIDTH:
            self.in_play = False
        
    def render(self, surface: pygame.Surface):
        surface.blit(settings.TEXTURES['star'], (self.x, self.y))
