"""
This file contains the implementation of a particle systems.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional

import numpy as np

import pygame


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        ax: float,
        ay: float,
        life_time: float,
        color: pygame.Color,
    ) -> None:
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
        self.__x: float = x
        self.__y: float = y

        # Velocity
        self.__vx: float = 0
        self.__vy: float = 0

        # Acceleration
        self.__ax: float = ax
        self.__ay: float = ay

        self.__lifetime: float = life_time
        self.__color: pygame.Color = color

    @property
    def lifetime(self):
        """
        Get the lifetime of the particle.

        @return: The lifetime of the particle.
        """
        return self.__lifetime

    def update(self, dt: float) -> None:
        """
        Update the particle position.

        :param dt: Time elapsed in seconds.
        """
        self.__vx += self.__ax * dt
        self.__vy += self.__ay * dt
        self.__x += self.__vx
        self.__y += self.__vy

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the particle.

        :param surface: The surface where the particle will be rendered.
        """
        s = pygame.Surface((4, 4))
        s.set_alpha(self.__color[3])
        pygame.draw.circle(s, self.__color, (2, 2), 2)
        surface.blit(s, (int(self.__x), int(self.__y)))


class ParticleSystem:
    def __init__(
        self, x: float, y: float, n: int, on_finish: Optional[callable] = None
    ) -> None:
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
        self.x_dev: float = 1
        self.y_dev: float = 1

        self.colors: list[pygame.Color] = []
        self.particles: list[Particle] = []

        self.on_finish = on_finish or (lambda: None)

    def set_life_time(self, minimum: float, maximum: float) -> None:
        """
        Set the lifetime for the particles.

        :param minimum: Minimum lifetime in seconds.
        :param maximum: Maximum lifetime in seconds.
        """
        self.min_life_time = minimum
        self.max_life_time = maximum

    def set_linear_acceleration(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> None:
        """
        Set the linear acceleration for the particles.

        :param x1: Minimum x acceleration.
        :param y1: Minimum y acceleration.
        :param x2: Maximum x acceleration.
        :param y2: Maximum y acceleration.
        """
        self.ax1 = x1
        self.ay1 = y1
        self.ax2 = x2
        self.ay2 = y2

    def set_colors(self, colors: list[pygame.Color]) -> None:
        """
        Set the possible colors for the particles.

        :param colors: List of colors.
        """
        self.colors = colors

    def set_area_spread(self, rx: float, ry: float) -> None:
        """
        Set the spread for the particles.

        :param rx: Spread in x.
        :param ry: Spread in y.
        """
        self.x_dev = rx
        self.y_dev = ry

    def generate(self) -> None:
        """
        Generate the particles.
        """
        for _ in range(self.size):
            ax: float = np.random.uniform(self.ax1, self.ax2)
            ay: float = np.random.uniform(self.ay1, self.ay2)
            px: float = np.random.normal(self.x_mean, self.x_dev)
            py: float = np.random.normal(self.y_mean, self.y_dev)
            color: pygame.Color = self.colors[np.random.choice(len(self.colors))]
            life_time: float = np.random.uniform(self.min_life_time, self.max_life_time)
            self.particles.append(Particle(px, py, ax, ay, life_time, color))

    def update(self, dt: float) -> None:
        """
        Update the particles.

        :param dt: Time elapsed in seconds.
        """
        if len(self.particles) == 0:
            return

        self.timer += dt

        if self.timer >= self.max_life_time:
            self.timer = 0
            self.particles = []
            self.on_finish()

        for particle in self.particles:
            if self.timer < particle.life_time:
                particle.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the particles.

        :param surface: The surface where the particles will be rendered.
        """
        for particle in self.particles:
            if self.timer < particle.lifetime:
                particle.render(surface)
