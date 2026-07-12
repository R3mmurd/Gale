import pygame

from gale.animation import Animation
from gale.cutscene import Cutscene, Dialogue, MoveActor, SetActorAnimation
from gale.input_handler import InputData
from gale.sequence import StepGroup
from gale.state import BaseState
from gale.text import render_text

import settings


class IntroCutsceneState(BaseState):
    """
    Plays automatically when a new session begins: the Hero walks up
    to the Elder while the Elder switches to a "greeting" pose at the
    same time (a StepGroup mixing a duration-based beat with an
    instant one), then a few lines of dialogue advance on the
    "confirm" input. While this state is active, the state machine
    never reaches PlayState, so gameplay movement is naturally
    disabled -- every input is forwarded to the cutscene instead.
    """

    def enter(self) -> None:
        game = self.state_machine.game
        self.hero = game.hero
        self.elder = game.elder

        self.hero.position = pygame.Vector2(settings.HERO_INTRO_START)
        self.hero.animation = Animation(["idle"])
        self.elder.position = pygame.Vector2(settings.ELDER_POS)
        self.elder.animation = Animation(["idle"])

        font = settings.FONTS["medium"]
        greet_animation = Animation(["greet"])

        self.cutscene = Cutscene(
            [
                StepGroup(
                    [
                        MoveActor(
                            self.hero, target=settings.HERO_MEET_ELDER, duration=1.5
                        ),
                        SetActorAnimation(self.elder, greet_animation),
                    ]
                ),
                Dialogue(
                    "Elder",
                    "Ah, you've come. The wolf in the forest has been"
                    " raiding our herb garden.",
                    font,
                    advance_on_input="confirm",
                ),
                Dialogue(
                    "Elder",
                    "Bring me 2 herbs and deal with the wolf, then come"
                    " back and tell me.",
                    font,
                    advance_on_input="confirm",
                ),
                Dialogue(
                    "Hero",
                    "I'll take care of it, Elder.",
                    font,
                    advance_on_input="confirm",
                ),
            ],
            actors=[self.hero, self.elder],
            on_finished=lambda: self.state_machine.change("play"),
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
