import pygame

from gale.input_handler import InputData
from gale.physics.world import World
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Car import Car
from src.Terrain import Terrain


class PlayState(BaseState):
    def enter(self) -> None:
        self.world = World(gravity=settings.GRAVITY)
        self.terrain = Terrain(self.world)
        start_y = settings.terrain_height(settings.CHASSIS_START_X) - 30
        self.car = Car(self.world, settings.CHASSIS_START_X, start_y)
        self.accelerating = False
        self.reversing = False
        self.ended = False

    def update(self, dt: float) -> None:
        if self.ended:
            return

        direction = int(self.accelerating) - int(self.reversing)
        self.car.drive(direction)
        self.world.update(dt)

        if self.car.chassis.position.x >= settings.GOAL_X:
            self.ended = True
            self.state_machine.change("win")
        elif self.car.has_flipped():
            self.ended = True
            self.state_machine.change("game_over")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.terrain.render(surface)
        self.car.render(surface)
        render_text(
            surface,
            "Right/D to accelerate, Left/A to reverse",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.ended:
            return

        if input_id == "accelerate":
            self.accelerating = input_data.pressed
        elif input_id == "reverse":
            self.reversing = input_data.pressed
