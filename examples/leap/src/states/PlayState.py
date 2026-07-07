import pygame

from gale.input_handler import InputData
from gale.physics.world import World
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Level import Level
from src.Player import Player


class PlayState(BaseState):
    def enter(self) -> None:
        self.world = World(gravity=settings.GRAVITY)
        self.level = Level(self.world)
        self.player = Player(self.world, 30, 100)
        self.move_direction = 0
        self.ended = False

        self.world.on_collision_begin(self._on_collision_begin)

    def _on_collision_begin(self, body_a, body_b) -> None:
        if self.ended:
            return

        tags = {body_a.user_data, body_b.user_data}

        if "player" in tags and "goal" in tags:
            self.ended = True
            self.state_machine.change("win")

    def update(self, dt: float) -> None:
        if self.ended:
            return

        self.player.move(self.move_direction)
        self.world.update(dt)
        self.level.update(dt)

        if self.player.position.y > settings.VIRTUAL_HEIGHT + 40:
            self.ended = True
            self.state_machine.change("game_over")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.level.render(surface)
        self.player.render(surface)
        render_text(
            surface,
            "Arrows/WASD to move, Space to jump",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.ended:
            return

        if input_id == "move_left":
            if input_data.pressed:
                self.move_direction = -1
            elif input_data.released and self.move_direction < 0:
                self.move_direction = 0
        elif input_id == "move_right":
            if input_data.pressed:
                self.move_direction = 1
            elif input_data.released and self.move_direction > 0:
                self.move_direction = 0
        elif input_id == "jump" and input_data.pressed:
            self.player.jump()
