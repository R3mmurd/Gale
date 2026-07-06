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

You can also pause and resume every scheduled item at once, for instance
while the game is paused, and clear everything, for instance when
changing levels:

.. code-block:: python

   Timer.pause()
   Timer.resume()
   Timer.clear()
