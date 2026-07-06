`← Back to the main README <../../README.rst>`_

gale.text
==========

``gale.text`` eases rendering text with pygame fonts, either as a
one-shot function call or as a reusable ``Text`` object that keeps track
of its own font, color, and position.

.. code-block:: python

   import pygame

   from gale.text import Text, render_text

   pygame.font.init()
   font = pygame.font.Font(None, 16)

   # One-shot rendering, useful for text that changes every frame, such as a score counter.
   def render(surface: pygame.Surface, score: int) -> None:
       render_text(
           surface, f"Score: {score}", font, x=10, y=10, color=pygame.Color("white"), shadowed=True
       )

   # A reusable Text object, useful for static labels.
   title = Text(
       "Game Over",
       font,
       x=160,
       y=90,
       color=pygame.Color("red"),
       center=True,
       shadowed=True,
   )

   # In your render loop:
   title.render(surface)
