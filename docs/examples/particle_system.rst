`← Back to the main README <../../README.rst>`_

gale.particle_system
======================

``ParticleSystem`` spawns a burst of particles around a point, each one
with its own random acceleration, lifetime, and color, useful for effects
such as explosions, sparks, or dust.

The constructor takes an ``on_finish`` callback that runs once, when all
of the system's particles have reached the end of their lifetime — handy
to flag the owning object as no longer needing this effect. The
non-varying knobs (``set_life_time``, ``set_linear_acceleration``,
``set_area_spread``) are usually configured once, right after
construction, while ``set_colors`` is often set again right before each
``generate()`` call, since the colors of a burst may depend on the event
that triggered it (for instance, the color of the object that was hit):

.. code-block:: python

   import pygame

   from gale.particle_system import ParticleSystem


   class Brick:
       def __init__(self, x: float, y: float, color: pygame.Color) -> None:
           self.x = x
           self.y = y
           self.color = color
           self.broken = False
           self.active = True

           self.particle_system = ParticleSystem(
               self.x + 16, self.y + 8, n=64, on_finish=lambda: setattr(self, "active", False)
           )
           self.particle_system.set_life_time(0.2, 0.4)
           self.particle_system.set_linear_acceleration(-0.3, 0.5, 0.3, 1)
           self.particle_system.set_area_spread(4, 7)

       def hit(self) -> None:
           self.broken = True
           r, g, b, _ = self.color
           self.particle_system.set_colors([(r, g, b, 128), (r, g, b, 255)])
           self.particle_system.generate()

       def update(self, dt: float) -> None:
           self.particle_system.update(dt)

       def render(self, surface: pygame.Surface) -> None:
           if not self.broken:
               ...  # draw the brick's own sprite

           # Particles keep rendering for a while even after the brick itself
           # is gone, since update/render on the particle system are
           # independent from the brick's own visibility.
           self.particle_system.render(surface)
