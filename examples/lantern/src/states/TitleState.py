import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings


class TitleState(BaseState):
    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        render_text(
            surface,
            "Lantern",
            settings.FONTS["large"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 - 40,
            settings.COLOR_TEXT,
            center=True,
        )
        render_text(
            surface,
            "Press Enter to start",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 10,
            settings.COLOR_TEXT,
            center=True,
        )
        render_text(
            surface,
            "Arrows/WASD to move",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 30,
            settings.COLOR_TEXT,
            center=True,
        )
        render_text(
            surface,
            "Find the two torches, then the exit, in the dark",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 50,
            settings.COLOR_TEXT,
            center=True,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("play")
