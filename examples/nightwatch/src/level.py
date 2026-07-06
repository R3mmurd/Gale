"""
The Nightwatch level: a fixed layout of wall obstacles and an exit,
plus the helpers built on top of gale.ai.graph.NavGraph and
gale.ai.search that let guards path around the walls.
"""

from typing import List, Sequence, Tuple

import pygame

from gale.ai.graph import NavGraph
from gale.ai.search import a_star

import settings

Point = Tuple[float, float]

BOUNDS = pygame.Rect(0, 0, settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)

# Two walls forming a zigzag corridor: a gap at the bottom of the first
# one, a gap at the top of the second one, connected by an open middle
# lane.
OBSTACLES: List[pygame.Rect] = [
    pygame.Rect(200, 0, 24, 240),
    pygame.Rect(416, 120, 24, 240),
]

EXIT_RECT = pygame.Rect(560, 20, 50, 40)

PLAYER_START: Point = (20, 340)

# (patrol point A, patrol point B) for each guard. Kept far enough from
# PLAYER_START that the player doesn't start the level already spotted.
GUARD_PATROLS: List[Tuple[Point, Point]] = [
    ((160, 300), (320, 300)),
    ((300, 60), (500, 60)),
]

CIVILIAN_START: Point = (320, 180)


def has_line_of_sight(
    a: Point, b: Point, obstacles: Sequence[pygame.Rect] = OBSTACLES
) -> bool:
    """
    :returns: Whether the straight segment from a to b is not blocked by any of obstacles.
    """
    return not any(obstacle.clipline(a, b) for obstacle in obstacles)


def _inflated_obstacles(clearance: float) -> List[pygame.Rect]:
    return [o.inflate(clearance * 2, clearance * 2) for o in OBSTACLES]


def build_nav_graph(
    extra_points: Sequence[Point], clearance: float = settings.NAV_CLEARANCE
) -> NavGraph:
    """
    Build a simple visibility graph: a node at every corner of every
    (inflated, for clearance) obstacle plus every point in
    extra_points, with an edge between any two nodes that have a clear
    line of sight to each other.

    :param extra_points: Extra nodes to always include, such as patrol points, the player's start, and the exit.
    :param clearance: How far, in pixels, obstacles are inflated and their corner nodes pushed out, so a path keeps this much distance from walls.
    :returns: The resulting NavGraph, ready to be searched with gale.ai.search.
    """
    inflated = _inflated_obstacles(clearance)
    nodes: List[Point] = list(extra_points)

    for obstacle in inflated:
        for corner in (
            obstacle.topleft,
            obstacle.topright,
            obstacle.bottomleft,
            obstacle.bottomright,
        ):
            if BOUNDS.collidepoint(corner) and not any(
                o.collidepoint(corner) for o in inflated
            ):
                nodes.append(corner)

    graph = NavGraph()

    for node in nodes:
        graph.add_node(node)

    for i, source in enumerate(nodes):
        for target in nodes[i + 1 :]:
            if has_line_of_sight(source, target, inflated):
                graph.add_edge(source, target)

    return graph


def find_path(nav_graph: NavGraph, start: Point, goal: Point) -> List[Point]:
    """
    Find a path from start to goal using nav_graph, temporarily
    connecting both points to it (they are not part of it, since they
    move every time this is called).

    :param nav_graph: The static NavGraph built by build_nav_graph.
    :param start: The point to path from.
    :param goal: The point to path to.
    :returns: The list of points from start to goal (both included), or an empty list if goal is unreachable.
    """
    working = NavGraph()

    for source, target, weight in nav_graph.edges:
        working.add_edge(source, target, weight)

    for point in (start, goal):
        working.add_node(point)

        for node in nav_graph.nodes:
            if node != point and has_line_of_sight(point, node):
                working.add_edge(point, node)

    if has_line_of_sight(start, goal):
        working.add_edge(start, goal)

    def heuristic(node: Point, goal_node: Point) -> float:
        return pygame.Vector2(node).distance_to(goal_node)

    path = a_star(start, goal, working, heuristic)
    return path or []


def resolve_circle_vs_obstacles(
    position: pygame.Vector2, radius: float
) -> pygame.Vector2:
    """
    Push position out of any obstacle it overlaps, treating the moving
    body as a circle of the given radius, and clamp it to the level
    bounds. Meant to be called after integrating movement every frame.

    :param position: The circle's center.
    :param radius: The circle's radius.
    :returns: The corrected position.
    """
    resolved = pygame.Vector2(position)

    for obstacle in OBSTACLES:
        closest = pygame.Vector2(
            max(obstacle.left, min(resolved.x, obstacle.right)),
            max(obstacle.top, min(resolved.y, obstacle.bottom)),
        )
        delta = resolved - closest

        if delta.length_squared() == 0:
            continue

        distance = delta.length()

        if distance < radius:
            resolved += delta.normalize() * (radius - distance)

    resolved.x = max(BOUNDS.left + radius, min(resolved.x, BOUNDS.right - radius))
    resolved.y = max(BOUNDS.top + radius, min(resolved.y, BOUNDS.bottom - radius))
    return resolved


def render(surface: pygame.Surface, nav_graph: NavGraph) -> None:
    """
    Render the level's walls, exit, and (faintly, for demo purposes)
    the nav graph's edges.
    """
    for source, target, _ in nav_graph.edges:
        pygame.draw.line(surface, settings.COLOR_NAV_EDGE, source, target)

    pygame.draw.rect(surface, settings.COLOR_EXIT, EXIT_RECT)

    for obstacle in OBSTACLES:
        pygame.draw.rect(surface, settings.COLOR_WALL, obstacle)
