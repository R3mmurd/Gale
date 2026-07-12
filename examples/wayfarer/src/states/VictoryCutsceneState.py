import pygame

from gale.animation import Animation
from gale.cutscene import Cutscene, Dialogue, MoveActor, SetActorAnimation
from gale.input_handler import InputData
from gale.sequence import StepGroup
from gale.state import BaseState
from gale.text import render_text

import settings


class VictoryCutsceneState(BaseState):
    """
    Triggered by Quest.on_completed (see src/quests.py and
    Wayfarer._on_wolf_trouble_completed) once "wolf_trouble" finishes
    its last stage: the Elder thanks the Hero, then the tale returns
    to the title screen.
    """

    def enter(self) -> None:
        game = self.state_machine.game
        self.hero = game.hero
        self.elder = game.elder

        self.elder.animation = Animation(["idle"])

        font = settings.FONTS["medium"]
        thanks_animation = Animation(["thanks"])

        self.cutscene = Cutscene(
            [
                StepGroup(
                    [
                        MoveActor(
                            self.hero, target=settings.HERO_MEET_ELDER, duration=1.0
                        ),
                        SetActorAnimation(self.elder, thanks_animation),
                    ]
                ),
                Dialogue(
                    "Elder",
                    "You've done it! The village is safe thanks to you.",
                    font,
                    advance_on_input="confirm",
                ),
                Dialogue(
                    "Hero",
                    "Just doing what needed to be done.",
                    font,
                    advance_on_input="confirm",
                ),
                Dialogue(
                    "Elder",
                    "Rest now, Wayfarer. Your journey here is complete.",
                    font,
                    advance_on_input="confirm",
                ),
            ],
            actors=[self.hero, self.elder],
            on_finished=lambda: self.state_machine.change("title"),
        )

    def update(self, dt: float) -> None:
        self.cutscene.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.cutscene.render(surface)
        render_text(
            surface,
            "Enter/Space to advance",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.cutscene.on_input(input_id, input_data)
