import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings


class GameOverState(BaseState):
    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("title")
        elif input_id == "restart" and input_data.pressed:
            self.state_machine.change("play")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        render_text(
            surface,
            "CAUGHT!",
            settings.FONTS["large"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 - 20,
            settings.COLOR_ALERT_TEXT,
            center=True,
        )
        render_text(
            surface,
            "Enter for title  -  Ctrl+R to try again",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 30,
            settings.COLOR_TEXT,
            center=True,
        )
