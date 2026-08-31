"""
Waterfall: a rock ledge with water spray falling from its lip into a
splash at the pool below. The spray combines shapes and a texture on
the very same gale.particle_system.ParticleSystem -- set_shapes and
set_textures both configured together -- so each generated droplet
independently draws either a plain SHAPE_CIRCLE/SHAPE_LINE or the
soft, tinted blob texture, mixing crisp droplets with soft ones in
the same burst.
"""

from typing import List

import pygame

from gale.particle_system import ParticleSystem, SHAPE_CIRCLE
from gale.timer import Timer

import settings
from src.textures import make_soft_blob


class Waterfall:
    def __init__(self, x: float, top_y: float, bottom_y: float) -> None:
        self.x: float = x
        self.top_y: float = top_y
        self.bottom_y: float = bottom_y

        self._droplet_texture: pygame.Surface = make_soft_blob(
            settings.SPRAY_TEXTURE_SIZE
        )

        self.spray_systems: List[ParticleSystem] = []
        self.splash_systems: List[ParticleSystem] = []

        # Same group trick as Campfire: Timer.clear(group=self) would
        # stop this waterfall alone.
        Timer.every(settings.SPRAY_SPAWN_INTERVAL, self._spawn_spray, group=self)
        Timer.every(settings.SPLASH_SPAWN_INTERVAL, self._spawn_splash, group=self)

    def _spawn_spray(self) -> None:
        system = ParticleSystem(
            self.x, self.top_y, n=settings.SPRAY_PARTICLES_PER_BURST
        )
        system.on_finish = lambda: self.spray_systems.remove(system)
        system.set_life_time(*settings.SPRAY_LIFE_TIME)
        system.set_linear_acceleration(*settings.SPRAY_ACCELERATION)
        system.set_colors(settings.SPRAY_COLORS)
        system.set_area_spread(*settings.SPRAY_SPREAD)
        # Combining both pools: some droplets in this very burst come
        # out as a plain shape, others as the tinted texture.
        system.set_shapes(settings.SPRAY_SHAPES)
        system.set_textures([self._droplet_texture])
        system.set_size(*settings.SPRAY_SIZE)
        system.generate()
        self.spray_systems.append(system)

    def _spawn_splash(self) -> None:
        system = ParticleSystem(
            self.x, self.bottom_y, n=settings.SPLASH_PARTICLES_PER_BURST
        )
        system.on_finish = lambda: self.splash_systems.remove(system)
        system.set_life_time(*settings.SPLASH_LIFE_TIME)
        system.set_linear_acceleration(*settings.SPLASH_ACCELERATION)
        system.set_colors(settings.SPLASH_COLORS)
        system.set_area_spread(*settings.SPLASH_SPREAD)
        system.set_shapes([SHAPE_CIRCLE])
        system.set_size(*settings.SPLASH_SIZE)
        system.generate()
        self.splash_systems.append(system)

    def update(self, dt: float) -> None:
        for system in (*self.spray_systems, *self.splash_systems):
            system.update(dt)

    def _render_scenery(self, surface: pygame.Surface) -> None:
        half_width = settings.WATERFALL_WIDTH / 2

        pygame.draw.polygon(
            surface,
            settings.COLOR_ROCK,
            [
                (self.x - half_width - 10, self.top_y - 10),
                (self.x + half_width + 10, self.top_y - 10),
                (self.x + half_width + 4, self.bottom_y),
                (self.x - half_width - 4, self.bottom_y),
            ],
        )
        pygame.draw.polygon(
            surface,
            settings.COLOR_ROCK_SHADOW,
            [
                (self.x - half_width - 10, self.top_y - 10),
                (self.x - half_width + 6, self.top_y - 10),
                (self.x - half_width, self.bottom_y),
                (self.x - half_width - 4, self.bottom_y),
            ],
        )
        pygame.draw.ellipse(
            surface,
            settings.COLOR_POOL,
            pygame.Rect(self.x - half_width - 20, self.bottom_y - 6, 100, 20),
        )

    def render(self, surface: pygame.Surface) -> None:
        self._render_scenery(surface)

        for system in self.spray_systems:
            system.render(surface)

        for system in self.splash_systems:
            system.render(surface)
