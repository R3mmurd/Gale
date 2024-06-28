"""
This file contains the implementation of the classes BaseState, StateMachine,
and StateStack. These classes are used to create a state machine that can
change between states.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import TypeVar, Tuple, Dict, Any

import pygame

from .input_handler import InputData


class BaseState:
    """
    This class represents an empty state. Any state machines
    will start in this state.

    It also is the base for any state. You should extend
    this class to implement any new state class.
    """

    def __init__(self, state_machine: TypeVar("StateMachine")) -> None:
        self.state_machine: TypeVar("StateMachine") = state_machine

    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        """
        Method to be executed when the state machine enters in the state.
        """
        pass

    def exit(self) -> None:
        """
        Method to be executed when the state machine exits from the state.
        """
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass


class StateMachine:
    """
    The state machine.

    Usage:
    States are instantiated when they are set to the attribute 'current'.
    They are passed to the constructor as a dictionary argument containing
    pairs either  (state_name, StateClass) or (state_name, function_to_build_state).

    It is expected that added states contain the methods: enter, exit,
    update, and render. It is recommended creating states by inheriting
    from BaseState in base_state module.

    Example:

        state_machine = StateMachine({
            'start': StartState,
            'play': lambda sm: return PlayState(sm)
        })
        state_machine.change('start')
    """

    def __init__(self, states: Dict[str, BaseState] = {}) -> None:
        """
        Set the state machine on its initial value.

        :param states: Dictionary of states. Each pair in the dictionary
        have to be the name of the state associated with the generator
        of the state. This could be either the name of the state class
        or a function that instantiates the state. That value should
        receive the instance of the state machine when it is called.
        """
        self.states: Dict[str, BaseState] = states

        # The initial state is the empty state
        self.current = BaseState(self)

    def change(
        self, state_name: str, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> None:
        """
        Change the state of the machine.

        :param state_name: The name of the state that will be set.
        *args and **kwargs: Any argument list of keyword arguments that are accepted by the enter method of the new state.

        :raises KeyError: If the arg state_name is not as a key in the states dictionary.
        """
        self.current.exit()
        self.current = self.states[state_name](self)
        self.current.enter(*args, **kwargs)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        Call the method on_input of the current state of the machine.

        :param input_id: The string that describes the input.
        :param input_data: Data associated to the input type.
        """
        self.current.on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        """
        Call to update of the current state of the machine.

        :param dt: Time elapsed of the game loop.
        """
        self.current.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Call to render of the current state of the machine.

        :param surface: The surface where the state should be rendered on.
        """
        self.current.render(surface)


class StateStack:
    """
    Class to stack states. It renders all of then but it only updates the top state.

    Usage:
    The stack is created empty. States are pushed to the stack and popped from it.

    state_stack = StateStack()
    state_stack.push(state1)
    state_stack.push(state2)
    state_stack.pop()
    """

    def __init__(self) -> None:
        """
        Creates an empty stack.
        """
        self.states = []

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        Call the method on_input of the top state of the stack.

        :param input_id: The string that describes the input.
        :param input_data: Data associated to the input type.
        """
        if len(self.states) == 0:
            raise RuntimeError("State stacks is empty")

        self.states[-1].on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        """
        Call to update of the top state of the stack.

        :param dt: Time elapsed of the game loop.
        :raises RuntimeError: If the stack is empty.
        """
        if len(self.states) == 0:
            raise RuntimeError("State stacks is empty")

        self.states[-1].update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Call to render all of the states in the stack.

        :param surface: The surface where the state should be rendered on.
        """
        for state in self.states:
            state.render(surface)

    def clear(self) -> None:
        """
        Clear the stack.
        """
        self.states = []

    def push(
        self, state: BaseState, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> None:
        """
        Add a new state on the top of the stack.

        :param state: The state to be added based on BaseState.
        :*args and **kwargs: Any argument list of keyword arguments that are accepted by the enter method of the new state.
        """
        self.states.append(state)
        state.enter(*args, **kwargs)

    def pop(self) -> None:
        """
        Remove the top state of the stack.

        :raises RuntimeError: If the stack is empty.
        """
        if len(self.states) == 0:
            raise RuntimeError("State stacks is empty")

        self.states[-1].exit()
        self.states.pop()
