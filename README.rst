.. image:: https://raw.githubusercontent.com/R3mmurd/Gale/main/logo.png
   :align: center
   :alt: Gale
   :target: https://github.com/R3mmurd/Gale/


|Python3| |Pygame2| |License| |PyPI| |GithubCommits| |BlackFormatBadge| |CIBadge|


Gale_ (Game Architecture & Logic Engine) is a modular Python_ toolkit
for building 2D games faster with Pygame_.

- **Solves**: the parts every Pygame_ project ends up reinventing --
  a real game loop, input handling, state machines, AI, physics,
  networking, UI, save files -- so you write your game, not its
  plumbing.
- **For**: Python developers building 2D games (or teaching/learning
  game programming) who want Pygame_'s directness without starting
  from a blank file every time.
- **Different because**: every piece is an independent, opt-in module
  -- import only what a given game needs, on top of plain Pygame_,
  never a replacement for it.

Full documentation: https://r3mmurd.github.io/Gale/


Installation
------------

.. code-block:: bash

   pip install gale-engine

The package is published on PyPI as ``gale-engine`` (``gale`` and
several close variants were already taken), but ``import gale`` stays
exactly the same either way.

To track ``main`` directly instead of the latest release:

.. code-block:: bash

   pip install https://github.com/R3mmurd/Gale/archive/main.zip


Quick start
-----------

.. code-block:: python

   import pygame

   from gale.game import Game
   from gale.input_handler import InputHandler, KEY_ESCAPE

   InputHandler.set_keyboard_action(KEY_ESCAPE, "quit")


   class MyGame(Game):
       def init(self) -> None:
           self.x = 0

       def update(self, dt: float) -> None:
           self.x = (self.x + 150 * dt) % self.virtual_width

       def render(self, surface: pygame.Surface) -> None:
           pygame.draw.circle(surface, "white", (int(self.x), 100), 20)

       def on_input(self, input_id, input_data) -> None:
           if input_id == "quit" and input_data.pressed:
               self.quit()


   MyGame(title="Quick Start").exec()

Save that as ``main.py`` and run it: a window opens with a white
circle sliding across the screen, closes on Escape. ``Game`` already
gives you the window, the virtual-resolution scaling, and the
update/render loop -- ``gale-admin create-project`` (see `Project
template <https://github.com/R3mmurd/Gale/blob/main/docs/examples/project_template.rst>`_)
scaffolds this same layout plus a ``settings.py`` for a real project.


Why Gale?
---------

- **Modular, not all-or-nothing.** ``gale.ai``, ``gale.net``,
  ``gale.physics``, ``gale.ui``, and every other submodule are
  independent -- a Pong clone only needs ``gale.net``/``gale.ui``, a
  platformer only needs ``gale.physics``/``gale.tilemap``. Nothing is
  forced on you for using one piece.
- **Batteries-included where it matters.** A game loop with
  fixed/variable timestep, Django-style overridable settings
  (``gale.conf``), input handling (keyboard, mouse, gamepad, local
  co-op), and a save system with schema migrations (``gale.save``) --
  the plumbing every project needs, solved once.
- **A real AI toolkit, not a token one.** ``gale.ai`` covers steering
  behaviors, behavior/decision trees, A*/HPA*, fuzzy logic, GOAP,
  Markov chains, tactical influence maps, and ``minimax`` -- most of a
  standard "AI for games" curriculum, ready to compose.
- **Physics without the pymunk/Chipmunk2D API leaking through.**
  ``gale.physics`` wraps pymunk for real 2D physics (bodies, joints,
  collisions) behind gale's own, much smaller API -- you never import
  pymunk directly.
- **Multiplayer building blocks that actually work over the internet.**
  ``gale.net`` is a hand-rolled reliable UDP layer with client-side
  prediction/server reconciliation, entity interpolation, LAN
  discovery, and shareable room codes -- pure Python, no external
  networking dependency.
- **Tested.** 670+ tests, black-formatted, CI across Python 3.9-3.13
  on every pull request.


Use cases
---------

