# Campfire & Waterfall

A non-interactive ambient scene — nothing to win, nothing to control
beyond quitting — built to show `gale.particle_system`'s shapes,
textures, and their combination side by side, and `gale.timer`'s
groups, driving two continuously-emitting effects at once:

- **Campfire**: sharp, shaped flame particles (`SHAPE_TRIANGLE`/
  `SHAPE_DIAMOND`) rising over soft, textured smoke (a procedurally
  generated blob, tinted grey — no image files, see
  `src/textures.py`).
- **Waterfall**: spray that mixes both on the very same
  `ParticleSystem` — `set_shapes` and `set_textures` configured
  together, so every burst comes out with a blend of plain-shaped and
  soft, textured droplets — falling into a splash at its base.

A `ParticleSystem` burst is one-shot; both effects work by having
`gale.timer.Timer.every` spawn a fresh, short-lived burst on a tight
interval, layering many of them to read as one continuous flame/smoke
column/waterfall — see `src/Campfire.py`/`src/Waterfall.py` for the
pattern. Each one tags its own timers with `group=self`, so
`Timer.clear(group=campfire)` would stop just that effect without
touching the other.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/campfire_waterfall
python main.py
```

## Controls

- `Escape`: quit
