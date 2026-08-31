"""
This file contains the classes Particle (a single point with
position/acceleration/velocity/lifetime, using numpy for the physics
integration) and ParticleSystem, spawning and managing bursts of them
— explosions, sparks, trails, and similar effects.

A particle's appearance is either a geometric shape (SHAPE_CIRCLE by
default, plus SHAPE_SQUARE/SHAPE_TRIANGLE/SHAPE_DIAMOND/SHAPE_STAR/
SHAPE_LINE — see PARTICLE_SHAPES) or a texture (any pygame.Surface,
tinted by the particle's own color through BLEND_RGBA_MULT, the same
"multiply a greyscale/white texture by a per-particle color" technique
Unity/Godot particle systems use); a texture always takes precedence
over a shape when both are set on a single particle. ParticleSystem's
set_shapes/set_textures let a single burst mix both — each generated
particle draws its own appearance from the combined pool, the same
way it already draws its own color from set_colors — so, for
instance, an explosion can combine sharp geometric sparks with a soft
textured smoke puff in the same effect.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math

from typing import Callable, Dict, List, Optional, Union

import numpy as np

import pygame


def _draw_circle(surface: pygame.Surface, color: pygame.Color, size: int) -> None:
    pygame.draw.circle(surface, color, (size // 2, size // 2), size // 2)


def _draw_square(surface: pygame.Surface, color: pygame.Color, size: int) -> None:
    surface.fill(color)


def _draw_triangle(surface: pygame.Surface, color: pygame.Color, size: int) -> None:
    points = [(size / 2, 0), (size, size), (0, size)]
    pygame.draw.polygon(surface, color, points)


def _draw_diamond(surface: pygame.Surface, color: pygame.Color, size: int) -> None:
    points = [(size / 2, 0), (size, size / 2), (size / 2, size), (0, size / 2)]
    pygame.draw.polygon(surface, color, points)


def _draw_star(surface: pygame.Surface, color: pygame.Color, size: int) -> None:
    center = size / 2
    outer_radius = size / 2
    inner_radius = outer_radius * 0.5
    points = []

    for i in range(10):
        angle = math.pi / 5 * i - math.pi / 2
        radius = outer_radius if i % 2 == 0 else inner_radius
        points.append(
            (center + radius * math.cos(angle), center + radius * math.sin(angle))
        )

    pygame.draw.polygon(surface, color, points)


def _draw_line(surface: pygame.Surface, color: pygame.Color, size: int) -> None:
    width = max(1, size // 4)
    pygame.draw.line(surface, color, (size / 2, 0), (size / 2, size), width)


SHAPE_CIRCLE = "circle"
SHAPE_SQUARE = "square"
SHAPE_TRIANGLE = "triangle"
SHAPE_DIAMOND = "diamond"
SHAPE_STAR = "star"
SHAPE_LINE = "line"

PARTICLE_SHAPES: Dict[str, Callable[[pygame.Surface, pygame.Color, int], None]] = {
    SHAPE_CIRCLE: _draw_circle,
    SHAPE_SQUARE: _draw_square,
    SHAPE_TRIANGLE: _draw_triangle,
    SHAPE_DIAMOND: _draw_diamond,
    SHAPE_STAR: _draw_star,
    SHAPE_LINE: _draw_line,
}


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        ax: float,
        ay: float,
        life_time: float,
        color: pygame.Color,
        shape: str = SHAPE_CIRCLE,
        texture: Optional[pygame.Surface] = None,
        size: float = 4.0,
        angular_velocity: float = 0.0,
    ) -> None:
        """
        Set the initial value for a particle

        :param x: X position.
        :param y: Y position.
        :param ax: X acceleration.
        :param ay: Y acceleration.
        :param life_time: duration in seconds of the particle.
        :param color: render color. Also tints texture, when given, through BLEND_RGBA_MULT.
        :param shape: One of PARTICLE_SHAPES' keys. Ignored when texture is given. The default value is SHAPE_CIRCLE, matching every particle drawn before shapes/textures existed.
        :param texture: A surface to render instead of shape. The default value is None.
        :param size: Side length, in pixels, of the square the particle is drawn/rotated within. The default value is 4.0, matching the fixed size every particle rendered at before this was configurable.
        :param angular_velocity: Degrees per second this particle spins at. The default value is 0.0 (no rotation), matching every particle before rotation existed.
        :raises RuntimeError: If shape is not a key of PARTICLE_SHAPES.
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

        if shape not in PARTICLE_SHAPES:
            raise RuntimeError(f"{shape} is not a valid particle shape")

        self.shape: str = shape
        self.texture: Optional[pygame.Surface] = texture
        self.size: float = size
        self.angle: float = 0.0
        self.angular_velocity: float = angular_velocity

    def update(self, dt: float) -> None:
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx
        self.y += self.vy
        self.angle += self.angular_velocity * dt

    def _build_image(self, size: int) -> pygame.Surface:
        if self.texture is not None:
            tinted = self.texture.copy()
            tinted.fill(self.color, special_flags=pygame.BLEND_RGBA_MULT)
            return tinted

        # Per-pixel alpha (SRCALPHA), starting fully transparent, so
        # whatever the shape function doesn't draw over stays
        # invisible -- a shape rarely fills its whole size x size box
        # (a triangle/diamond/star leaves its corners empty, and even
        # a circle leaves its four corners just outside it), and a
        # rotated image's own newly-exposed corners need to stay
        # transparent too. A plain (non-SRCALPHA) surface with only a
        # whole-surface set_alpha() would instead paint every one of
        # those untouched pixels a solid, semi-transparent black.
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        PARTICLE_SHAPES[self.shape](image, self.color, size)
        return image

    def render(self, surface: pygame.Surface) -> None:
        size = int(round(self.size))
        image = self._build_image(size)

        if self.angle:
            center = (self.x + size / 2, self.y + size / 2)
            image = pygame.transform.rotate(image, self.angle)
            rect = image.get_rect(center=(int(center[0]), int(center[1])))
            surface.blit(image, rect)
        else:
            surface.blit(image, (int(self.x), int(self.y)))


