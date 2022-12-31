"""
This file contains the implementation of a particle systems.

Author: Alejandro Mujica (aledrums@gmail.com)
"""
import random
from typing import List

import pygame


class Particle:
    def __init__(self, x: float, y: float, ax: float, ay: float, life_time: float, color: pygame.Color) -> None:
        """
        Set the initial value for a particle

        :param x: X position.
        :param y: Y position.
        :param ax: X acceleration.
        :param ay: Y acceleration.
        :param life_time: duration in seconds of the particle.
        :param color: render color.
        """
        # Position
        self.x: float = x
        self.y: float = y

        # Velocity
        self.vx: float = 0
        self.vy: float = 0

        # Acceleration
        self.ax: float = ax
        self.ay: float = ay

        self.life_time: float = life_time
        self.color: pygame.Color = color

    def update(self, dt: float) -> None:
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx
        self.y += self.vy

    def render(self, surface: pygame.Surface) -> None:
        s = pygame.Surface((4, 4))
        s.set_alpha(self.color[3])
        pygame.draw.circle(s, self.color, (2, 2), 2)
        surface.blit(s, (int(self.x), int(self.y)))


class ParticleSystem:
    def __init__(self, x: float, y: float, n: int) -> None:
        """
        Builds a particle system.

        :param x: Center x of the system.
        :param y: Center y of the system.
        :param n: Number of particles.
        """
        self.x_mean: float = x
        self.y_mean: float = y
        self.size: int = n

        self.min_life_time: float = 0
        self.max_life_time: float = 0
        self.timer: float = 0
        self.ax1: float = 0
        self.ax2: float = 0
        self.ay1: float = 0
        self.ay2: float = 0
        self.x_desv: float = 1
        self.y_desv: float = 1

        self.colors: List[pygame.Color] = []
        self.particles: List[Particle] = []

    def set_life_time(self, minimum: float, maximum: float) -> None:
        self.min_life_time = minimum
        self.max_life_time = maximum

    def set_linear_acceleration(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.ax1 = x1
        self.ay1 = y1
        self.ax2 = x2
        self.ay2 = y2

    def set_colors(self, colors: List[pygame.Color]) -> None:
        self.colors = colors

    def set_area_spread(self, rx: float, ry: float) -> None:
        self.x_desv = rx
        self.y_desv = ry

    def generate(self) -> None:
        for _ in range(self.size):
            ax: float = random.uniform(self.ax1, self.ax2)
            ay: float = random.uniform(self.ay1, self.ay2)
            px: float = random.gauss(self.x_mean, self.x_desv)
            py: float = random.gauss(self.y_mean, self.y_desv)
            color: pygame.Color = random.choice(self.colors)
            life_time: float = random.uniform(
                self.min_life_time, self.max_life_time)
            self.particles.append(Particle(px, py, ax, ay, life_time, color))
        self.timer = 0

    def update(self, dt: float) -> None:
        self.timer += dt

        if self.timer >= self.max_life_time:
            self.particles = []

        for particle in self.particles:
            if self.timer < particle.life_time:
                particle.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            if self.timer < particle.life_time:
                particle.render(surface)
