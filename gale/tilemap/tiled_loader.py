"""
This file contains the implementation of load_tiled_map: builds a
TileMap from a map exported by Tiled (https://www.mapeditor.org/) as
JSON (File > Export As... > JSON map files, or Ctrl+Shift+E) — not the
XML .tmx format.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import pygame

from .tilemap import TileMap, Tileset


class TiledLoadError(Exception):
    """Raised when a Tiled JSON export uses a feature load_tiled_map doesn't support."""


@dataclass
class TiledObject:
    """
    One entry from a Tiled object layer (a spawn point, a trigger, a
    checkpoint...) — plain data. What each one means, and what to do
    with it, is entirely up to the game; load_tiled_map never
    interprets name/type itself.
    """

    name: str
    type: str
    x: float
    y: float
    width: float
    height: float
    properties: Dict[str, Any] = field(default_factory=dict)


def load_tiled_map(path: str) -> TileMap:
    """
    :param path: Path to a map exported by Tiled as JSON.
    :returns: A TileMap with every tile layer, tileset, and object layer the export contains.
    :raises TiledLoadError: If the map is infinite, or uses a tile layer/tileset encoding this loader doesn't support (compressed tile data, or a tileset referenced in the old XML .tsx format).
    """
    with open(path, "r", encoding="utf-8") as f:
        map_data = json.load(f)

    if map_data.get("infinite"):
        raise TiledLoadError(
            "Infinite maps are not supported. In Tiled, disable "
            "Map > Map Properties > Infinite before exporting."
        )

    tile_width = map_data["tilewidth"]
    tile_height = map_data["tileheight"]
    cols = map_data["width"]
    rows = map_data["height"]

    tilemap = TileMap(tile_width, tile_height, cols, rows)
    base_dir = os.path.dirname(path)

    for tileset_ref in map_data.get("tilesets", []):
        tilemap.add_tileset(_load_tileset(tileset_ref, base_dir))

    for layer in map_data.get("layers", []):
        _load_layer(tilemap, layer, cols, rows)

    return tilemap


def _load_tileset(tileset_ref: Dict[str, Any], base_dir: str) -> Tileset:
    if "source" in tileset_ref:
        source = tileset_ref["source"]

        if source.endswith(".tsx"):
            raise TiledLoadError(
                f"External tileset {source!r} is in Tiled's XML format (.tsx), "
                "which load_tiled_map does not support. Re-export it as a JSON "
                "tileset (.tsj) from Tiled, or embed the tileset directly in "
                "the map instead of referencing an external file."
            )

        tileset_path = os.path.join(base_dir, source)

        with open(tileset_path, "r", encoding="utf-8") as f:
            tileset_data = json.load(f)

        tileset_base_dir = os.path.dirname(tileset_path)
        first_gid = tileset_ref["firstgid"]
    else:
        tileset_data = tileset_ref
        tileset_base_dir = base_dir
        first_gid = tileset_ref["firstgid"]

    image_path = os.path.join(tileset_base_dir, tileset_data["image"])
    image = pygame.image.load(image_path).convert_alpha()

    tile_properties: Dict[int, Dict[str, Any]] = {}

    for tile_entry in tileset_data.get("tiles", []):
        properties = _properties_to_dict(tile_entry.get("properties", []))

        if properties:
            tile_properties[tile_entry["id"]] = properties

    return Tileset(
        image,
        tileset_data["tilewidth"],
        tileset_data["tileheight"],
        first_gid=first_gid,
        margin=tileset_data.get("margin", 0),
        spacing=tileset_data.get("spacing", 0),
        tile_properties=tile_properties,
    )


def _load_layer(tilemap: TileMap, layer: Dict[str, Any], cols: int, rows: int) -> None:
    layer_type = layer.get("type")

    if layer_type == "group":
        for child in layer.get("layers", []):
            _load_layer(tilemap, child, cols, rows)
    elif layer_type == "tilelayer":
        tilemap.add_layer(layer["name"], _load_tile_grid(layer, cols, rows))
    elif layer_type == "objectgroup":
        tilemap.object_layers[layer["name"]] = [
            _load_object(obj) for obj in layer.get("objects", [])
        ]


def _load_tile_grid(layer: Dict[str, Any], cols: int, rows: int) -> List[List[int]]:
    data = layer["data"]

    if not isinstance(data, list):
        raise TiledLoadError(
            f"Layer {layer.get('name')!r} uses compressed/base64-encoded tile "
            "data, which load_tiled_map does not support. In Tiled, set "
            "File > Preferences > Saving files > Tile Layer Format to "
            '"CSV" and re-export.'
        )

    return [data[row * cols : (row + 1) * cols] for row in range(rows)]


def _load_object(obj: Dict[str, Any]) -> TiledObject:
    return TiledObject(
        name=obj.get("name", ""),
        type=obj.get("type") or obj.get("class") or "",
        x=obj["x"],
        y=obj["y"],
        width=obj.get("width", 0),
        height=obj.get("height", 0),
        properties=_properties_to_dict(obj.get("properties", [])),
    )


def _properties_to_dict(properties: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {prop["name"]: prop["value"] for prop in properties}
