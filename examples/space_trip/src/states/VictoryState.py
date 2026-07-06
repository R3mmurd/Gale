import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings


class VictoryState(BaseState):
    def enter(self, score: int = 0) -> None:
        self.score = score

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("start")

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["background"], (0, 0))
        render_text(
            surface,
            "YOU MADE IT!",
            settings.FONTS["stars_title"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 - 40,
            (255, 255, 0),
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            f"Final score: {self.score}",
            settings.FONTS["stars"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 20,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "Press Enter to continue",
            settings.FONTS["stars"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 50,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )
