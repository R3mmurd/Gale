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

Switching between named animations
-----------------------------------

In practice, a character usually owns a dictionary of animations (one per
action) and switches between them, resetting the new one so it always
starts from its first frame. Most gameplay animations are left looping
forever (``loops=None``, the default), letting a state machine — see
`gale.state <state.rst>`_ — decide when to switch to a different
animation, instead of relying on ``on_finish``:

.. code-block:: python

   from gale.animation import Animation


   class Character:
       def __init__(self) -> None:
           self.animations = {
               "idle": Animation(["idle_0", "idle_1"], time_interval=0.2),
               "walk": Animation(["walk_0", "walk_1", "walk_2", "walk_3"], time_interval=0.1),
           }
           self.current_animation = self.animations["idle"]

       def change_animation(self, animation_id: str) -> None:
           new_animation = self.animations[animation_id]
           if new_animation is not self.current_animation:
               self.current_animation = new_animation
               self.current_animation.reset()

       def update(self, dt: float) -> None:
           self.current_animation.update(dt)

       def get_current_frame(self):
           return self.current_animation.get_current_frame()
