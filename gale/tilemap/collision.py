"""
This file contains platformer collision helpers for TileMap: an
optional, opt-in layer on top of it, not a required part of using
TileMap at all. It never touches gale.physics/Box2D — this is plain
AABB-against-a-grid, the same kind of hand-rolled collision most 2D
platformers actually use, in or out of a physics engine.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Iterator, Optional, Tuple

from .tilemap import TileMap

DEFAULT_COLLISION_PROPERTY: str = "collision"

# Tile overlap tests treat the right/bottom edge of a rect as
# exclusive (a rect from x=0 to x=16 with 16-pixel tiles overlaps
# column 0 only, not column 1). Subtracting a tiny epsilon before
# dividing by tile size — rather than a whole pixel, which is what
# you'd subtract for an integer-pixel rect — keeps that exclusive-edge
# handling correct for the continuous (float) positions this module
# works in, where a rect can end at, say, x=16.0001.
_EPSILON: float = 1e-6


class CollisionType:
    """
    The two kinds of blocking tile move_and_collide understands, read
    from a tile's custom property (see collision_type_at). Everything
    else — slopes, conveyor belts, ladders, hazards — is deliberately
    left out: define your own property (e.g. "damage") and read it
    with TileMap.properties_of_gid/get_gid yourself, the same way
    these two are read.
    """

    NONE: str = "none"
    SOLID: str = "solid"
    # One-way: blocks only when approached from above (walking on top
    # of it, landing on it), never from below or the sides — the
    # "platform you can jump up through" every Mario/Metroidvania-style
    # game has.
    PLATFORM: str = "platform"


def collision_type_at(
    tilemap: TileMap,
    layer_name: str,
    row: int,
    col: int,
    collision_property: str = DEFAULT_COLLISION_PROPERTY,
) -> str:
    """
    :param tilemap: The map to check.
    :param layer_name: Which of its layers to check.
    :param row: A tile row.
    :param col: A tile column.
    :param collision_property: The custom tile property (set in Tiled's tileset editor) collision-checking reads. The default value is "collision".
    :returns: One of the CollisionType constants: CollisionType.NONE for an empty cell, an out-of-bounds cell, or a tile whose collision_property isn't "solid"/"platform".
    """
    if not tilemap.in_bounds(row, col):
        return CollisionType.NONE

    gid = tilemap.get_gid(layer_name, row, col)

    if gid == 0:
        return CollisionType.NONE

    value = tilemap.properties_of_gid(gid).get(collision_property, CollisionType.NONE)
    return (
        value
        if value in (CollisionType.SOLID, CollisionType.PLATFORM)
        else (CollisionType.NONE)
    )


def move_and_collide(
    tilemap: TileMap,
    layer_name: str,
    x: float,
    y: float,
    width: float,
    height: float,
    dx: float,
    dy: float,
    collision_property: str = DEFAULT_COLLISION_PROPERTY,
) -> Tuple[float, float, bool, bool]:
    """
    Moves an entity's top-left corner by (dx, dy), one axis at a time
    (x, then y — the usual order for a 2D platformer, so a corner case
    sliding along a wall still gets stopped by the wall rather than a
    floor first), snapping it flush against whatever it runs into
    instead of leaving a gap.

    Works entirely in floats, and never rounds x/y to whole pixels
    anywhere internally — including for the tile-overlap test itself,
    not just for the position you get back. Rounding either one is
    enough to reintroduce the bug this is written to avoid: at a
    typical frame rate, one frame's movement under gravity near the
    ground is a fraction of a pixel, so an entity resting on solid
    ground keeps re-falling that fraction and re-colliding every
    frame — which reads as the ground-check flickering on and off,
    since a rounded position can stay numerically unchanged call after
    call while the real, unrounded one keeps drifting down into the
    floor. Round only when you need a pygame.Rect for rendering/hit
    testing elsewhere (e.g. pygame.Rect(round(x), round(y), width, height)).

    A "solid" tile blocks in every direction. A "platform" tile only
    blocks downward movement, and only if the entity was already at or
    above the platform's top edge before this call — never from below
    (walking/jumping up through it) or from the sides (walking through
    it at the same height).

    :param tilemap: The map to collide against.
    :param layer_name: Which of its layers to collide against.
    :param x: The entity's current x position (top-left corner), before this move.
    :param y: The entity's current y position (top-left corner), before this move.
    :param width: The entity's width.
    :param height: The entity's height.
    :param dx: Horizontal movement this call, in pixels (e.g. vx * dt).
    :param dy: Vertical movement this call, in pixels (e.g. vy * dt).
    :param collision_property: Forwarded to collision_type_at.
    :returns: (new_x, new_y, collided_x, collided_y) — the resulting position, and whether it was stopped short on each axis.
    """
    collided_x = False
    collided_y = False

    if dx != 0:
        moving_right = dx > 0
        new_x = x + dx
        left = min(x, new_x)
        right = max(x + width, new_x + width)
        blocking_col = _find_blocking_column(
            tilemap,
            layer_name,
            left,
            y,
            right,
            y + height,
            collision_property,
            moving_right,
        )

        if blocking_col is not None:
            new_x = (
                blocking_col * tilemap.tile_width - width
                if moving_right
                else (blocking_col + 1) * tilemap.tile_width
            )
            collided_x = True

        x = new_x

    if dy != 0:
        moving_down = dy > 0
        new_y = y + dy
        top = min(y, new_y)
        bottom = max(y + height, new_y + height)
        blocking_row = _find_blocking_row(
            tilemap,
            layer_name,
            y + height,
            x,
            top,
            x + width,
            bottom,
            collision_property,
            moving_down,
        )

        if blocking_row is not None:
            new_y = (
                blocking_row * tilemap.tile_height - height
                if moving_down
                else (blocking_row + 1) * tilemap.tile_height
            )
            collided_y = True

        y = new_y

    return x, y, collided_x, collided_y


def _overlapping_cells(
    tilemap: TileMap, left: float, top: float, right: float, bottom: float
) -> Iterator[Tuple[int, int]]:
    min_row = max(0, int(top // tilemap.tile_height))
    min_col = max(0, int(left // tilemap.tile_width))
    max_row = min(tilemap.rows - 1, int((bottom - _EPSILON) // tilemap.tile_height))
    max_col = min(tilemap.cols - 1, int((right - _EPSILON) // tilemap.tile_width))

    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            yield row, col


def _find_blocking_column(
    tilemap: TileMap,
    layer_name: str,
    left: float,
    top: float,
    right: float,
    bottom: float,
    collision_property: str,
    moving_right: bool,
) -> Optional[int]:
    blocking: Optional[int] = None

    for row, col in _overlapping_cells(tilemap, left, top, right, bottom):
        ctype = collision_type_at(tilemap, layer_name, row, col, collision_property)

        if ctype != CollisionType.SOLID:
            continue

        if blocking is None or (col < blocking if moving_right else col > blocking):
            blocking = col

    return blocking


def _find_blocking_row(
    tilemap: TileMap,
    layer_name: str,
    original_bottom: float,
    left: float,
    top: float,
    right: float,
    bottom: float,
    collision_property: str,
    moving_down: bool,
) -> Optional[int]:
    blocking: Optional[int] = None

    for row, col in _overlapping_cells(tilemap, left, top, right, bottom):
        ctype = collision_type_at(tilemap, layer_name, row, col, collision_property)

        if ctype == CollisionType.SOLID:
            blocks = True
        elif ctype == CollisionType.PLATFORM and moving_down:
            tile_top = row * tilemap.tile_height
            blocks = original_bottom <= tile_top
        else:
            blocks = False

        if not blocks:
            continue

        if blocking is None or (row < blocking if moving_down else row > blocking):
            blocking = row

    return blocking
