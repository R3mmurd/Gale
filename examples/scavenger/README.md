# Scavenger

A small top-down coin-collecting game built to exercise `gale.camera`:
following a target, zooming, screen shake, and clamping the view to
the world's bounds.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/scavenger
python main.py
```

## Controls

- Arrow keys / WASD: move
- `+`/`-`: zoom in/out
- `Enter`: confirm (start, and play again after winning)
- `Escape`: quit

## How it plays

- `TitleState`: title screen. Press Enter to play.
- `PlayState`: the world (1600x1200) is much bigger than the viewport
  (400x240) — a grid is drawn across it so scrolling is visible.
  Collect every coin scattered across the map; the camera shakes
  briefly each time you pick one up. Collect them all to win.
- `WinState`: press Enter to go back to the title screen and play
  again (coins and their positions are re-randomized).

## What it uses

- `gale.camera.Camera`, created once in `PlayState.enter()`:
  - `camera.follow(self.player, rate=...)`: tracks the player every
    `update()` with frame-rate-independent smoothing rather than
    snapping to it.
  - `camera.bounds`: a `pygame.Rect` covering the whole world, so the
    view never scrolls past its edges.
  - `camera.zoom`: adjusted directly by the `zoom_in`/`zoom_out`
    bindings.
  - `camera.shake(...)`: triggered on every coin pickup.
  - `camera.world_to_screen`/`camera.apply`: every render call
    (`Player.render`, `Coin.render`, and the background grid in
    `PlayState._render_grid`) goes through the camera to turn a world
    position into where it should actually be drawn on screen.
- `gale.state`/`gale.text.render_text`, the same shape every other
  example uses for its states/HUD.

## Credits

- Source code by [R3mmurd](https://github.com/R3mmurd).
- No image/font/sound assets — everything is drawn with
  `pygame.draw` primitives.