- **2D platformer** -- `examples/leap <https://github.com/R3mmurd/Gale/blob/main/examples/leap/README.md>`__ (all three ``gale.physics`` body types) or `examples/planks <https://github.com/R3mmurd/Gale/blob/main/examples/planks/README.md>`__ (a Tiled map, one-way platforms, no physics engine at all).
- **Top-down adventure** -- `examples/wayfarer <https://github.com/R3mmurd/Gale/blob/main/examples/wayfarer/README.md>`__: an intro cutscene, free-roam quests, a victory cutscene.
- **Tactical/AI-heavy game** -- `examples/skirmish <https://github.com/R3mmurd/Gale/blob/main/examples/skirmish/README.md>`__: formations, fuzzy logic, GOAP, an influence map, gravity-aware targeting, all driving one squad-tactics demo.
- **Networked multiplayer** -- `examples/rally <https://github.com/R3mmurd/Gale/blob/main/examples/rally/README.md>`__: an online Pong playable over LAN or the internet.


Examples
--------
Short, focused snippets, one per module:

- `Project template (gale-admin) <https://github.com/R3mmurd/Gale/blob/main/docs/examples/project_template.rst>`_: scaffolds a new project's directory structure.
- `gale.animation <https://github.com/R3mmurd/Gale/blob/main/docs/examples/animation.rst>`_
- `gale.camera <https://github.com/R3mmurd/Gale/blob/main/docs/examples/camera.rst>`_: following, zoom, bounds, screen shake.
- `gale.command <https://github.com/R3mmurd/Gale/blob/main/docs/examples/command.rst>`_: Command pattern, bound to input_handler through CommandBindings/CommandControlled.
- `gale.factory <https://github.com/R3mmurd/Gale/blob/main/docs/examples/factory.rst>`_
- `gale.frames <https://github.com/R3mmurd/Gale/blob/main/docs/examples/frames.rst>`_
- `gale.input_handler <https://github.com/R3mmurd/Gale/blob/main/docs/examples/input_handler.rst>`_: includes keyboard key combos and gamepads.
- `gale.log <https://github.com/R3mmurd/Gale/blob/main/docs/examples/log.rst>`_: console/file defaults, adding Graylog, Sentry, Discord, or any other destination.
- `gale.net <https://github.com/R3mmurd/Gale/blob/main/docs/examples/net.rst>`_: ``Server``/``Client``, channel choice, RTT, LAN discovery, room codes.
- `gale.particle_system <https://github.com/R3mmurd/Gale/blob/main/docs/examples/particle_system.rst>`_
- `gale.physics <https://github.com/R3mmurd/Gale/blob/main/docs/examples/physics.rst>`_: bodies, shapes, joints, collision callbacks, and the scene graph, with pymunk never exposed directly.
- `gale.state <https://github.com/R3mmurd/Gale/blob/main/docs/examples/state.rst>`_
- `gale.stencil <https://github.com/R3mmurd/Gale/blob/main/docs/examples/stencil.rst>`_: mask an arbitrary shape out of a surface, love2d-stencil style.
- `gale.text <https://github.com/R3mmurd/Gale/blob/main/docs/examples/text.rst>`_
- `gale.tilemap <https://github.com/R3mmurd/Gale/blob/main/docs/examples/tilemap.rst>`_: layers, tilesets, loading a Tiled JSON map, one-way platform collision.
- `gale.timer <https://github.com/R3mmurd/Gale/blob/main/docs/examples/timer.rst>`_
- `gale.ui <https://github.com/R3mmurd/Gale/blob/main/docs/examples/ui.rst>`_: menus, HUDs, and forms built from panels, buttons, list views, text inputs, closable windows, and more.
- `gale.ai <https://github.com/R3mmurd/Gale/blob/main/docs/examples/gale_ai.rst>`_: steering behaviors (and their combination/motor-control variants), behavior tree, decision tree, data-driven scripting, Blackboard, graphs/search/pathfinding, the ``Agent`` class, fuzzy logic, learning models, targeting, formations, Markov chains, GOAP, rules, and tactical influence maps.
- `gale.ecs <https://github.com/R3mmurd/Gale/blob/main/docs/examples/ecs.rst>`_: World, components, queries, and Systems/SystemScheduler.
- `gale.sequence <https://github.com/R3mmurd/Gale/blob/main/docs/examples/sequence.rst>`_: Step, StepGroup, and Sequence, the shared engine behind quests and cutscenes.
- `gale.quest <https://github.com/R3mmurd/Gale/blob/main/docs/examples/quest.rst>`_: Objective, Stage, Quest, and QuestLog.
- `gale.cutscene <https://github.com/R3mmurd/Gale/blob/main/docs/examples/cutscene.rst>`_: Cutscene and its beats — images, "video", actor movement, dialogue.
- `gale.save <https://github.com/R3mmurd/Gale/blob/main/docs/examples/save.rst>`_: SaveManager, slots, metadata, schema versioning/migrations, pluggable serialization.

