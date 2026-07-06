# Nightwatch

A small top-down stealth demo: sneak past two patrolling guards and a
skittish civilian to reach the exit. It exists to exercise gale.ai (and
the rest of gale) end to end, in an actual running game rather than in
isolated snippets.

Every visual is drawn with `pygame.draw` primitives (no image, font, or
sound assets), so it runs as-is. The nav graph's edges are rendered as
faint lines for the same reason the guards patrol it out loud: this is
a showcase, not a polished game.

## Running it

```bash
cd examples/nightwatch
python main.py
```

## Controls

- `WASD` / arrow keys: move
- `Enter`: confirm (start, back to title)
- `Ctrl+R`: restart the level at any time (a keyboard combo, see `gale.input_handler`)
- `Escape`: quit

## What it exercises

- `gale.ai.steering`: `Kinematic`, `Seek`, `Pursue`, `Flee`, `Wander` drive the player's physical body and every NPC's movement.
- `gale.ai.behavior_tree`: each `Guard`'s decision (chase / investigate / patrol) is a `Selector`/`Sequence`/`Condition`/`Action` tree, re-evaluated fresh every tick (see the docstring in `src/entities/Guard.py` for why every `Action` returns `SUCCESS`, never `RUNNING`).
- `gale.ai.decision_tree`: the `Civilian` picks between fleeing and wandering with a single `DecisionNode`, as a simpler alternative to a behavior tree.
- `gale.ai.blackboard`: all `Guard`s share one `Blackboard`. A guard that spots the player posts `alert_position`/`is_alerted` to it, so the *other* guard reacts and investigates without ever seeing the player itself. The HUD's "SPOTTED!" flash is a `Blackboard.observe` callback reacting to `is_alerted` immediately, instead of polling it every frame.
- `gale.ai.graph` / `gale.ai.search`: `src/level.py` builds a `NavGraph` (a visibility graph over the level's wall corners) once, and guards path across it with `a_star` to investigate the last known player position, walking around walls instead of through them.
- `gale.ai.agent.Agent`: `Player`, `Guard`, and `Civilian` are all `Agent` subclasses, spawned through `gale.factory.Factory`.
- `gale.state`: a `StateMachine` drives `TitleState` → `PlayState` → `GameOverState`/`VictoryState`.
- `gale.input_handler`: movement bindings (two keys per direction) plus the `Ctrl+R` modifier combo.
- `gale.particle_system`: a burst plays wherever the player ends the level, colored red when caught and gold on the exit.
- `gale.timer`: `Timer.tween` fades the level in on entry; `Timer.after` delays the state change until the particle burst has had a moment to play, and resets the one-shot alert flash.
- `gale.text`: all HUD/menu text.

`gale.ai.graph.DependencyGraph` is the one piece of `gale.ai` this demo
doesn't use — a prerequisite/build-order graph doesn't have a natural
place in real-time gameplay like this. See `docs/examples/gale_ai.rst`
for a runnable example of it on its own.
