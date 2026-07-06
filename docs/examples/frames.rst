`← Back to the main README <../../README.rst>`_

gale.frames
============

``generate_frames`` slices a spritesheet into a flat list of
``pygame.Rect`` regions, one per sprite, scanning the sheet row by row.
It's usually called once in ``settings.py``, right after loading the
spritesheet texture, and the resulting list is stored in a shared
``FRAMES`` dictionary:

.. code-block:: python

   import pygame

   from gale import frames

   TEXTURES = {
       "player": pygame.image.load("assets/graphics/player.png"),
   }

   FRAMES = {
       "player": frames.generate_frames(TEXTURES["player"], sprite_width=16, sprite_height=16),
   }

Elsewhere, you index into that list (or slice it) to build an
``Animation`` (see `gale.animation <animation.rst>`_) or to pick a single
frame to blit:

.. code-block:: python

   import settings

   idle_frames = settings.FRAMES["player"][0:2]
   surface.blit(settings.TEXTURES["player"], (x, y), settings.FRAMES["player"][0])

If your spritesheet doesn't fit a single uniform grid (for instance,
sprites of different sizes packed together, or frames that need
reshaping into a 2D grid of variants), write your own slicing helper
instead — ``generate_frames`` only covers the common, uniform-grid case.
