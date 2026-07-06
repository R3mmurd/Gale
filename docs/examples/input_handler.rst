`← Back to the main README <../../README.rst>`_

gale.input_handler
===================

``InputHandler`` is a small observer-pattern-based dispatcher: you bind
keyboard keys, mouse buttons, the mouse wheel, or mouse motion to an
``action_id``, and every object that implements ``InputListener`` and is
registered gets notified through ``on_input`` whenever that action fires.

Basic usage
-----------

.. code-block:: python

   from gale.input_handler import InputData, InputHandler, InputListener, KEY_ESCAPE, KEY_SPACE


   class Player(InputListener):
       def __init__(self) -> None:
           InputHandler.register_listener(self)

       def on_input(self, input_id: str, input_data: InputData) -> None:
           if input_id == "jump" and input_data.pressed:
               self.jump()

       def jump(self) -> None:
           ...


   InputHandler.set_keyboard_action(KEY_ESCAPE, "quit")
   InputHandler.set_keyboard_action(KEY_SPACE, "jump")

   player = Player()

The ``Game`` base class (see ``gale.game``) already calls
``InputHandler.handle_input`` for every relevant pygame event on each
frame of its game loop, so in practice you only need to register
listeners and set bindings.

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
