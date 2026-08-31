"""
Campfire: two logs crossed over a bed of embers, continuously feeding
gale.timer.Timer.every to spawn short-lived gale.particle_system.
ParticleSystem bursts -- sharp, shaped flame particles (SHAPE_TRIANGLE/
SHAPE_DIAMOND) rising over soft, textured smoke (a procedurally
generated blob, tinted grey). A burst is itself a one-shot effect, so
stacking many overlapping ones on a timer is how gale.particle_system
is meant to model a *continuous* effect like a flame or a smoke column.
"""

from typing import List

import pygame

from gale.particle_system import ParticleSystem
from gale.timer import Timer

import settings
from src.textures import make_soft_blob


class Campfire:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y

        self._smoke_texture: pygame.Surface = make_soft_blob(
            settings.SMOKE_TEXTURE_SIZE
        )

        self.flame_systems: List[ParticleSystem] = []
        self.smoke_systems: List[ParticleSystem] = []

        # Tagging both timers with this Campfire as their group means
        # a single Timer.clear(group=self) would stop every burst this
        # campfire has scheduled -- for instance if the fire gets
        # extinguished mid-game -- without touching anything else
        # Timer is tracking (the waterfall's own bursts, included).
        Timer.every(settings.FLAME_SPAWN_INTERVAL, self._spawn_flame, group=self)
        Timer.every(settings.SMOKE_SPAWN_INTERVAL, self._spawn_smoke, group=self)

    def _spawn_flame(self) -> None:
        system = ParticleSystem(self.x, self.y, n=settings.FLAME_PARTICLES_PER_BURST)
        system.on_finish = lambda: self.flame_systems.remove(system)
        system.set_life_time(*settings.FLAME_LIFE_TIME)
        system.set_linear_acceleration(*settings.FLAME_ACCELERATION)
        system.set_colors(settings.FLAME_COLORS)
        system.set_area_spread(*settings.FLAME_SPREAD)
        system.set_shapes(settings.FLAME_SHAPES)
        system.set_size(*settings.FLAME_SIZE)
        system.set_angular_velocity(*settings.FLAME_ANGULAR_VELOCITY)
        system.generate()
        self.flame_systems.append(system)

    def _spawn_smoke(self) -> None:
        system = ParticleSystem(
            self.x,
            self.y - settings.SMOKE_Y_OFFSET,
            n=settings.SMOKE_PARTICLES_PER_BURST,
        )
        system.on_finish = lambda: self.smoke_systems.remove(system)
        system.set_life_time(*settings.SMOKE_LIFE_TIME)
        system.set_linear_acceleration(*settings.SMOKE_ACCELERATION)
        system.set_colors(settings.SMOKE_COLORS)
        system.set_area_spread(*settings.SMOKE_SPREAD)
        system.set_textures([self._smoke_texture])
        system.set_size(*settings.SMOKE_SIZE)
        system.set_angular_velocity(*settings.SMOKE_ANGULAR_VELOCITY)
        system.generate()
        self.smoke_systems.append(system)

    def update(self, dt: float) -> None:
        for system in (*self.flame_systems, *self.smoke_systems):
            system.update(dt)

    def _render_logs(self, surface: pygame.Surface) -> None:
        half = 16
        pygame.draw.line(
            surface,
            settings.COLOR_LOG,
            (self.x - half, self.y + 6),
            (self.x + half, self.y - 2),
            4,
        )
        pygame.draw.line(
            surface,
            settings.COLOR_LOG,
            (self.x - half, self.y - 2),
            (self.x + half, self.y + 6),
            4,
        )

    def render(self, surface: pygame.Surface) -> None:
        self._render_logs(surface)

        # Smoke behind the flame, for a bit of depth.
        for system in self.smoke_systems:
            system.render(surface)

        for system in self.flame_systems:
            system.render(surface)
