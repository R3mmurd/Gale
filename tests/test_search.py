import math
import unittest

from gale.ai.graph import Graph, NavGraph, StateGraph
from gale.ai.search import (
    a_star,
    breadth_first_search,
    depth_first_search,
    dijkstra,
    path_cost,
)


def build_sample_graph() -> Graph:
    # A -- B -- D
    #  \        |
    #   \       |
    #    ------ C -- E (unreachable from A/B/D/C's component below)
    graph = Graph()
    graph.add_edge("A", "B", 1)
    graph.add_edge("B", "D", 1)
    graph.add_edge("A", "C", 5)
    graph.add_edge("C", "D", 1)
    graph.add_node("E")  # disconnected
    return graph


class UninformedSearchTestCase(unittest.TestCase):
    def test_bfs_finds_shortest_path_in_edges(self) -> None:
        graph = build_sample_graph()
        path = breadth_first_search("A", "D", graph)
        self.assertEqual(path, ["A", "B", "D"])

    def test_dfs_finds_a_path(self) -> None:
        graph = build_sample_graph()
        path = depth_first_search("A", "D", graph)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], "A")
        self.assertEqual(path[-1], "D")

    def test_returns_single_node_path_when_start_is_goal(self) -> None:
        graph = build_sample_graph()
        self.assertEqual(breadth_first_search("A", "A", graph), ["A"])
        self.assertEqual(depth_first_search("A", "A", graph), ["A"])

    def test_returns_none_when_unreachable(self) -> None:
        graph = build_sample_graph()
        self.assertIsNone(breadth_first_search("A", "E", graph))
        self.assertIsNone(depth_first_search("A", "E", graph))

    def test_works_with_a_plain_neighbors_callable(self) -> None:
        graph = build_sample_graph()
        path = breadth_first_search("A", "D", graph.weighted_neighbors)
        self.assertEqual(path, ["A", "B", "D"])


class DijkstraTestCase(unittest.TestCase):
    def test_finds_cheapest_path_not_fewest_edges(self) -> None:
        graph = build_sample_graph()
        # A->B->D costs 2, A->C->D costs 6: Dijkstra must prefer the former
        # even though both paths have 2 edges.
        path = dijkstra("A", "D", graph)
        self.assertEqual(path, ["A", "B", "D"])
        self.assertAlmostEqual(path_cost(graph, path), 2)

    def test_returns_none_when_unreachable(self) -> None:
        graph = build_sample_graph()
        self.assertIsNone(dijkstra("A", "E", graph))

    def test_start_equals_goal(self) -> None:
        graph = build_sample_graph()
        self.assertEqual(dijkstra("A", "A", graph), ["A"])


class AStarTestCase(unittest.TestCase):
    def test_matches_dijkstra_on_nav_graph(self) -> None:
        graph = NavGraph()
        graph.add_edge((0, 0), (1, 0))
        graph.add_edge((1, 0), (2, 0))
        graph.add_edge((0, 0), (0, 2))
        graph.add_edge((0, 2), (2, 0))  # a shortcut that is actually longer

        def heuristic(node, goal):
            return math.hypot(goal[0] - node[0], goal[1] - node[1])

        dijkstra_path = dijkstra((0, 0), (2, 0), graph)
        a_star_path = a_star((0, 0), (2, 0), graph, heuristic)

        self.assertEqual(a_star_path, dijkstra_path)
        self.assertAlmostEqual(
            path_cost(graph, a_star_path), path_cost(graph, dijkstra_path)
        )

    def test_zero_heuristic_still_finds_optimal_path(self) -> None:
        graph = build_sample_graph()
        path = a_star("A", "D", graph, heuristic=lambda node, goal: 0)
        self.assertEqual(path, ["A", "B", "D"])

    def test_returns_none_when_unreachable(self) -> None:
        graph = build_sample_graph()
        path = a_star("A", "E", graph, heuristic=lambda node, goal: 0)
        self.assertIsNone(path)


def hanoi_successors(state):
    """
    state is a tuple of 3 tuples, one per peg, listing disk sizes from
    bottom to top. Yields (next_state, cost=1) for every legal move.
    """
    for source in range(3):
        if not state[source]:
            continue

        disk = state[source][-1]

        for target in range(3):
            if target == source:
                continue

            if state[target] and state[target][-1] < disk:
                continue

            next_state = list(state)
            next_state[source] = state[source][:-1]
            next_state[target] = state[target] + (disk,)
            yield tuple(next_state), 1


class TowersOfHanoiTestCase(unittest.TestCase):
    def test_optimal_solution_has_two_to_the_n_minus_one_moves(self) -> None:
        n = 3
        start = (tuple(range(n, 0, -1)), (), ())
        goal = ((), (), tuple(range(n, 0, -1)))

        graph = StateGraph.expand(start, hanoi_successors)

        # 2**n - 1 moves is the known optimal solution length for n disks.
        self.assertEqual(len(graph.nodes), 3**n)

        bfs_path = breadth_first_search(start, goal, graph)
        dijkstra_path = dijkstra(start, goal, graph)

        self.assertEqual(len(bfs_path) - 1, 2**n - 1)
        self.assertEqual(len(dijkstra_path) - 1, 2**n - 1)

        # Every move in the found path must be a legal transition.
        for source, target in zip(bfs_path, bfs_path[1:]):
            self.assertTrue(graph.has_edge(source, target))
