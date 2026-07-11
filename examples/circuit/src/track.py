"""
The circuit itself: a small rectangular oval (an outer rect minus an
inner one, so the driveable surface is the ring between them), plus the
waypoints AI racers path-follow around it and the finish line used for
lap counting.

Every function here is a pure function of its arguments (no randomness,
no wall-clock time, no mutable module state beyond the constants
imported from settings), since is_on_track is called from
src/car.py's apply_input, which PredictionBuffer.reconcile replays
after the fact and must therefore behave identically every time it is
given the same state/input/dt.
"""

import math
from typing import List, Tuple

import pygame

from gale.ai.graph import NavGraph

import settings

Point = Tuple[float, float]


def is_on_track(x: float, y: float) -> bool:
    """
    :returns: Whether (x, y) lies on the driveable ring between the outer and inner rectangles, rather than off in the grass.
    """
    on_outer = settings.OUTER_RECT.collidepoint(x, y)
    on_inner = settings.INNER_RECT.collidepoint(x, y)
    return on_outer and not on_inner


def build_waypoints() -> List[Point]:
    """
    :returns: The centerline waypoints going clockwise around the ring, starting just before the finish line, used both to build the NavGraph AI racers path-follow and as the human cars' spawn line.
    """
    outer = settings.OUTER_RECT
    inner = settings.INNER_RECT
    half_width = (outer.width - inner.width) / 4 + inner.width / 2
    half_height = (outer.height - inner.height) / 4 + inner.height / 2
    cx, cy = outer.centerx, outer.centery

    return [
        (cx, cy + half_height),  # bottom-center (start/finish straight)
        (cx + half_width, cy + half_height),  # bottom-right
        (cx + half_width, cy - half_height),  # top-right
        (cx, cy - half_height),  # top-center
        (cx - half_width, cy - half_height),  # top-left
        (cx - half_width, cy + half_height),  # bottom-left
    ]


WAYPOINTS: List[Point] = build_waypoints()


def build_nav_graph() -> NavGraph:
    """
    :returns: A directed NavGraph connecting each waypoint to the next one going clockwise (and the last one back to the first), so a_star over it always finds "keep going forward around the loop" as the only path.
    """
    graph = NavGraph(directed=True)
    count = len(WAYPOINTS)

    for i in range(count):
        graph.add_edge(WAYPOINTS[i], WAYPOINTS[(i + 1) % count])

    return graph


def nearest_waypoint_index(x: float, y: float) -> int:
    """
    :returns: The index of the waypoint closest to (x, y).
    """
    return min(
        range(len(WAYPOINTS)),
        key=lambda i: math.hypot(WAYPOINTS[i][0] - x, WAYPOINTS[i][1] - y),
    )


def crosses_finish_line(previous: Point, current: Point) -> bool:
    """
    Detect a lap by checking whether the segment from previous to
    current crosses the finish line segment while moving rightward
    (the direction WAYPOINTS travels through the bottom straight, i.e.
    from bottom-left, through bottom-center, to bottom-right), which is
    good enough for this small oval (no self intersections to worry
    about).

    :param previous: The car's position last tick.
    :param current: The car's position this tick.
    :returns: Whether a lap was just completed.
    """
    x0, y0 = previous
    x1, y1 = current

    if x1 <= x0 or not (x0 <= settings.FINISH_X <= x1):
        return False

    t = (settings.FINISH_X - x0) / (x1 - x0)
    crossing_y = y0 + (y1 - y0) * t
    return settings.FINISH_Y0 <= crossing_y <= settings.FINISH_Y1


def render(surface: pygame.Surface) -> None:
    surface.fill(settings.COLOR_GRASS, settings.OUTER_RECT)
    pygame.draw.rect(surface, settings.COLOR_TRACK, settings.OUTER_RECT)
    surface.fill(settings.COLOR_GRASS, settings.INNER_RECT)
    pygame.draw.line(
        surface,
        settings.COLOR_FINISH,
        (settings.FINISH_X, settings.FINISH_Y0),
        (settings.FINISH_X, settings.FINISH_Y1),
        3,
    )
