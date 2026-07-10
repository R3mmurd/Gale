# Planks

A small platformer built to exercise `gale.tilemap`: loading a level
made in [Tiled](https://www.mapeditor.org/) and exported as JSON,
one-way platform/solid wall collision, object-layer spawns, and a
`gale.camera` that scrolls across a level wider than the viewport.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/planks
python main.py
```

## Controls

- Arrow keys / WASD: move
- `Space`/`Up`/`W`: jump
- `Enter`: confirm (start, and play again after winning)
- `Escape`: quit

## How it plays

- `TitleState`: title screen. Press Enter to play.
- `PlayState`: a level 40 tiles wide (`assets/tilemaps/level.json`,
  made by hand in Tiled's JSON format — see `assets/graphics/tileset.png`
  for the three tiles it uses: ground, a one-way platform, and a solid
  wall). Jump onto the floating platforms to collect all three coins,
  clear the wall in the middle, then reach the flag at the far end.
  Reaching the flag before collecting every coin does nothing — the
  goal only counts once every coin is collected.
- `WinState`: press Enter to go back to the title screen and play
  again.

## What it uses

- `gale.tilemap.load_tiled_map`, once in `PlayState.enter()`, to load
  the whole level: its tile layer (nested inside a Tiled *group*, to
  exercise that too), its tileset (with the two custom `collision`
  tile properties, `"solid"`/`"platform"`), and its object layer
  (`spawns`) — the player's start position, every coin, and the goal
  are all Tiled objects, read as plain data in `PlayState.enter()`
  rather than encoded as extra tile layers.
- `gale.tilemap.move_and_collide`, every frame in `Player.update()`:
  resolves the player's movement against the `"ground"` layer, stopping
  at solid tiles (the wall) in every direction and at platform tiles
  only when landing on top of them from above — jump up through a
  platform from underneath, or walk under it, and it doesn't block you
  at all.
- `gale.camera.Camera`, following the player with smoothing and
  `bounds` clamped to the level's actual pixel size
  (`tilemap.pixel_width`/`pixel_height`), so the view never scrolls
  past either edge.
- `gale.state`/`gale.text.render_text`, the same shape every other
  example uses for its states/HUD.

## Credits

- Source code by [R3mmurd](https://github.com/R3mmurd).
- `assets/graphics/tileset.png` is a small hand-drawn tileset (three
  16x16 tiles) made for this example; everything else is drawn with
  `pygame.draw` primitives.
