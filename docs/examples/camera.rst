`← Back to the main README <../../README.rst>`_

gale.camera
============

love2d has ``love.graphics.push``/``translate``/``scale``/``pop`` to
scroll and zoom a whole scene at once; pygame has no GPU transform
stack to piggyback on the same way, so ``gale.camera.Camera`` instead
turns world coordinates into screen ones for you — you still ``blit``
each entity yourself, just at the position (and size) the camera says
to.

See `examples/scavenger <../../examples/scavenger/README.md>`_ for a
full game built on this: a coin-collecting game where the camera
follows the player around a world much bigger than the viewport, with
zoom and screen shake.

Basic usage
------------

.. code-block:: python

   from gale.camera import Camera

   camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)

   # In your state:
   def update(self, dt):
       camera.update(dt)

   def render(self, surface):
       for entity in self.entities:
           surface.blit(entity.image, camera.apply(entity.rect))

``camera.x``/``camera.y`` are the world point the camera is centered
on — set them directly for an instant cut (a new room, a teleport).

Following a target
--------------------

Any object with ``x``/``y`` attributes (a ``gale.physics.Node``, your
own player, ...) can be tracked automatically:

.. code-block:: python

   camera.follow(player)               # snaps to the player every update()
   camera.follow(player, rate=6.0)     # or eases toward it instead — higher rate, snappier
   camera.unfollow()                   # stop tracking, x/y stay wherever they last were

Zoom
-----

.. code-block:: python

   camera.zoom = 2.0   # zoomed in
   camera.zoom = 0.5   # zoomed out

``apply()`` scales both the position and the size of the rect you pass
it, so a zoomed camera also needs whatever you're blitting to be drawn
at (or scaled to) that same size — see ``pygame.transform.scale`` if
your sprites are a fixed image size.

Keeping the camera inside the map
------------------------------------

.. code-block:: python

   import pygame

   camera.bounds = pygame.Rect(0, 0, world_width, world_height)

Every ``update()``, ``x``/``y`` are clamped so the viewport never
shows anything past ``bounds`` — unless the map itself is smaller than
the viewport, in which case the camera centers on it instead of
clamping to an inverted range.

Screen shake
-------------

.. code-block:: python

   camera.shake(magnitude=8, duration=0.3)  # e.g. on taking damage, an explosion

A single call replaces any shake already running rather than stacking
with it. The offset decays linearly to 0 over ``duration`` seconds.

Screen ↔ world coordinates
-----------------------------

For anything that isn't a plain ``blit`` — mouse picking, a minimap,
particles spawned at a world position:

.. code-block:: python

   world_point = camera.screen_to_world(rescaled_mouse_position)
   screen_point = camera.world_to_screen(entity.position)

Known limitations
-------------------

- No rotation — only scroll (``x``/``y``) and uniform zoom. Rotating a
  whole pygame scene means rotating every surface individually
  (``pygame.transform.rotate``, which is also lossy/blurry at
  non-right angles), which is a much bigger cost than scroll/zoom and
  rarely needed for a 2D top-down/platformer camera; add it yourself
  with ``pygame.transform.rotate`` on a per-entity basis if a specific
  effect needs it.
- A single ``Camera`` renders one viewport. For split-screen, use one
  ``Camera`` per player, each with its own ``bounds``, and blit each
  player's entities to their own sub-surface.
