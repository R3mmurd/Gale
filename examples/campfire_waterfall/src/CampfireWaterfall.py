"""
CampfireWaterfall: a non-interactive ambient scene -- nothing to win,
nothing to control beyond quitting -- built to show off
gale.particle_system's shapes/textures/combination side by side with
gale.timer's groups, driving two continuously-emitting effects at
once. See src/Campfire.py and src/Waterfall.py for how each is built.
"""

import pygame

from gale.game import Game
from gale.input_handler import InputData
from gale.timer import Timer

import settings
from src.Campfire import Campfire
from src.Waterfall import Waterfall


class CampfireWaterfall(Game):
    def init(self) -> None:
        # A fresh start regardless of whatever Timer items a previous
        # run (or, in gale's own test suite, a previous example)
        # might have left scheduled.
        Timer.clear()

        self.campfire = Campfire(settings.CAMPFIRE_X, settings.CAMPFIRE_Y)
        self.waterfall = Waterfall(
            settings.WATERFALL_X, settings.WATERFALL_TOP_Y, settings.WATERFALL_BOTTOM_Y
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "quit" and input_data.pressed:
            self.quit()

    def update(self, dt: float) -> None:
        self.campfire.update(dt)
        self.waterfall.update(dt)

    def _render_background(self, surface: pygame.Surface) -> None:
        # A simple three-band sky gradient -- no image assets, just a
        # handful of filled rects.
        bands = 6
        band_height = self.virtual_height / bands

        for i in range(bands):
            t = i / (bands - 1)
            color = tuple(
                int(top + (bottom - top) * t)
                for top, bottom in zip(
                    settings.COLOR_SKY_TOP, settings.COLOR_SKY_BOTTOM
                )
            )
            pygame.draw.rect(
                surface,
                color,
                pygame.Rect(
                    0, int(i * band_height), self.virtual_width, int(band_height) + 1
                ),
            )

        ground_height = 40
        pygame.draw.rect(
            surface,
            settings.COLOR_GROUND,
            pygame.Rect(
                0,
                self.virtual_height - ground_height,
                self.virtual_width,
                ground_height,
            ),
        )

    def render(self, surface: pygame.Surface) -> None:
        self._render_background(surface)
        self.waterfall.render(surface)
        self.campfire.render(surface)
