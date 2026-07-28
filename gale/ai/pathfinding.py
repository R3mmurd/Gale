"""
This file contains pathfinding support that builds on the primitives
in gale.ai.search instead of replacing them: incremental_a_star and
a_star_to_predicate are generator/open-goal variants of a_star,
PathfindingRequest/PlannerPool let an incremental search be advanced a
few steps at a time so its cost is spread across several frames
instead of spiking on one, and HierarchicalGraph groups a graph's nodes
into clusters to pathfind over an auto-derived abstract graph first,
then refine within each cluster -- much cheaper than a flat search over
a very large graph.

Re-planning when a graph changes needs no dedicated support here: since
gale.ai.graph.Graph is a plain mutable object, the usual pattern is to
just call a_star/incremental_a_star again (checking first, e.g., that
every edge along the current path still exists) whenever the graph
changes in a way that might affect a path already in use.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

from .graph import Graph
from .search import (
    GraphLike,
    NeighborsFn,
    _best_first_search_steps,
    _resolve_neighbors_fn,
)
from .search import dijkstra as _dijkstra

T = TypeVar("T")


def incremental_a_star(
    start: T,
    goal: T,
    graph_or_neighbors_fn: GraphLike,
    heuristic: Callable[[T, T], float],
) -> Iterator[Optional[List[T]]]:
    """
    Like gale.ai.search.a_star, but as a generator that yields None
    after expanding each node instead of running to completion in one
    call -- advance it a limited number of steps per frame (see
    PathfindingRequest/PlannerPool) to spread a search's cost over
    several frames instead of spiking on the one that requested it.

    :param start: The node to start the search from.
    :param goal: The node to reach.
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, describing the graph to search. Weights must not be negative.
    :param heuristic: Callable (node, goal) -> estimated cost to reach goal from node. Must not overestimate the real cost for the found path to be guaranteed optimal.
    :yields: None after every node expansion, then the cheapest list of nodes from start to goal (both included), or None if goal is unreachable, once the search is done.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)
    yield from _best_first_search_steps(
        start,
        lambda node: node == goal,
        neighbors_fn,
        lambda node: heuristic(node, goal),
    )


def a_star_to_predicate(
    start: T,
    goal_predicate: Callable[[T], bool],
    graph_or_neighbors_fn: GraphLike,
    heuristic_to_predicate: Callable[[T], float],
) -> Optional[List[T]]:
    """
    An "open goal" variant of gale.ai.search.a_star: instead of a
    single fixed goal node, any node satisfying goal_predicate is a
    valid destination -- for instance, the nearest node tagged as
    cover, whichever one that turns out to be, rather than one decided
    in advance.

    :param start: The node to start the search from.
    :param goal_predicate: Callable returning whether a node is an acceptable goal.
    :param graph_or_neighbors_fn: A Graph, or a callable node -> iterable of (neighbor, weight) pairs, describing the graph to search. Weights must not be negative.
    :param heuristic_to_predicate: Callable (node) -> estimated cost to reach the nearest node satisfying goal_predicate from node. Must not overestimate the real cost for the found path to be guaranteed optimal.
    :returns: The cheapest list of nodes from start to some node satisfying goal_predicate (both included), or None if no such node is reachable.
    """
    neighbors_fn = _resolve_neighbors_fn(graph_or_neighbors_fn)
    result = None

    for result in _best_first_search_steps(
        start, goal_predicate, neighbors_fn, heuristic_to_predicate
    ):
        pass

    return result


class PathfindingRequest:
    """
    Wraps an incremental search (see incremental_a_star) so it can be
    advanced a limited number of steps at a time instead of run to
    completion in one call.

    Usage example:

        request = PathfindingRequest(incremental_a_star(start, goal, graph, heuristic))
        # Each frame:
        if request.step(max_iterations=20):
            path = request.result  # None if unreachable
    """

    def __init__(self, search: Iterator[Optional[List[T]]]) -> None:
        """
        :param search: A generator such as one returned by incremental_a_star.
        """
        self._search: Iterator[Optional[List[T]]] = search
        self.done: bool = False
        self.result: Optional[List[T]] = None

    def step(self, max_iterations: int = 1) -> bool:
        """
        Advance the underlying search by up to max_iterations node
        expansions.

        :param max_iterations: Maximum number of expansions to perform in this call.
        :returns: Whether the search finished (successfully or not) during this call. Once True, self.result holds the outcome and further calls do nothing.
        """
        if self.done:
            return True

        for _ in range(max_iterations):
            try:
                path = next(self._search)
            except StopIteration:
                self.done = True
                return True

            if path is not None:
                self.result = path
                self.done = True
                return True

        return False


