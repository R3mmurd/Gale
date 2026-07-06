import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings


class StartState(BaseState):
    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("play")

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["background"], (0, 0))
        render_text(
            surface,
            "SPACE TRIP",
            settings.FONTS["stars_title"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 - 40,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "Collect stars, dodge the rocks.",
            settings.FONTS["stars"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 20,
            (255, 255, 0),
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            f"Reach {settings.SCORE_TO_WIN} points to win",
            settings.FONTS["stars"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 50,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )
        render_text(
            surface,
            "Press Enter to start",
            settings.FONTS["stars"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 75,
            (255, 255, 255),
            center=True,
            shadowed=True,
        )
