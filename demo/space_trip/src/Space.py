import random

import pygame

from gale.factory import Factory
from gale.timer import Timer

import settings
from src.Star import Star


class Space:
    def __init__(self) -> None:
        self.x = 0
        self.stars = []
        self.star_factory = Factory(Star)

        def generate_star():
            y = random.uniform(0, settings.VIRTUAL_HEIGHT - settings.STAR_HEIGHT)
            star = self.star_factory.create(settings.VIRTUAL_WIDTH, y)
            self.stars.append(star)
        
        Timer.every(3, generate_star)
    
    def count_colliding_stars(self, rect: pygame.Rect) -> int:
        counter = 0
        for star in self.stars:
            if rect.colliderect(star.get_collision_rect()):
                settings.SOUNDS['take_star'].stop()
                settings.SOUNDS['take_star'].play()
                star.in_play = False
                counter += 1
        
        return counter
    
    def update(self, dt: float) -> None:
        self.x -= settings.BACKGROUND_SPEED * dt

        if self.x <= -settings.BACKGROUND_LOOPING_X:
            self.x = 0

        for star in self.stars:
            star.update(dt)
        
        self.stars = [s for s in self.stars if s.in_play]

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES['background'], (self.x, 0))

        for star in self.stars:
            star.render(surface)
