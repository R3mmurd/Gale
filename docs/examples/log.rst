`← Back to the main README <../../README.rst>`_

gale.log
=========

``gale.log`` sets up logging for a gale game: printed to the terminal
and written to a plain-text file by default, extensible to send
records anywhere else (Graylog and friends) by attaching another
handler. It's a thin configuration layer over Python's own
``logging`` module — every handler you attach already *is* the
"where do records go" strategy the standard library gives you for
free, so ``gale.log`` never reinvents formatting, levels, or record
dispatch, only wires up sane defaults and returns real
``logging.Logger`` instances.

Basic usage
------------

.. code-block:: python

   from gale.log import get_logger

   logger = get_logger("space_trip")
   logger.info("saucer destroyed a rock")
   logger.warning("player near the edge of the screen")

Calling ``get_logger`` without ever calling ``configure`` first still
works — it configures itself with the defaults (console + a
``gale.log`` file in the current directory) the first time it's
called. Call ``configure`` yourself, once, near the start of your
game, to override those defaults:

.. code-block:: python

   from gale.log import configure
   from gale.log.level import LogLevel

   configure(level=LogLevel.DEBUG, log_file="my_game.log", console=True)

Pass ``log_file=None`` to disable file logging, or ``console=False``
to disable printing to the terminal.

Adding another destination (Graylog and friends)
-----------------------------------------------------

Any ``logging.Handler`` can be attached on top of the console/file
defaults with ``add_handler`` — that's the whole extension point:

.. code-block:: python

   from gale.log import add_handler
   from gale.log.graylog_handler import GraylogHandler

   add_handler(GraylogHandler("graylog.example.com", 12201))

``GraylogHandler`` sends each record as a GELF (Graylog Extended Log
Format) datagram over UDP. Anything passed as ``extra`` to a logging
call becomes a custom GELF field:

.. code-block:: python

   logger.info("player scored", extra={"player_id": 7, "points": 100})

For anything other than Graylog — a different log aggregator, a
custom webhook, whatever — write a small ``logging.Handler``
subclass the same way and hand it to ``add_handler``; ``gale.log``
doesn't need to know about it specifically.

Named loggers
---------------

.. code-block:: python

   logger = get_logger("nightwatch.guard")  # -> "gale.nightwatch.guard"

Nesting names under gale's own top-level logger keeps every gale
game's log lines identifiable and lets you filter/configure a whole
subsystem's verbosity independently if you ever need to (through the
standard library's own logger-hierarchy features — ``get_logger``
returns a plain ``logging.Logger``, so everything else in the
``logging`` documentation applies unchanged).
