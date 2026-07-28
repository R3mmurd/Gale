"""
This file contains support for Markov-process-driven behavior:
MarkovChain (a weighted-random transition table) and MarkovState (a
gale.sequence.Step -- the same lifecycle already used by gale.quest and
gale.cutscene) tied together by MarkovStateMachine, which picks its
next state probabilistically through the chain whenever the current
one completes. Useful to vary a character's idle/patrol behavior
without scripting a fixed sequence, while still reusing the same
enter/update/is_complete lifecycle as the rest of gale.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import random

from typing import Any, Dict, Generic, Hashable, List, Tuple, TypeVar

from ..sequence import Step

T = TypeVar("T", bound=Hashable)


class MarkovChain(Generic[T]):
    """
    A weighted-random transition table between states: add_transition
    records how likely one state is to lead to another, and next_state
    samples a next state according to those weights.

    Usage example:

        chain = MarkovChain()
        chain.add_transition("idle", "patrol", 0.7)
        chain.add_transition("idle", "investigate", 0.3)
        chain.next_state("idle")  # "patrol" about 70% of the time
    """

    def __init__(self) -> None:
        self._transitions: Dict[T, List[Tuple[T, float]]] = {}

    def add_transition(self, state: T, next_state: T, weight: float) -> None:
        """
        :param state: The state this transition starts from.
        :param next_state: The state this transition leads to.
        :param weight: Relative likelihood of this transition being chosen, among every transition added for state. Weights don't need to add up to 1; they're normalized when sampled.
        """
        self._transitions.setdefault(state, []).append((next_state, weight))

    def next_state(self, state: T) -> T:
        """
        :param state: The state to sample a transition from.
        :returns: A next state chosen among state's transitions, weighted by the weight each was added with.
        :raises KeyError: If state has no transitions added.
        """
        transitions = self._transitions[state]
        states, weights = zip(*transitions)
        return random.choices(states, weights=weights, k=1)[0]


class MarkovState(Step):
    """
    A single named state of a MarkovStateMachine: a gale.sequence.Step
    (so it gets enter/update/is_complete, and can complete after a
    fixed duration or on a specific input for free) that also does
    whatever per-frame work it needs via update/render, exactly like
    any other Step.
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """
        :param name: This state's name, matching how it's referred to in the MarkovChain passed to MarkovStateMachine.
        :param kwargs: Forwarded to Step (duration, advance_on_input).
        """
        super().__init__(**kwargs)
        self.name: str = name


class MarkovStateMachine:
    """
    Drives a set of MarkovState objects, picking the next one
    probabilistically (via a MarkovChain over their names) whenever the
    current one's is_complete() turns True -- the same "run the active
    one until it's done" idea as gale.sequence.Sequence, except the
    next step is chosen randomly instead of following a fixed order.

    Usage example:

        chain = MarkovChain()
        chain.add_transition("idle", "patrol", 0.7)
        chain.add_transition("idle", "investigate", 0.3)
        chain.add_transition("patrol", "idle", 1.0)
        chain.add_transition("investigate", "idle", 1.0)

        machine = MarkovStateMachine(
            chain,
            {
                "idle": IdleState("idle", duration=2.0),
                "patrol": PatrolState("patrol", duration=5.0),
                "investigate": InvestigateState("investigate", duration=3.0),
            },
            start="idle",
        )

        # In the game loop:
        machine.update(dt)
    """

    def __init__(
        self,
        chain: MarkovChain,
        states: Dict[str, MarkovState],
        start: str,
    ) -> None:
        """
        :param chain: The transition probabilities between state names.
        :param states: Every state this machine can be in, by name.
        :param start: Name of the state to begin in.
        """
        self.chain: MarkovChain = chain
        self.states: Dict[str, MarkovState] = states
        self.current: MarkovState = states[start]
        self.current.enter()

    def update(self, dt: float) -> None:
        """
        :param dt: Time elapsed (in seconds) since the last update.
        """
        self.current._tick(dt)

        if self.current.is_complete():
            self.current.exit()
            next_name = self.chain.next_state(self.current.name)
            self.current = self.states[next_name]
            self.current.enter()

    def render(self, surface: Any) -> None:
        """
        :param surface: The surface to draw on.
        """
        self.current.render(surface)
