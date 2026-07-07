# Hillclimb

A small vehicle-physics demo built to exercise `gale.physics`'s
joints: a chassis and two wheels connected by motorized wheel joints
(with a spring/damper suspension), driving over bumpy static terrain.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/hillclimb
python main.py
```

## Controls

- Right arrow / `D`: accelerate
- Left arrow / `A`: reverse
- `Enter`: confirm (start, and continue past the win/game over screen)
- `Escape`: quit

## How it plays

- `TitleState`: title screen. Press Enter to play.
- `PlayState`: drive across bumpy procedurally-generated terrain
  (`src/Terrain.py`, a chain of static polygon segments following a
  sum of two sine waves) toward a goal at the far end. Tip the car
  over too far and it's game over instead.
- `WinState`/`GameOverState`: press Enter to go back to the title
  screen and try again.

## What it uses

- `gale.physics.World`: one per `PlayState`, stepped once a frame via
  `world.update(dt)`.
- `gale.physics`'s joints (`src/Car.py`): a dynamic chassis and two
  dynamic wheels, each attached to the chassis with a `WheelJoint`
  (`frequency`/`damping_ratio` give it a real spring/damper
  suspension; `enable_motor`/`motor_speed`/`max_motor_torque` drive
  it). Accelerating/reversing just sets both wheel joints'
  `motor_speed` — the suspension and traction are what turn that into
  actual forward motion over uneven ground.
- A static body per terrain segment (`src/Terrain.py`), each a small
  convex polygon fixture rather than one long chain, since Box2D
  polygons must be convex.
- `gale.state`/`gale.text.render_text`, the same shape every other
  example uses for its states/HUD.

## Credits

- Source code by [R3mmurd](https://github.com/R3mmurd).
- No image/font/sound assets — everything is drawn with
  `pygame.draw` primitives.
