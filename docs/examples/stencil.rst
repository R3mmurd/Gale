`← Back to the main README <../../README.rst>`_

gale.stencil
=============

Pygame has no GPU stencil buffer, so ``gale.stencil`` gives you the
same end result love2d's
`love.graphics.stencil <https://love2d.org/wiki/love.graphics.stencil>`__
gets on the CPU: draw an arbitrary shape (a circle, a polygon,
another sprite, text — anything you can draw or blit) into a
``Stencil``'s own mask surface, then ``apply`` it to any other
surface to zero out the alpha of every pixel outside that shape (or,
with ``invert=True``, every pixel inside it).

That is the classic building block for a top-down game: a circular
torch/vision reveal over a dark fog-of-war overlay, a minimap cropped
to a circle, a doorway that only shows what's behind it once you're
close enough.

See `examples/lantern <../../examples/lantern/README.md>`_ for a full
game built on this: a top-down exploration game where the room is
covered in darkness except for a circle of light around the player.

Fog of war / vision reveal
----------------------------

.. code-block:: python

   import pygame
   from gale.stencil import Stencil

   stencil = Stencil((width, height))

   # In render(), every frame the light's position/radius might change:
   stencil.clear()
   stencil.draw(lambda mask: pygame.draw.circle(mask, "white", light_pos, radius))

   overlay = pygame.Surface((width, height), pygame.SRCALPHA)
   overlay.fill((0, 0, 0, 230))
   stencil.apply(overlay, invert=True)  # punch the circle out of the dark overlay
   surface.blit(overlay, (0, 0))

Cropping to a shape
---------------------

Without ``invert``, ``apply`` keeps only what's *inside* the drawn
shape — handy for cropping a minimap (or any other surface) to a
circle instead of a rectangle:

.. code-block:: python

   minimap = pygame.Surface((96, 96), pygame.SRCALPHA)
   minimap.blit(world_snapshot, (0, 0))

   crop = Stencil((96, 96))
   crop.draw(lambda mask: pygame.draw.circle(mask, "white", (48, 48), 48))
   crop.apply(minimap)  # everything outside the circle is now fully transparent

   surface.blit(minimap, (8, 8))

How it works
-------------

``draw()`` hands you the ``Stencil``'s own surface to draw the
"visible" shape onto, in opaque white — that's the convention this
module relies on (any alpha in your draw calls is fine; the RGB
channels should stay white). ``apply()`` then multiplies the target
surface's own RGBA by the mask's (``pygame.BLEND_RGBA_MULT``): inside
the shape, that leaves the target's color and alpha untouched
(``channel * 255 / 255``); outside it, it zeroes both out
(``channel * 0``). ``invert=True`` just applies the same
multiplication against ``255 - mask`` instead.

For this to have any visible effect once the masked surface is
blit somewhere else, it must have per-pixel alpha — create it with
``pygame.SRCALPHA`` (or call ``.convert_alpha()``), the same
requirement any other alpha-blended surface has.

A single ``Stencil`` can be ``apply``'d to as many surfaces as you
like once its shape is drawn; call ``clear()`` before ``draw()`` again
to reuse it for a new shape (e.g. next frame, once the light moves).
