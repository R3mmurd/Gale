import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings


class FullTimeState(BaseState):
    def enter(self, score_a: int = 0, score_b: int = 0) -> None:
        self.score_a = score_a
        self.score_b = score_b

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        render_text(
            surface,
            "Full time",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 - 30,
            settings.COLOR_TEXT,
            center=True,
        )
        render_text(
            surface,
            f"A {self.score_a} - {self.score_b} B",
            settings.FONTS["large"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 6,
            settings.COLOR_FLASH,
            center=True,
        )
        render_text(
            surface,
            "Press Enter for a new match",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 40,
            settings.COLOR_TEXT,
            center=True,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("title")
