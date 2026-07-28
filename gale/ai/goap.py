"""
This file contains support for goal-oriented action planning (GOAP):
GoapAction describes one thing an agent can do (its preconditions, its
effects, and its cost), and plan finds the cheapest sequence of actions
that turns a starting world state into one satisfying a goal. It works
by reusing gale.ai.pathfinding.a_star_to_predicate (an open-goal A*: any
world state satisfying the goal, not one fixed in advance) over the
space of possible world states -- the same idea gale.ai.graph.StateGraph's
docstring already uses for the Towers of Hanoi puzzle, applied here to
states generated on the fly from a list of actions instead of a
pre-built graph.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from .pathfinding import a_star_to_predicate

WorldState = Dict[str, Any]
_FrozenState = FrozenSet[Tuple[str, Any]]


class GoapAction:
    """
    One action an agent can take: applicable when its preconditions
    are a subset of the current world state, and, once taken, applies
    its effects on top of it.

    Usage example:

        chop_wood = GoapAction(
            "chop_wood",
            preconditions={"has_axe": True},
            effects={"has_wood": True},
            cost=2.0,
        )
    """

    def __init__(
        self,
        name: str,
        preconditions: WorldState,
        effects: WorldState,
        cost: float = 1.0,
    ) -> None:
        """
        :param name: Name of this action.
        :param preconditions: Key-value pairs that must already hold in the world state for this action to be applicable.
        :param effects: Key-value pairs this action sets in the world state once taken.
        :param cost: How expensive this action is, all else equal preferring plans with a lower total cost. The default value is 1.0.
        """
        self.name: str = name
        self.preconditions: WorldState = preconditions
        self.effects: WorldState = effects
        self.cost: float = cost

    def is_applicable(self, state: WorldState) -> bool:
        """
        :param state: The world state to check.
        :returns: Whether every one of this action's preconditions holds in state.
        """
        return all(state.get(key) == value for key, value in self.preconditions.items())

    def apply(self, state: WorldState) -> WorldState:
        """
        :param state: The world state to apply this action's effects on top of.
        :returns: A new world state with this action's effects merged in, leaving state unmodified.
        """
        new_state = dict(state)
        new_state.update(self.effects)
        return new_state


def _freeze(state: WorldState) -> _FrozenState:
    return frozenset(state.items())


def _unfreeze(frozen: _FrozenState) -> WorldState:
    return dict(frozen)


def plan(
    world_state: WorldState, goal: WorldState, actions: Sequence[GoapAction]
) -> Optional[List[GoapAction]]:
    """
    Find the cheapest sequence of actions that turns world_state into
    one satisfying every key-value pair in goal.

    :param world_state: The starting world state.
    :param goal: Key-value pairs the final world state must satisfy.
    :param actions: Every action the agent may take.
    :returns: The cheapest list of actions achieving goal from world_state, in order, or None if no combination of actions does.
    """

    def neighbors(
        frozen_state: _FrozenState,
    ) -> Iterable[Tuple[_FrozenState, float]]:
        state = _unfreeze(frozen_state)

        for action in actions:
            if action.is_applicable(state):
                yield _freeze(action.apply(state)), action.cost

    def is_goal(frozen_state: _FrozenState) -> bool:
        state = _unfreeze(frozen_state)
        return all(state.get(key) == value for key, value in goal.items())

    start = _freeze(world_state)
    state_path = a_star_to_predicate(
        start,
        is_goal,
        neighbors,
        heuristic_to_predicate=lambda state: _unsatisfied_count(_unfreeze(state), goal),
    )

    if state_path is None:
        return None

    return _actions_for_state_path(state_path, actions)


def _unsatisfied_count(state: WorldState, goal: WorldState) -> float:
    return sum(1 for key, value in goal.items() if state.get(key) != value)


def _actions_for_state_path(
    state_path: List[_FrozenState], actions: Sequence[GoapAction]
) -> List[GoapAction]:
    result = []

    for frozen_source, frozen_target in zip(state_path, state_path[1:]):
        source = _unfreeze(frozen_source)
        target = _unfreeze(frozen_target)

        for action in actions:
            if action.is_applicable(source) and action.apply(source) == target:
                result.append(action)
                break

    return result
