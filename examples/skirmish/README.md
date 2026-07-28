# Skirmish

A small squad-tactics demo: get your 3-person squad to the extraction
zone while a captain and their guards patrol, spot you, take up
tactical positions, and shoot back. It exists to exercise the rest of
`gale.ai` — the parts `examples/nightwatch` doesn't already cover — end
to end, in an actual running game rather than in isolated snippets.

Every visual is drawn with `pygame.draw` primitives (no image, font, or
sound assets), so it runs as-is.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/skirmish
python main.py
```

## Controls

- `WASD` / arrow keys: move the squad (the two followers tag along in formation)
- `Enter`: confirm (start, back to title)
- `Ctrl+R`: restart the level at any time
- `Escape`: quit

## What it exercises

- `gale.ai.formation`: the squad's two followers are steered towards
  whatever slot `FormationManager` assigns them in a `WedgeFormation`
  behind the leader — "two-level" steering, since a follower only ever
  chases its own slot, never the squad's actual plan.
- `gale.ai.fuzzy`: each `Guard`'s alertness is a `FuzzyRuleSet` over
  fuzzified distance-to-squad and line-of-sight, defuzzified into one
  crisp number, so it rises and falls smoothly instead of snapping
  between "calm" and "alert".
- `gale.ai.scripting`: once alert, a `Guard`'s top-level decision
  (fight / investigate / patrol) is a `BehaviorTree` built with
  `build_behavior_tree` from a plain dict spec (see
  `src/entities/Guard.py`), not hand-assembled `Selector`/`Sequence`
  nodes.
- `gale.ai.markov`: a calm `Guard` alternates between two patrol legs
  and standing idle via a `MarkovStateMachine`, so its patrol isn't a
  rigid, predictable back-and-forth.
- `gale.ai.tactical`: an `InfluenceMap`, rebuilt every frame from every
  guard's and squad member's position, scores candidate cover points
  (`best_position`) so an alerted `Guard`/the `Captain` heads for
  wherever guards currently have the edge, not just the nearest spot.
- `gale.ai.targeting`: guards lead their shots with
  `predict_intercept_time` (a straight, constant-speed bullet); the
  `Captain`'s lobbed grenades use `iterative_targeting_angle` to find a
  launch angle under gravity, since a closed-form solution doesn't
  apply once a launch angle (rather than a straight line) is involved.
- `gale.ai.learning`: the `Captain` tracks the squad leader's recent
  movement direction with an `NGramPredictor` and biases a grenade's
  aim point towards where the leader is predicted to be headed next.
- `gale.ai.goap`: once engaged, the `Captain` plans a short sequence of
  actions (call the alarm, take up position, throw a grenade) with
  `plan`, and executes it one action at a time.
- `gale.ai.rules`: a `RuleEngine` decides the guard force's overall
  stance (calm / engage / desperate) from a shared working memory
  (how many guards are alert, how close the squad is to extraction).
- `gale.ai.steering`: `WallAvoidance` (against the arena's cover
  blocks) and `CollisionAvoidance` (against other guards) wrapped
  around each guard's current movement choice with `PrioritySteering`,
  plus `PathFollow` for patrol/investigate/repositioning and `Arrive`
  for the squad's followers.
- `gale.ai.graph` / `gale.ai.search`: `src/level.py` builds a `NavGraph`
  (a visibility graph over the arena's cover-block corners) once, and
  guards/the captain path across it with `a_star`.
- `gale.ai.blackboard`: guards and the captain share one `Blackboard`;
  spotting the squad (or the captain calling the alarm) posts
  `alert_position`/`is_alerted` to it, so every guard can investigate
  even without seeing the squad themselves.
- `gale.ai.agent.Agent`: `Squad`'s members, `Guard`, and `Captain` are
  all `Agent` subclasses, spawned through `gale.factory.Factory`.
- `gale.state`: a `StateMachine` drives `TitleState` → `PlayState` →
  `GameOverState`/`VictoryState`.
- `gale.input_handler`, `gale.timer`, `gale.text`: input bindings, the
  entry fade and end-of-level delay, and all HUD/menu text.

See `examples/nightwatch` for `gale.ai.behavior_tree` hand-assembled
(rather than built from data), `gale.ai.decision_tree`, and
`gale.ai.graph.DependencyGraph`; and `docs/examples/gale_ai.rst` for
every piece of `gale.ai` demonstrated in isolated, runnable snippets,
including `minimax` (not a natural fit for either demo's real-time
gameplay).