For full running games built with gale, see ``examples/space_trip`` and,
in particular for ``gale.ai``, `examples/nightwatch <https://github.com/R3mmurd/Gale/blob/main/examples/nightwatch/README.md>`_, a
small stealth demo whose guards patrol, chase, and coordinate through a
shared behavior tree, blackboard, and pathfinding, and
`examples/skirmish <https://github.com/R3mmurd/Gale/blob/main/examples/skirmish/README.md>`_, a small
squad-tactics demo covering the rest of the toolkit: a formation of
allies following an anchor, guards whose alertness is driven by fuzzy
logic and whose decisions come from a data-driven behavior tree, a
Markov state machine varying their patrol routine, an influence map
guiding where they take up position, GOAP planning for an
objective-driven captain, and gravity-aware projectile targeting; for
``gale.net``/``gale.ui``, `examples/rally <https://github.com/R3mmurd/Gale/blob/main/examples/rally/README.md>`_,
a small online Pong playable over a LAN or the internet; for
``gale.physics``, `examples/leap <https://github.com/R3mmurd/Gale/blob/main/examples/leap/README.md>`_, a
platformer using all three body types, and
`examples/hillclimb <https://github.com/R3mmurd/Gale/blob/main/examples/hillclimb/README.md>`_, a small
vehicle-physics demo built on motorized wheel joints; for
``gale.camera``, `examples/scavenger <https://github.com/R3mmurd/Gale/blob/main/examples/scavenger/README.md>`_,
a coin-collecting game with a scrolling/zooming camera; and, for
``gale.stencil``, `examples/lantern <https://github.com/R3mmurd/Gale/blob/main/examples/lantern/README.md>`_, a
top-down exploration game where the room is only revealed in a circle
around the player; and, for ``gale.tilemap``,
`examples/planks <https://github.com/R3mmurd/Gale/blob/main/examples/planks/README.md>`_,
a platformer loading a level made in Tiled, with one-way platforms and
a scrolling camera.

Three more full games showcase the isometric tilemap, perception,
HFSM, minimax, networked prediction/interpolation, and ECS additions:
`examples/outpost <https://github.com/R3mmurd/Gale/blob/main/examples/outpost/README.md>`_,
a small isometric stealth prototype where patrolling guards spot the
player through a vision cone and a hierarchical state machine, and a
terminal minigame is defended by a minimax AI; `examples/circuit
<https://github.com/R3mmurd/Gale/blob/main/examples/circuit/README.md>`_,
a small online racing prototype with client-side prediction/server
reconciliation, entity interpolation, lag compensation, and an AI
racer following the track with A*/steering; and `examples/futsal
<https://github.com/R3mmurd/Gale/blob/main/examples/futsal/README.md>`_,
a small futsal match simulation where each team's behavior
tree/Blackboard-driven roles decide intent that a ``gale.ecs``
World/SystemScheduler simulates in bulk (movement, fatigue, ball/player
collisions).

`examples/wayfarer <https://github.com/R3mmurd/Gale/blob/main/examples/wayfarer/README.md>`_
showcases the ``gale.sequence``/``gale.quest``/``gale.cutscene``
additions: a small top-down adventure where an intro cutscene (a
character walking to a mark, pose changes, input-advanced dialogue)
hands off into free-roam play, collecting herbs, defeating a wolf, and
reporting back to an NPC progress a two-stage ``QuestLog``-tracked
quest, completing it triggers a victory cutscene.

