`← Back to the main README <../../README.rst>`_

gale.event
===========

``Signal`` is a single event channel — ``connect``/``disconnect``/
``emit``, priority-ordered, with ``connect(..., once=True)`` for a
listener that detaches itself before it runs. ``EventEmitter`` is a
mixin/composable object owning any number of ad hoc, string-named
Signals, created lazily on first use (``on``/``off``/``once``/
``emit``). ``EventBus`` is a ready-to-use global ``EventEmitter``
(classmethods over a single module-level instance, the same shape
`InputHandler <input_handler.rst>`_ already uses) for modules that
want to publish/subscribe without sharing an object reference to do
it.

Every ``emit`` isolates each listener: one that raises is logged
(through `gale.log <log.rst>`_) and dispatch continues to the rest, so
one broken subscriber can never break every other, independently
owned listener on the same event.

A plain Signal
----------------

.. code-block:: python

   from gale.event import Signal


   class Enemy:
       def __init__(self) -> None:
           self.hp = 10
           self.died = Signal()

       def take_damage(self, amount: int) -> None:
           self.hp -= amount

           if self.hp <= 0:
               self.died.emit(self)


   def drop_loot(enemy: Enemy) -> None:
       print(f"{enemy} dropped loot")


   def award_experience(enemy: Enemy) -> None:
       print(f"gained xp for killing {enemy}")


   enemy = Enemy()
   enemy.died.connect(drop_loot)
   enemy.died.connect(award_experience)
   enemy.take_damage(10)  # both listeners run, in connection order

A listener connected with ``once=True`` is disconnected right before
it runs, so a single ``emit`` never reaches it twice and it can safely
reconnect itself (or something else) from inside its own callback:

.. code-block:: python

   def show_first_blood_banner(enemy: Enemy) -> None:
       ui.show_banner("First Blood!")

   enemy.died.connect(show_first_blood_banner, once=True)

Listeners run highest ``priority`` first (ties keep connection order)
— handy when one listener's result depends on another having already
run, such as a save-triggering listener that should only fire after
every gameplay listener has updated state:

.. code-block:: python

   enemy.died.connect(award_experience, priority=10)
   enemy.died.connect(autosave, priority=0)

EventEmitter: many named events on one object
------------------------------------------------

Combine ``EventEmitter`` by multiple inheritance with any class in
your game, the same way ``InputListener``/``CommandControlled``
already can, to give it an open-ended set of named events instead of
declaring a ``Signal`` attribute for each one:

.. code-block:: python

   from gale.event import EventEmitter


   class QuestLog(EventEmitter):
       def __init__(self) -> None:
           super().__init__()
           self.progress: dict = {}

       def notify(self, key: str, amount: int = 1) -> None:
           self.progress[key] = self.progress.get(key, 0) + amount
           self.emit("progress", key, self.progress[key])


   def on_progress(key: str, total: int) -> None:
       print(f"{key}: {total}")


   quest_log = QuestLog()
   quest_log.on("progress", on_progress)
   quest_log.notify("wolves_killed")

``off``/``once``/``is_on``/``has_listeners``/``clear`` round out the
same API a plain ``Signal`` gives, scoped to one event name at a time;
``signal(event_name)`` returns the underlying ``Signal`` directly for
anything that needs it (``len()``, ``is_connected()``, ...).

EventBus: cross-module communication
----------------------------------------

Where two modules need to react to the same event without either one
importing the other (say, ``gale.ai`` and ``gale.ui`` both reacting to
a quest module's progress), ``EventBus`` gives every caller the same
global ``EventEmitter`` without either side holding a reference to it:

.. code-block:: python

   from gale.event import EventBus

   # Anywhere gameplay code lives:
   EventBus.emit("wolves_killed", count=1)

   # Anywhere UI code lives, with no import of the gameplay module:
   EventBus.on("wolves_killed", lambda count: hud.flash_objective())

Being global and process-wide, ``EventBus`` is best kept for events
that are genuinely cross-cutting; an event scoped to one object (an
enemy's ``died``, a window's ``closed``) reads better, and is easier
to reason about, as a plain ``Signal`` or through ``EventEmitter``.
