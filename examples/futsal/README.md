# Futsal

A small, autonomous 3-a-side indoor-soccer simulation: two 3-player
teams (goalkeeper, defender, attacker) chase, mark, dribble, and shoot
on a single small court, entirely AI-driven. It exists to exercise
`gale.ecs` (the brand-new Entity-Component-System module) and
`gale.ai` (behavior trees + a shared blackboard) together, in an
actual running game rather than in isolated snippets.

Every visual is drawn with `pygame.draw` primitives (no image, font,
or sound assets), so it runs as-is.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run the example from its own directory, since it looks for
`settings.py` and `src/` next to `main.py`:

```bash
cd examples/futsal
python main.py
```

## Controls

- `Enter`: confirm (kick off from the title screen, start a new match after full time)
- `Escape`: quit

There is no player-controlled entity: press Enter and watch the match
play itself out for `settings.MATCH_DURATION` seconds, then check the
final score.

## How it plays

- `TitleState`: title screen. Press Enter to kick off.
- `PlayState`: builds a fresh `gale.ecs.World`, six player entities,
  and a ball entity, and runs the match until the clock runs out.
- `FullTimeState`: shows the final score. Press Enter to go back to
  the title screen and start a brand new match.

## What it exercises

- `gale.ecs.World`/`System`/`SystemScheduler`: the ball and all six
  players are entities carrying `Position`/`Velocity` (and, for
  players, `Fatigue`, `TeamId`, `PlayerTag`) components defined in
  `src/components.py`. Four systems in `src/systems.py`, run in order
  by one `SystemScheduler` every frame, each touch only the components
  they care about:
  - `MovementSystem`: integrates every `Position`/`Velocity` entity —
    the only place `Velocity` actually becomes movement.
  - `FatigueSystem`: drains stamina while a player runs above a jog
    threshold (faster above a sprint threshold), regenerates it while
    idle/walking, and recomputes the effective max speed the team
    AI's steering is allowed to reach, clamping `Velocity` to it.
  - `BallSystem`: friction, bouncing off the court's walls (except
    through a goal mouth), and scoring/resetting the ball on a goal.
  - `CollisionSystem`: ball-vs-player proximity decides possession
    (posted to the shared blackboard), and player-vs-player proximity
    pushes overlapping players apart.
- `gale.ai.behavior_tree` + `gale.ai.blackboard`: `src/entities/PlayerAI.py`
  builds one `Selector`/`Sequence`/`Condition`/`Action` tree per role
  (goalkeeper/defender/attacker), re-evaluated fresh every tick (every
  `Action` returns `Status.SUCCESS`, never `RUNNING`, for the same
  reason given in `examples/nightwatch`'s `Guard`). All six players
  share one match-wide `Blackboard` holding `possession_entity`,
  `possession_team`, and `ball_position` — a defender or attacker never
  holds a direct reference to the ball carrier, it only checks
  `has_possession`/`team_has_possession` Condition nodes against the
  blackboard, the same "coordinate through shared state" rationale
  nightwatch's guards use to react to each other's sightings without
  seeing each other. `PlayState` also uses `Blackboard.observe` on
  `score_a`/`score_b` to trigger the "GOAL!" flash immediately, instead
  of polling the score every frame.
- `gale.ai.steering` (`Seek`, `Arrive`, `Separation`, `BlendedSteering`)
  and `gale.ai.agent.Agent`: `PlayerAI` subclasses `Agent` purely for
  its composition (a `Kinematic` body, a swappable steering behavior, a
  behavior tree "brain", a `Blackboard`) but deliberately does **not**
  use `Agent.update`'s own position integration — `gale.ecs.MovementSystem`
  owns that instead. Every frame, `PlayerAI.step` syncs its `Kinematic`
  from the entity's ECS `Position`/`Fatigue` components, ticks the
  behavior tree (which sets a `Seek`/`Arrive`/blended-with-`Separation`
  steering behavior and a target), and writes the resulting *desired*
  velocity into the entity's `Velocity` component. That `Velocity`
  component is the seam between the two layers this example is built
  to showcase: the behavior tree/steering stack is the OOP "brain"
  that decides intent, `gale.ecs` is the bulk, data-oriented "body"
  that actually simulates it.
- `gale.state`: a `StateMachine` drives `TitleState` → `PlayState` →
  `FullTimeState`.
- `gale.text.render_text`: the score/clock HUD and every menu.

`gale.ai.decision_tree`, `gale.ai.graph`/`gale.ai.search`, and
`gale.ai.minimax`/`gale.ai.perception` are the pieces of `gale.ai` this
demo doesn't use — there's no pathfinding around obstacles or turn-based
decision on an open court. See `examples/nightwatch` and
`docs/examples/gale_ai.rst` for those.
