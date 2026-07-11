# Circuit

A small online racing prototype built to exercise the newest additions
to `gale.net` (client-side prediction/server reconciliation, entity
interpolation, and lag compensation) together with `gale.ai`'s
steering-based path following. One lap-and-a-bit around a small oval,
60-90 seconds to play - not a full racing game, the same way
`examples/rally` is a minimal 2-paddle Pong rather than a full arcade
game.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run it:

```bash
cd examples/circuit
python main.py
```

Pick **Host Race** to open a server and start racing the AI car
immediately (a solo practice lap is still a complete race); a second
player can pick **Join Race** at any point and type the host's `ip:port`
(or click **Scan LAN**) to join the race already under way. To try both
sides locally, host in one window and join at `127.0.0.1:9100` in
another.

## Controls

- `Up`/`W`, `Down`/`S`: throttle / brake
- `Left`/`A`, `Right`/`D`: steer
- `Space`: attempt to bump the AI car (joiner only - see "Lag
  compensation" below)
- `Enter`: confirm the highlighted menu item
- `Escape`: quit

## How it plays

- `TitleState`: Host Race / Join Race / Quit, built with `gale.ui`.
- `LobbyState`: as host, opens a `gale.net.Server`, advertises it over
  LAN discovery, and heads straight into `PlayState` (a joiner can
  still connect later); as the joining player, connects a
  `gale.net.Client` to a typed or discovered address.
- `PlayState`: the host simulates every car authoritatively - its own,
  the joiner's, and the AI's - and broadcasts a `"snapshot"` every
  tick. See "What it exercises" below for how each car demonstrates a
  different networking recipe.
- `GameOverState`: final lap counts, a button back to the title screen.

The track (`src/track.py`) is a small rectangular oval - an outer rect
minus an inner one, so the driveable surface is the ring between them -
drawn entirely with `pygame.draw` primitives. First to `LAPS_TO_WIN`
(2) laps wins; driving off the ring instantly saps your speed.

## What it exercises

- **`gale.net.PredictionBuffer`** (client-side prediction + server
  reconciliation): the joiner's own car is moved immediately from
  local input (`src/car.py`'s `apply_input`, a pure function of
  `{x, y, heading, speed}` + `{throttle, steer}` + `dt`), recorded
  alongside its input in a `PredictionBuffer`, and reconciled against
  the host's authoritative echo of it whenever a `"snapshot"` arrives
  (`PlayState._on_snapshot`). This is exactly the limitation
  `examples/rally`'s README calls out for its own joining paddle ("No
  client-side prediction/reconciliation") - `circuit` is the example
  that has it.
- **`gale.net.SnapshotInterpolator`** (entity interpolation): the
  joiner buffers and smooths the host's car and the AI car through two
  `SnapshotInterpolator` instances (`PlayState._update_joiner`),
  sampled a little in the past (`settings.INTERP_DELAY` plus half the
  measured RTT) instead of snapping to the latest UDP packet - the
  same recipe `examples/rally/src/snapshot_buffer.py` implemented by
  hand, now promoted into `gale.net` itself.
- **`gale.net.lag_compensated_position`** (lag compensation): the host
  keeps its own timeline of the AI car's position in a
  `SnapshotInterpolator` (`ai_lag_history`). When the joiner presses
  `Space` to "bump" the AI car, the host does not check that against
  the AI's *current* position - by the time the joiner's packet
  arrives, the AI has moved on from where they actually saw it - it
  rewinds `ai_lag_history` back by the joiner's RTT/2 plus their own
  interpolation delay and checks the bump against *that* instead (see
  `PlayState._on_bump_attempt`'s docstring for the full explanation).
- **`gale.ai.steering` path following**: the AI racer
  (`src/ai_car.py`) is a `gale.ai.steering.Kinematic` steered by
  `Arrive` towards successive waypoints of a path computed with
  `gale.ai.search.a_star` over the track's
  `gale.ai.graph.NavGraph` (`src/track.py`'s `WAYPOINTS`/
  `build_nav_graph`); once a lap's path is exhausted, `a_star` is asked
  for the next one around the same one-way loop. Simulated only on the
  host, its resulting state is mirrored into the exact same
  `{x, y, heading, speed}` shape the human cars use and broadcast/
  interpolated identically - a remote car doesn't know or care whether
  it's a human or the AI on the other end.

## Known limitations

- No NAT traversal: internet play needs a reachable `host:port`.
- Reconciled state is applied by snapping, not smoothly correcting
  towards it - good enough to see the mechanism work; a shipping game
  would likely blend the visible correction over a few frames.
- A joiner connecting mid-race spawns at the start line regardless of
  how far into the race the host already is, rather than a synced
  grid start.
- `TextInput` (used for the "host:port" field) only supports ASCII
  input, not IME/composed characters - see `gale.ui.TextInput`'s
  docstring.
