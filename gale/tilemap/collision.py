"""
This file contains platformer collision helpers for TileMap: an
optional, opt-in layer on top of it, not a required part of using
TileMap at all. It never touches gale.physics/Box2D — this is plain
AABB-against-a-grid, the same kind of hand-rolled collision most 2D
platformers actually use, in or out of a physics engine.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Iterator, Optional, Tuple

import pygame

from .tilemap import TileMap

DEFAULT_COLLISION_PROPERTY: str = "collision"


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
    rect: pygame.Rect,
    dx: float,
    dy: float,
    collision_property: str = DEFAULT_COLLISION_PROPERTY,
) -> Tuple[pygame.Rect, bool, bool]:
    """
    Moves rect by (dx, dy), one axis at a time (x, then y — the usual
    order for a 2D platformer, so a corner case sliding along a wall
    still gets stopped by the wall rather than a floor first), snapping
    it flush against whatever it runs into instead of leaving a gap.

    A "solid" tile blocks in every direction. A "platform" tile only
    blocks downward movement, and only if rect was already at or above
    its top edge before this call — never from below (walking/jumping
    up through it) or from the sides (walking through it at the same
    height).

    :param tilemap: The map to collide against.
    :param layer_name: Which of its layers to collide against.
    :param rect: The moving entity's current rect, before this move.
    :param dx: Horizontal movement this call, in pixels (e.g. vx * dt).
    :param dy: Vertical movement this call, in pixels (e.g. vy * dt).
    :param collision_property: Forwarded to collision_type_at.
    :returns: (new_rect, collided_x, collided_y) — the resulting rect, and whether it was stopped short on each axis.
    """
    rect = rect.copy()
    collided_x = False
    collided_y = False

    if dx != 0:
        moving_right = dx > 0
        candidate = rect.move(dx, 0)
        swept = _swept_rect_x(rect, candidate)
        blocking_col = _find_blocking_column(
            tilemap, layer_name, swept, collision_property, moving_right
        )

        if blocking_col is not None:
            if moving_right:
                candidate.right = blocking_col * tilemap.tile_width
            else:
                candidate.left = (blocking_col + 1) * tilemap.tile_width

            collided_x = True

        rect = candidate

    if dy != 0:
        moving_down = dy > 0
        candidate = rect.move(0, dy)
        swept = _swept_rect_y(rect, candidate)
        blocking_row = _find_blocking_row(
            tilemap, layer_name, rect, swept, collision_property, moving_down
        )

        if blocking_row is not None:
            if moving_down:
                candidate.bottom = blocking_row * tilemap.tile_height
            else:
                candidate.top = (blocking_row + 1) * tilemap.tile_height

            collided_y = True

        rect = candidate

    return rect, collided_x, collided_y


def _swept_rect_x(original: pygame.Rect, candidate: pygame.Rect) -> pygame.Rect:
    # The full horizontal range the rect passes through this move,
    # kept at its (unchanging) vertical extent — so a move larger than
    # a tile can never skip over ("tunnel through") a thin obstacle by
    # only ever checking the destination cell.
    left = min(original.left, candidate.left)
    right = max(original.right, candidate.right)
    return pygame.Rect(left, original.top, right - left, original.height)


def _swept_rect_y(original: pygame.Rect, candidate: pygame.Rect) -> pygame.Rect:
    top = min(original.top, candidate.top)
    bottom = max(original.bottom, candidate.bottom)
    return pygame.Rect(original.left, top, original.width, bottom - top)


def _overlapping_cells(
    tilemap: TileMap, rect: pygame.Rect
) -> Iterator[Tuple[int, int]]:
    min_row, min_col = tilemap.tile_at(rect.left, rect.top)
    max_row, max_col = tilemap.tile_at(rect.right - 1, rect.bottom - 1)
    min_row = max(0, min_row)
    min_col = max(0, min_col)
    max_row = min(tilemap.rows - 1, max_row)
    max_col = min(tilemap.cols - 1, max_col)

    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            yield row, col


def _find_blocking_column(
    tilemap: TileMap,
    layer_name: str,
    swept_rect: pygame.Rect,
    collision_property: str,
    moving_right: bool,
) -> Optional[int]:
    blocking: Optional[int] = None

    for row, col in _overlapping_cells(tilemap, swept_rect):
        ctype = collision_type_at(tilemap, layer_name, row, col, collision_property)

        if ctype != CollisionType.SOLID:
            continue

        if blocking is None or (col < blocking if moving_right else col > blocking):
            blocking = col

    return blocking


def _find_blocking_row(
    tilemap: TileMap,
    layer_name: str,
    original_rect: pygame.Rect,
    swept_rect: pygame.Rect,
    collision_property: str,
    moving_down: bool,
) -> Optional[int]:
    blocking: Optional[int] = None

    for row, col in _overlapping_cells(tilemap, swept_rect):
        ctype = collision_type_at(tilemap, layer_name, row, col, collision_property)

        if ctype == CollisionType.SOLID:
            blocks = True
        elif ctype == CollisionType.PLATFORM and moving_down:
            tile_top = row * tilemap.tile_height
            blocks = original_rect.bottom <= tile_top
        else:
            blocks = False

        if not blocks:
            continue

        if blocking is None or (row < blocking if moving_down else row > blocking):
            blocking = row

    return blocking
