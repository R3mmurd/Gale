`← Back to the main README <../../README.rst>`_

gale.cutscene
=============

A small toolkit for scripted, non-interactive scenes, built on
`gale.sequence <sequence.rst>`_: ``Cutscene`` (a sequence of beats that
also ticks/renders any actors involved every frame) and the beats
themselves -- ``ShowImage``, ``PlayAnimation``, ``MoveActor``,
``SetActorAnimation``, ``Dialogue``, and ``Wait``. Every beat is a
``gale.sequence.Step``, so ``duration``/``advance_on_input`` (and
``gale.sequence.StepGroup``, to run several beats at once) all just work.

.. code-block:: python

   from gale.cutscene import Cutscene, Dialogue, MoveActor, ShowImage

   cutscene = Cutscene(
       [
           ShowImage(pygame.image.load("village_establishing_shot.png"), duration=2.0),
           MoveActor(elder, target=(400, 200), duration=1.5),
           Dialogue("Elder", "The forest holds many secrets...", font, advance_on_input="confirm"),
           Dialogue("Hero", "I'll be careful.", font, advance_on_input="confirm"),
       ],
       actors=[elder, hero],
       on_finished=lambda: state_machine.change("play"),
   )

   # In the game loop:
   cutscene.update(dt)
   cutscene.render(surface)
   cutscene.on_input(input_id, input_data)  # forward from wherever input is dispatched

``actors`` are ticked (``update(dt)``)/drawn (``render(surface)``) every
frame regardless of which beat is currently active, so a character keeps
idling/animating in the background even while another one is delivering
a line -- exactly the "characters that are in the scene at that moment
move on their own" a conversation cutscene needs. ``MoveActor``/
``SetActorAnimation`` are duck-typed: any object with a ``.position``
(a ``pygame.Vector2``, or a value ``pygame.Vector2(...)`` accepts) and/or
``.animation`` attribute works, whatever character class a game already
has (an ``Agent``, a custom ``Player`` class, ...).

Running several beats at once
------------------------------

Use ``gale.sequence.StepGroup`` to have a beat play *while* another one
does, instead of one after the other:

.. code-block:: python

   from gale.sequence import StepGroup

   Cutscene([
       StepGroup([
           MoveActor(hero, target=(400, 200), duration=1.5),
           Dialogue("Hero", "This way!", font),
       ]),
       ...
   ])

"Playing a video"
-----------------

``PlayAnimation`` plays a ``gale.animation.Animation`` as a cutscene beat
-- gale's stand-in for video playback. This is deliberately *not* real
video-codec (mp4/webm) decoding: gale never depends on a decoder library
(ffmpeg, OpenCV, ...), the same way ``gale.tilemap`` never depends on
``gale.physics``. Pre-render the actual footage as a frame sequence (most
video editors, and ffmpeg itself, can export a PNG-per-frame sequence)
and load those the same way any other sprite animation would:

.. code-block:: python

   from gale.animation import Animation
   from gale.cutscene import PlayAnimation

   frames = [pygame.image.load(f"intro_{i:03d}.png") for i in range(90)]
   PlayAnimation(Animation(frames, time_interval=1 / 30, loops=1))

Writing your own beats
-----------------------

Anything game-specific (a screen shake, a particle burst, a sound cue
that must finish before continuing, ...) is just a ``Step`` subclass:

.. code-block:: python

   from gale.sequence import Step

   class PlaySound(Step):
       def __init__(self, sound, **kwargs) -> None:
           super().__init__(**kwargs)
           self.sound = sound

       def enter(self, *args, **kwargs) -> None:
           super().enter(*args, **kwargs)
           self.channel = self.sound.play()

       def is_complete(self) -> bool:
           return not self.channel.get_busy() or super().is_complete()
