from typing import Any, Dict, List

import pygame

from gale.ai.blackboard import Blackboard
from gale.ai.tactical import InfluenceMap
from gale.factory import Factory
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src import level
from src.entities import Captain, Guard, Projectile, Squad

MOVEMENT_INPUTS = {
    "move_left": (-1, 0),
    "move_right": (1, 0),
    "move_up": (0, -1),
    "move_down": (0, 1),
}


class PlayState(BaseState):
    def enter(self) -> None:
        extra_points: List[Any] = [
            level.SQUAD_START,
            level.EXTRACTION_RECT.center,
            level.CAPTAIN_START,
            *level.COVER_POINTS,
        ]
        for point_a, point_b in level.GUARD_PATROLS:
            extra_points.append(point_a)
            extra_points.append(point_b)
        self.nav_graph = level.build_nav_graph(extra_points)
        self.walls = level.build_walls()

        self.blackboard = Blackboard({"is_alerted": False, "alert_position": None})
        self.influence_map = InfluenceMap(
            settings.VIRTUAL_WIDTH,
            settings.VIRTUAL_HEIGHT,
            cell_size=settings.INFLUENCE_CELL_SIZE,
        )

        self.squad = Squad(level.SQUAD_START)

        self.projectiles: List[Projectile] = []

        guard_factory = Factory(Guard)
        self.guards: List[Guard] = []
        for patrol_a, patrol_b in level.GUARD_PATROLS:
            guard = guard_factory.create(
                patrol_a[0],
                patrol_a[1],
                {
                    "patrol_points": (patrol_a, patrol_b),
                    "squad": self.squad,
                    "guards": self.guards,
                    "walls": self.walls,
                    "nav_graph": self.nav_graph,
                    "influence_map": self.influence_map,
                    "blackboard": self.blackboard,
                    "fire_callback": self._on_fire,
                },
            )
            self.guards.append(guard)

        captain_factory = Factory(Captain)
        self.captain = captain_factory.create(
            level.CAPTAIN_START[0],
            level.CAPTAIN_START[1],
            {
                "squad": self.squad,
                "nav_graph": self.nav_graph,
                "influence_map": self.influence_map,
                "blackboard": self.blackboard,
                "fire_callback": self._on_fire,
            },
        )

        self._keys_held: Dict[str, bool] = {key: False for key in MOVEMENT_INPUTS}
        self.ending = False
        self.fade_alpha = 255
        Timer.tween(0.5, [(self, {"fade_alpha": 0})])

    def exit(self) -> None:
        Timer.clear()

    def _on_fire(
        self, kind: str, position: pygame.Vector2, velocity: pygame.Vector2
    ) -> None:
        self.projectiles.append(Projectile(kind, position, velocity))

    def _rebuild_influence_map(self) -> None:
        self.influence_map.clear()

        for guard in self.guards:
            self.influence_map.add_influence(
                guard.position,
                strength=1.0,
                radius=settings.INFLUENCE_RADIUS,
                team="ally",
            )

        self.influence_map.add_influence(
            self.captain.position,
            strength=1.0,
            radius=settings.INFLUENCE_RADIUS,
            team="ally",
        )

        for position in self.squad.all_positions():
            self.influence_map.add_influence(
                position, strength=1.0, radius=settings.INFLUENCE_RADIUS, team="enemy"
            )

        self.influence_map.propagate()

    def _update_player_input_direction(self) -> None:
        direction = pygame.Vector2()

        for input_id, (dx, dy) in MOVEMENT_INPUTS.items():
            if self._keys_held[input_id]:
                direction.x += dx
                direction.y += dy

        self.squad.set_input_direction(direction.x, direction.y)

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
        Timer.after(0.6, lambda: self.state_machine.change(next_state))

    def update(self, dt: float) -> None:
        if self.ending:
            return

        self._rebuild_influence_map()

        self.squad.update(dt)

        for guard in self.guards:
            guard.update(dt)

        alert_count = sum(1 for guard in self.guards if guard.is_alert)
        self.captain.update(dt, alert_count)

        for projectile in self.projectiles:
            projectile.update(dt)

            if projectile.alive:
                for position in self.squad.all_positions():
                    if projectile.hits(position, self.squad.radius):
                        projectile.alive = False
                        self.squad.register_hit()
                        break

        self.projectiles = [p for p in self.projectiles if p.alive]

        if self.squad.hits_taken >= settings.SQUAD_HITS_TO_LOSE:
            self._end("game_over")
        elif level.EXTRACTION_RECT.collidepoint(self.squad.position):
            self._end("victory")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        level.render(surface, self.nav_graph)

        for guard in self.guards:
            guard.render(surface)

        self.captain.render(surface)
        self.squad.render(surface)

        for projectile in self.projectiles:
            projectile.render(surface)

        render_text(
            surface,
            "WASD/Arrows: move to the yellow extraction zone   Ctrl+R: restart",
            settings.FONTS["small"],
            8,
            settings.VIRTUAL_HEIGHT - 20,
            settings.COLOR_TEXT,
        )
        render_text(
            surface,
            f"Hits taken: {self.squad.hits_taken}/{settings.SQUAD_HITS_TO_LOSE}   Stance: {self.captain.stance}",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )

        if self.fade_alpha > 0:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.fade_alpha)))
            surface.blit(overlay, (0, 0))
