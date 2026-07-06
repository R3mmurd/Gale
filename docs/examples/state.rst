`← Back to the main README <../../README.rst>`_

gale.state
===========

This module contains two ways to organize the states of your game (or of
any object in it, such as a character): ``StateMachine``, which holds a
single active state, and ``StateStack``, which stacks states on top of
each other (useful, for instance, to open a pause menu on top of the
gameplay state without destroying it). In practice, ``StateMachine`` is
by far the most used of the two: at the game level, to drive its overall
flow (title screen, play, pause, game over, ...), and at the entity
level, to drive a single character's behavior (idle, walk, jump, ...).

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

States are meant to be disposable: ``StateMachine.change`` throws the
previous state away and builds a brand new one every time, so any data a
state needs to keep going has to flow through ``enter(**params)``. A
common pattern is passing a state's *entire* live context forward when
transitioning away from it, so it can be restored unchanged when coming
back, for instance to implement pause/resume:

.. code-block:: python

   class PlayState(BaseState):
       def enter(self, level=1, score=0, lives=3) -> None:
           self.level, self.score, self.lives = level, score, lives

       def on_input(self, input_id, input_data) -> None:
           if input_id == "pause" and input_data.pressed:
               self.state_machine.change(
                   "pause", level=self.level, score=self.score, lives=self.lives
               )


   class PauseState(BaseState):
       def enter(self, **play_state_params) -> None:
           self.play_state_params = play_state_params

       def on_input(self, input_id, input_data) -> None:
           if input_id == "pause" and input_data.pressed:
               self.state_machine.change("play", **self.play_state_params)

When a state needs a dependency other than the state machine itself
(the owning ``Game`` instance, or the entity a state belongs to), pass a
lambda instead of the class directly, and override ``__init__`` to accept
the extra argument:

.. code-block:: python

   class StartState(BaseState):
       def __init__(self, state_machine: StateMachine, game) -> None:
           super().__init__(state_machine)
           self.game = game


   state_machine = StateMachine({
       "start": lambda sm: StartState(sm, game=my_game),
       "play": PlayState,
   })

The same trick is handy to give every character of a given type its own
``StateMachine`` built from a shared dictionary of state classes:

.. code-block:: python

   class Creature:
       def __init__(self, states: dict) -> None:
           self.state_machine = StateMachine(
               {name: (lambda sm, cls=cls: cls(self, sm)) for name, cls in states.items()}
           )
           self.state_machine.change("walk")

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
