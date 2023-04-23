import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.FlyingSaucer import FlyingSaucer
from src.Space import Space


class PlayState(BaseState):
    def enter(self) -> None:
        self.space = Space()
        self.flying_saucer = FlyingSaucer(
            settings.VIRTUAL_WIDTH // 2, settings.VIRTUAL_HEIGHT // 2
        )
        self.score = 0
        pygame.mixer.music.play(loops=-1)

    def update(self, dt: float) -> None:
        self.space.update(dt)
        self.flying_saucer.update(dt)

        colling_stars_number = self.space.count_colliding_stars(
            self.flying_saucer.get_collision_rect()
        )
        if colling_stars_number > 0:
            self.score += 100 * colling_stars_number

    def render(self, surface: pygame.Surface) -> None:
        self.space.render(surface)
        self.flying_saucer.render(surface)
        render_text(
            surface,
            f"score: {self.score}",
            settings.FONTS["stars"],
            10,
            10,
            (255, 255, 0),
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "left":
            if input_data.pressed:
                self.flying_saucer.accelerate(-1, 0)
            elif input_data.released and self.flying_saucer.velocity.x < 0:
                self.flying_saucer.accelerate(0, 0)
        if input_id == "right":
            if input_data.pressed:
                self.flying_saucer.accelerate(1, 0)
            elif input_data.released and self.flying_saucer.velocity.x > 0:
                self.flying_saucer.accelerate(0, 0)
        if input_id == "up":
            if input_data.pressed:
                self.flying_saucer.accelerate(0, -1)
            elif input_data.released and self.flying_saucer.velocity.y < 0:
                self.flying_saucer.accelerate(0, 0)
        if input_id == "down":
            if input_data.pressed:
                self.flying_saucer.accelerate(0, 1)
            elif input_data.released and self.flying_saucer.velocity.y > 0:
                self.flying_saucer.accelerate(0, 0)
