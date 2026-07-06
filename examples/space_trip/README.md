# Space Trip

A simple demo game of a flying saucer tripping through infinite space.
Stars scroll in from the right; fly into them to collect points.
Rocks scroll in too, less predictably — touch one and the saucer is
destroyed. Reach the target score before that happens to win.

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
- `Enter`: confirm (start, and continue past the victory/game over screen)
- `Escape`: quit

## How it plays

- `StartState`: title screen. Press Enter to play.
- `PlayState`: collect stars (+100 points each) and dodge the rocks
  that scroll in at random intervals. Colliding with a rock destroys
  the saucer (a particle burst plays where it was, plus a sound
  effect) and leads to `GameOverState` shortly after. Reaching
  `settings.SCORE_TO_WIN` instead leads to `VictoryState`.
- `GameOverState` / `VictoryState`: show the final score. Press Enter
  to go back to the title screen and play again.

## What it uses

This example is intentionally simple, closer to what `gale-admin
create-project` scaffolds than to a full showcase — a good first
example to read. See `examples/nightwatch` for a larger one built
specifically to exercise `gale.ai`.

- `gale.game.Game`: the `SpaceTrip` class driving the game loop.
- `gale.state`: a `StateMachine` with four states
  (`start`/`play`/`victory`/`game_over`) — see their
  `enter`/`update`/`render`/`on_input` methods for the basic shape
  every state follows, and `PlayState.exit` for why `Timer.clear()`
  matters when a state that scheduled timers can be re-entered (star
  and rock spawning would otherwise keep running once per past
  playthrough, on top of the current one).
- `gale.input_handler`: arrow keys bound to `left`/`right`/`up`/`down`,
  and `Enter` to `confirm`, in `settings.py`.
- `gale.factory.Factory`: `Space` uses one each for `Star` and `Rock`.
- `gale.timer.Timer`: `Space` uses `Timer.every` to spawn a new star
  on a fixed schedule, and `Timer.after` (rescheduling itself) to spawn
  rocks at a random interval instead. `PlayState` uses `Timer.after` to
  delay the transition to `GameOverState` until the explosion has had a
  moment to play.
- `gale.particle_system.ParticleSystem`: the burst when the saucer is
  destroyed.
- `gale.text.render_text`: the score display and every menu screen.

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
- Take star sound effect by [Aeva](https://opengameart.org/users/aeva).
- Rock texture and death flash sound effect: source/author not on
  file yet — please fill this in with proper attribution if they come
  from a licensed source.
