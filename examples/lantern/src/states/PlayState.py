import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.stencil import Stencil
from gale.text import render_text
from gale.timer import Timer

import settings
from src.Player import Player
from src.Room import Room


class PlayState(BaseState):
    def enter(self) -> None:
        self.player = Player(*Room.START_POSITION)
        self.torches = Room.create_torches()
        self.torches_found = 0
        self.light_radius = settings.LIGHT_RADIUS_START

        self.stencil = Stencil((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT))
        self.overlay = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )

    def exit(self) -> None:
        Timer.clear()

    def update(self, dt: float) -> None:
        self.player.update(dt, Room.WALLS)

        for torch in self.torches:
            if not torch.collected and torch.touches(
                self.player.x, self.player.y, self.player.radius
            ):
                torch.collected = True
                self.torches_found += 1
                target_radius = self.light_radius + settings.LIGHT_RADIUS_STEP
                Timer.tween(
                    settings.LIGHT_GROW_TIME,
                    [(self, {"light_radius": target_radius})],
                    ease_function_name="out_quad",
                )

        if self.player.get_rect().colliderect(Room.EXIT_RECT):
            self.state_machine.change("win")

    def render(self, surface: pygame.Surface) -> None:
        Room.render(surface)

        for torch in self.torches:
            torch.render(surface)

        self.player.render(surface)

        self._render_darkness(surface)

        render_text(
            surface,
            f"Torches: {self.torches_found}/{len(self.torches)}",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )

    def _render_darkness(self, surface: pygame.Surface) -> None:
        self.stencil.clear()
        self.stencil.draw(
            lambda mask: pygame.draw.circle(
                mask,
                "white",
                (round(self.player.x), round(self.player.y)),
                round(self.light_radius),
            )
        )

        self.overlay.fill((*settings.COLOR_OVERLAY, settings.OVERLAY_ALPHA))
        self.stencil.apply(self.overlay, invert=True)
        surface.blit(self.overlay, (0, 0))

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id in ("move_left", "move_right"):
            if input_data.pressed:
                self.player.vx = (
                    -settings.PLAYER_SPEED
                    if input_id == "move_left"
                    else settings.PLAYER_SPEED
                )
            elif input_data.released:
                sign = -1 if input_id == "move_left" else 1
                if self.player.vx == sign * settings.PLAYER_SPEED:
                    self.player.vx = 0
        elif input_id in ("move_up", "move_down"):
            if input_data.pressed:
                self.player.vy = (
                    -settings.PLAYER_SPEED
                    if input_id == "move_up"
                    else settings.PLAYER_SPEED
                )
            elif input_data.released:
                sign = -1 if input_id == "move_up" else 1
                if self.player.vy == sign * settings.PLAYER_SPEED:
                    self.player.vy = 0
