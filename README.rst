.. raw:: html

   <p align="center">
     <a href="https://github.com/R3mmurd/Gale/">
       <img src="logo.png" alt="Gale">
     </a>
   </p>


|Python3| |Pygame2| |License| |GithubCommits| |BlackFormatBadge| |CIBadge|


Gale_ is a collection of reusable codes to ease your life when building games with Python_ and Pygame_.


Modules
-------
- ``gale.ai``: Contains a modular toolkit to build autonomous characters: the ``Kinematic`` body and steering behaviors, a behavior tree, a decision tree, a shared ``Blackboard``, generic graphs with search algorithms, and the ``Agent`` class that ties them together. (`example <docs/examples/gale_ai.rst>`__)
- ``gale.animation``: Contains the class ``Animation``. (`example <docs/examples/animation.rst>`__)
- ``gale.camera``: Contains the class ``Camera``, a 2D scrolling/zooming camera — following a target, screen shake, bounds clamping, and screen/world coordinate conversion. (`example <docs/examples/camera.rst>`__)
- ``gale.factory``: Contains the classes ``Factory`` and ``Abstract Factory``. (`example <docs/examples/factory.rst>`__)
- ``gale.frames``: Contains a util function to generate rectangle frames from a sprite sheet. (`example <docs/examples/frames.rst>`__)
- ``gale.game``: Contains a base class ``Game`` to be inherited to ease your game building.
- ``gale.input_handler``: Contains key definitions, mouse button definitions, mouse wheel input definitions, mouse move input definitions, gamepad button/axis definitions (local multiplayer included), classes to store the information about an input, an interface to listen the input handler and the class ``InputHandler``. (`example <docs/examples/input_handler.rst>`__)
- ``gale.log``: Contains logging configuration for gale games — printed to the terminal and written to a plain-text file by default, extensible to Graylog, Sentry, a Discord channel, or anywhere else by attaching another ``logging.Handler``. (`example <docs/examples/log.rst>`__)
- ``gale.net``: Contains a pure-Python, pygame-free toolkit for LAN/internet multiplayer: ``Server``, ``Client``, a hand-rolled reliability layer over UDP, per-peer round-trip-time tracking, LAN discovery, and configurable-format room codes (``encode``/``decode``) for sharing a host/port pair as a short, human-typeable string. (`example <docs/examples/net.rst>`__)
- ``gale.particle_system``: Contains classes to handle particle systems in your game. (`example <docs/examples/particle_system.rst>`__)
- ``gale.physics``: Contains a Box2D-backed 2D physics toolkit — ``World``, ``Body``, body types, shapes, joints — that never exposes Box2D itself, plus a lightweight scene graph (``Node``) for organizing physics entities. (`example <docs/examples/physics.rst>`__)
- ``gale.state``: Contains the class ``BaseState``, a basic class ``StateMachine`` and a basic class ``StateStack``. (`example <docs/examples/state.rst>`__)
- ``gale.stencil``: Contains the class ``Stencil``, a CPU-side equivalent of `love.graphics.stencil <https://love2d.org/wiki/love.graphics.stencil>`__ to mask an arbitrary shape (a circle, a polygon, a sprite) out of a surface's alpha channel — handy for a top-down game's fog-of-war/vision reveal, a circular minimap crop, and similar effects. (`example <docs/examples/stencil.rst>`__)
- ``gale.text``: Contains a util function to ease text rendering and a class ``Text``. (`example <docs/examples/text.rst>`__)
- ``gale.timer``: Contains classes to handle timers that execute action every x seconds, after x seconds, and tweening. (`example <docs/examples/timer.rst>`__)
- ``gale.ui``: Contains a widget toolkit for menus, HUDs, and forms — panels, labels, buttons, progress bars, checkboxes, list views, containers, text boxes (click/Enter-paginated, or button-paginated through ``PaginatedTextBox``), text inputs, cursors, and closable ``Window``\\ s, styled through a shared theme. (`example <docs/examples/ui.rst>`__)


Installation
------------

.. code-block:: bash

   pip install https://github.com/R3mmurd/Gale/archive/main.zip


Examples
--------
- `Project template (gale-admin) <docs/examples/project_template.rst>`_: scaffolds a new project's directory structure.
- `gale.animation <docs/examples/animation.rst>`_
- `gale.camera <docs/examples/camera.rst>`_: following, zoom, bounds, screen shake.
- `gale.factory <docs/examples/factory.rst>`_
- `gale.frames <docs/examples/frames.rst>`_
- `gale.input_handler <docs/examples/input_handler.rst>`_: includes keyboard key combos and gamepads.
- `gale.log <docs/examples/log.rst>`_: console/file defaults, adding Graylog, Sentry, Discord, or any other destination.
- `gale.net <docs/examples/net.rst>`_: ``Server``/``Client``, channel choice, RTT, LAN discovery, room codes.
- `gale.particle_system <docs/examples/particle_system.rst>`_
- `gale.physics <docs/examples/physics.rst>`_: bodies, shapes, joints, collision callbacks, and the scene graph, with Box2D never exposed directly.
- `gale.state <docs/examples/state.rst>`_
- `gale.stencil <docs/examples/stencil.rst>`_: mask an arbitrary shape out of a surface, love2d-stencil style.
- `gale.text <docs/examples/text.rst>`_
- `gale.timer <docs/examples/timer.rst>`_
- `gale.ui <docs/examples/ui.rst>`_: menus, HUDs, and forms built from panels, buttons, list views, text inputs, closable windows, and more.
- `gale.ai <docs/examples/gale_ai.rst>`_: steering behaviors, behavior tree, decision tree, Blackboard, graphs/search, and the ``Agent`` class.

These are short, focused snippets per module. For full running games
built with gale, see ``examples/space_trip`` and, in particular for
``gale.ai``, `examples/nightwatch <examples/nightwatch/README.md>`_, a
small stealth demo whose guards patrol, chase, and coordinate through a
shared behavior tree, blackboard, and pathfinding; for
``gale.net``/``gale.ui``, `examples/rally <examples/rally/README.md>`_,
a small online Pong playable over a LAN or the internet; and, for
``gale.physics``, `examples/leap <examples/leap/README.md>`_, a
platformer using all three body types, and
`examples/hillclimb <examples/hillclimb/README.md>`_, a small
vehicle-physics demo built on motorized wheel joints.

Each example under ``examples/`` is a standalone project (its own
``settings.py`` and ``src/``), so it doesn't see the copy of ``gale``
inside this repository unless it's actually installed. From the
repository root, run ``pip install -e .`` once, then ``cd`` into the
example's directory and run ``python main.py`` from there.


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
Gale is obviously strongly dependent on Python and Pygame. It also depends on the
library Click for our command line implementation.


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

.. |GithubCommits| image:: https://img.shields.io/github/commits-since/R3mmurd/Gale/v1.5.0.svg
   :target: https://github.com/R3mmurd/Gale/compare/v1.5.0...main

.. |BlackFormatBadge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |CIBadge| image:: https://github.com/R3mmurd/Gale/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/R3mmurd/Gale/actions/workflows/ci.yml

.. _gale: https://github.com/R3mmurd/Gale
.. _Python: https://www.python.org/
.. _Pygame: https://www.pygame.org
.. _The MIT License: https://opensource.org/licenses
