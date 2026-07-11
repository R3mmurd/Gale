# Outpost

A small isometric, "Commandos"-style stealth prototype: sneak across a
guarded outpost and hack a terminal to win. It exists to exercise four
gale features added for a university course -- isometric tilemaps,
vision-cone perception, hierarchical state machines, and minimax with
alpha-beta pruning -- in an actual running game rather than in isolated
snippets.

Movement, collision, and perception all happen in a plain cartesian
"world space" (see `settings.CELL_SIZE`), exactly like a regular
top-down game; only rendering projects that world position through the
isometric diamond projection (`src/level.py`'s `to_screen`). The
isometric tileset is three small diamonds drawn with `pygame.draw` at
startup, so, like every other from-scratch example in this repository,
it needs no image, font, or sound assets to run.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/outpost
python main.py
```

## Controls

- `WASD` / arrow keys: move (also moves the cursor in the terminal minigame)
- `Enter` / `Space`: confirm (start, interact with the terminal, place a mark in the minigame)
- `Ctrl+R`: restart the level at any time
- `Escape`: quit

## What it exercises

- `gale.tilemap.isometric.IsometricTileMap`: `src/level.py`'s `build_tilemap` lays out a 12x10 grid with a floor/wall/terminal tileset generated in code, and `PlayState` renders it every frame with `tilemap.render(surface)`. `cartesian_to_isometric` (exposed directly by the module) is reused by `to_screen` to project every entity's world position into the same diamond projection, without going through the tilemap itself.
- `gale.ai.perception`: each `Guard` owns a `VisionCone` (a near zone for instant detection, a far zone for partial, distance-scaled detection) feeding a `Perception`, which turns sightings blocked by the level's wall obstacles into an `AlertLevel` (`UNAWARE`/`SUSPICIOUS`/`ALERTED`) posted, together with the last known player position, on the guard's own `Blackboard`.
- `gale.state.HierarchicalState`: `src/entities/guard_states.py`'s `Patrol` is a `HierarchicalState` whose `walking`/`looking_around` substates drive the guard back and forth along its patrol path and pause to scan; it sits inside each guard's top-level `patrol`/`search`/`alert` `StateMachine`, whose transitions are driven directly by the `Perception`'s `AlertLevel` (see `Guard.update`).
- `gale.ai.minimax`: `src/hack_game.py`'s terminal defense AI is a tic-tac-toe opponent that always plays the move `gale.ai.minimax.best_move` (full-depth alpha-beta search) deems optimal -- it never loses, so the player must win or draw to hack the terminal and win the game.
- `gale.ai.graph.NavGraph` / `gale.ai.search.a_star`: `src/level.py` builds a visibility graph over the level's wall corners once, and a guard in the `search` state paths across it to the player's last known position, walking around walls instead of through them (the same approach `examples/nightwatch/src/level.py` uses).
- `gale.ai.agent.Agent`: `Player` and `Guard` are both `Agent` subclasses, spawned through `gale.factory.Factory`.
- `gale.state.StateMachine`: drives `TitleState` -> `PlayState` -> `TerminalHackState` -> `VictoryState`/`GameOverState` at the game level, and each `Guard`'s own patrol/search/alert machine at the entity level.
- `gale.input_handler`: movement bindings (two keys per direction), a shared `confirm` action reused across the title screen, the terminal interact prompt, and the minigame's cursor, plus the `Ctrl+R` modifier combo.
- `gale.particle_system`: a burst plays wherever the player ends the level, colored red when caught and green on a successful hack.
- `gale.timer`: `Timer.tween` fades the level in on entry; `Timer.after` delays the state change until the particle burst has had a moment to play.
- `gale.text`: all HUD/menu/minigame text.

## Design notes

- The map, its two wall segments, the guards' patrol points, and the
  terminal's position are all built directly in code (`src/level.py`),
  the same "no Tiled file needed" approach `examples/nightwatch` takes.
- Losing the terminal minigame just denies access (back to `PlayState`
  restarted fresh) rather than ending the game -- only a guard reaching
  `ALERTED` within catching distance is a game over.