class ParticleSystem:
    def __init__(
        self, x: float, y: float, n: int, on_finish: Optional[Callable[[], None]] = None
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
        self.x_desv: float = 1
        self.y_desv: float = 1

        self.colors: List[pygame.Color] = []
        self.shapes: List[str] = []
        self.textures: List[pygame.Surface] = []
        self.min_particle_size: float = 4.0
        self.max_particle_size: float = 4.0
        self.min_angular_velocity: float = 0.0
        self.max_angular_velocity: float = 0.0

        self.particles: List[Particle] = []

        self.on_finish = on_finish or (lambda: None)

    def set_life_time(self, minimum: float, maximum: float) -> None:
        self.min_life_time = minimum
        self.max_life_time = maximum

    def set_linear_acceleration(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> None:
        self.ax1 = x1
        self.ay1 = y1
        self.ax2 = x2
        self.ay2 = y2

    def set_colors(self, colors: List[pygame.Color]) -> None:
        self.colors = colors

    def set_area_spread(self, rx: float, ry: float) -> None:
        self.x_desv = rx
        self.y_desv = ry

    def set_shapes(self, shapes: List[str]) -> None:
        """
        :param shapes: Pool of PARTICLE_SHAPES keys each generated particle may draw its appearance from. Combined with set_textures' pool, if any is set too — see generate(). The default value is [], meaning every particle defaults to SHAPE_CIRCLE.
        """
        self.shapes = shapes

    def set_textures(self, textures: List[pygame.Surface]) -> None:
        """
        :param textures: Pool of surfaces each generated particle may draw its appearance from, tinted by its own color. Combined with set_shapes' pool, if any is set too — see generate(). The default value is [], meaning no particle uses a texture.
        """
        self.textures = textures

    def set_size(self, minimum: float, maximum: float) -> None:
        self.min_particle_size = minimum
        self.max_particle_size = maximum

    def set_angular_velocity(self, minimum: float, maximum: float) -> None:
        self.min_angular_velocity = minimum
        self.max_angular_velocity = maximum

    def generate(self) -> None:
        appearance_pool: List[Union[str, pygame.Surface]] = [
            *self.shapes,
            *self.textures,
        ]

        for _ in range(self.size):
            ax: float = np.random.uniform(self.ax1, self.ax2)
            ay: float = np.random.uniform(self.ay1, self.ay2)
            px: float = np.random.normal(self.x_mean, self.x_desv)
            py: float = np.random.normal(self.y_mean, self.y_desv)
            color: pygame.Color = self.colors[np.random.choice(len(self.colors))]
            life_time: float = np.random.uniform(self.min_life_time, self.max_life_time)
            size: float = np.random.uniform(
                self.min_particle_size, self.max_particle_size
            )
            angular_velocity: float = np.random.uniform(
                self.min_angular_velocity, self.max_angular_velocity
            )

            shape, texture = SHAPE_CIRCLE, None

            if appearance_pool:
                appearance = appearance_pool[np.random.choice(len(appearance_pool))]
                if isinstance(appearance, pygame.Surface):
                    texture = appearance
                else:
                    shape = appearance

            self.particles.append(
                Particle(
                    px,
                    py,
                    ax,
                    ay,
                    life_time,
                    color,
                    shape=shape,
                    texture=texture,
                    size=size,
                    angular_velocity=angular_velocity,
                )
            )

    def update(self, dt: float) -> None:
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
        for particle in self.particles:
            if self.timer < particle.life_time:
                particle.render(surface)
