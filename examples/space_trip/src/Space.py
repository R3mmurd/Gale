import random

import pygame

from gale.factory import Factory
from gale.timer import Timer

import settings
from src.Rock import Rock
from src.Star import Star


class Space:
    def __init__(self) -> None:
        self.x = 0
        self.stars = []
        self.rocks = []
        self.star_factory = Factory(Star)
        self.rock_factory = Factory(Rock)

        def generate_star():
            y = random.uniform(0, settings.VIRTUAL_HEIGHT - settings.STAR_HEIGHT)
            star = self.star_factory.create(settings.VIRTUAL_WIDTH, y)
            self.stars.append(star)

        def generate_rock():
            y = random.uniform(0, settings.VIRTUAL_HEIGHT - settings.ROCK_HEIGHT)
            rock = self.rock_factory.create(settings.VIRTUAL_WIDTH, y)
            self.rocks.append(rock)
            Timer.after(random.uniform(*settings.ROCK_SPAWN_DELAY_RANGE), generate_rock)

        Timer.every(3, generate_star)
        Timer.after(random.uniform(*settings.ROCK_SPAWN_DELAY_RANGE), generate_rock)

    def count_colliding_stars(self, rect: pygame.Rect) -> int:
        counter = 0
        for star in self.stars:
            if rect.colliderect(star.get_collision_rect()):
                settings.SOUNDS["take_star"].stop()
                settings.SOUNDS["take_star"].play()
                star.in_play = False
                counter += 1

        return counter

    def has_colliding_rock(self, rect: pygame.Rect) -> bool:
        return any(rect.colliderect(rock.get_collision_rect()) for rock in self.rocks)

    def update(self, dt: float) -> None:
        self.x -= settings.BACKGROUND_SPEED * dt

        if self.x <= -settings.BACKGROUND_LOOPING_X:
            self.x = 0

        for star in self.stars:
            star.update(dt)

        self.stars = [s for s in self.stars if s.in_play]

        for rock in self.rocks:
            rock.update(dt)

        self.rocks = [r for r in self.rocks if r.in_play]

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["background"], (self.x, 0))

        for star in self.stars:
            star.render(surface)

        for rock in self.rocks:
            rock.render(surface)
