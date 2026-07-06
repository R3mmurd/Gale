"""
This file contains a generic, reusable graph implementation, along with
specialized graphs built on top of it: NavGraph for navigation
(waypoints/positions), DependencyGraph for prerequisite/build-order
relationships, and StateGraph for state-space problems, such as every
reachable configuration of the Towers of Hanoi puzzle. They are meant to
be paired with the search algorithms in gale.ai.search.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math

from collections import deque
from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

T = TypeVar("T")


class CycleError(Exception):
    """
    Raised when an operation that requires an acyclic graph, such as
    DependencyGraph.topological_sort, finds a cycle.
    """

    pass


class Graph(Generic[T]):
    """
    A generic graph of hashable nodes connected by weighted edges. It
    can be directed or undirected, and is meant to be generic and
    reusable enough to serve as the base for more specific graphs, such
    as NavGraph, DependencyGraph, or StateGraph, as well as to be
    searched directly with the functions in gale.ai.search.
    """

    def __init__(self, directed: bool = False) -> None:
        """
        :param directed: Whether edges are one-way. The default value is False, so every edge added is also added in the opposite direction.
        """
        self.directed: bool = directed
        self._adjacency: Dict[T, Dict[T, float]] = {}

    @property
    def nodes(self) -> Iterable[T]:
        """
        :returns: Every node currently in the graph.
        """
        return self._adjacency.keys()

    @property
    def edges(self) -> Iterator[Tuple[T, T, float]]:
        """
        :returns: Every edge currently in the graph as (source, target, weight) tuples. Each edge of an undirected graph is yielded only once.
        """
        seen = set()

        for source, neighbors in self._adjacency.items():
            for target, weight in neighbors.items():
                if not self.directed and (target, source) in seen:
                    continue

                seen.add((source, target))
                yield source, target, weight

    def add_node(self, node: T) -> None:
        """
        Add a node to the graph. Does nothing if it is already present.

        :param node: The node to add.
        """
        self._adjacency.setdefault(node, {})

    def has_node(self, node: T) -> bool:
        """
        :param node: The node to look for.
        :returns: Whether the node is present in the graph.
        """
        return node in self._adjacency

    def remove_node(self, node: T) -> None:
        """
        Remove a node and every edge connected to it.

        :param node: The node to remove.
        :raises KeyError: If the node is not present in the graph.
        """
        del self._adjacency[node]

        for neighbors in self._adjacency.values():
            neighbors.pop(node, None)

    def add_edge(self, source: T, target: T, weight: float = 1.0) -> None:
        """
        Add an edge between source and target, creating either node
        that is not already present. If the graph is undirected, the
        edge is also added from target to source.

        :param source: The origin node.
        :param target: The destination node.
        :param weight: The cost of traversing the edge. The default value is 1.0.
        """
        self.add_node(source)
        self.add_node(target)
        self._adjacency[source][target] = weight

        if not self.directed:
            self._adjacency[target][source] = weight

    def has_edge(self, source: T, target: T) -> bool:
        """
        :param source: The origin node.
        :param target: The destination node.
        :returns: Whether there is an edge from source to target.
        """
        return source in self._adjacency and target in self._adjacency[source]

    def remove_edge(self, source: T, target: T) -> None:
        """
        Remove the edge from source to target (and from target to
        source, if the graph is undirected).

        :param source: The origin node.
        :param target: The destination node.
        :raises KeyError: If there is no such edge.
        """
        del self._adjacency[source][target]

        if not self.directed:
            del self._adjacency[target][source]

    def get_weight(self, source: T, target: T) -> float:
        """
        :param source: The origin node.
        :param target: The destination node.
        :returns: The weight of the edge from source to target.
        :raises KeyError: If there is no such edge.
        """
        return self._adjacency[source][target]

    def neighbors(self, node: T) -> Iterable[T]:
        """
        :param node: The node to get the neighbors of.
        :returns: The nodes directly reachable from node.
        :raises KeyError: If the node is not present in the graph.
        """
        return self._adjacency[node].keys()

    def weighted_neighbors(self, node: T) -> Iterable[Tuple[T, float]]:
        """
        :param node: The node to get the neighbors of.
        :returns: Pairs (neighbor, weight) directly reachable from node. This is the shape expected by the search functions in gale.ai.search.
        :raises KeyError: If the node is not present in the graph.
        """
        return self._adjacency[node].items()

    def __contains__(self, node: T) -> bool:
        return self.has_node(node)

    def __len__(self) -> int:
        return len(self._adjacency)


def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


class NavGraph(Graph[Tuple[float, float]]):
    """
    A graph specialized for navigation, where nodes are 2D positions,
    such as waypoints or the centers of a navigation mesh's polygons.
    The weight of an edge defaults to the euclidean distance between
    the two positions it connects, since that is normally what you want
    to minimize when pathfinding, but it can still be overridden
    explicitly, for instance to penalize hazardous terrain.
    """

    def add_edge(
        self,
        source: Tuple[float, float],
        target: Tuple[float, float],
        weight: Optional[float] = None,
    ) -> None:
        """
        :param source: The origin position.
        :param target: The destination position.
        :param weight: The cost of traversing the edge. The default value is the euclidean distance between source and target.
        """
        super().add_edge(
            source, target, _distance(source, target) if weight is None else weight
        )


class DependencyGraph(Graph[T]):
    """
    A directed graph to express prerequisite/build-order relationships,
    such as a skill tree, a quest chain, or a build pipeline.
    """

    def __init__(self) -> None:
        super().__init__(directed=True)

    def add_dependency(self, item: T, depends_on: T) -> None:
        """
        Declare that item requires depends_on to happen/exist first.

        :param item: The dependent item.
        :param depends_on: The item that must come before it.
        """
        self.add_edge(depends_on, item)

    def topological_sort(self) -> List[T]:
        """
        :returns: The nodes ordered so that every node comes after all of the items it depends on.
        :raises CycleError: If the graph has a cycle, since no valid order exists in that case.
        """
        in_degree = {node: 0 for node in self.nodes}

        for node in self.nodes:
            for neighbor in self.neighbors(node):
                in_degree[neighbor] += 1

        queue = deque(node for node, degree in in_degree.items() if degree == 0)
        order: List[T] = []

        while queue:
            node = queue.popleft()
            order.append(node)

            for neighbor in self.neighbors(node):
                in_degree[neighbor] -= 1

                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(in_degree):
            raise CycleError("DependencyGraph has at least one cycle")

        return order

    def has_cycle(self) -> bool:
        """
        :returns: Whether the graph has at least one cycle.
        """
        try:
            self.topological_sort()
        except CycleError:
            return True

        return False


class StateGraph(Graph[T]):
    """
    A directed graph representing a state space: nodes are problem
    states and edges are the transitions (actions/moves) between them,
    such as every reachable configuration of the Towers of Hanoi puzzle
    and the moves connecting them.

    Building the full state space by hand does not scale, so use expand
    to generate it automatically from a starting state and a function
    that yields the valid transitions out of any given state.
    """

    def __init__(self) -> None:
        super().__init__(directed=True)

    @classmethod
    def expand(
        cls,
        start: T,
        successors: Callable[[T], Iterable[Tuple[T, float]]],
    ) -> "StateGraph[T]":
        """
        Build the full graph of states reachable from start.

        :param start: The initial state.
        :param successors: Callable that, given a state, returns an iterable of (next_state, cost) pairs, one for every valid transition out of it.
        :returns: A StateGraph with every state reachable from start and the transitions between them.
        """
        graph: "StateGraph[T]" = cls()
        graph.add_node(start)
        pending = deque([start])

        while pending:
            state = pending.popleft()

            for next_state, cost in successors(state):
                is_new = not graph.has_node(next_state)
                graph.add_edge(state, next_state, cost)

                if is_new:
                    pending.append(next_state)

        return graph
