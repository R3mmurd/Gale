"""
The Skirmish arena: a fixed layout of wall obstacles, a set of cover
points guards can take tactical positions at, and an extraction zone
the squad is trying to reach, plus the helpers built on top of
gale.ai.graph.NavGraph/gale.ai.search (for pathfinding) and
gale.ai.steering.Wall (for WallAvoidance) that everyone in the level
needs.
"""

from typing import List, Sequence, Tuple

import pygame

from gale.ai.graph import NavGraph
from gale.ai.search import a_star
from gale.ai.steering import Wall

import settings

Point = Tuple[float, float]

BOUNDS = pygame.Rect(0, 0, settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)

# A handful of cover blocks scattered across the arena.
OBSTACLES: List[pygame.Rect] = [
    pygame.Rect(220, 60, 28, 140),
    pygame.Rect(220, 260, 28, 140),
    pygame.Rect(420, 150, 140, 28),
    pygame.Rect(620, 40, 28, 160),
    pygame.Rect(620, 260, 28, 150),
]

EXTRACTION_RECT = pygame.Rect(740, 200, 40, 50)

SQUAD_START: Point = (30, 220)

# Tactical cover points guards retreat to once alerted (fed to
# gale.ai.tactical.best_position, scored by an InfluenceMap).
COVER_POINTS: List[Point] = [
    (260, 40),
    (260, 230),
    (260, 420),
    (500, 100),
    (500, 350),
    (660, 30),
    (660, 230),
    (660, 420),
]

GUARD_PATROLS: List[Tuple[Point, Point]] = [
    ((300, 60), (400, 60)),
    ((300, 390), (400, 390)),
    ((520, 220), (600, 220)),
]

CAPTAIN_START: Point = (700, 400)


def has_line_of_sight(
    a: Point, b: Point, obstacles: Sequence[pygame.Rect] = OBSTACLES
) -> bool:
    """
    :returns: Whether the straight segment from a to b is not blocked by any of obstacles.
    """
    return not any(obstacle.clipline(a, b) for obstacle in obstacles)


def _inflated_obstacles(clearance: float) -> List[pygame.Rect]:
    return [o.inflate(clearance * 2, clearance * 2) for o in OBSTACLES]


def build_walls() -> List[Wall]:
    """
    :returns: One Wall per edge of every obstacle, for WallAvoidance.
    """
    walls = []

    for obstacle in OBSTACLES:
        corners = [
            obstacle.topleft,
            obstacle.topright,
            obstacle.bottomright,
            obstacle.bottomleft,
        ]

        for start, end in zip(corners, corners[1:] + corners[:1]):
            walls.append(Wall(start, end))

    return walls


def build_nav_graph(
    extra_points: Sequence[Point], clearance: float = settings.NAV_CLEARANCE
) -> NavGraph:
    """
    Build a simple visibility graph: a node at every corner of every
    (inflated, for clearance) obstacle plus every point in
    extra_points, with an edge between any two nodes that have a clear
    line of sight to each other.

    :param extra_points: Extra nodes to always include, such as patrol points, cover points, the squad's start, and the extraction zone.
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
    bounds.
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


def blocked_by_obstacle(position: Tuple[float, float]) -> bool:
    """
    :returns: Whether position falls inside any obstacle (used to stop bullets/grenades on impact).
    """
    return any(obstacle.collidepoint(position) for obstacle in OBSTACLES)


def render(surface: pygame.Surface, nav_graph: NavGraph) -> None:
    """
    Render the level's walls, extraction zone, and (faintly, for demo
    purposes) the nav graph's edges.
    """
    for source, target, _ in nav_graph.edges:
        pygame.draw.line(surface, settings.COLOR_NAV_EDGE, source, target)

    pygame.draw.rect(surface, settings.COLOR_EXTRACTION, EXTRACTION_RECT)

    for obstacle in OBSTACLES:
        pygame.draw.rect(surface, settings.COLOR_WALL, obstacle)
