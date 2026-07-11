import pygame

from gale.game import Game
from gale.input_handler import InputData
from gale.state import StateMachine

import settings
from src.states import GameOverState, LobbyState, PlayState, TitleState


class Circuit(Game):
    def init(self) -> None:
        try:
            settings.CURSORS["pointer"].set_as_system_cursor()
        except pygame.error:
            # Not every video driver supports custom cursors (notably
            # the "dummy" one used for headless testing); the game is
            # fully playable with the OS default cursor either way.
            pass

        self.state_machine = StateMachine(
            {
                "title": TitleState,
                "lobby": LobbyState,
                "play": PlayState,
                "game_over": GameOverState,
            }
        )
        self.state_machine.change("title")

    def update(self, dt: float) -> None:
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_machine.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "quit" and input_data.pressed:
            self.quit()
        else:
            self.state_machine.on_input(input_id, input_data)
