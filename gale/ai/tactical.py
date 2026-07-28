"""
This file contains support for tactical/strategic decisions: an
InfluenceMap tracks, over a grid, how much presence each side has
across an area (propagated outward from wherever influence was added,
decaying with distance), so an agent can query "who controls this
spot" or "which of these candidate positions is safest/most
contested" instead of only reacting to what's immediately visible. It
is deliberately generic about what "influence" means -- add whatever
sources make sense for your game (unit positions, alarms, resources)
and score positions with best_position's score function.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math

from typing import Callable, Dict, Optional, Sequence, Tuple

import pygame

Cell = Tuple[int, int]


class InfluenceMap:
    """
    A grid over a rectangular world area, each cell accumulating a
    signed influence value per team: positive for one team, negative
    for another, so value_at reads as "how strongly, and by whom, is
    this position controlled".

    Usage example:

        influence_map = InfluenceMap(width=800, height=600, cell_size=40)
        for enemy in enemies:
            influence_map.add_influence(enemy.position, strength=1.0, radius=150, team="enemy")
        for ally in allies:
            influence_map.add_influence(ally.position, strength=1.0, radius=150, team="ally")
        influence_map.propagate()
        influence_map.dominance_at(candidate_position)  # > 0: ally-favored, < 0: enemy-favored
    """

    def __init__(self, width: float, height: float, cell_size: float = 40) -> None:
        """
        :param width: Width of the area this map covers.
        :param height: Height of the area this map covers.
        :param cell_size: Side length of each square cell. The default value is 40.
        """
        self.width: float = width
        self.height: float = height
        self.cell_size: float = cell_size
        self.columns: int = max(1, int(math.ceil(width / cell_size)))
        self.rows: int = max(1, int(math.ceil(height / cell_size)))
        self._values: Dict[str, Dict[Cell, float]] = {}

    def _cell_of(self, position: pygame.Vector2) -> Cell:
        column = min(self.columns - 1, max(0, int(position.x // self.cell_size)))
        row = min(self.rows - 1, max(0, int(position.y // self.cell_size)))
        return column, row

    def _cell_center(self, cell: Cell) -> pygame.Vector2:
        column, row = cell
        return pygame.Vector2(
            (column + 0.5) * self.cell_size, (row + 0.5) * self.cell_size
        )

    def add_influence(
        self,
        position: pygame.Vector2,
        strength: float,
        radius: float,
        team: str = "default",
    ) -> None:
        """
        Add a source of influence centered on position, falling off
        linearly to 0 at radius. Call propagate() after adding every
        source for a round to get a smoothed result.

        :param position: World position the influence radiates from.
        :param strength: Influence value at position itself.
        :param radius: Distance at and beyond which this source no longer contributes.
        :param team: Which team's influence this source adds to. The default value is "default".
        """
        team_values = self._values.setdefault(team, {})
        center_cell = self._cell_of(position)
        cell_radius = int(math.ceil(radius / self.cell_size))

        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                column, row = center_cell[0] + dx, center_cell[1] + dy

                if not (0 <= column < self.columns and 0 <= row < self.rows):
                    continue

                cell = (column, row)
                distance = (self._cell_center(cell) - position).length()

                if distance >= radius:
                    continue

                team_values[cell] = team_values.get(cell, 0.0) + strength * (
                    1 - distance / radius
                )

    def propagate(self, iterations: int = 1, decay: float = 0.5) -> None:
        """
        Blur each team's influence into neighboring cells, so
        influence spreads a little beyond exactly where it was added.

        :param iterations: Number of blur passes to perform. The default value is 1.
        :param decay: Fraction of a cell's influence that spreads into each direct neighbor per pass. The default value is 0.5.
        """
        for _ in range(iterations):
            for team, team_values in self._values.items():
                spread: Dict[Cell, float] = dict(team_values)

                for (column, row), value in team_values.items():
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        neighbor = (column + dx, row + dy)

                        if (
                            0 <= neighbor[0] < self.columns
                            and 0 <= neighbor[1] < self.rows
                        ):
                            spread[neighbor] = spread.get(neighbor, 0.0) + value * decay

                self._values[team] = spread

    def value_at(self, position: pygame.Vector2, team: str = "default") -> float:
        """
        :param position: The world position to query.
        :param team: Which team's influence to read. The default value is "default".
        :returns: The accumulated influence of team at position's cell, or 0 if none has reached it.
        """
        return self._values.get(team, {}).get(self._cell_of(position), 0.0)

    def dominance_at(
        self, position: pygame.Vector2, team_a: str = "ally", team_b: str = "enemy"
    ) -> float:
        """
        :param position: The world position to query.
        :param team_a: The team whose dominance reads as positive. The default value is "ally".
        :param team_b: The team whose dominance reads as negative. The default value is "enemy".
        :returns: team_a's influence at position minus team_b's.
        """
        return self.value_at(position, team_a) - self.value_at(position, team_b)

    def clear(self) -> None:
        """
        Remove every source of influence added so far.
        """
        self._values.clear()


def best_position(
    candidates: Sequence[pygame.Vector2],
    score: Callable[[pygame.Vector2], float],
) -> Optional[pygame.Vector2]:
    """
    Pick whichever of candidates scores highest -- a generic tactical
    waypoint scorer, meant to be paired with any scoring function you
    like, including one that reads from an InfluenceMap (e.g. "prefer
    positions dominated by my team but still within some distance of
    the enemy", or a cover system, or line-of-sight checks).

    :param candidates: The positions to choose among.
    :param score: Callable(position) -> float ranking a candidate; higher is better.
    :returns: The highest-scoring candidate, or None if candidates is empty.
    """
    if not candidates:
        return None

    return max(candidates, key=score)
