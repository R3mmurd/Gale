`← Back to the main README <../../README.rst>`_

gale.memoize
=============

``Memoized`` wraps a function, caching its return value per distinct
positional/keyword argument combination. ``Memo`` is a process-wide
registry of every ``Memoized`` created through ``Memo.memoize`` — call
``Memo.update(dt)`` once a frame to age all of them, the same shape
`gale.timer <timer.rst>`_'s ``Timer`` already gives ``Every``/``After``/
``Tween``. `gale.game <../../README.rst>`_'s ``Game`` already calls
``Memo.update(dt)`` for you every frame, right alongside ``Timer.update(dt)``.

What ``ttl`` means
--------------------

A ``Memoized``'s ``ttl`` is measured in seconds of accumulated
``update(dt)`` — game time, not the wall clock — so a cache pauses
right along with the rest of the game instead of quietly expiring
while a menu is open:

- ``ttl=None`` (the default): cached forever, exactly like
  ``functools.lru_cache``, until ``clear()``/``invalidate()`` is
  called explicitly.
- ``ttl=0``: valid only for the remainder of the current frame —
  however many times it's called before the next ``update(dt)``, the
  wrapped function runs once.
- ``ttl=N`` (seconds): cached for up to N seconds of game time.

Caching an expensive query for the rest of the frame
--------------------------------------------------------

Several independent systems asking "who's the nearest enemy?" in the
same frame shouldn't each pay for their own search:

.. code-block:: python

   from gale.memoize import Memo


   @Memo.memoize(ttl=0)
   def nearest_enemy(world, x, y):
       return min(world.enemies, key=lambda e: (e.x - x) ** 2 + (e.y - y) ** 2)

Every call this frame with the same arguments reuses the first
result; next frame, the first call recomputes it again.

Letting a perception check go stale for a moment
----------------------------------------------------

An AI's line-of-sight check is expensive enough that recomputing it
every single frame is wasteful, but it's fine for it to be up to,
say, half a second stale:

.. code-block:: python

   class Guard:
       @Memo.memoize(ttl=0.5)
       def can_see_player(self, player):
           return raycast(self.eye_position, player.position)

Unlike ``functools.lru_cache``, this entry actually expires — so
decorating an instance method here doesn't keep that ``Guard`` pinned
in memory forever just because it was cached once.

A plain, unregistered cache
------------------------------

``Memoized`` also works stand-alone, without going through ``Memo``
at all, when a cache doesn't need to be aged automatically every
frame — for instance a lookup table built once and never invalidated:

.. code-block:: python

   from gale.memoize import Memoized

   @Memoized
   def load_texture(path):
       return pygame.image.load(path).convert_alpha()

Manual control
----------------

.. code-block:: python

   nearest_enemy.invalidate(world, 10, 20)  # drop one specific entry
   nearest_enemy.clear()                     # drop every entry

   Memo.pause()   # stop every registered cache from aging
   Memo.resume()
   Memo.clear()   # unregister everything (each Memoized keeps its own
                   # already-cached entries; they just stop aging)
