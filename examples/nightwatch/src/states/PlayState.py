from typing import Any, Dict

import pygame

from gale.ai.blackboard import Blackboard
from gale.factory import Factory
from gale.input_handler import InputData
from gale.particle_system import ParticleSystem
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src import level
from src.entities import Civilian, Guard, Player

MOVEMENT_INPUTS = {
    "move_left": (-1, 0),
    "move_right": (1, 0),
    "move_up": (0, -1),
    "move_down": (0, 1),
}


class PlayState(BaseState):
    def enter(self) -> None:
        extra_points = [
            level.PLAYER_START,
            level.EXIT_RECT.center,
            level.CIVILIAN_START,
        ]
        for point_a, point_b in level.GUARD_PATROLS:
            extra_points.append(point_a)
            extra_points.append(point_b)
        self.nav_graph = level.build_nav_graph(extra_points)

        self.blackboard = Blackboard({"alert_position": None, "is_alerted": False})
        self.blackboard.observe("is_alerted", self._on_alert_changed)

        player_factory = Factory(Player)
        self.player = player_factory.create(*level.PLAYER_START)

        guard_factory = Factory(Guard)
        self.guards = [
            guard_factory.create(
                patrol_a[0],
                patrol_a[1],
                {
                    "patrol_points": (patrol_a, patrol_b),
                    "player": self.player,
                    "nav_graph": self.nav_graph,
                    "blackboard": self.blackboard,
                },
            )
            for patrol_a, patrol_b in level.GUARD_PATROLS
        ]

        civilian_factory = Factory(Civilian)
        self.civilian = civilian_factory.create(
            *level.CIVILIAN_START, {"guards": self.guards}
        )

        self._keys_held: Dict[str, bool] = {key: False for key in MOVEMENT_INPUTS}

        self.particle_system = ParticleSystem(0, 0, 40)
        self.particle_system.set_life_time(0.3, 0.6)
        self.particle_system.set_linear_acceleration(-40, -40, 40, 40)
        self.particle_system.set_area_spread(6, 6)

        self.ending = False
        self.alert_flash_timer = 0.0

        self.fade_alpha = 255
        Timer.tween(0.5, [(self, {"fade_alpha": 0})])

    def exit(self) -> None:
        Timer.clear()

    def _on_alert_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        if new_value and not old_value:
            self.alert_flash_timer = 1.5
            # This is a one-shot "spotted" pulse: reset it almost right
            # away so the next sighting can trigger the flash again too.
            Timer.after(0.15, lambda: self.blackboard.set("is_alerted", False))

    def _update_player_input_direction(self) -> None:
        direction = pygame.Vector2()

        for input_id, (dx, dy) in MOVEMENT_INPUTS.items():
            if self._keys_held[input_id]:
                direction.x += dx
                direction.y += dy

        self.player.set_input_direction(direction.x, direction.y)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id in MOVEMENT_INPUTS:
            if input_data.pressed:
                self._keys_held[input_id] = True
            elif input_data.released:
                self._keys_held[input_id] = False

            self._update_player_input_direction()
        elif input_id == "restart" and input_data.pressed:
            self.state_machine.change("play")

    def _end(self, next_state: str) -> None:
        if self.ending:
            return

        self.ending = True
        self.particle_system.x_mean = self.player.position.x
        self.particle_system.y_mean = self.player.position.y
        color = (
            settings.COLOR_ALERT_TEXT
            if next_state == "game_over"
            else settings.COLOR_EXIT
        )
        self.particle_system.set_colors([(*color, 220), (*color, 255)])
        self.particle_system.generate()
        Timer.after(0.6, lambda: self.state_machine.change(next_state))

    def update(self, dt: float) -> None:
        self.particle_system.update(dt)

        if self.alert_flash_timer > 0:
            self.alert_flash_timer -= dt

        if self.ending:
            return

        self.player.update(dt)
        self.civilian.update(dt)

        for guard in self.guards:
            guard.update(dt)

            if (
                guard.position - self.player.position
            ).length() <= settings.CATCH_RADIUS:
                self._end("game_over")

        if level.EXIT_RECT.collidepoint(self.player.position):
            self._end("victory")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        level.render(surface, self.nav_graph)

        self.civilian.render(surface)

        for guard in self.guards:
            guard.render(surface)

        self.player.render(surface)
        self.particle_system.render(surface)

        render_text(
            surface,
            "WASD/Arrows: move   Ctrl+R: restart",
            settings.FONTS["small"],
            8,
            settings.VIRTUAL_HEIGHT - 20,
            settings.COLOR_TEXT,
        )

        if self.alert_flash_timer > 0:
            render_text(
                surface,
                "SPOTTED!",
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH // 2,
                20,
                settings.COLOR_ALERT_TEXT,
                center=True,
            )

        if self.fade_alpha > 0:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.fade_alpha)))
            surface.blit(overlay, (0, 0))
