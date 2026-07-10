import random

import pygame

from gale.camera import Camera
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Coin import Coin
from src.Player import Player


class PlayState(BaseState):
    def enter(self) -> None:
        self.player = Player(settings.WORLD_WIDTH / 2, settings.WORLD_HEIGHT / 2)

        self.coins = [
            Coin(
                random.uniform(40, settings.WORLD_WIDTH - 40),
                random.uniform(40, settings.WORLD_HEIGHT - 40),
            )
            for _ in range(settings.COIN_COUNT)
        ]
        self.collected_count = 0

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.bounds = pygame.Rect(
            0, 0, settings.WORLD_WIDTH, settings.WORLD_HEIGHT
        )

    def update(self, dt: float) -> None:
        self.player.update(dt)
        self.camera.update(dt)

        for coin in self.coins:
            if not coin.collected and coin.touches(
                self.player.x, self.player.y, self.player.radius
            ):
                coin.collected = True
                self.collected_count += 1
                self.camera.shake(settings.SHAKE_MAGNITUDE, settings.SHAKE_DURATION)

        if self.collected_count == len(self.coins):
            self.state_machine.change("win")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self._render_grid(surface)

        for coin in self.coins:
            coin.render(surface, self.camera)

        self.player.render(surface, self.camera)

        render_text(
            surface,
            f"Coins: {self.collected_count}/{len(self.coins)}",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )
        render_text(
            surface,
            f"Zoom: {self.camera.zoom:.1f}x",
            settings.FONTS["small"],
            8,
            24,
            settings.COLOR_TEXT,
        )

    def _render_grid(self, surface: pygame.Surface) -> None:
        spacing = settings.GRID_SPACING

        for world_x in range(0, settings.WORLD_WIDTH + 1, spacing):
            start = self.camera.world_to_screen((world_x, 0))
            end = self.camera.world_to_screen((world_x, settings.WORLD_HEIGHT))
            pygame.draw.line(surface, settings.COLOR_GRID, start, end)

        for world_y in range(0, settings.WORLD_HEIGHT + 1, spacing):
            start = self.camera.world_to_screen((0, world_y))
            end = self.camera.world_to_screen((settings.WORLD_WIDTH, world_y))
            pygame.draw.line(surface, settings.COLOR_GRID, start, end)

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
        elif input_id == "zoom_in" and input_data.pressed:
            self.camera.zoom = min(
                settings.CAMERA_MAX_ZOOM, self.camera.zoom + settings.CAMERA_ZOOM_STEP
            )
        elif input_id == "zoom_out" and input_data.pressed:
            self.camera.zoom = max(
                settings.CAMERA_MIN_ZOOM, self.camera.zoom - settings.CAMERA_ZOOM_STEP
            )
