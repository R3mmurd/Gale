`← Back to the main README <../../README.rst>`_

gale.tilemap
=============

A grid of tile layers, sliced from one or more tileset images,
rendered with ``gale.camera`` culling built in — plus, if your map was
made in `Tiled <https://www.mapeditor.org/>`__, a loader for its JSON
export (tile layers, tilesets, and object layers/spawns), and an
optional platformer collision helper (solid walls, one-way platforms)
on top.

None of these three pieces require each other: build a ``TileMap`` by
hand without ever touching Tiled, load one from Tiled and roll your
own collision, or use all three together.

Building a TileMap by hand
------------------------------

.. code-block:: python

   import pygame
   from gale.tilemap import TileMap, Tileset

   tiles_image = pygame.image.load("tiles.png").convert_alpha()
   tileset = Tileset(tiles_image, tile_width=16, tile_height=16, first_gid=1)

   tilemap = TileMap(tile_width=16, tile_height=16, cols=50, rows=12)
   tilemap.add_tileset(tileset)
   ground = tilemap.add_layer("ground")
   ground[10][0] = 1  # gid 1, at row 10, column 0

   # Every frame:
   tilemap.render(surface, camera)  # camera is optional; omit it to render 1:1 at (0, 0)

``tile_at(x, y)``/``position_of(row, col)`` convert between world
pixels and grid cells, the same conversion every tile-based game ends
up writing by hand otherwise.

Loading a map made in Tiled
------------------------------

Export the map as JSON from Tiled (File > Export As..., or
Ctrl+Shift+E) — not the default ``.tmx`` (XML) format:

.. code-block:: python

   from gale.tilemap import load_tiled_map

   tilemap = load_tiled_map("assets/maps/level1.json")

This reads every tile layer (including ones nested inside a Tiled
*group*, flattened in order), every tileset referenced (embedded in
the map or an external ``.tsj``/JSON tileset — see "Known
limitations" below), and every custom tile property (set in Tiled's
tileset editor, read back with ``tilemap.properties_of_gid(gid)``).

Object layers (spawn points, triggers, checkpoints...) come back as
plain data, one ``TiledObject`` per object, keyed by layer name —
``load_tiled_map`` never interprets what an object means, that part is
entirely up to your game:

.. code-block:: python

   for spawn in tilemap.object_layers["spawns"]:
       if spawn.type == "enemy":
           spawn_enemy(spawn.x, spawn.y, kind=spawn.properties.get("kind"))

Collision: solid walls and one-way platforms
------------------------------------------------

An optional layer on top — ``TileMap``/``load_tiled_map`` never
require it, and it never touches ``gale.physics``/Box2D, so it works
the same whether your game uses that or nothing at all.

Mark a tile as a wall or a platform with a custom property named
``"collision"`` (in Tiled's tileset editor, on the tile itself), set
to ``"solid"`` or ``"platform"``:

.. code-block:: python

   from gale.tilemap import move_and_collide

   # In your Player's update(), instead of just self.x += dx; self.y += dy:
   self.x, self.y, hit_wall, hit_floor = move_and_collide(
       tilemap, "ground", self.x, self.y, self.width, self.height, self.vx * dt, self.vy * dt
   )

   if hit_floor and self.vy > 0:
       self.vy = 0
       self.on_ground = True

- **"solid"** blocks movement from every direction — walls, ground.
- **"platform"** only blocks downward movement, and only if the entity
  was already at or above the platform's top edge before the move —
  the standard "stand on it, walk on it, jump up through it from
  below" one-way platform every Mario/Metroidvania-style game has.
  It never blocks sideways movement or upward movement, on purpose.

``move_and_collide`` takes and returns plain floats — ``self.x``/``self.y``,
not a ``pygame.Rect`` — and never rounds them internally either, not
even for the tile-overlap test itself. That matters more than it might
seem: at a typical frame rate, one frame's movement under gravity near
the ground is a fraction of a pixel, so if that got rounded away
anywhere in the chain, an entity resting on solid ground would keep
re-falling that fraction and re-colliding only once every few frames
instead of every frame — which reads as flickering on and off the
ground. Build a ``pygame.Rect`` only where you actually need one (to
render, or to hit-test against something else):
``pygame.Rect(round(self.x), round(self.y), self.width, self.height)``.

``move_and_collide`` also resolves one axis at a time and snaps flush
against whatever it hits (rather than just refusing to move), and
sweeps the whole distance travelled this call rather than only
checking the destination cell — a fast-moving body can't tunnel
through a thin wall/platform by skipping over it in a single big
step.

Anything beyond solid/platform — slopes, ladders, conveyor belts,
damage tiles — is deliberately not built in: define your own custom
tile property (Tiled lets you add any property, of any name, to any
tile) and read it yourself with ``tilemap.properties_of_gid(gid)``,
the same way ``collision`` is read. ``collision_type_at`` and
``move_and_collide`` also both take a ``collision_property`` argument,
if you'd rather reuse a property you already have under a different
name.

Isometric maps
------------------

``gale.tilemap.isometric`` renders the same rows x cols grid of gids
as a 2:1 isometric diamond projection instead of an axis-aligned one
— useful for a "Commandos"-style top-down-but-diamond prototype.
``IsometricTileMap`` is a drop-in ``TileMap`` subclass: same
``Tileset``/layers/``object_layers`` API, only ``position_of``,
``tile_at``, ``pixel_width``/``pixel_height`` and ``render`` change:

.. code-block:: python

   import pygame
   from gale.tilemap.isometric import IsometricTileMap

   tiles_image = pygame.image.load("iso_tiles.png").convert_alpha()
   tileset = Tileset(tiles_image, tile_width=64, tile_height=32, first_gid=1)

   tilemap = IsometricTileMap(tile_width=64, tile_height=32, cols=20, rows=20)
   tilemap.add_tileset(tileset)
   ground = tilemap.add_layer("ground")
   ground[5][10] = 1  # gid 1, at row 5, column 10

   # Every frame:
   tilemap.render(surface, camera)  # camera is optional, same as TileMap

``(row 0, col 0)`` sits at the map's top corner, row increasing
toward the bottom-left and col toward the bottom-right. Tile images
are anchored at their top-center (the diamond's topmost point), since
an isometric tile image is wider than it is tall. The module also
exposes the underlying ``cartesian_to_isometric``/
``isometric_to_cartesian`` functions directly, for converting any
cartesian world/grid position to/from isometric screen space without
going through a map at all — useful on their own in any context that
needs isometric coordinate math (an entity's world position, a
minimap, a cursor), not just for tile maps.

Known limitations
-------------------

- JSON only — Tiled's original XML ``.tmx``/``.tsx`` formats aren't
  supported. Re-export as JSON (map) and, for any *external* tileset
  file specifically, JSON (``.tsj``) instead of XML — or just embed
  the tileset directly in the map, which sidesteps the issue entirely
  (Tiled's "Embed Tileset" button, in the tileset editor).
- Infinite maps aren't supported (disable "Infinite" in Tiled's map
  properties before exporting).
- Tile layer data must be uncompressed (Tiled's default "CSV" tile
  layer format) — Base64, with or without zlib/gzip compression, isn't
  supported. ``load_tiled_map`` raises a clear error naming the
  offending layer for both of these, rather than silently
  misinterpreting the data.
- No animated tiles (Tiled's per-tile animation frames).
- ``move_and_collide`` only understands "solid"/"platform" — anything
  else is on the game to interpret, as described above.