Each example under ``examples/`` is a standalone project (its own
``settings.py`` and ``src/``), so it doesn't see the copy of ``gale``
inside this repository unless it's actually installed. From the
repository root, run ``pip install -e .`` once, then ``cd`` into the
example's directory and run ``python main.py`` from there.

.. TODO: this section would benefit from real gameplay screenshots or
   short GIFs per example -- left as text + links for now since none
   exist yet and a title-screen auto-capture wouldn't represent the
   games fairly.


What Gale includes
-------------------
- ``gale.ai``: Contains a modular toolkit to build autonomous characters: the ``Kinematic`` body and a full set of steering behaviors (seek/flee/arrive/align/pursue/evade/wander/wall & obstacle & collision avoidance/path following) plus combination (blending, priority, cooperative arbitration) and motor-control (output filtering, capability limits) variants; a behavior tree, a decision tree, and data-driven scripting to build either from a plain dict; a shared ``Blackboard``; generic graphs with search algorithms — flat, hierarchical, interruptible/time-sliced, and open-goal; the ``Agent`` class that ties them together; a vision-cone ``Perception`` system; fuzzy logic; naive-Bayes/n-gram learning models; projectile aiming/targeting (including under drag); coordinated-movement formations; Markov chains/state machines; goal-oriented action planning (GOAP); a forward-chaining rule engine; tactical influence maps; and ``minimax`` search with alpha-beta pruning for turn-based adversarial decisions. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/gale_ai.rst>`__)
- ``gale.animation``: Contains the class ``Animation``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/animation.rst>`__)
- ``gale.camera``: Contains the class ``Camera``, a 2D scrolling/zooming camera — following a target, screen shake, bounds clamping, and screen/world coordinate conversion. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/camera.rst>`__)
- ``gale.command``: Contains ``Command``, a stateless, reusable Command-pattern action (and its ``__call__`` alias, so it can also be used directly as a ``gale.ai`` callable), ``CommandBindings`` (maps an ``input_handler`` action id to a press/release pair of commands), and ``CommandControlled``, an ``InputListener`` mixin that dispatches ``on_input`` through a ``CommandBindings``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/command.rst>`__)
- ``gale.conf``: Contains ``settings``, a lazily-loaded, overridable settings object. It reads your project's own ``settings.py`` first, falling back to ``gale.conf.global_settings`` (the same defaults ``gale.game.Game`` used to hardcode directly) for anything you don't override, and lets you define your own extra settings the same way. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/project_template.rst>`__)
- ``gale.cutscene``: Contains ``Cutscene`` (a ``gale.sequence.Sequence`` of beats that also ticks/renders any actors involved every frame) and its beats — ``ShowImage``, ``PlayAnimation`` (a dependency-free stand-in for video playback), ``MoveActor``, ``SetActorAnimation``, ``Dialogue``, ``Wait`` — each lasting a fixed duration or advancing on a specific input. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/cutscene.rst>`__)
- ``gale.ease_functions``: Contains the 30 standard easing functions (linear, sine/quad/cubic/quart/quint/expo/circ/back/elastic/bounce, each with an ``in``/``out``/``in_out`` variant) used by ``gale.timer.Tween``, plus an ``EASE_FUNCTIONS`` dict looking them up by name.
- ``gale.ecs``: Contains a Data-Oriented Design (ECS) toolkit — a ``World`` storing entities (plain integer ids) and components (plain Python objects), queried by ``System``/``SystemScheduler`` to process them in bulk every frame. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/ecs.rst>`__)
- ``gale.factory``: Contains the classes ``Factory`` and ``Abstract Factory``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/factory.rst>`__)
- ``gale.frames``: Contains a util function to generate rectangle frames from a sprite sheet. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/frames.rst>`__)
- ``gale.game``: Contains a base class ``Game`` to be inherited to ease your game building — a variable-rate ``update``/``render`` pair driven by real elapsed time, plus a ``fixed_update`` that steps at a constant rate regardless of frame rate, for anything that needs to be frame-rate-independent (e.g. driving a ``gale.physics.World``). Every constructor argument (title, window/virtual size, fps, ...) defaults to whatever ``gale.conf.settings`` resolves it to when omitted.
- ``gale.input_handler``: Contains key definitions, mouse button definitions, mouse wheel input definitions, mouse move input definitions, gamepad button/axis definitions (local multiplayer included), classes to store the information about an input, an interface to listen the input handler and the class ``InputHandler``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/input_handler.rst>`__)
- ``gale.log``: Contains logging configuration for gale games — printed to the terminal and written to a plain-text file by default, extensible to Graylog, Sentry, a Discord channel, or anywhere else by attaching another ``logging.Handler``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/log.rst>`__)
- ``gale.management``: Contains ``gale-admin``, the ``create-project``/``create-state`` command-line tool that scaffolds a new game's ``main.py``/``settings.py``/``src/`` layout, or a new ``BaseState`` subclass inside one. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/project_template.rst>`__)
- ``gale.math_util``: Contains ``real_equal``, a tolerance-based float equality check used by ``gale.ease_functions`` to detect ``t=0``/``t=1`` exactly despite floating-point drift.
- ``gale.net``: Contains a pure-Python, pygame-free toolkit for LAN/internet multiplayer: ``Server``, ``Client``, a hand-rolled reliability layer over UDP, per-peer round-trip-time tracking, LAN discovery, configurable-format room codes (``encode``/``decode``) for sharing a host/port pair as a short, human-typeable string, a ``PredictionBuffer`` for client-side prediction/server reconciliation, and a ``SnapshotInterpolator``/``lag_compensated_position`` for entity interpolation and lag compensation. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/net.rst>`__)
- ``gale.particle_system``: Contains classes to handle particle systems in your game. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/particle_system.rst>`__)
- ``gale.physics``: Contains a pymunk-backed 2D physics toolkit — ``World``, ``Body``, body types, shapes, joints — that never exposes pymunk itself, plus a lightweight scene graph (``Node``) for organizing physics entities. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/physics.rst>`__)
- ``gale.quest``: Contains a customizable-per-game quest system built on ``gale.sequence`` — ``Objective``, ``Stage`` (a group of objectives), ``Quest`` (a sequence of stages), and ``QuestLog`` (tracks/starts every quest and broadcasts progress events to whichever are active). (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/quest.rst>`__)
- ``gale.save``: Contains ``SaveManager``, a general-purpose save-game system — persists whatever JSON-serializable dict a game gives it into named slots on disk, with per-slot metadata for a save-select screen, a pluggable ``serializer``/``deserializer`` for the wire format, and a schema ``version``/``migrations`` mapping for evolving what a save contains across releases without breaking old saves. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/save.rst>`__)
- ``gale.sequence``: Contains ``Step``, ``StepGroup``, and ``Sequence`` — the generic "do this until it's done, then do the next thing" engine shared by ``gale.quest`` and ``gale.cutscene``; a step completes after a fixed duration, on a specific input, or by a subclass's own condition. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/sequence.rst>`__)
- ``gale.state``: Contains the class ``BaseState``, a basic class ``StateMachine``, a basic class ``StateStack``, and ``HierarchicalState`` for nesting a sub-``StateMachine`` inside a state (HFSM). (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/state.rst>`__)
- ``gale.stencil``: Contains the class ``Stencil``, a CPU-side equivalent of `love.graphics.stencil <https://love2d.org/wiki/love.graphics.stencil>`__ to mask an arbitrary shape (a circle, a polygon, a sprite) out of a surface's alpha channel — handy for a top-down game's fog-of-war/vision reveal, a circular minimap crop, and similar effects. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/stencil.rst>`__)
- ``gale.text``: Contains a util function to ease text rendering and a class ``Text``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/text.rst>`__)
- ``gale.tilemap``: Contains ``TileMap``/``Tileset`` (grid-of-tiles rendering with ``gale.camera`` culling built in), ``IsometricTileMap`` (the same kind of map rendered in a diamond/isometric projection, plus the standalone ``cartesian_to_isometric``/``isometric_to_cartesian`` transforms, reusable for isometric coordinate math outside of tile maps too), ``load_tiled_map`` (loads a map exported as JSON from `Tiled <https://www.mapeditor.org/>`__, tilesets/object layers included), and an optional ``move_and_collide`` platformer collision helper (solid walls, one-way platforms) that never depends on ``gale.physics``. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/tilemap.rst>`__)
- ``gale.timer``: Contains classes to handle timers that execute action every x seconds, after x seconds, and tweening. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/timer.rst>`__)
- ``gale.ui``: Contains a widget toolkit for menus, HUDs, and forms — panels, labels, buttons, progress bars, checkboxes, list views, containers, text boxes (click/Enter-paginated, or button-paginated through ``PaginatedTextBox``), text inputs, cursors, and closable ``Window``\\ s, styled through a shared theme. (`example <https://github.com/R3mmurd/Gale/blob/main/docs/examples/ui.rst>`__)


Development
-----------
To work on this library, install the development dependencies, which include
the runtime dependencies plus ``pytest`` and ``pre-commit``:

.. code-block:: bash

   pip install -r requirements/dev.txt

Then install the git hook so that ``black`` and the test suite run
automatically before every commit:

.. code-block:: bash

   pre-commit install

You can also run both checks manually at any time:

.. code-block:: bash

   black .
   pytest


Git workflow
------------
``main`` and ``develop`` are protected: nobody (including admins) can push
to them directly, so every change has to go through a pull request.

- New work branches off ``develop`` and is merged back into ``develop``
  through a pull request.
- Releases are cut by opening a pull request from ``develop`` into ``main``.
  See `PACKAGING.md <https://github.com/R3mmurd/Gale/blob/main/PACKAGING.md>`_ for the full release/publishing
  process — publishing a GitHub Release automatically pushes the new
  version to PyPI.

Every pull request (and every push to a branch with an open pull request)
triggers the ``CI`` workflow defined in ``.github/workflows/ci.yml``, which
installs the dependencies (including ``pytest``, since GitHub-hosted
runners don't ship it) and runs:

- ``black --check --diff .`` to enforce the code style.
- ``pytest`` to run the whole test suite.

Both checks are required status checks on ``main`` and ``develop``: a pull
request cannot be merged until they pass.


Contributors
------------
.. image:: https://contrib.rocks/image?repo=R3mmurd/Gale
   :target: https://github.com/R3mmurd/Gale/graphs/contributors


Dependencies
------------
Gale is obviously strongly dependent on Python and Pygame. It also depends on
Click for the ``gale-admin`` command line tool, NumPy for ``gale.particle_system``,
and pymunk for ``gale.physics``.


Changelog
---------
See `CHANGELOG.md <https://github.com/R3mmurd/Gale/blob/main/CHANGELOG.md>`_
for the history of notable changes across releases.


License
-------

This library is distributed under `the MIT License`_, which can
be found in the file ``LICENSE``.  We reserve the right to place
future versions of this library under a different license.

See docs/licenses for licenses of dependencies.


.. |Python3| image:: https://img.shields.io/badge/python-3-blue.svg?v=1
   :target: https://docs.python.org/3/

.. |Pygame2| image:: https://img.shields.io/badge/pygame-green.svg?v=1
   :target: https://www.pygame.org/docs/

.. |License| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT

.. |PyPI| image:: https://img.shields.io/pypi/v/gale-engine.svg
   :target: https://pypi.org/project/gale-engine/

.. |GithubCommits| image:: https://img.shields.io/github/commits-since/R3mmurd/Gale/v1.16.0.svg
   :target: https://github.com/R3mmurd/Gale/compare/v1.16.0...main

.. |BlackFormatBadge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |CIBadge| image:: https://github.com/R3mmurd/Gale/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/R3mmurd/Gale/actions/workflows/ci.yml

.. _gale: https://github.com/R3mmurd/Gale
.. _Python: https://www.python.org/
.. _Pygame: https://www.pygame.org
.. _The MIT License: https://opensource.org/licenses
