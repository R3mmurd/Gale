"""
This file contains the isometric counterpart of gale.tilemap.tilemap:
cartesian_to_isometric/isometric_to_cartesian (the cartesian <->
isometric screen-space conversion every diamond-grid project ends up
writing by hand — useful on their own for any isometric coordinate
math, not just tile maps) and IsometricTileMap, a TileMap subclass that
renders its grid as a 2:1 diamond projection instead of an
axis-aligned one.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math
from typing import Any, Optional, Tuple

import pygame

from .tilemap import TileMap, Tileset


def cartesian_to_isometric(
    x: float, y: float, tile_width: int, tile_height: int
) -> Tuple[float, float]:
    """
    Converts a cartesian grid-space position (in tile units — x is the
    column, y is the row, either can be fractional) into isometric
    screen-space pixel coordinates, using the standard 2:1 diamond
    projection.

    :param x: A grid-space x coordinate, in tile units (column).
    :param y: A grid-space y coordinate, in tile units (row).
    :param tile_width: The width, in pixels, of a diamond tile.
    :param tile_height: The height, in pixels, of a diamond tile.
    :returns: The equivalent (screen_x, screen_y) in pixels.
    """
    screen_x = (x - y) * tile_width / 2
    screen_y = (x + y) * tile_height / 2
    return (screen_x, screen_y)


def isometric_to_cartesian(
    screen_x: float, screen_y: float, tile_width: int, tile_height: int
) -> Tuple[float, float]:
    """
    The exact inverse of cartesian_to_isometric: turns an isometric
    screen-space pixel position back into a cartesian grid-space one
    (in tile units).

    :param screen_x: A screen-space x coordinate, in pixels.
    :param screen_y: A screen-space y coordinate, in pixels.
    :param tile_width: The width, in pixels, of a diamond tile.
    :param tile_height: The height, in pixels, of a diamond tile.
    :returns: The equivalent (x, y) in grid space (tile units).
    """
    x = screen_x / tile_width + screen_y / tile_height
    y = screen_y / tile_height - screen_x / tile_width
    return (x, y)


class IsometricTileMap(TileMap):
    """
    A TileMap rendered as a 2:1 isometric diamond grid rather than an
    axis-aligned one — same rows x cols grid(s) of gids, same
    tileset(s)/layers/object_layers API, only the projection from
    (row, col) to pixels (and back) changes.

    Conventions used throughout this class:

    - (row 0, col 0) sits at the map's top corner (the diamond's
      topmost point on screen), with row increasing toward the
      bottom-left and col increasing toward the bottom-right — the
      usual isometric "diamond" layout.
    - position_of(row, col) returns that cell's diamond's *top
      vertex* (not a bounding-box top-left corner), shifted right by
      origin_x = (rows - 1) * tile_width / 2 so the whole map's top
      vertex column never goes negative.
    - Tile images are anchored at their *top-center*: the pixel
      position_of returns is where the top-center point of the
      tile_width x tile_height source image should land. render()
      accounts for this by blitting at
      (position_of(row, col)[0] - tile_width / 2, position_of(row, col)[1]).

    Because row + col increases monotonically along a plain row-major
    (row ascending, then col ascending) iteration, that iteration order
    already paints back-to-front for a diamond grid — no extra sort is
    needed, unlike a general isometric scene with freely-placed
    entities.

    Usage example:

        tileset = Tileset(tiles_image, tile_width=64, tile_height=32, first_gid=1)
        tilemap = IsometricTileMap(tile_width=64, tile_height=32, cols=20, rows=20)
        tilemap.add_tileset(tileset)
        ground = tilemap.add_layer("ground")
        ground[5][10] = 1

        # Every frame:
        tilemap.render(surface, camera)
    """

    @property
    def pixel_width(self) -> int:
        return round((self.cols + self.rows) * self.tile_width / 2)

    @property
    def pixel_height(self) -> int:
        return round((self.cols + self.rows) * self.tile_height / 2)

    def position_of(self, row: int, col: int) -> Tuple[float, float]:
        """
        :param row: A tile row.
        :param col: A tile column.
        :returns: The screen/world pixel position of that cell's diamond's top vertex (see the class docstring for the anchor/origin convention).
        """
        origin_x = (self.rows - 1) * self.tile_width / 2
        screen_x, screen_y = cartesian_to_isometric(
            col, row, self.tile_width, self.tile_height
        )
        return (screen_x + origin_x, screen_y)

    def tile_at(self, x: float, y: float) -> Tuple[int, int]:
        """
        :param x: A screen/world x position, in pixels.
        :param y: A screen/world y position, in pixels.
        :returns: The (row, col) of the tile whose diamond contains that point (not clamped to this map's bounds — check in_bounds if the point might fall outside it).
        """
        origin_x = (self.rows - 1) * self.tile_width / 2
        col_f, row_f = isometric_to_cartesian(
            x - origin_x, y, self.tile_width, self.tile_height
        )
        return (int(math.floor(row_f)), int(math.floor(col_f)))

    def render(self, surface: pygame.Surface, camera: Optional[Any] = None) -> None:
        """
        :param surface: The surface to draw every layer onto.
        :param camera: A gale.camera.Camera to translate/scale tiles through and cull whatever falls outside its viewport. The default value is None, rendering the whole map at a 1:1 scale starting at (0, 0).
        """
        viewport_rect: Optional[pygame.Rect] = None

        if camera is not None:
            viewport_rect = pygame.Rect(
                0, 0, camera.viewport_width, camera.viewport_height
            )

        for name in self.layer_names():
            grid = self.get_layer(name)

            for row in range(self.rows):
                for col in range(self.cols):
                    gid = grid[row][col]

                    if gid == 0:
                        continue

                    tileset = self.tileset_for_gid(gid)

                    if tileset is None:
                        continue

                    source_rect = tileset.rect_for(gid)
                    top_x, top_y = self.position_of(row, col)
                    dest_rect = pygame.Rect(
                        round(top_x - self.tile_width / 2),
                        round(top_y),
                        self.tile_width,
                        self.tile_height,
                    )

                    if camera is None:
                        surface.blit(tileset.image, dest_rect, source_rect)
                    else:
                        screen_rect = camera.apply(dest_rect)

                        if viewport_rect is not None and not screen_rect.colliderect(
                            viewport_rect
                        ):
                            continue

                        surface.blit(tileset.image, screen_rect, source_rect)