class PlannerPool:
    """
    Manages several concurrent PathfindingRequest objects, sharing a
    fixed per-update iteration budget round-robin across whichever are
    still pending -- so having many outstanding pathfinding requests at
    once costs a predictable amount of work per frame instead of
    spiking however many of them happen to be expensive that frame.

    Usage example:

        pool = PlannerPool(iterations_per_update=100)
        request = pool.request(incremental_a_star(start, goal, graph, heuristic))
        # Each frame:
        pool.update()
        if request.done:
            path = request.result
    """

    def __init__(self, iterations_per_update: int = 100) -> None:
        """
        :param iterations_per_update: Total node expansions to distribute across pending requests on each update() call.
        """
        self.iterations_per_update: int = iterations_per_update
        self._pending: List[PathfindingRequest] = []

    def request(self, search: Iterator[Optional[List[T]]]) -> PathfindingRequest:
        """
        :param search: A generator such as one returned by incremental_a_star.
        :returns: A PathfindingRequest tracking this search, already queued for the next update().
        """
        pathfinding_request = PathfindingRequest(search)
        self._pending.append(pathfinding_request)
        return pathfinding_request

    def update(self) -> None:
        """
        Distribute this update's iteration budget round-robin across
        every pending request, dropping each one from the pool as soon
        as it finishes.
        """
        if not self._pending:
            return

        share = max(1, self.iterations_per_update // len(self._pending))
        still_pending = []

        for pathfinding_request in self._pending:
            if not pathfinding_request.step(share):
                still_pending.append(pathfinding_request)

        self._pending = still_pending


class HierarchicalGraph:
    """
    A two-level view over a Graph: nodes are grouped into clusters, and
    an abstract graph is automatically derived with one node per
    cluster "entrance" (a node with at least one neighbor outside its
    own cluster) and edges weighted by the shortest intra-cluster path
    between entrances of the same cluster, plus the original inter-
    cluster edges. find_path searches the (much smaller) abstract graph
    first, then refines each abstract edge into the real path segment
    within its cluster -- cheaper than a flat search over a very large
    graph, at the cost of a possibly slightly longer path.
    """

    def __init__(self, graph: Graph, clusters: Dict[T, int]) -> None:
        """
        :param graph: The fine-grained graph to build a hierarchical view over.
        :param clusters: Mapping from every node in graph to the id of the cluster it belongs to.
        """
        self.graph: Graph = graph
        self.clusters: Dict[T, int] = clusters
        self.abstract_graph: Graph[T] = Graph(directed=True)
        self._entrances_by_cluster: Dict[int, List[T]] = {}
        self._build()

    def _build(self) -> None:
        entrances = [
            node
            for node in self.graph.nodes
            if any(
                self.clusters[neighbor] != self.clusters[node]
                for neighbor in self.graph.neighbors(node)
            )
        ]

        for node in entrances:
            self.abstract_graph.add_node(node)
            self._entrances_by_cluster.setdefault(self.clusters[node], []).append(node)

        for source, target, weight in self.graph.edges:
            if source in self.abstract_graph and target in self.abstract_graph:
                if self.clusters[source] != self.clusters[target]:
                    self.abstract_graph.add_edge(source, target, weight)
                    self.abstract_graph.add_edge(target, source, weight)

        for cluster_entrances in self._entrances_by_cluster.values():
            for i, source in enumerate(cluster_entrances):
                for target in cluster_entrances[i + 1 :]:
                    path = _dijkstra(
                        source,
                        target,
                        self._intra_cluster_neighbors(self.clusters[source]),
                    )

                    if path is not None:
                        weight = _path_weight(self.graph, path)
                        self.abstract_graph.add_edge(source, target, weight)

    def _intra_cluster_neighbors(self, cluster: int) -> NeighborsFn:
        def neighbors(node: T) -> Iterable[Tuple[T, float]]:
            return [
                (neighbor, weight)
                for neighbor, weight in self.graph.weighted_neighbors(node)
                if self.clusters.get(neighbor) == cluster
            ]

        return neighbors

    def find_path(
        self, start: T, goal: T, heuristic: Callable[[T, T], float]
    ) -> Optional[List[T]]:
        """
        :param start: The node to start the search from.
        :param goal: The node to reach.
        :param heuristic: Callable (node, goal) -> estimated cost, used both on the abstract graph and to refine each segment within a cluster.
        :returns: The full path from start to goal, refined down to the fine-grained graph, or None if goal is unreachable.
        """
        from .search import a_star as _a_star

        start_cluster = self.clusters[start]
        goal_cluster = self.clusters[goal]

        if start_cluster == goal_cluster:
            return _a_star(
                start, goal, self._intra_cluster_neighbors(start_cluster), heuristic
            )

        start_entrances = self._entrances_by_cluster.get(start_cluster, [])
        goal_entrances = self._entrances_by_cluster.get(goal_cluster, [])

        best_path: Optional[List[T]] = None
        best_cost = float("inf")

        for start_entrance in start_entrances:
            to_entrance = _a_star(
                start,
                start_entrance,
                self._intra_cluster_neighbors(start_cluster),
                heuristic,
            )

            if to_entrance is None:
                continue

            for goal_entrance in goal_entrances:
                abstract_path = _a_star(
                    start_entrance, goal_entrance, self.abstract_graph, heuristic
                )

                if abstract_path is None:
                    continue

                from_entrance = _a_star(
                    goal_entrance,
                    goal,
                    self._intra_cluster_neighbors(goal_cluster),
                    heuristic,
                )

                if from_entrance is None:
                    continue

                full_path = _stitch_paths(
                    self, to_entrance, abstract_path, from_entrance
                )
                cost = _path_weight(self.graph, full_path)

                if cost < best_cost:
                    best_cost = cost
                    best_path = full_path

        return best_path


def _path_weight(graph: Graph, path: Sequence[T]) -> float:
    total = 0.0

    for source, target in zip(path, path[1:]):
        total += graph.get_weight(source, target)

    return total


def _stitch_paths(
    hierarchical_graph: "HierarchicalGraph",
    to_entrance: List[T],
    abstract_path: List[T],
    from_entrance: List[T],
) -> List[T]:
    full_path = list(to_entrance)

    for i in range(len(abstract_path) - 1):
        source, target = abstract_path[i], abstract_path[i + 1]

        if hierarchical_graph.abstract_graph.has_edge(source, target):
            cluster = hierarchical_graph.clusters[source]

            if hierarchical_graph.clusters.get(target) == cluster:
                from .search import a_star as _a_star

                segment = _a_star(
                    source,
                    target,
                    hierarchical_graph._intra_cluster_neighbors(cluster),
                    lambda a, b: 0.0,
                )
                full_path.extend(segment[1:])
                continue

        full_path.append(target)

    full_path.extend(from_entrance[1:])
    return full_path
