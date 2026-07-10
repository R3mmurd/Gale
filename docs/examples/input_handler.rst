`← Back to the main README <../../README.rst>`_

gale.input_handler
===================

``InputHandler`` is a small observer-pattern-based dispatcher: you bind
keyboard keys, mouse buttons, the mouse wheel, or mouse motion to an
``action_id``, and every registered ``InputListener`` gets notified
through ``on_input(input_id, input_data)`` whenever that action fires.

Typical project setup
----------------------

Bindings are usually all set up in ``settings.py``, at import time, so
every other module can just ``import settings`` and rely on them already
being in place. You can bind more than one physical key to the same
action, for instance to support both WASD and the arrow keys:

.. code-block:: python

   from gale import input_handler

   input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
   input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
   input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
   input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "jump")
   input_handler.InputHandler.set_mouse_click_action(input_handler.MOUSE_BUTTON_1, "jump")

``Game`` (from ``gale.game``) already implements
``InputListener``, registers itself with ``InputHandler`` on
construction, and calls ``InputHandler.handle_input`` for every relevant
pygame event on each frame of its game loop. So in practice you only
need to implement ``on_input`` on your ``Game`` subclass and forward it
to whatever is driving your game (typically a ``StateMachine``, see
`gale.state <state.rst>`_):

.. code-block:: python

   from gale.game import Game
   from gale.input_handler import InputData


   class MyGame(Game):
       def on_input(self, input_id: str, input_data: InputData) -> None:
           if input_id == "quit" and input_data.pressed:
               self.quit()
           else:
               self.state_machine.on_input(input_id, input_data)

Individual states (or any other object) then just inspect ``input_id``
and ``input_data.pressed``/``input_data.released``:

.. code-block:: python

   def on_input(self, input_id, input_data) -> None:
       if input_id == "move_left":
           if input_data.pressed:
               self.paddle.vx = -PADDLE_SPEED
           elif input_data.released and self.paddle.vx < 0:
               self.paddle.vx = 0

If your game renders to a smaller "virtual" surface that ``Game`` scales
up to the real window (via ``virtual_width``/``virtual_height``), remember
to rescale ``input_data.position`` for mouse clicks/motion back down to
virtual coordinates:

.. code-block:: python

   if input_id == "click" and input_data.pressed:
       x, y = input_data.position
       x = x * settings.VIRTUAL_WIDTH // settings.WINDOW_WIDTH
       y = y * settings.VIRTUAL_HEIGHT // settings.WINDOW_HEIGHT

Registering a listener manually
---------------------------------

You don't have to go through ``Game``: any object can implement
``InputListener`` and register itself directly, which is handy for
objects that should react to input on their own:

.. code-block:: python

   from gale.input_handler import InputData, InputHandler, InputListener, KEY_SPACE


   class Player(InputListener):
       def __init__(self) -> None:
           InputHandler.register_listener(self)

       def on_input(self, input_id: str, input_data: InputData) -> None:
           if input_id == "jump" and input_data.pressed:
               self.jump()

       def jump(self) -> None:
           ...


   InputHandler.set_keyboard_action(KEY_SPACE, "jump")
   player = Player()

Key combos
----------

Keyboard bindings can also require one or more modifiers
(``MOD_SHIFT``, ``MOD_CTRL``, ``MOD_ALT``, and/or ``MOD_META``, joined
with the bitwise or operator ``|``) to be held together with the key. A
binding registered without modifiers keeps triggering regardless of
which ones are held, as long as there is no more specific combo bound
to the same key:

.. code-block:: python

   from gale.input_handler import InputHandler, KEY_s, MOD_CTRL, MOD_SHIFT

   InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
   InputHandler.set_keyboard_action(KEY_s, "save_as", modifiers=MOD_CTRL | MOD_SHIFT)

With both bindings above in place:

- Pressing Ctrl+S notifies ``"save"``.
- Pressing Ctrl+Shift+S notifies ``"save_as"`` (the most specific combo wins).
- Pressing S alone notifies nothing, since there is no plain binding for that key.

Gamepads
---------

Gamepad support is built on SDL's "game controller" abstraction
(pygame's ``CONTROLLER*`` events, not the lower-level, per-device
``JOY*`` ones), so button/axis meaning (A, B, the D-pad, the left
stick...) is consistent across controller brands instead of varying
by raw button index per vendor.

Call ``init_gamepads()`` once, at startup (in ``settings.py``,
alongside ``pygame.mixer.init()``/``pygame.font.init()``) — until
then, no gamepad event is ever generated at all, even with a
controller already plugged in:

.. code-block:: python

   from gale.input_handler import InputHandler

   InputHandler.init_gamepads()

Then bind buttons and axes the same way as everything else:

.. code-block:: python

   from gale.input_handler import (
       GAMEPAD_AXIS_LEFT_X,
       GAMEPAD_BUTTON_A,
       GAMEPAD_BUTTON_DPAD_LEFT,
       GAMEPAD_BUTTON_DPAD_RIGHT,
       InputHandler,
   )

   InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_A, "jump")
   InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_DPAD_LEFT, "move_left")
   InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_DPAD_RIGHT, "move_right")
   InputHandler.set_gamepad_axis_action(GAMEPAD_AXIS_LEFT_X, "move_x")

A button behaves like a keyboard key (``input_data.pressed``/``released``);
an axis behaves like mouse motion — bound once, notified continuously
as it moves, with the current position in ``input_data.value``
(``-1.0``–``1.0``, or ``0.0``–``1.0`` for a trigger). Since a resting
stick rarely reports exactly ``0.0``, run it through ``apply_deadzone``
before acting on it:

.. code-block:: python

   from gale.input_handler import apply_deadzone

   def on_input(self, input_id, input_data) -> None:
       if input_id == "move_x":
           self.player.vx = apply_deadzone(input_data.value) * PLAYER_SPEED

Local multiplayer, where each player has their own gamepad, binds the
same button/axis to a different ``action_id`` per player by passing
``gamepad_id`` (every ``GamepadButtonData``/``GamepadAxisData`` carries
which gamepad it came from as ``gamepad_id``, handy for a "press A on
your controller" setup screen that asks each player to identify
theirs):

.. code-block:: python

   InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_A, "p1_jump", gamepad_id=player_1_id)
   InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_A, "p2_jump", gamepad_id=player_2_id)

A binding registered without ``gamepad_id`` (the default) matches
every connected gamepad, unless a more specific one for the same
button/axis also exists for whichever gamepad triggered the event —
the usual choice for a single local player, so it doesn't matter which
port their controller is plugged into.
