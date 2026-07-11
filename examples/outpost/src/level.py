"""
The Outpost level: a small isometric grid built directly in code (no
Tiled file, no image assets), rendered with
gale.tilemap.isometric.IsometricTileMap. Movement/collision/perception
all happen in "world space" (see settings.CELL_SIZE), exactly like a
regular top-down game's pixel space -- to_screen is the one place that
projects a world position through cartesian_to_isometric for drawing. Wall
obstacles double as both tiles to render (see build_tilemap) and
rectangles that gale.ai.perception's line-of-sight checks and the
guards' NavGraph both use, the same "one obstacle list, several
consumers" approach examples/nightwatch/src/level.py takes.
"""

from typing import List, Sequence, Tuple

import pygame

from gale.ai.graph import NavGraph
from gale.ai.search import a_star
from gale.tilemap import Tileset
from gale.tilemap.isometric import IsometricTileMap, cartesian_to_isometric

import settings

Point = Tuple[float, float]

GID_FLOOR = 1
GID_WALL = 2
GID_TERMINAL = 3

CELL = settings.CELL_SIZE

BOUNDS = pygame.Rect(0, 0, settings.GRID_COLS * CELL, settings.GRID_ROWS * CELL)

# Two wall segments forming a zigzag corridor across the middle of the
# map, the same shape of obstacle nightwatch uses, in world units.
OBSTACLES: List[pygame.Rect] = [
    pygame.Rect(5 * CELL, 0 * CELL, 1 * CELL, 6 * CELL),
    pygame.Rect(8 * CELL, 4 * CELL, 1 * CELL, 6 * CELL),
]

TERMINAL_CELL: Tuple[int, int] = (1, 10)  # (row, col), tile-grid coordinates
TERMINAL_POSITION: Point = (
    (TERMINAL_CELL[1] + 0.5) * CELL,
    (TERMINAL_CELL[0] + 0.5) * CELL,
)

PLAYER_START: Point = (1.5 * CELL, 8.5 * CELL)

# (patrol point A, patrol point B), in world units, for each guard.
GUARD_PATROLS: List[Tuple[Point, Point]] = [
    ((2.5 * CELL, 2.5 * CELL), (4.5 * CELL, 2.5 * CELL)),
    ((9.5 * CELL, 7.5 * CELL), (9.5 * CELL, 2.5 * CELL)),
]


def _build_tileset() -> Tileset:
    """
    Draw a tiny 3-tile isometric tileset (floor, wall, terminal) with
    pygame.draw, so this example needs no image asset to run.
    """
    tile_width, tile_height = settings.TILE_WIDTH, settings.TILE_HEIGHT
    image = pygame.Surface((tile_width * 3, tile_height), pygame.SRCALPHA)

    def diamond(index: int, fill: pygame.Color, edge: pygame.Color) -> None:
        left = index * tile_width
        points = [
            (left + tile_width / 2, 0),
            (left + tile_width, tile_height / 2),
            (left + tile_width / 2, tile_height),
            (left, tile_height / 2),
        ]
        pygame.draw.polygon(image, fill, points)
        pygame.draw.polygon(image, edge, points, 1)

    diamond(0, settings.COLOR_FLOOR, settings.COLOR_FLOOR_EDGE)
    diamond(1, settings.COLOR_WALL, settings.COLOR_WALL_EDGE)
    diamond(2, settings.COLOR_TERMINAL_TILE, settings.COLOR_TERMINAL_EDGE)
    return Tileset(image, tile_width, tile_height, first_gid=1)


def build_tilemap() -> IsometricTileMap:
    """
    :returns: A fresh IsometricTileMap for the level: one "ground" layer with a floor tile everywhere, a wall tile wherever OBSTACLES covers a cell's center, and the terminal tile at TERMINAL_CELL.
    """
    tilemap = IsometricTileMap(
        tile_width=settings.TILE_WIDTH,
        tile_height=settings.TILE_HEIGHT,
        cols=settings.GRID_COLS,
        rows=settings.GRID_ROWS,
    )
    tilemap.add_tileset(_build_tileset())
    ground = tilemap.add_layer("ground")

    for row in range(settings.GRID_ROWS):
        for col in range(settings.GRID_COLS):
            if (row, col) == TERMINAL_CELL:
                ground[row][col] = GID_TERMINAL
            elif any(
                o.collidepoint((col + 0.5) * CELL, (row + 0.5) * CELL)
                for o in OBSTACLES
            ):
                ground[row][col] = GID_WALL
            else:
                ground[row][col] = GID_FLOOR

    return tilemap


def to_screen(x: float, y: float) -> Tuple[float, float]:
    """
    Convert a world-space position into virtual-screen pixel
    coordinates, using the exact same projection
    IsometricTileMap.position_of uses for a cell's top vertex, plus
    settings.MAP_OFFSET. Used to draw entities (which live in
    continuous world space, unlike a tile's fixed integer row/col) at
    the same isometric projection the tilemap's tiles use.

    :param x: A world-space x coordinate.
    :param y: A world-space y coordinate.
    :returns: The (screen_x, screen_y) pixel position.
    """
    grid_x, grid_y = x / CELL, y / CELL
    origin_x = (settings.GRID_ROWS - 1) * settings.TILE_WIDTH / 2
    screen_x, screen_y = cartesian_to_isometric(
        grid_x, grid_y, settings.TILE_WIDTH, settings.TILE_HEIGHT
    )
    offset_x, offset_y = settings.MAP_OFFSET
    # No extra tile_height adjustment is needed here, unlike it might
    # seem from position_of returning a diamond's top vertex rather
    # than its center: x/y are already continuous world-space
    # coordinates (e.g. a cell center is (col + 0.5, row + 0.5) in
    # grid units), so projecting them directly already lands on the
    # exact point on the diamond they represent -- adding a further
    # offset here used to double-count that and draw every entity a
    # half (or, before that, a full) tile_height below where it
    # visually belongs relative to the tiles.
    return (screen_x + origin_x + offset_x, screen_y + offset_y)


def has_line_of_sight(
    a: Point, b: Point, obstacles: Sequence[pygame.Rect] = OBSTACLES
) -> bool:
    """
    :returns: Whether the straight segment from a to b (in world units) is not blocked by any of obstacles.
    """
    return not any(obstacle.clipline(a, b) for obstacle in obstacles)


def _inflated_obstacles(clearance: float) -> List[pygame.Rect]:
    return [
        pygame.Rect(
            o.x - clearance,
            o.y - clearance,
            o.width + 2 * clearance,
            o.height + 2 * clearance,
        )
        for o in OBSTACLES
    ]


def build_nav_graph(
    extra_points: Sequence[Point], clearance: float = settings.NAV_CLEARANCE
) -> NavGraph:
    """
    Build a visibility graph: a node at every corner of every (inflated,
    for clearance) obstacle plus every point in extra_points, with an
    edge between any two nodes that have a clear line of sight to each
    other. Same approach as examples/nightwatch/src/level.py, using
    world units (see settings.CELL_SIZE) instead of pixels.

    :param extra_points: Extra nodes to always include, such as patrol points and the terminal.
    :param clearance: How far, in world units, obstacles are inflated and their corner nodes pushed out.
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
    :param start: The point to path from, in world units.
    :param goal: The point to path to, in world units.
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
    body as a circle of the given radius (in world units), and clamp it
    to the level bounds.

    :param position: The circle's center, in world units.
    :param radius: The circle's radius, in world units.
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
