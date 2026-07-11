"""
gale.tilemap: grid-of-tiles maps — rendering (with gale.camera culling
built in), tileset slicing, and grid/pixel coordinate conversion,
independent of where the map data comes from. IsometricTileMap (plus
the standalone cartesian_to_isometric/isometric_to_cartesian
transforms) renders the same kind of layered, tileset-backed map in a
diamond/isometric projection instead of the default orthogonal one.

load_tiled_map loads a map exported by Tiled (https://www.mapeditor.org/)
as JSON, including its tilesets and object layers (spawns, triggers...,
exposed as plain data for the game to interpret).

Collision is a separate, opt-in layer on top (move_and_collide):
solid tiles block in every direction, platform tiles are one-way
(stand on top, jump up through). Anything richer (slopes, hazards,
ladders...) is deliberately left to the game, read from whatever
custom tile properties it defines in Tiled — this module never
requires gale.physics/Box2D, or any particular physics approach at
all.

See docs/examples/tilemap.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .collision import CollisionType, collision_type_at, move_and_collide
from .isometric import (
    IsometricTileMap,
    cartesian_to_isometric,
    isometric_to_cartesian,
)
from .tiled_loader import TiledLoadError, TiledObject, load_tiled_map
from .tilemap import TileMap, Tileset

__all__ = [
    "CollisionType",
    "IsometricTileMap",
    "TileMap",
    "TiledLoadError",
    "TiledObject",
    "Tileset",
    "cartesian_to_isometric",
    "collision_type_at",
    "isometric_to_cartesian",
    "load_tiled_map",
    "move_and_collide",
]
