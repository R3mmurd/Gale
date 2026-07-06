# Space Trip

A simple demo game of a flying saucer tripping through infinite space.
Stars scroll in from the right; fly into them to collect points before
they scroll off the left edge.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/space_trip
python main.py
```

## Controls

- Arrow keys: move the flying saucer
- `Escape`: quit

## What it uses

This example is intentionally simple, closer to what `gale-admin
create-project` scaffolds than to a full showcase — a good first
example to read. See `examples/nightwatch` for a larger one built
specifically to exercise `gale.ai`.

- `gale.game.Game`: the `SpaceTrip` class driving the game loop.
- `gale.state`: a single-state `StateMachine` (`PlayState`) — see its
  `enter`/`update`/`render`/`on_input` methods for the basic shape
  every state follows.
- `gale.input_handler`: arrow keys bound to `left`/`right`/`up`/`down`
  in `settings.py`, read in `PlayState.on_input`.
- `gale.factory.Factory`: `Space` uses one to spawn `Star` instances.
- `gale.timer.Timer`: `Space` uses `Timer.every` to spawn a new star
  every few seconds.
- `gale.text.render_text`: the score display in `PlayState.render`.

`FlyingSaucer`'s own movement (in `src/FlyingSaucer.py`) is a small
hand-rolled velocity integrator, not `gale.ai.steering` — it predates
that module and is direct player input, not an autonomous behavior.

## Credits

- Source code by [R3mmurd](https://github.com/R3mmurd).
- Background texture by [Westbeam](https://opengameart.org/users/westbeam).
- UFO texture by [Bleed](https://opengameart.org/users/bleed).
- Star texture by [ecovah](https://opengameart.org/users/ecovah).
- Stars font by [Tim_Supermonkey](https://opengameart.org/users/timsupermonkey).
- Space music by [onky](https://opengameart.org/users/onky).
- Take start sound effect by [Aeva](https://opengameart.org/users/aeva).
