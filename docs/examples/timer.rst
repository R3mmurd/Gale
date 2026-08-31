`← Back to the main README <../../README.rst>`_

gale.timer
===========

``Timer`` schedules callbacks and interpolates (tweens) object attributes
over time. It is a class-level singleton: register items on the ``Timer``
class itself, and call ``Timer.update(dt)`` once per frame (the ``Game``
base class already does this for you).

.. code-block:: python

   from gale.timer import Timer

   # Call a function every 2 seconds, forever.
   Timer.every(2, lambda: print("tick"))

   # Call a function every 0.5 seconds, up to 3 times, then run on_finish.
   Timer.every(0.5, lambda: print("spawn enemy"), limit=3, on_finish=lambda: print("done spawning"))

   # Call a function once, after 1 second.
   Timer.after(1, lambda: print("go!"))

   # Interpolate attributes of one or more objects over time.
   class Sprite:
       def __init__(self) -> None:
           self.x = 0
           self.alpha = 255

   sprite = Sprite()
   Timer.tween(
       1.5,
       [(sprite, {"x": 100, "alpha": 0})],
       ease_function_name="out_quad",
       on_finish=lambda: print("faded out"),
   )

   # In your game loop:
   Timer.update(dt)

``ease_function_name`` defaults to ``"linear"`` and accepts any of the
~30 curves in ``gale.ease_functions`` (``"in_quad"``, ``"out_bounce"``,
``"in_out_elastic"``, ...) — most tweens are fine left at the default,
reach for a specific ease only where the extra motion polish matters.

You can tween more than one object in the same call (they all take the
same ``duration``), and chain several tweens through nested
``on_finish`` callbacks to build a short cutscene, such as a fade in,
followed by a pause, followed by a fade out:

.. code-block:: python

   Timer.tween(1, [(self, {"transition_alpha": 0})], on_finish=lambda: (
       Timer.after(1.5, lambda: (
           Timer.tween(1, [(self, {"transition_alpha": 255})], on_finish=self.start_game)
       ))
   ))

You can also pause and resume every scheduled item at once, for instance
while the game is paused, and clear everything, for instance when
changing levels or when the player skips a cutscene (manually restoring
whatever final values the interrupted tweens were animating towards):

.. code-block:: python

   Timer.pause()
   Timer.resume()

   if skipped:
       Timer.clear()
       self.transition_alpha = 0

``During`` runs a raw per-frame callback instead of interpolating an
object's attributes — for effects ``Tween`` doesn't fit, such as a
camera shake or a shader uniform. It's fed ``dt`` and ``progress``
(0 to 1) every update, then ``on_finish`` once:

.. code-block:: python

   Timer.during(
       0.3,
       lambda dt, progress: camera.shake(intensity=8 * (1 - progress)),
       on_finish=lambda: camera.reset_shake(),
   )

Any item — ``Every``/``After``/``Tween``/``During`` — exposes its own
``.progress`` (0 to 1) and can be paused/resumed on its own, without
touching anything else ``Timer`` is tracking:

.. code-block:: python

   fade = Timer.tween(2.0, [(self, {"alpha": 0})])
   hud.set_progress(fade.progress)

   fade.pause()
   fade.resume()

Groups: pausing/clearing a subset
------------------------------------

Tag any item with ``group`` (a string, or any other hashable — even
the owning object itself) to pause, resume, or clear just that subset
instead of everything ``Timer`` is tracking — handy for dropping every
timer an enemy started when it dies, without touching the player's:

.. code-block:: python

   Timer.every(1.0, enemy.fire, group=enemy)
   Timer.tween(0.5, [(enemy, {"flash_alpha": 0})], group=enemy)

   # The enemy died -- stop everything it had scheduled, and nothing else.
   Timer.clear(group=enemy)

``group`` also composes with a global pause/resume for the common
case of "gameplay timers should freeze while paused, but the pause
menu's own animations shouldn't" — set ``ignore_global_pause=True`` on
whatever shouldn't stop for a groupless ``Timer.pause()``:

.. code-block:: python

   Timer.tween(
       0.2, [(pause_menu, {"alpha": 255})], ignore_global_pause=True
   )
   Timer.pause()  # gameplay timers stop; pause_menu's tween keeps animating

A group can still be paused on its own, even if every item in it set
``ignore_global_pause`` — that flag only exempts an item from a
*groupless* ``Timer.pause()``, never from ``Timer.pause(group=...)``.
