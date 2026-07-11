from typing import Dict, Set

import pygame

from gale.ai.perception import AlertLevel
from gale.factory import Factory
from gale.input_handler import InputData
from gale.particle_system import ParticleSystem
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src import level
from src.entities import Guard, Player

MOVEMENT_INPUTS = {
    "move_left": (-1, 0),
    "move_right": (1, 0),
    "move_up": (0, -1),
    "move_down": (0, 1),
}

INTERACT_RADIUS = settings.CELL_SIZE * 0.7


class PlayState(BaseState):
    def enter(self) -> None:
        self.tilemap = level.build_tilemap()

        extra_points = [level.PLAYER_START, level.TERMINAL_POSITION]
        for point_a, point_b in level.GUARD_PATROLS:
            extra_points.append(point_a)
            extra_points.append(point_b)
        self.nav_graph = level.build_nav_graph(extra_points)

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
                },
            )
            for patrol_a, patrol_b in level.GUARD_PATROLS
        ]

        # Two physical keys are bound to each direction (e.g. move_left is
        # both the left arrow and 'a'); tracking held-ness per input_id as
        # a single bool would make releasing either one clear it even
        # while the other is still physically held down, killing movement
        # under normal two-handed/overlapping key presses. Tracking the
        # actual set of physical keys (input_data.key) currently holding
        # each input_id down fixes that: the direction is only released
        # once every key bound to it is.
        self._keys_held: Dict[str, Set[int]] = {key: set() for key in MOVEMENT_INPUTS}

        self.particle_system = ParticleSystem(0, 0, 40)
        self.particle_system.set_life_time(0.3, 0.6)
        self.particle_system.set_linear_acceleration(-40, -40, 40, 40)
        self.particle_system.set_area_spread(6, 6)

        self.ending = False
        self.caught_flash_timer = 0.0

        self.fade_alpha = 255
        Timer.tween(0.5, [(self, {"fade_alpha": 0})])

    def exit(self) -> None:
        Timer.clear()

    def _update_player_input_direction(self) -> None:
        direction = pygame.Vector2()

        for input_id, (dx, dy) in MOVEMENT_INPUTS.items():
            if self._keys_held[input_id]:
                direction.x += dx
                direction.y += dy

        self.player.set_input_direction(direction.x, direction.y)

    def _near_terminal(self) -> bool:
        return (
            self.player.position - pygame.Vector2(level.TERMINAL_POSITION)
        ).length() <= INTERACT_RADIUS

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.ending:
            return

        if input_id in MOVEMENT_INPUTS:
            if input_data.pressed:
                self._keys_held[input_id].add(input_data.key)
            elif input_data.released:
                self._keys_held[input_id].discard(input_data.key)

            self._update_player_input_direction()
        elif input_id == "confirm" and input_data.pressed and self._near_terminal():
            self.state_machine.change("hack")
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
            else settings.COLOR_GOOD_TEXT
        )
        self.particle_system.set_colors([(*color, 220), (*color, 255)])
        self.particle_system.generate()
        Timer.after(0.6, lambda: self.state_machine.change(next_state))

    def update(self, dt: float) -> None:
        self.particle_system.update(dt)

        if self.caught_flash_timer > 0:
            self.caught_flash_timer -= dt

        if self.ending:
            return

        self.player.update(dt)

        for guard in self.guards:
            guard.update(dt)

            distance = (guard.position - self.player.position).length()

            if (
                guard.alert_level == AlertLevel.ALERTED
                and distance <= settings.CATCH_RADIUS
            ):
                self.caught_flash_timer = 1.0
                self._end("game_over")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        # IsometricTileMap.render draws at raw (unshifted) grid
        # coordinates, while level.to_screen (used for every entity,
        # the nav graph, and this state's own HUD checks) adds
        # settings.MAP_OFFSET. Rendering the tilemap directly onto
        # `surface` would leave it out of alignment with everything
        # else drawn through to_screen -- entities would appear to
        # wander off tiles that are actually elsewhere on screen.
        # Rendering it onto a subsurface positioned at MAP_OFFSET keeps
        # both perfectly in sync.
        tilemap_surface = surface.subsurface(
            pygame.Rect(
                *settings.MAP_OFFSET,
                self.tilemap.pixel_width,
                self.tilemap.pixel_height,
            )
        )
        self.tilemap.render(tilemap_surface)

        for source, target, _ in self.nav_graph.edges:
            pygame.draw.line(
                surface,
                settings.COLOR_NAV_EDGE,
                level.to_screen(*source),
                level.to_screen(*target),
            )

        for guard in self.guards:
            guard.render(surface)

        self.player.render(surface)
        self.particle_system.render(surface)

        render_text(
            surface,
            "WASD/Arrows: move   Enter: interact   Ctrl+R: restart",
            settings.FONTS["small"],
            8,
            settings.VIRTUAL_HEIGHT - 20,
            settings.COLOR_TEXT,
        )

        if self._near_terminal() and not self.ending:
            render_text(
                surface,
                "Press Enter to hack the terminal",
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH // 2,
                20,
                settings.COLOR_TERMINAL_EDGE,
                center=True,
            )

        if self.caught_flash_timer > 0:
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
