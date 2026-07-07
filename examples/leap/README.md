# Leap

A small platformer built to exercise `gale.physics`'s three body
types together: static ground, a dynamic player, and a kinematic
moving platform that ferries you across a gap.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/leap
python main.py
```

## Controls

- Arrow keys / WASD: move
- `Space`/`Up`/`W`: jump
- `Enter`: confirm (start, and continue past the win/game over screen)
- `Escape`: quit

## How it plays

- `TitleState`: title screen. Press Enter to play.
- `PlayState`: two ground segments with a gap between them, and a
  kinematic platform (`src/Level.py`) that oscillates back and forth
  to carry you across it. Reach the goal on the far side to win;
  falling through the gap (or off the level) ends the run.
- `WinState`/`GameOverState`: press Enter to go back to the title
  screen and play again.

## What it uses

- `gale.physics.World`: one per `PlayState`, created in `enter()`,
  stepped once a frame via `world.update(dt)` (see
  `src/states/PlayState.py`).
- All three `gale.physics` body types, in `src/Level.py`/`src/Player.py`:
  **static** ground segments and boundary walls, a **dynamic** player
  (`Player.jump`/`Player.move` drive it via `apply_impulse`/
  `set_velocity`), and a **kinematic** platform whose velocity is
  simply flipped at each end of its range (`Level.update`).
- `Body.touching_bodies` for the player's grounded check
  (`Player.is_grounded`), tagging what counts as "ground" via
  `user_data` rather than treating every contact as solid footing.
- `World.on_collision_begin` for the win condition: the goal is a
  sensor fixture, and reaching it (registered in `PlayState.enter`)
  transitions straight to `WinState`.
- `gale.state`/`gale.text.render_text`, the same shape every other
  example uses for its states/HUD.

## Credits

- Source code by [R3mmurd](https://github.com/R3mmurd).
- No image/font/sound assets — everything is drawn with
  `pygame.draw` primitives.
