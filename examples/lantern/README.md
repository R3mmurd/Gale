# Lantern

A small top-down exploration game built to exercise `gale.stencil`:
the room is covered in darkness except for a circle around the
player, punched out of the overlay every frame.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/lantern
python main.py
```

## Controls

- Arrow keys / WASD: move
- `Enter`: confirm (start, and play again after winning)
- `Escape`: quit

## How it plays

- `TitleState`: title screen. Press Enter to play.
- `PlayState`: a single room (`src/Room.py`), covered in darkness
  except for a circle of light around the player. Bump around the
  walls to feel your way to the two torches — each one grows the
  light radius — then find the exit tile in the far corner.
- `WinState`: press Enter to go back to the title screen and play
  again.

## What it uses

- `gale.stencil.Stencil`, created once in `PlayState.enter()` and
  redrawn every frame in `PlayState._render_darkness`:
  1. Everything in the room (floor, walls, torches, exit, player) is
     drawn normally first.
  2. `stencil.clear()` then `stencil.draw(...)` draws a white circle,
     centered on the player, sized to the current `light_radius`, onto
     the stencil's own mask surface.
  3. A dark, near-opaque overlay surface is filled fresh, then
     `stencil.apply(overlay, invert=True)` punches that circle out of
     it — everywhere outside the circle stays dark, everywhere inside
     it becomes fully transparent again.
  4. The overlay is blit on top of everything else, last.
- `gale.timer.Timer.tween`: each torch smoothly grows `light_radius`
  over `settings.LIGHT_GROW_TIME` seconds instead of snapping to the
  new value.
- `gale.state`/`gale.text.render_text`, the same shape every other
  example uses for its states/HUD.

## Credits

- Source code by [R3mmurd](https://github.com/R3mmurd).
- No image/font/sound assets — everything is drawn with
  `pygame.draw` primitives.
