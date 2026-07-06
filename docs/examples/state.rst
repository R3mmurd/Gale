`← Back to the main README <../../README.rst>`_

gale.state
===========

This module contains two ways to organize the states of your game (or of
any object in it, such as a character): ``StateMachine``, which holds a
single active state, and ``StateStack``, which stacks states on top of
each other (useful, for instance, to open a pause menu on top of the
gameplay state without destroying it).

StateMachine
------------

.. code-block:: python

   from gale.state import BaseState, StateMachine


   class TitleState(BaseState):
       def enter(self) -> None:
           print("Showing title screen")

       def on_input(self, input_id, input_data) -> None:
           if input_id == "start" and input_data.pressed:
               self.state_machine.change("play")


   class PlayState(BaseState):
       def enter(self, level: int = 1) -> None:
           self.level = level

       def update(self, dt: float) -> None:
           ...


   state_machine = StateMachine({"title": TitleState, "play": PlayState})
   state_machine.change("title")

   # Later on, for instance when the player presses "start":
   state_machine.change("play", level=1)

StateStack
----------

.. code-block:: python

   from gale.state import BaseState, StateStack


   class PlayState(BaseState):
       def render(self, surface) -> None:
           ...


   class PauseState(BaseState):
       def render(self, surface) -> None:
           ...  # draw a translucent overlay on top of PlayState


   state_stack = StateStack()
   play_state = PlayState(state_stack)
   state_stack.push(play_state)

   # Opening the pause menu keeps PlayState in the stack, so it still renders
   # underneath, but only PauseState (the top of the stack) gets updated.
   pause_state = PauseState(state_stack)
   state_stack.push(pause_state)

   # Closing the pause menu.
   state_stack.pop()
