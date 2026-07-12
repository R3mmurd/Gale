import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Herb import Herb
from src.Wolf import Wolf


class PlayState(BaseState):
    """
    Free-roam play: the Hero (moved with the same Actor the intro
    cutscene just walked up to the Elder) collects herbs and defeats
    the wolf, both reported to the shared QuestLog as they happen --
    the game decides what "progress" means and calls notify() itself,
    gale.quest never hardcodes any of it. A small HUD, built entirely
    on top of the generic QuestLog/Quest/Stage/Objective API, shows
    the active quest and its current stage's objectives.
    """

    def enter(self) -> None:
        game = self.state_machine.game
        self.hero = game.hero
        self.elder = game.elder
        self.quest_log = game.quest_log

        self.hero.velocity = pygame.Vector2(0, 0)
        self.hero.clamp_to_world()

        self.herbs = [Herb(*position) for position in settings.HERB_POSITIONS]
        self.wolf = Wolf(*settings.WOLF_POS)

        self.quest_log.start("wolf_trouble")

    def update(self, dt: float) -> None:
        self.hero.update(dt)
        self.hero.clamp_to_world()

        for herb in self.herbs:
            if not herb.collected and herb.touches(
                self.hero.position, self.hero.radius
            ):
                herb.collected = True
                self.quest_log.notify("herbs_collected", 1)

        self.quest_log.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        pygame.draw.rect(
            surface,
            settings.COLOR_GROUND,
            pygame.Rect(0, 0, settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT),
        )

        for decoration in settings.DECORATIONS:
            pygame.draw.rect(surface, settings.COLOR_DECORATION, decoration)

        for herb in self.herbs:
            herb.render(surface)

        self.wolf.render(surface)
        self.elder.render(surface)
        self.hero.render(surface)

        self._render_hud(surface)

    def _render_hud(self, surface: pygame.Surface) -> None:
        if self.quest_log.is_completed("wolf_trouble"):
            render_text(
                surface,
                "Wolf Trouble -- complete!",
                settings.FONTS["small"],
                8,
                8,
                settings.COLOR_QUEST_DONE,
            )
            return

        if not self.quest_log.is_active("wolf_trouble"):
            return

        quest = self.quest_log.get("wolf_trouble")
        render_text(
            surface,
            quest.title,
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_QUEST_TITLE,
        )

        y = 24
        for objective in quest.current_stage.steps:
            mark = "x" if objective.is_complete() else " "
            render_text(
                surface,
                f"[{mark}] {objective.description} ({objective.progress}/{objective.target})",
                settings.FONTS["small"],
                8,
                y,
                settings.COLOR_TEXT,
            )
            y += 16

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.quest_log.on_input(input_id, input_data)

        if input_id in ("move_left", "move_right"):
            if input_data.pressed:
                self.hero.velocity.x = (
                    -settings.PLAYER_SPEED
                    if input_id == "move_left"
                    else settings.PLAYER_SPEED
                )
            elif input_data.released:
                sign = -1 if input_id == "move_left" else 1
                if self.hero.velocity.x == sign * settings.PLAYER_SPEED:
                    self.hero.velocity.x = 0
        elif input_id in ("move_up", "move_down"):
            if input_data.pressed:
                self.hero.velocity.y = (
                    -settings.PLAYER_SPEED
                    if input_id == "move_up"
                    else settings.PLAYER_SPEED
                )
            elif input_data.released:
                sign = -1 if input_id == "move_up" else 1
                if self.hero.velocity.y == sign * settings.PLAYER_SPEED:
                    self.hero.velocity.y = 0
        elif input_id == "confirm" and input_data.pressed:
            self._try_interact()

    def _try_interact(self) -> None:
        if not self.wolf.defeated and self.wolf.is_adjacent_to(
            self.hero.position, settings.INTERACT_RADIUS
        ):
            self.wolf.defeated = True
            self.quest_log.notify("wolf_defeated", 1)
            return

        if (
            self.elder.position.distance_to(self.hero.position)
            <= settings.INTERACT_RADIUS
        ):
            self.quest_log.notify("reported", 1)
