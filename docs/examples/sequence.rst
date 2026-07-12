`← Back to the main README <../../README.rst>`_

gale.sequence
=============

This module is the shared engine behind ``gale.quest`` and
``gale.cutscene``: both are, underneath, an ordered series of steps that
each run for a while before handing off to the next one. ``Step`` is one
such step (complete after a fixed duration, as soon as a specific input is
pressed, or by whatever custom condition a subclass implements),
``StepGroup`` runs several steps side by side, and ``Sequence`` drives a
list of steps one at a time.

Step
----

.. code-block:: python

   from gale.sequence import Sequence, Step


   class ShowBanner(Step):
       def __init__(self, text, font, **kwargs) -> None:
           super().__init__(**kwargs)
           self.text = text
           self.font = font

       def render(self, surface) -> None:
           render_text(surface, self.text, self.font, 400, 300, "white", center=True)


   sequence = Sequence([
       # Shown for 2 seconds, or skipped early with the "confirm" input.
       ShowBanner("Chapter 1", font, duration=2.0, advance_on_input="confirm"),
       ShowBanner("A new adventure begins...", font, advance_on_input="confirm"),
   ])

   # In the game loop:
   sequence.update(dt)
   sequence.render(surface)
   # And forward input from wherever your game dispatches it:
   sequence.on_input(input_id, input_data)

``duration``/``advance_on_input`` cover the two most common ways a step
finishes on its own. Passing neither leaves ``is_complete()`` at its
default of "never, on its own" -- override it in a subclass instead (a
quest objective's progress is exactly this: see ``gale.quest``). Call
``super().is_complete()`` too if duration/advance_on_input should still be
able to force it, the same way ``gale.state.HierarchicalState`` expects
overrides of ``enter``/``update``/``render`` to call through to keep its
own delegation working.

StepGroup
---------

Runs several steps side by side -- a character walking across the screen
while a line of dialogue plays over it, for instance -- completing once
all of them are done, or any one of them with ``require_all=False``:

.. code-block:: python

   from gale.sequence import StepGroup

   StepGroup([
       MoveActor(hero, target=(400, 200), duration=1.5),
       Dialogue("Hero", "This way!", font),
   ])

A ``StepGroup`` is itself a ``Step``, so it can also be given its own
``duration``/``advance_on_input``, which forcibly completes the whole
group regardless of its children (a hard timeout).

Sequence
--------

``Sequence`` is the runner: it enters the first step right away, and
every ``update``/``render``/``on_input`` call is forwarded to whichever
step is currently active. ``on_finished`` fires once, with no arguments,
when the last step completes:

.. code-block:: python

   sequence = Sequence(
       [Step(duration=1.0), Step(advance_on_input="confirm")],
       on_finished=lambda: print("done"),
   )

``sequence.skip_current()`` forces the active step to end immediately
regardless of its own ``is_complete()`` -- handy for a "hold to skip"
input layered on top of whatever the steps themselves already allow.
