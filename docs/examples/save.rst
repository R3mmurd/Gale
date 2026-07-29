`← Back to the main README <../../README.rst>`_

gale.save
=========

``gale.save`` is a general-purpose save-game system: ``SaveManager``
persists whatever JSON-serializable dict a game gives it into named
"slots" on disk, so the same class works for any game, no matter what
it needs to remember.

Basic usage
-----------

.. code-block:: python

   from gale.save import SaveManager

   manager = SaveManager()
   manager.save("slot1", {"level": 3, "hp": 80})

   data = manager.load("slot1")   # {"level": 3, "hp": 80}

By default, saves live under a ``saves/`` directory next to the
project's own ``main.py`` (``settings.SAVE_DIR``, overridable in
``settings.py`` like every other gale setting).

Slots and a save-select screen
--------------------------------

A slot is just a name -- ``"slot1"``, ``"quicksave"``, ``"autosave"``,
whatever a game's own save UI calls it. Extra keyword arguments to
``save()`` are stored as metadata, readable without loading (and
migrating) the full save, which is exactly what a save-select screen
needs:

.. code-block:: python

   manager.save("slot1", {"level": 3}, chapter="The Forest", play_time=1523.4)

   for info in manager.list_saves():   # most recently updated first
       print(info.slot, info.extra["chapter"], info.extra["play_time"])

   manager.exists("slot1")     # True
   manager.delete("slot1")

``list_saves()`` silently skips a slot that fails to read (for
instance, a save file corrupted by a crash mid-write from another
program) rather than raising -- a save-select screen should still show
every *other* slot.

Autosaving
----------

Not a built-in feature (a game decides its own cadence and trigger),
but a one-liner on top of ``gale.timer.Every``:

.. code-block:: python

   from gale.timer import Timer

   Timer.every(60.0, lambda: manager.save("autosave", get_game_state()))

Evolving what a save contains
---------------------------------

A shipped game's save format inevitably needs to change (a new
inventory system, a renamed field). ``SaveManager`` supports this with
a schema ``version`` plus a ``migrations`` dict mapping "upgrade from
this version" functions:

.. code-block:: python

   def add_mana(data):
       return {**data, "mana": 50}   # new field, gets a sane default

   manager = SaveManager(
       version=2,
       migrations={1: add_mana},   # 1 -> 2
   )

``load()`` reads a save's stored version and applies every migration
needed to reach the manager's current one, in order, before handing
the data back -- a save written by an older release of the game keeps
working. Loading a save whose stored version is *newer* than the
manager's own (an old game binary opening a save from a newer one)
raises ``SaveError``, as does a stored version with no registered
migration path forward.

Customizing the format
--------------------------

``save_dir``, ``version``, and ``file_extension`` are also
constructor parameters (each falls back to a ``gale.conf`` setting
when omitted), and the wire format itself is pluggable, the same
``serializer``/``deserializer`` pattern ``gale.net.Server``/``Client``
already use -- swap in a different one for a more compact binary
format, or wrap the default to add compression/encryption:

.. code-block:: python

   import gzip

   from gale.save import SaveManager, json_deserialize, json_serialize

   def compressed_serialize(envelope):
       return gzip.compress(json_serialize(envelope))

   def compressed_deserialize(data):
       return json_deserialize(gzip.decompress(data))

   manager = SaveManager(
       serializer=compressed_serialize,
       deserializer=compressed_deserialize,
       file_extension="sav.gz",
   )

Errors
------

Every failure ``SaveManager`` can hit while reading a save --
a missing slot, a corrupted file, an unreachable schema version -- is
raised as ``SaveError``, so a game only needs to catch one exception
type around ``load()``:

.. code-block:: python

   from gale.save import SaveError

   try:
       data = manager.load("slot1")
   except SaveError as error:
       show_error_dialog(str(error))

Writes are atomic (a temporary file is renamed into place), so a crash
or power loss mid-save can never leave a corrupted file behind --
worst case, the previous save is still there untouched.
