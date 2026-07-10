import pygame

from gale.camera import Camera
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text
from gale.tilemap import load_tiled_map

import settings
from src.Coin import Coin
from src.Player import Player


class PlayState(BaseState):
    def enter(self) -> None:
        self.tilemap = load_tiled_map(settings.LEVEL_PATH)

        spawns = self.tilemap.object_layers["spawns"]
        player_start = next(obj for obj in spawns if obj.type == "spawn")
        self.player = Player(player_start.x, player_start.y)

        self.coins = [Coin(obj.x, obj.y) for obj in spawns if obj.type == "coin"]
        self.collected_count = 0

        goal = next(obj for obj in spawns if obj.type == "goal")
        self.goal_rect = pygame.Rect(goal.x, goal.y, goal.width, goal.height)
        self.won = False

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.bounds = pygame.Rect(
            0, 0, self.tilemap.pixel_width, self.tilemap.pixel_height
        )
        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

    def update(self, dt: float) -> None:
        if self.won:
            return

        self.player.update(dt, self.tilemap, "ground")
        self.camera.update(dt)

        for coin in self.coins:
            if not coin.collected and coin.touches(self.player.get_rect()):
                coin.collected = True
                self.collected_count += 1

        all_coins_collected = self.collected_count == len(self.coins)

        if all_coins_collected and self.player.get_rect().colliderect(self.goal_rect):
            self.won = True
            self.state_machine.change("win")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self.tilemap.render(surface, self.camera)

        goal_dest = self.camera.apply(self.goal_rect)
        pygame.draw.rect(surface, settings.COLOR_GOAL, goal_dest)

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
        elif input_id == "jump" and input_data.pressed:
            self.player.jump()
