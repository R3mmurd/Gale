import pygame

from gale.game import Game
from gale.input_handler import InputData
from gale.state import StateMachine

import settings
from src.Actor import Actor
from src.quests import build_quest_log
from src.states import IntroCutsceneState, PlayState, TitleState, VictoryCutsceneState


class Wayfarer(Game):
    def init(self) -> None:
        self.state_machine = StateMachine(
            {
                "title": TitleState,
                "intro_cutscene": IntroCutsceneState,
                "play": PlayState,
                "victory_cutscene": VictoryCutsceneState,
            }
        )
        # Every state reaches shared session data (the hero/elder actors
        # and the quest log) through the state machine that owns it,
        # rather than each state rebuilding its own copy -- the intro
        # cutscene moves the very same Hero/Elder that free-roam play
        # and the victory cutscene go on to use.
        self.state_machine.game = self
        self.new_session()
        self.state_machine.change("title")

    def new_session(self) -> None:
        self.hero = Actor("Hero", *settings.HERO_INTRO_START, settings.COLOR_HERO)
        self.elder = Actor("Elder", *settings.ELDER_POS, settings.COLOR_ELDER)
        self.quest_log = build_quest_log(self._on_wolf_trouble_completed)

    def _on_wolf_trouble_completed(self) -> None:
        self.state_machine.change("victory_cutscene")

    def update(self, dt: float) -> None:
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_machine.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "quit" and input_data.pressed:
            self.quit()
        else:
            self.state_machine.on_input(input_id, input_data)
