"""
This file contains the implementation of the class StateMachine.

Author: Alejandro Mujica (aledrums@gmail.com)
Date: 07/11/2020

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
from typing import TypeVar, Tuple, Dict, Any

import pygame


class BaseState:
    """
    This class represents an empty state. Any state machines
    will start in this state.

    It also is the base for any state. You should extend
    this class to implement any new state class.
    """

    def __init__(self, state_machine: TypeVar('StateMachine')) -> None:
        self.state_machine: TypeVar('StateMachine') = state_machine

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

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass


class StateMachine:
    """
    The state machine.
    """

    def __init__(self, states: Dict[str, BaseState] = {}) -> None:
        """
        Set the state machine on its initial value.

        Args:
            :param states: Dictionary of states. Each pair in the dictionary
            have to be the name of the state associated with the generator
            of the state. This could be either the name of the state class
            or a function that instantiates the state. That value should
            receive the instance of the state machine when it is called.
        """
        self.states: Dict[str, BaseState] = states

        # The initial state is the empty state
        self.current = BaseState(self)

    def change(self, state_name: str, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        """
        Change the state of the machine.

        Args:
            :param state_name: The name of the state that
            will be set.
            *args and **kwargs: Any argument list of keyword arguments
            that are accepted by the enter method of the new state.

        Raises:
            ValueError: If the arg state_name is not as a key in
            the states dictionary.
        """
        self.current.exit()
        self.current = self.states[state_name](self)
        self.current.enter(*args, **kwargs)

    def update(self, dt: float) -> None:
        """
        Call to update of the current state of the machine.

        Args:
            :param dt: Time elapsed of the game loop.
        """
        self.current.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Call to render of the current state of the machine.

        Args:
            :param surface: The surface where the state should be rendered on.
        """
        self.current.render(surface)
