`← Back to the main README <../../README.rst>`_

gale.particle_system
======================

``ParticleSystem`` spawns a burst of particles around a point, each one
with its own random acceleration, lifetime, and color, useful for
effects such as explosions, sparks, or dust.

.. code-block:: python

   import pygame

   from gale.particle_system import ParticleSystem

   explosion = ParticleSystem(x=200, y=150, n=40, on_finish=lambda: print("explosion done"))
   explosion.set_life_time(minimum=0.3, maximum=0.8)
   explosion.set_linear_acceleration(x1=-50, y1=-50, x2=50, y2=50)
   explosion.set_colors([pygame.Color("orange"), pygame.Color("red"), pygame.Color("yellow")])
   explosion.set_area_spread(rx=4, ry=4)
   explosion.generate()

   # In your update/render loop:
   explosion.update(dt)
   explosion.render(surface)
