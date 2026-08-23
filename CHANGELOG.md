# Changelog

All notable changes to this project are documented here, condensed
from the [GitHub releases](https://github.com/R3mmurd/Gale/releases),
newest first. This project follows [semantic versioning](https://semver.org/).

## [1.16.0] - 2026-08-23

### Added
- `gale.command`: a stateless, reusable Command-pattern implementation integrated with `gale.input_handler` -- `Command` (the receiver is passed into `execute`/`__call__`, never the constructor, so a single instance can be shared across every entity that performs it, and used directly as an AI-driven callable), `CommandBindings` (maps an `input_handler` action id to a press/release pair of commands), and `CommandControlled` (an `InputListener` mixin dispatching `on_input` through a `CommandBindings`).

## [1.15.0] - 2026-08-19

### Changed
- `gale.physics`'s backend is now pymunk instead of Box2D (the `Box2D` PyPI package has no wheels or sdist for Python 3.14 and no upstream activity to add them, so `pip install gale-engine` failed outright there). `World`/`Body`/`BodyType`/`Joint`/`RevoluteJoint`/`WheelJoint`/`Node`/shapes keep every name, signature, and documented behavior -- no game built on gale should need to change a line.
- Raised the Python floor to 3.9 (from 3.7): pymunk 7.x, needed for the contact-handling API this backend swap relies on, itself requires 3.9+.

### Added
- `Body.set_damping(linear_damping, angular_damping)`: gale.physics had no per-body damping before, which had led at least one project to reach past `Body` into the wrapped engine directly to get it.
- `RevoluteJoint.enable_limit`/`lower_angle`/`upper_angle`, and `enableMotor`/`motorSpeed`/`maxMotorTorque`/`enableLimit`/`lowerAngle`/`upperAngle` (or their snake_case equivalents) as `create_revolute_joint`/`create_wheel_joint` construction-time options.

### Fixed
- `Body.touching_bodies` never reported a sensor fixture's overlaps (a wind zone, a goal trigger) -- only solid-vs-solid contacts.

## [1.14.5] - 2026-08-03

### Changed
- Restructured README.rst around what Gale solves (tagline, "Why Gale?", quick start, use cases) instead of opening straight into a long module list; the module list is still there, now titled "What Gale includes" further down.

## [1.14.4] - 2026-07-31

### Added
- Gale now has a full name: Game Architecture & Logic Engine.

## [1.14.3] - 2026-07-31

### Changed
- `gale.conf`'s docstrings and docs no longer describe it by comparing it to Django's settings module -- they just describe what it does and how to use it.

## [1.14.2] - 2026-07-30

### Changed
- The pygame-initialization guarantee from v1.14.1 moved from every project's `settings.py` into `gale/__init__.py` itself: importing anything under the `gale` package now initializes pygame automatically, so a project's `settings.py` never needs a `pygame.init()` call of its own (the ones v1.14.1 added to gale-admin's template and every example were reverted).

## [1.14.1] - 2026-07-29

### Fixed
- `settings.py` (gale-admin's generated template and every example) could crash with `pygame.error: font not initialized` while building `FONTS`: it relied on pygame being initialized as a side effect of some other module importing `gale.game` first, instead of guaranteeing it itself. It now calls `pygame.init()` directly.

## [1.14.0] - 2026-07-28

### Added
- `gale.save`: a general-purpose save-game system. `SaveManager` persists any JSON-serializable dict into named slots on disk, with per-slot metadata for a save-select screen, a pluggable serializer/deserializer for the wire format, a schema version + migrations for evolving what a save contains across releases, and atomic (crash-safe) writes.

## [1.13.0] - 2026-07-28

### Added
- `gale.net.Server`/`Client` support the context manager protocol (`with Server(...) as server:`), guaranteeing the socket closes even on exceptions.

### Changed
- Expanded CI to a Python 3.8-3.13 test matrix and added coverage reporting.
- Removed the unused `wheel` dependency.

### Fixed
- `gale.log.config.configure()` leaked a file descriptor on every call by never closing the handlers it replaced.
- `Server.enable_lan_discovery()` leaked its UDP socket if called more than once.
- `Game` no longer hangs forever if constructed with `fixed_timestep <= 0`; it now raises `ValueError` instead.
- `Game.quit()` now unregisters the game from `InputHandler`, matching what `__init__` registered.

## [1.12.1] - 2026-07-28

### Fixed
- Games crashed on machines without a working audio device: `settings.py` called `pygame.mixer.init()` explicitly (which raises when no audio device is available) instead of relying on `gale.game`'s own `pygame.init()` (which degrades gracefully). Fixed in `gale-admin`'s generated template and every example game.

### Changed
- `Game.exec()`'s teardown simplified to a single `pygame.quit()` call.

## [1.12.0] - 2026-07-28

### Added
- `gale.conf`: a lazily-loaded, overridable settings object, the same role `django.conf.settings` plays for Django. `gale.game.Game`'s constructor arguments resolve through it (falling back to `gale.conf.global_settings`) when omitted; `gale-admin create-project`'s generated template uses it, so a new project's `main.py` no longer needs to pass anything to `Game()` explicitly.

### Changed
- All example games migrated to the new settings pattern for consistency.
- Removed an unnecessary love2d comparison from `docs/examples/camera.rst`.

## [1.11.0] - 2026-07-28

### Added
- `gale.ai` covers the rest of the classic game-AI toolkit: fuzzy logic (`gale.ai.fuzzy`), agent knowledge/learning (`gale.ai.learning`), the remaining steering behaviors and combination/motor-control variants, physics-prediction targeting (`gale.ai.targeting`), coordinated-movement formations (`gale.ai.formation`), hierarchical/interruptible/open-goal pathfinding (`gale.ai.pathfinding`), Markov chains/state machines (`gale.ai.markov`), goal-oriented action planning (`gale.ai.goap`), a forward-chaining rule engine (`gale.ai.rules`), data-driven behavior/decision tree scripting (`gale.ai.scripting`), and tactical influence maps (`gale.ai.tactical`).
- New example `examples/skirmish`: a squad-tactics demo exercising all of the above end to end.

### Changed
- `docs/examples/gale_ai.rst` documents every new module, plus two pre-existing gaps (`minimax`, `perception`).

## [1.10.0] - 2026-07-27

### Added
- `Game.fixed_update()`: an optional, constant-rate hook alongside the existing variable-rate `update()`, for logic that must advance the same amount every call regardless of frame rate.

### Changed
- Normalized the one stray "private via double underscore" usage in the codebase to a single underscore, per PEP 8.

## [1.9.2] - 2026-07-18

### Fixed
- The `Documentation` project URL now correctly points at the current docs site.

## [1.9.1] - 2026-07-13

### Changed
- Added a `Documentation` link to the project's PyPI metadata and README.

## [1.9.0] - 2026-07-12

### Added
- `gale.sequence`: `Step`, `StepGroup`, `Sequence` — a generic "do this until it's done, then do the next thing" engine.
- `gale.quest`: `Objective`, `Stage`, `Quest`, `QuestLog` — a customizable-per-game quest system built on `gale.sequence`.
- `gale.cutscene`: `Cutscene` + beats (`ShowImage`, `PlayAnimation`, `MoveActor`, `SetActorAnimation`, `Dialogue`, `Wait`).
- New example `examples/wayfarer`: an intro cutscene, quests, and a victory cutscene.

## [1.8.0] - 2026-07-11

### Added
- `gale.tilemap.IsometricTileMap` + `cartesian_to_isometric`/`isometric_to_cartesian`.
- `gale.ai.perception`: `VisionCone`, `Perception`, `AlertLevel`, `has_line_of_sight`.
- `gale.state.HierarchicalState`: hierarchical state machines (HFSM).
- `gale.ai.minimax`: `minimax`/`best_move` with alpha-beta pruning.
- `gale.net.PredictionBuffer`, `gale.net.SnapshotInterpolator`/`lag_compensated_position`.
- `gale.ecs`: `World`, `System`, `SystemScheduler`.
- New examples `examples/outpost`, `examples/circuit`, `examples/futsal`.

## [1.7.0] - 2026-07-10

### Added
- `gale.tilemap`: `TileMap`/`Tileset`, `load_tiled_map` (Tiled JSON), `move_and_collide` (dependency-free platformer collision).
- New example `examples/planks`.

### Changed
- `gale.frames.generate_frames` gains optional `margin`/`spacing` parameters.

## [1.6.2] - 2026-07-10

### Fixed
- README/PyPI links resolved relative to pypi.org, 404ing every example/module link; now absolute GitHub URLs.

## [1.6.1] - 2026-07-10

### Changed
- Published to PyPI as `gale-engine`. Publishing automated via Trusted Publishing (OIDC). Packaging migrated to `pyproject.toml` (PEP 621).

## [1.6.0] - 2026-07-10

### Added
- `gale.camera`: a 2D scrolling/zooming `Camera`.
- `gale.input_handler`: gamepad support (SDL GameController), local co-op, hotplug.
- `gale.stencil`: a CPU-side equivalent of a GPU stencil buffer.
- `gale.ui`: `PaginatedTextBox`, `Window`.
- `gale.net.room_code`: `encode`/`decode` + `RoomCodeFormat`.
- `gale.log`: `SentryHandler`, `DiscordWebhookHandler`.
- `gale-admin create-state`.
- New examples `examples/scavenger`, `examples/lantern`.

## [1.5.0] - 2026-07-07

### Added
- `gale.physics`: a 2D physics toolkit wrapping Box2D — `World`, `Body`, `BodyType`, shapes, joints, `Node`.
- `gale.log`: console/file logging defaults, `GraylogHandler`.
- New examples `examples/leap`, `examples/hillclimb`.

## [1.4.0] - 2026-07-06

### Added
- `gale.net`: a pure-Python, pygame-free LAN/internet multiplayer toolkit — `Server`/`Client`, reliability channels, RTT tracking, LAN discovery.
- `gale.ui`: a widget toolkit — `Panel`, `Label`, `Button`, `ProgressBar`, `Checkbox`, `ListView`, `Container`, `TextBox`, `TextInput`, `Cursor`, `UIManager`, `Theme`.
- New example `examples/rally`.

### Fixed
- `gale.ui.Container` giving keyboard focus to non-interactive widgets.
- `InputHandler.set_mouse_motion_action` not accepting `None` as a wildcard direction.

## [1.3.0] - 2026-07-06

### Added
- `gale.ai`: `Kinematic` and steering behaviors (Seek, Flee, Arrive, Align, Face, VelocityMatch, Pursue, Evade, Wander, Separation, ObstacleAvoidance, BlendedSteering, PrioritySteering), a behavior tree, a decision tree, `Blackboard`, graphs and search algorithms, `Agent`.
- `gale.input_handler`: keyboard key combos (`modifiers=MOD_CTRL`).
- New example `examples/nightwatch`.

### Fixed
- `Animation.reset()`/`update()`: a dead `reset()` and an off-by-one in loop completion.
- `Factory.create()` mutating the caller's `properties` dict.
- `StateMachine` using a mutable dict as a default argument.
- Keyboard combos never matching a real single-sided modifier press.

## [1.2.0] - 2024-06-28

No release notes recorded.

## [1.1.1] - 2023-04-23

No release notes recorded.

## [1.1.0] - 2023-02-05

### Added
- `Factory`, `AbstractFactory`.
- A callback to `ParticleSystem`.

## [1.0.0] - 2023-01-27

Initial release.

[1.16.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.16.0
[1.15.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.15.0
[1.14.5]: https://github.com/R3mmurd/Gale/releases/tag/v1.14.5
[1.14.4]: https://github.com/R3mmurd/Gale/releases/tag/v1.14.4
[1.14.3]: https://github.com/R3mmurd/Gale/releases/tag/v1.14.3
[1.14.2]: https://github.com/R3mmurd/Gale/releases/tag/v1.14.2
[1.14.1]: https://github.com/R3mmurd/Gale/releases/tag/v1.14.1
[1.14.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.14.0
[1.13.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.13.0
[1.12.1]: https://github.com/R3mmurd/Gale/releases/tag/v1.12.1
[1.12.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.12.0
[1.11.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.11.0
[1.10.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.10.0
[1.9.2]: https://github.com/R3mmurd/Gale/releases/tag/v1.9.2
[1.9.1]: https://github.com/R3mmurd/Gale/releases/tag/v1.9.1
[1.9.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.9.0
[1.8.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.8.0
[1.7.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.7.0
[1.6.2]: https://github.com/R3mmurd/Gale/releases/tag/v1.6.2
[1.6.1]: https://github.com/R3mmurd/Gale/releases/tag/v1.6.1
[1.6.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.6.0
[1.5.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.5.0
[1.4.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.4.0
[1.3.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.3.0
[1.2.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.2.0
[1.1.1]: https://github.com/R3mmurd/Gale/releases/tag/v1.1.1
[1.1.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.1.0
[1.0.0]: https://github.com/R3mmurd/Gale/releases/tag/v1.0.0
