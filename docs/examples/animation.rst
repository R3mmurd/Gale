`← Back to the main README <../../README.rst>`_

gale.animation
===============

``Animation`` cycles through a sequence of frames (they can be anything:
``pygame.Rect`` regions of a spritesheet, image names, surfaces, etc.) at a
fixed time interval.

.. code-block:: python

   from gale.animation import Animation

   # Loops forever, changing frame every 0.15 seconds.
   idle_animation = Animation(["idle_0", "idle_1", "idle_2"], time_interval=0.15)

   # Plays 3 times and then freezes on its last frame, invoking on_finish.
   attack_animation = Animation(
       ["attack_0", "attack_1", "attack_2", "attack_3"],
       time_interval=0.08,
       loops=3,
       on_finish=lambda: print("Attack animation finished"),
   )

   # In your update loop:
   idle_animation.update(dt)
   current_frame = idle_animation.get_current_frame()

   # Play attack_animation again from the beginning, for instance when the
   # player presses the attack button:
   attack_animation.reset()
