`← Back to the main README <../../README.rst>`_

gale.quest
==========

A generic, customizable-per-game quest system built on
`gale.sequence <sequence.rst>`_: ``Objective`` (one trackable goal),
``Stage`` (a group of objectives tracked together), ``Quest`` (a sequence
of stages), and ``QuestLog`` (tracks every quest a game has, starts them,
and broadcasts progress events to whichever are active).

None of this hardcodes what an objective actually means: a game defines
its own progress-event keys (``"wolves_killed"``, ``"herbs_collected"``,
...) and reports progress from wherever that event actually happens.

.. code-block:: python

   from gale.quest import Objective, Quest, QuestLog, Stage

   log = QuestLog()
   log.register(
       Quest(
           "wolf_trouble",
           "Wolf Trouble",
           [
               Stage([Objective("wolves_killed", "Defeat 3 wolves", target=3)]),
               Stage([Objective("report", "Report back to the elder", target=1)]),
           ],
           on_completed=lambda: print("Wolf Trouble completed!"),
       )
   )
   log.start("wolf_trouble")

   # Wherever a wolf actually dies in your game:
   log.notify("wolves_killed", 1)

   # Every frame (only active quests do anything):
   log.update(dt)

A ``Stage`` completes once every one of its objectives does (or just one
of them, with ``require_all=False``, e.g. "reach the gate OR find the
secret passage"), and a ``Quest`` moves to its next stage the same way a
``Sequence`` moves to its next step. ``Quest.notify``/``QuestLog.notify``
only ever reach the *current* stage of each active quest -- objectives in
stages that haven't started yet, or that already finished, are left
alone.

``Objective`` is a ``Step`` underneath, so ``duration``/``advance_on_input``
work on it too: an objective that's just "wait a moment" or "press a key
to confirm reading the quest" needs no progress counter at all:

.. code-block:: python

   Objective(description="Read the notice board", advance_on_input="confirm")

Anything that doesn't fit a simple progress counter (checking an
inventory, a flag on a shared ``gale.ai.blackboard.Blackboard``, ...) is
just a matter of subclassing ``Objective`` and overriding ``is_complete``:

.. code-block:: python

   class HasItemObjective(Objective):
       def __init__(self, inventory, item_name, **kwargs) -> None:
           super().__init__(description=f"Obtain {item_name}", **kwargs)
           self.inventory = inventory
           self.item_name = item_name

       def is_complete(self) -> bool:
           return self.item_name in self.inventory or super().is_complete()

A ``Blackboard`` observer bridges the two systems naturally, if a game
already tracks some state there:

.. code-block:: python

   blackboard.observe(
       "is_alerted", lambda key, old, new: log.notify("guard_alerted", 1) if new else None
   )
