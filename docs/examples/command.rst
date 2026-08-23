`← Back to the main README <../../README.rst>`_

gale.command
=============

``Command`` is a stateless action executed against a ``receiver`` passed
in on every call, never held by the command itself — so the very same
instance can be shared as a singleton between a player and any number
of autonomous creatures that perform the same action.
``CommandBindings`` maps an `InputHandler <input_handler.rst>`_
``input_id`` to the pair of commands run on press and on release, and
``CommandControlled`` is an ``InputListener`` mixin that registers
itself and routes every ``on_input`` notification straight into a
``CommandBindings``.

Defining a command
--------------------

.. code-block:: python

   from gale.command import Command


   class Jump(Command):
       def execute(self, receiver, dt: float = 0.0) -> None:
           receiver.vy = -receiver.jump_speed


   class MoveRight(Command):
       def execute(self, receiver, dt: float = 0.0) -> None:
           receiver.vx = receiver.speed


   class StopMovingRight(Command):
       def execute(self, receiver, dt: float = 0.0) -> None:
           if receiver.vx > 0:
               receiver.vx = 0

Commands hold no state of their own, so one instance of each is enough
for every entity in the game:

.. code-block:: python

   jump = Jump()
   move_right = MoveRight()
   stop_moving_right = StopMovingRight()

Binding commands to input
---------------------------

.. code-block:: python

   from gale.command import CommandBindings, CommandControlled
   from gale.input_handler import InputHandler, KEY_d, KEY_SPACE

   InputHandler.set_keyboard_action(KEY_SPACE, "jump")
   InputHandler.set_keyboard_action(KEY_d, "move_right")

   bindings = CommandBindings()
   bindings.bind("jump", press=jump)
   bindings.bind("move_right", press=move_right, release=stop_moving_right)


   class Player(CommandControlled):
       def __init__(self, command_bindings: CommandBindings) -> None:
           super().__init__(command_bindings)
           self.x = self.y = self.vx = self.vy = 0
           self.speed = 200
           self.jump_speed = 400


   player = Player(bindings)

``CommandControlled`` can be combined by multiple inheritance with any
entity class of your game, the same way ``InputListener`` already can:

.. code-block:: python

   class Player(CommandControlled, Kinematic):
       def __init__(self, command_bindings: CommandBindings, x: float, y: float) -> None:
           super().__init__(command_bindings, x, y)

The same command, driven from input or from AI
--------------------------------------------------

Because a ``Command`` never holds a reference to the entity it acts
upon, the exact same ``jump`` instance bound above can also drive a
creature that has nothing to do with the input system, for instance
from an AI update loop:

.. code-block:: python

   class Creature:
       def __init__(self) -> None:
           self.x = self.y = self.vx = self.vy = 0
           self.jump_speed = 300

       def update(self, dt: float) -> None:
           if self.should_jump():
               jump(self, dt)  # Command.__call__ delegates to execute.

   creature = Creature()
   creature.update(dt=1 / 60)
