"""
This file contains the implementation of the classes Tileset (one
tileset image sliced into tiles, occupying a range of global tile
ids) and TileMap (a stack of named tile layers sharing tileset(s),
rendered with gale.camera culling built in).

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Dict, List, Optional, Tuple

import pygame

from gale.frames import generate_frames

# Tiled (https://www.mapeditor.org/) encodes a flipped/rotated tile by
# setting one or more of a gid's top 3 bits instead of using a
# different gid, so a raw value read from a layer's data always needs
# decode_gid before it can be used as a plain tile id.
FLIP_HORIZONTAL_FLAG = 0x80000000
FLIP_VERTICAL_FLAG = 0x40000000
FLIP_DIAGONAL_FLAG = 0x20000000
_FLIP_FLAGS_MASK = FLIP_HORIZONTAL_FLAG | FLIP_VERTICAL_FLAG | FLIP_DIAGONAL_FLAG
_GID_MASK = ~_FLIP_FLAGS_MASK & 0xFFFFFFFF


def decode_gid(raw_gid: int) -> Tuple[int, bool, bool, bool]:
    """
    :param raw_gid: A tile id as read straight from a Tiled layer's data -- a plain gid, or one with its top 3 bits set to flag a flipped/rotated tile.
    :returns: (gid, flip_horizontal, flip_vertical, flip_diagonal) -- raw_gid with the flip flags cleared, and each flag as a bool. All False and gid == raw_gid for a tile that isn't flipped/rotated.
    """
    return (
        raw_gid & _GID_MASK,
        bool(raw_gid & FLIP_HORIZONTAL_FLAG),
        bool(raw_gid & FLIP_VERTICAL_FLAG),
        bool(raw_gid & FLIP_DIAGONAL_FLAG),
    )


def _flipped_tile_image(
    tileset: "Tileset",
    gid: int,
    flip_horizontal: bool,
    flip_vertical: bool,
    flip_diagonal: bool,
) -> pygame.Surface:
    tile_image = tileset.image.subsurface(tileset.rect_for(gid))

    if flip_diagonal:
        # Reflecting across the top-left/bottom-right diagonal is a
        # 90-degree rotation followed by a vertical flip.
        tile_image = pygame.transform.flip(
            pygame.transform.rotate(tile_image, 90), False, True
        )

    if flip_horizontal or flip_vertical:
        tile_image = pygame.transform.flip(tile_image, flip_horizontal, flip_vertical)

    return tile_image


class Tileset:
    """
    One tileset image, sliced into tiles, occupying a contiguous range
    of global tile ids (gids) starting at first_gid — the same model
    Tiled (https://www.mapeditor.org/) uses to let a single map
    reference more than one tileset image.

    Usage example:

        tileset = Tileset(pygame.image.load("tiles.png"), 16, 16, first_gid=1)
    """

    def __init__(
        self,
        image: pygame.Surface,
        tile_width: int,
        tile_height: int,
        first_gid: int = 1,
        margin: int = 0,
        spacing: int = 0,
        tile_properties: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        """
        :param image: The tileset's source image.
        :param tile_width: The width, in pixels, of each tile.
        :param tile_height: The height, in pixels, of each tile.
        :param first_gid: The global tile id this tileset's first tile occupies. The default value is 1 (0 is reserved by Tiled to mean "empty").
        :param margin: Empty pixels around the whole image, before the first tile. The default value is 0.
        :param spacing: Empty pixels between adjacent tiles. The default value is 0.
        :param tile_properties: Custom properties per tile, keyed by local id (0-based, relative to this tileset — add first_gid to get the matching global id). The default value is None (no tile has any custom properties).
        """
        self.image: pygame.Surface = image
        self.tile_width: int = tile_width
        self.tile_height: int = tile_height
        self.first_gid: int = first_gid
        self._rects: List[pygame.Rect] = generate_frames(
            image, tile_width, tile_height, margin=margin, spacing=spacing
        )
        self._tile_properties: Dict[int, Dict[str, Any]] = tile_properties or {}

    @property
    def tile_count(self) -> int:
        return len(self._rects)

    @property
    def last_gid(self) -> int:
        return self.first_gid + self.tile_count - 1

    def contains(self, gid: int) -> bool:
        """
        :param gid: A global tile id.
        :returns: Whether gid falls within this tileset's range.
        """
        return self.first_gid <= gid <= self.last_gid

    def rect_for(self, gid: int) -> pygame.Rect:
        """
        :param gid: A global tile id known to be within this tileset's range (see contains).
        :returns: The area of this tileset's image that gid's tile occupies.
        """
        return self._rects[gid - self.first_gid]

    def properties_for(self, gid: int) -> Dict[str, Any]:
        """
        :param gid: A global tile id known to be within this tileset's range (see contains).
        :returns: gid's custom properties, or {} if it has none.
        """
        return self._tile_properties.get(gid - self.first_gid, {})


class TileMap:
    """
    A grid of tile layers (each a rows x cols grid of gids, 0 meaning
    "empty") sharing one coordinate system, plus the tileset(s) that
    render them and any object layers (spawn points, triggers...)
    carried along for the game to interpret however it wants.

    Layers render in the order they were added (the first one is the
    back-most), the same top-to-bottom-is-back-to-front convention
    gale.ui.Container uses for widgets.

    Usage example:

        tilemap = TileMap(tile_width=16, tile_height=16, cols=50, rows=12)
        tilemap.add_tileset(Tileset(tiles_image, 16, 16, first_gid=1))
        ground = tilemap.add_layer("ground")
        ground[5][10] = 1  # place tile gid 1 at row 5, col 10

        # Every frame:
        tilemap.render(surface, camera)

    Typically built by load_tiled_map rather than by hand — see
    docs/examples/tilemap.rst.
    """

    def __init__(self, tile_width: int, tile_height: int, cols: int, rows: int) -> None:
        """
        :param tile_width: The width, in pixels, of every tile in every layer.
        :param tile_height: The height, in pixels, of every tile in every layer.
        :param cols: How many tile columns every layer has.
        :param rows: How many tile rows every layer has.
        """
        self.tile_width: int = tile_width
        self.tile_height: int = tile_height
        self.cols: int = cols
        self.rows: int = rows
        self.tilesets: List[Tileset] = []
        self.object_layers: Dict[str, List[Any]] = {}
        self._layers: Dict[str, List[List[int]]] = {}
        self._layer_order: List[str] = []
        self._flip_cache: Dict[Tuple[int, int, bool, bool, bool], pygame.Surface] = {}

    @property
    def pixel_width(self) -> int:
        return self.cols * self.tile_width

    @property
    def pixel_height(self) -> int:
        return self.rows * self.tile_height

    def add_tileset(self, tileset: Tileset) -> None:
        """
        :param tileset: A Tileset to make available to this map's layers. Order doesn't matter — tileset_for_gid resolves the right one for a given gid regardless of add order.
        """
        self.tilesets.append(tileset)
        self.tilesets.sort(key=lambda t: t.first_gid)

    def add_layer(
        self, name: str, grid: Optional[List[List[int]]] = None
    ) -> List[List[int]]:
        """
        :param name: This layer's name, used to refer back to it (get_layer, get_gid, collision helpers...).
        :param grid: The layer's initial rows x cols gids. The default value is None, filling a new all-empty (every gid 0) grid.
        :returns: The layer's grid (also reachable later through get_layer), so it can be filled in directly.
        """
        self._layers[name] = (
            grid if grid is not None else [[0] * self.cols for _ in range(self.rows)]
        )
        self._layer_order.append(name)
        return self._layers[name]

    def layer_names(self) -> List[str]:
        """
        :returns: Every tile layer's name, in render order (back to front).
        """
        return list(self._layer_order)

    def get_layer(self, name: str) -> List[List[int]]:
        """
        :param name: A layer added through add_layer.
        :returns: That layer's rows x cols grid of gids.
        """
        return self._layers[name]

    def get_gid(self, layer_name: str, row: int, col: int) -> int:
        """
        :param layer_name: A layer added through add_layer.
        :param row: A tile row.
        :param col: A tile column.
        :returns: The gid at that cell (0 means empty), with any Tiled flip/rotation flags (see decode_gid) already cleared -- use get_flip to read those.
        """
        gid, _, _, _ = decode_gid(self._layers[layer_name][row][col])
        return gid

    def get_flip(self, layer_name: str, row: int, col: int) -> Tuple[bool, bool, bool]:
        """
        :param layer_name: A layer added through add_layer.
        :param row: A tile row.
        :param col: A tile column.
        :returns: (flip_horizontal, flip_vertical, flip_diagonal) for the tile at that cell, decoded from the raw gid Tiled stored there. All False for a tile that isn't flipped/rotated.
        """
        _, flip_horizontal, flip_vertical, flip_diagonal = decode_gid(
            self._layers[layer_name][row][col]
        )
        return (flip_horizontal, flip_vertical, flip_diagonal)

    def set_gid(self, layer_name: str, row: int, col: int, gid: int) -> None:
        """
        :param layer_name: A layer added through add_layer.
        :param row: A tile row.
        :param col: A tile column.
        :param gid: The gid to place there (0 to clear it).
        """
        self._layers[layer_name][row][col] = gid

    def in_bounds(self, row: int, col: int) -> bool:
        """
        :returns: Whether (row, col) falls inside this map's rows x cols grid.
        """
        return 0 <= row < self.rows and 0 <= col < self.cols

    def tile_at(self, x: float, y: float) -> Tuple[int, int]:
        """
        :param x: A world x position, in pixels.
        :param y: A world y position, in pixels.
        :returns: The (row, col) of the tile containing that point (not clamped to this map's bounds — check in_bounds if the point might fall outside it).
        """
        return (int(y // self.tile_height), int(x // self.tile_width))

    def position_of(self, row: int, col: int) -> Tuple[float, float]:
        """
        :param row: A tile row.
        :param col: A tile column.
        :returns: The world pixel position of that cell's top-left corner.
        """
        return (col * self.tile_width, row * self.tile_height)

    def tileset_for_gid(self, gid: int) -> Optional[Tileset]:
        """
        :param gid: A global tile id (a raw one straight from Tiled, with its flip flags still set, works too -- see decode_gid).
        :returns: Whichever added Tileset's range gid falls in, or None (gid is 0/empty, or out of range of every tileset added so far).
        """
        gid, _, _, _ = decode_gid(gid)

        if gid <= 0:
            return None

        match: Optional[Tileset] = None

        for tileset in self.tilesets:
            if tileset.first_gid <= gid:
                match = tileset
            else:
                break

        return match if match is not None and match.contains(gid) else None

    def properties_of_gid(self, gid: int) -> Dict[str, Any]:
        """
        :param gid: A global tile id (a raw one straight from Tiled, with its flip flags still set, works too -- see decode_gid).
        :returns: That tile's custom properties (as set on the tile in Tiled's tileset editor), or {} if it has none or gid is empty/unknown.
        """
        gid, _, _, _ = decode_gid(gid)
        tileset = self.tileset_for_gid(gid)
        return tileset.properties_for(gid) if tileset is not None else {}

    def _tile_image(
        self,
        tileset: Tileset,
        gid: int,
        flip_horizontal: bool,
        flip_vertical: bool,
        flip_diagonal: bool,
    ) -> Tuple[pygame.Surface, Optional[pygame.Rect]]:
        if not (flip_horizontal or flip_vertical or flip_diagonal):
            return tileset.image, tileset.rect_for(gid)

        key = (id(tileset), gid, flip_horizontal, flip_vertical, flip_diagonal)
        tile_image = self._flip_cache.get(key)

        if tile_image is None:
            tile_image = _flipped_tile_image(
                tileset, gid, flip_horizontal, flip_vertical, flip_diagonal
            )
            self._flip_cache[key] = tile_image

        return tile_image, None

    def render(self, surface: pygame.Surface, camera: Optional[Any] = None) -> None:
        """
        :param surface: The surface to draw every layer onto.
        :param camera: A gale.camera.Camera to translate/scale tiles through and cull to only the visible range. The default value is None, rendering the whole map at a 1:1 scale starting at (0, 0).
        """
        if camera is None:
            row_range: range = range(self.rows)
            col_range: range = range(self.cols)
        else:
            row_range, col_range = self._visible_range(camera)

        for name in self._layer_order:
            grid = self._layers[name]

            for row in row_range:
                for col in col_range:
                    raw_gid = grid[row][col]

                    if raw_gid == 0:
                        continue

                    gid, flip_horizontal, flip_vertical, flip_diagonal = decode_gid(
                        raw_gid
                    )
                    tileset = self.tileset_for_gid(gid)

                    if tileset is None:
                        continue

                    tile_image, source_rect = self._tile_image(
                        tileset, gid, flip_horizontal, flip_vertical, flip_diagonal
                    )
                    x, y = self.position_of(row, col)

                    if camera is None:
                        surface.blit(tile_image, (x, y), source_rect)
                    else:
                        dest_rect = camera.apply(
                            pygame.Rect(x, y, self.tile_width, self.tile_height)
                        )
                        surface.blit(tile_image, dest_rect, source_rect)

    def _visible_range(self, camera: Any) -> Tuple[range, range]:
        offset_x, offset_y = camera.offset
        view_width = camera.viewport_width / camera.zoom
        view_height = camera.viewport_height / camera.zoom

        min_col = max(0, int(offset_x // self.tile_width))
        min_row = max(0, int(offset_y // self.tile_height))
        max_col = min(self.cols - 1, int((offset_x + view_width) // self.tile_width))
        max_row = min(self.rows - 1, int((offset_y + view_height) // self.tile_height))

        return range(min_row, max_row + 1), range(min_col, max_col + 1)
