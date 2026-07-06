import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.ui.container import Container
from gale.ui.label import Label
from gale.ui.list_view import ListView
from gale.ui.manager import UIManager
from gale.ui.panel import Panel

import settings


class TitleState(BaseState):
    def enter(self) -> None:
        menu_width, menu_height = 200, 120
        menu_x = settings.VIRTUAL_WIDTH / 2 - menu_width / 2
        menu_y = settings.VIRTUAL_HEIGHT / 2 - menu_height / 2 + 20

        root = Container(
            0,
            0,
            settings.VIRTUAL_WIDTH,
            settings.VIRTUAL_HEIGHT,
            children=[
                Label(
                    settings.VIRTUAL_WIDTH / 2,
                    settings.VIRTUAL_HEIGHT / 2 - 60,
                    "Rally",
                    font=settings.FONTS["large"],
                    center=True,
                ),
                Container(
                    menu_x,
                    menu_y,
                    menu_width,
                    menu_height,
                    children=[
                        Panel(menu_x, menu_y, menu_width, menu_height),
                        ListView(
                            menu_x + 8,
                            menu_y + 8,
                            menu_width - 16,
                            menu_height - 16,
                            items=[
                                ("Host Game", self._host),
                                ("Join Game", self._join),
                                ("Quit", self._quit),
                            ],
                        ),
                    ],
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
            navigate_actions={"move_up": (0, -1), "move_down": (0, 1)},
        )

    def _host(self) -> None:
        self.state_machine.change("lobby", is_host=True)

    def _join(self) -> None:
        self.state_machine.change("lobby", is_host=False)

    def _quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt: float) -> None:
        self.ui.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.ui.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.ui.on_input(input_id, input_data)
