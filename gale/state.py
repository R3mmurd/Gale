"""
This file contains the implementation of the classes BaseState, StateMachine,
HierarchicalState, and StateStack. These classes are used to create a state
machine that can change between states.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import TypeVar, Tuple, Dict, Any, Optional

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

    def __init__(self, states: Optional[Dict[str, BaseState]] = None) -> None:
        """
        Set the state machine on its initial value.

        :param states: Dictionary of states. Each pair in the dictionary
        have to be the name of the state associated with the generator
        of the state. This could be either the name of the state class
        or a function that instantiates the state. That value should
        receive the instance of the state machine when it is called.
        """
        self.states: Dict[str, BaseState] = states if states is not None else {}

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


class HierarchicalState(BaseState):
    """
    A state that owns a nested StateMachine (its "substate machine").

    A HierarchicalState is a regular state from the point of view of the
    StateMachine (or StateStack) that owns it -- it can be added to a
    'states' dictionary and driven through enter/exit/on_input/update/render
    just like any other BaseState -- but it also behaves as the root of a
    sub-machine: entering it can select a default substate, and its
    on_input/update/render delegate down to whichever substate is currently
    active in that sub-machine.

    This is enough to build a hierarchical state machine (HFSM): a
    "superstate" is simply a HierarchicalState whose substates are BaseState
    (or, recursively, HierarchicalState) instances. Nesting composes for
    free: a substate that is itself a HierarchicalState will delegate down
    to its own substate machine in turn, so arbitrarily deep hierarchies
    require no extra machinery.

    Usage:
    Subclasses that override enter, on_input, update, or render and still
    want the substate machine to be driven MUST call the corresponding
    super().foo(...) method (typically first). Subclasses that do not
    override these methods inherit the delegation directly, so they nest
    correctly with no extra code.

    Example:

        class Walking(BaseState):
            def update(self, dt: float) -> None:
                ...  # move towards the next waypoint

        class LookingAround(BaseState):
            def update(self, dt: float) -> None:
                ...  # rotate in place scanning the surroundings

        class Patrol(HierarchicalState):
            def __init__(self, state_machine: StateMachine) -> None:
                super().__init__(
                    state_machine,
                    substates={"walking": Walking, "looking_around": LookingAround},
                    initial_substate="walking",
                )

            def update(self, dt: float) -> None:
                super().update(dt)
                if self.reached_waypoint():
                    self.change_substate("looking_around")

        guard_fsm = StateMachine({"patrol": Patrol, "alert": Alert})
        guard_fsm.change("patrol")
    """

    def __init__(
        self,
        state_machine: TypeVar("StateMachine"),
        substates: Optional[Dict[str, BaseState]] = None,
        initial_substate: Optional[str] = None,
    ) -> None:
        """
        :param state_machine: The state machine that owns this state.
        :param substates: Dictionary of substates, with the same shape
        accepted by StateMachine's constructor (name -> state class or
        factory function).
        :param initial_substate: Name of the substate to enter automatically
        when this state's enter method runs. If None, no substate is
        selected automatically and the substate machine stays in its empty
        BaseState until change_substate is called explicitly.
        """
        super().__init__(state_machine)
        self.substate_machine: StateMachine = StateMachine(substates)
        self.initial_substate: Optional[str] = initial_substate

    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        """
        Select the initial substate, if one was configured, forwarding any
        received arguments to its enter method.

        :param args and kwargs: Any argument list or keyword arguments
        accepted by the initial substate's enter method.
        """
        if self.initial_substate is not None:
            self.substate_machine.change(self.initial_substate, *args, **kwargs)

    def change_substate(
        self, state_name: str, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> None:
        """
        Change the state of the nested substate machine.

        :param state_name: The name of the substate that will be set.
        :param args and kwargs: Any argument list or keyword arguments
        accepted by the enter method of the new substate.

        :raises KeyError: If state_name is not a key in the substates
        dictionary.
        """
        self.substate_machine.change(state_name, *args, **kwargs)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        Delegate on_input to the current substate of the substate machine.

        :param input_id: The string that describes the input.
        :param input_data: Data associated to the input type.
        """
        self.substate_machine.on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        """
        Delegate update to the current substate of the substate machine.

        :param dt: Time elapsed of the game loop.
        """
        self.substate_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Delegate render to the current substate of the substate machine.

        :param surface: The surface where the state should be rendered on.
        """
        self.substate_machine.render(surface)


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
