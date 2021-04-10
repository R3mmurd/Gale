"""
This file contains the implementation of a particle systems.

Author: Alejandro Mujica (aledrums@gmail.com)
"""
import random

import pygame


class Particle:
    def __init__(self, x, y, ax, ay, life_time, color):
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
        self.x = x
        self.y = y

        # Velocity
        self.vx = 0
        self.vy = 0

        # Acceleration
        self.ax = ax
        self.ay = ay

        self.life_time = life_time
        self.color = color

    def update(self, dt):
        self.vx += self.ax*dt
        self.vy += self.ay*dt
        self.x += self.vx
        self.y += self.vy 

    def render(self, surface):
        s = pygame.Surface((4, 4))
        s.set_alpha(self.color[3])
        pygame.draw.circle(s, self.color, (2, 2), 2)
        surface.blit(s, (int(self.x), int(self.y)))

class ParticleSystem:
    def __init__(self, x, y, n):
        """
        Builds a particle system.

        :param x: Center x of the system.
        :param y: Center y of the system.
        :param n: Number of particles.
        """
        self.x_mean = x
        self.y_mean = y
        self.size = n

        self.min_life_time = 0
        self.max_life_time = 0
        self.timer = 0
        self.ax1 = 0
        self.ax2 = 0
        self.ay1 = 0
        self.ay2 = 0
        self.x_desv = 1
        self.y_desv = 1

        self.colors = []
        self.particles = []
    
    def set_life_time(self, minimum, maximum):
        self.min_life_time = minimum
        self.max_life_time = maximum

    def set_linear_acceleration(self, x1, y1, x2, y2):
        self.ax1 = x1
        self.ay1 = y1
        self.ax2 = x2
        self.ay2 = y2

    def set_colors(self, colors):
        self.colors = colors

    def set_area_spread(self, rx, ry):
        self.x_desv = rx
        self.y_desv = ry

    def generate(self):
        for _ in range(self.size):
            ax = random.uniform(self.ax1, self.ax2)
            ay = random.uniform(self.ay1, self.ay2)
            px = random.gauss(self.x_mean, self.x_desv)
            py = random.gauss(self.y_mean, self.y_desv)
            color = random.choice(self.colors)
            life_time = random.uniform(self.min_life_time, self.max_life_time)
            self.particles.append(
                Particle(px, py, ax, ay, life_time, color)
            )
        self.timer = 0

    def update(self, dt):
        self.timer += dt

        if self.timer >= self.max_life_time:
            self.particles = []

        for particle in self.particles:
            if self.timer < particle.life_time:
                particle.update(dt)

    def render(self, surface):        
        for particle in self.particles:
            if self.timer < particle.life_time:
                particle.render(surface)

