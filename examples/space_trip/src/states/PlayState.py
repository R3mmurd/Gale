import pygame

from gale.input_handler import InputData
from gale.particle_system import ParticleSystem
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

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
        self.ending = False

        self.explosion = ParticleSystem(0, 0, 60)
        self.explosion.set_life_time(0.3, 0.7)
        self.explosion.set_linear_acceleration(-60, -60, 60, 60)
        self.explosion.set_area_spread(10, 10)
        self.explosion.set_colors(
            [(255, 220, 120, 255), (255, 140, 60, 220), (200, 70, 40, 180)]
        )

        pygame.mixer.music.play(loops=-1)

    def exit(self) -> None:
        Timer.clear()

    def update(self, dt: float) -> None:
        self.explosion.update(dt)

        if self.ending:
            return

        self.space.update(dt)
        self.flying_saucer.update(dt)

        colling_stars_number = self.space.count_colliding_stars(
            self.flying_saucer.get_collision_rect()
        )
        if colling_stars_number > 0:
            self.score += 100 * colling_stars_number

        if self.space.has_colliding_rock(self.flying_saucer.get_collision_rect()):
            self._lose()
        elif self.score >= settings.SCORE_TO_WIN:
            self._win()

    def _win(self) -> None:
        self.ending = True
        pygame.mixer.music.stop()
        self.state_machine.change("victory", score=self.score)

    def _lose(self) -> None:
        self.ending = True
        pygame.mixer.music.stop()

        center = self.flying_saucer.position + pygame.Vector2(
            self.flying_saucer.width / 2, self.flying_saucer.height / 2
        )
        self.explosion.x_mean, self.explosion.y_mean = center.x, center.y
        self.explosion.generate()
        settings.SOUNDS["death_flash"].play()

        Timer.after(
            1.2, lambda: self.state_machine.change("game_over", score=self.score)
        )

    def render(self, surface: pygame.Surface) -> None:
        self.space.render(surface)

        if not self.ending:
            self.flying_saucer.render(surface)

        self.explosion.render(surface)

        render_text(
            surface,
            f"score: {self.score}",
            settings.FONTS["stars"],
            10,
            10,
            (255, 255, 0),
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.ending:
            return

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
