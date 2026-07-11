import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.ui.button import Button
from gale.ui.container import Container
from gale.ui.label import Label
from gale.ui.manager import UIManager

import settings

_WINNER_LABELS = {"host": "Host", "joiner": "Joiner", "ai": "the AI"}


class GameOverState(BaseState):
    def enter(self, is_host: bool, server, client, winner: str, laps: dict) -> None:
        self.server = server
        self.client = client
        my_role = "host" if is_host else "joiner"
        headline = (
            "You win!" if winner == my_role else f"{_WINNER_LABELS[winner]} wins!"
        )

        root = Container(
            0,
            0,
            settings.VIRTUAL_WIDTH,
            settings.VIRTUAL_HEIGHT,
            children=[
                Label(
                    settings.VIRTUAL_WIDTH / 2,
                    settings.VIRTUAL_HEIGHT / 2 - 40,
                    headline,
                    font=settings.FONTS["large"],
                    center=True,
                ),
                Label(
                    settings.VIRTUAL_WIDTH / 2,
                    settings.VIRTUAL_HEIGHT / 2,
                    f"laps - host: {laps.get('host', 0)}"
                    f"  joiner: {laps.get('joiner', 0)}"
                    f"  ai: {laps.get('ai', 0)}",
                    font=settings.FONTS["medium"],
                    center=True,
                ),
                Button(
                    settings.VIRTUAL_WIDTH / 2 - 80,
                    settings.VIRTUAL_HEIGHT / 2 + 40,
                    160,
                    36,
                    "Back to Title",
                    on_click=self._back_to_title,
                ),
            ],
        )
        self.ui = UIManager(
            root,
            virtual_width=settings.VIRTUAL_WIDTH,
            window_width=settings.WINDOW_WIDTH,
            virtual_height=settings.VIRTUAL_HEIGHT,
            window_height=settings.WINDOW_HEIGHT,
            confirm_action="confirm",
        )

    def _back_to_title(self) -> None:
        if self.client is not None:
            self.client.close()

        if self.server is not None:
            self.server.close()

        self.state_machine.change("title")

    def update(self, dt: float) -> None:
        self.ui.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.ui.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.ui.on_input(input_id, input_data)
