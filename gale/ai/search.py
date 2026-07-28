"""
This file contains generic graph search algorithms: depth-first search,
breadth-first search, and the shortest-path algorithms Dijkstra and A*.
They all work over any graph-like object exposing weighted neighbors,
such as a gale.ai.graph.Graph (or one of its subclasses) or a plain
callable, so they are not tied to any single graph representation.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import heapq

from collections import deque
from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from .graph import Graph

T = TypeVar("T")

NeighborsFn = Callable[[T], Iterable[Tuple[T, float]]]
GraphLike = Union[Graph, NeighborsFn]


def _resolve_neighbors_fn(graph_or_neighbors_fn: GraphLike) -> NeighborsFn:
    if isinstance(graph_or_neighbors_fn, Graph):
        return graph_or_neighbors_fn.weighted_neighbors

    return graph_or_neighbors_fn


def _reconstruct_path(came_from: Dict[T, T], start: T, goal: T) -> List[T]:
    path = [goal]

    while path[-1] != start:
        path.append(came_from[path[-1]])

    path.reverse()
    return path


def path_cost(graph_or_neighbors_fn: GraphLike, path: List[T]) -> float:
    """
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, to get edge weights from.
    :param path: A sequence of nodes, as returned by any of the search functions in this module.
    :returns: The total weight of traversing path in order.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)
    total = 0.0

    for source, target in zip(path, path[1:]):
        total += next(
            weight for neighbor, weight in neighbors_fn(source) if neighbor == target
        )

    return total


def depth_first_search(
    start: T, goal: T, graph_or_neighbors_fn: GraphLike
) -> Optional[List[T]]:
    """
    Find a path between start and goal using an iterative depth-first
    search. It does not consider edge weights, and, unlike
    breadth_first_search, the path it finds is not guaranteed to be the
    shortest one.

    :param start: The node to start the search from.
    :param goal: The node to reach.
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, describing the graph to search.
    :returns: The list of nodes from start to goal (both included), or None if goal is unreachable from start.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)

    if start == goal:
        return [start]

    visited = {start}
    came_from: Dict[T, T] = {}
    stack = [start]

    while stack:
        node = stack.pop()

        for neighbor, _ in neighbors_fn(node):
            if neighbor in visited:
                continue

            visited.add(neighbor)
            came_from[neighbor] = node

            if neighbor == goal:
                return _reconstruct_path(came_from, start, goal)

            stack.append(neighbor)

    return None


def breadth_first_search(
    start: T, goal: T, graph_or_neighbors_fn: GraphLike
) -> Optional[List[T]]:
    """
    Find the shortest path (in number of edges, ignoring weights)
    between start and goal using an iterative breadth-first search.

    :param start: The node to start the search from.
    :param goal: The node to reach.
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, describing the graph to search.
    :returns: The shortest list of nodes from start to goal (both included), or None if goal is unreachable from start.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)

    if start == goal:
        return [start]

    visited = {start}
    came_from: Dict[T, T] = {}
    queue = deque([start])

    while queue:
        node = queue.popleft()

        for neighbor, _ in neighbors_fn(node):
            if neighbor in visited:
                continue

            visited.add(neighbor)
            came_from[neighbor] = node

            if neighbor == goal:
                return _reconstruct_path(came_from, start, goal)

            queue.append(neighbor)

    return None


def _best_first_search_steps(
    start: T,
    is_goal: Callable[[T], bool],
    neighbors_fn: NeighborsFn,
    heuristic: Callable[[T], float],
) -> Iterator[Optional[List[T]]]:
    """
    Generator core shared by _uniform_cost_search (behind dijkstra and
    a_star) and the incremental/open-goal searches in
    gale.ai.pathfinding: explores nodes ordered by cost-so-far plus
    heuristic(node), yielding None after every node expansion so a
    caller can advance it a limited number of steps at a time, then
    finally yielding the found path, or None if the goal is
    unreachable, as its last value.

    :param start: The node to start the search from.
    :param is_goal: Callable returning whether a node is an acceptable goal.
    :param neighbors_fn: Callable node -> iterable of (neighbor, weight) pairs. Weights must not be negative.
    :param heuristic: Callable node -> estimated cost to reach the goal from it. Must not overestimate the real cost for the found path to be guaranteed optimal.
    """
    if is_goal(start):
        yield [start]
        return

    costs: Dict[T, float] = {start: 0.0}
    came_from: Dict[T, T] = {}
    visited = set()
    # The counter breaks ties between equal-priority entries so the
    # heap never needs to compare two nodes directly against each other.
    counter = 1
    queue: List[Tuple[float, int, T]] = [(heuristic(start), 0, start)]

    while queue:
        _, _, node = heapq.heappop(queue)

        if node in visited:
            yield None
            continue

        visited.add(node)

        if is_goal(node):
            yield _reconstruct_path(came_from, start, node)
            return

        for neighbor, weight in neighbors_fn(node):
            new_cost = costs[node] + weight

            if new_cost < costs.get(neighbor, float("inf")):
                costs[neighbor] = new_cost
                came_from[neighbor] = node
                priority = new_cost + heuristic(neighbor)
                heapq.heappush(queue, (priority, counter, neighbor))
                counter += 1

        yield None

    yield None


def _uniform_cost_search(
    start: T, goal: T, neighbors_fn: NeighborsFn, heuristic: Callable[[T, T], float]
) -> Optional[List[T]]:
    """
    Shared implementation behind dijkstra and a_star: both explore
    nodes ordered by cost-so-far plus heuristic(node, goal), which
    degenerates to plain Dijkstra when heuristic always returns 0. Runs
    _best_first_search_steps to completion in one call.
    """
    result = None

    for result in _best_first_search_steps(
        start,
        lambda node: node == goal,
        neighbors_fn,
        lambda node: heuristic(node, goal),
    ):
        pass

    return result


def dijkstra(start: T, goal: T, graph_or_neighbors_fn: GraphLike) -> Optional[List[T]]:
    """
    Find the cheapest path (by total edge weight) between start and
    goal using Dijkstra's algorithm.

    :param start: The node to start the search from.
    :param goal: The node to reach.
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, describing the graph to search. Weights must not be negative.
    :returns: The cheapest list of nodes from start to goal (both included), or None if goal is unreachable from start.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)
    return _uniform_cost_search(
        start, goal, neighbors_fn, heuristic=lambda node, goal: 0.0
    )


def a_star(
    start: T,
    goal: T,
    graph_or_neighbors_fn: GraphLike,
    heuristic: Callable[[T, T], float],
) -> Optional[List[T]]:
    """
    Find the cheapest path (by total edge weight) between start and
    goal using the A* algorithm, which uses heuristic to focus the
    search towards goal instead of expanding outward evenly like
    dijkstra does.

    :param start: The node to start the search from.
    :param goal: The node to reach.
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, describing the graph to search. Weights must not be negative.
    :param heuristic: Callable (node, goal) -> estimated cost to reach goal from node. For the found path to be guaranteed optimal, it must not overestimate the real cost, for instance euclidean distance when weights are also distances (an admissible heuristic).
    :returns: The cheapest list of nodes from start to goal (both included), or None if goal is unreachable from start.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)
    return _uniform_cost_search(start, goal, neighbors_fn, heuristic)
