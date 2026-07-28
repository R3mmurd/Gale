import math
import unittest

from gale.ai.graph import Graph, NavGraph
from gale.ai.pathfinding import (
    HierarchicalGraph,
    PathfindingRequest,
    PlannerPool,
    a_star_to_predicate,
    incremental_a_star,
)


def _zero_heuristic(a, b):
    return 0.0


class IncrementalAStarTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        self.graph.add_edge("a", "b", 1)
        self.graph.add_edge("b", "c", 1)
        self.graph.add_edge("a", "c", 10)

    def test_yields_none_then_the_path(self) -> None:
        search = incremental_a_star("a", "c", self.graph, _zero_heuristic)
        steps = list(search)
        self.assertTrue(all(step is None for step in steps[:-1]))
        self.assertEqual(steps[-1], ["a", "b", "c"])

    def test_matches_a_star_result(self) -> None:
        from gale.ai.search import a_star

        search = incremental_a_star("a", "c", self.graph, _zero_heuristic)
        *_, incremental_result = search
        eager_result = a_star("a", "c", self.graph, _zero_heuristic)
        self.assertEqual(incremental_result, eager_result)

    def test_yields_none_for_unreachable_goal(self) -> None:
        self.graph.add_node("isolated")
        search = incremental_a_star("a", "isolated", self.graph, _zero_heuristic)
        self.assertIsNone(list(search)[-1])


class AStarToPredicateTestCase(unittest.TestCase):
    def test_finds_the_nearest_node_satisfying_the_predicate(self) -> None:
        graph = Graph()
        graph.add_edge("start", "a", 1)
        graph.add_edge("a", "cover_1", 1)
        graph.add_edge("start", "cover_2", 5)
        path = a_star_to_predicate(
            "start",
            lambda node: node.startswith("cover"),
            graph,
            lambda node: 0.0,
        )
        self.assertEqual(path, ["start", "a", "cover_1"])

    def test_start_satisfying_predicate_returns_immediately(self) -> None:
        graph = Graph()
        graph.add_node("start")
        path = a_star_to_predicate("start", lambda node: True, graph, lambda node: 0.0)
        self.assertEqual(path, ["start"])

    def test_none_when_no_node_satisfies_the_predicate(self) -> None:
        graph = Graph()
        graph.add_edge("start", "a", 1)
        path = a_star_to_predicate("start", lambda node: False, graph, lambda node: 0.0)
        self.assertIsNone(path)


class PathfindingRequestTestCase(unittest.TestCase):
    def test_step_returns_false_until_the_search_finishes(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b", 1)
        graph.add_edge("b", "c", 1)
        graph.add_edge("c", "d", 1)
        request = PathfindingRequest(
            incremental_a_star("a", "d", graph, _zero_heuristic)
        )
        finished_early = request.step(max_iterations=1)
        self.assertFalse(finished_early)
        self.assertFalse(request.done)

        while not request.step(max_iterations=1):
            pass

        self.assertTrue(request.done)
        self.assertEqual(request.result, ["a", "b", "c", "d"])


class PlannerPoolTestCase(unittest.TestCase):
    def test_resolves_every_request_after_enough_updates(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b", 1)
        graph.add_edge("b", "c", 1)
        pool = PlannerPool(iterations_per_update=1)
        request_1 = pool.request(incremental_a_star("a", "c", graph, _zero_heuristic))
        request_2 = pool.request(incremental_a_star("a", "b", graph, _zero_heuristic))

        for _ in range(20):
            pool.update()

        self.assertTrue(request_1.done)
        self.assertTrue(request_2.done)
        self.assertEqual(request_1.result, ["a", "b", "c"])
        self.assertEqual(request_2.result, ["a", "b"])


class HierarchicalGraphTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = NavGraph()
        # Two clusters of 3 nodes each, connected by a single bridge edge.
        self.graph.add_edge((0, 0), (1, 0))
        self.graph.add_edge((1, 0), (2, 0))
        self.graph.add_edge((2, 0), (3, 0))  # bridge
        self.graph.add_edge((3, 0), (4, 0))
        self.graph.add_edge((4, 0), (5, 0))
        self.clusters = {
            (0, 0): 0,
            (1, 0): 0,
            (2, 0): 0,
            (3, 0): 1,
            (4, 0): 1,
            (5, 0): 1,
        }

    def test_find_path_within_a_single_cluster(self) -> None:
        hierarchical = HierarchicalGraph(self.graph, self.clusters)
        path = hierarchical.find_path((0, 0), (2, 0), heuristic=lambda a, b: 0.0)
        self.assertEqual(path, [(0, 0), (1, 0), (2, 0)])

    def test_find_path_across_clusters(self) -> None:
        hierarchical = HierarchicalGraph(self.graph, self.clusters)
        path = hierarchical.find_path((0, 0), (5, 0), heuristic=lambda a, b: 0.0)
        self.assertEqual(path, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)])

    def test_find_path_returns_none_when_unreachable(self) -> None:
        self.graph.add_node((10, 10))
        self.clusters[(10, 10)] = 2
        hierarchical = HierarchicalGraph(self.graph, self.clusters)
        path = hierarchical.find_path((0, 0), (10, 10), heuristic=lambda a, b: 0.0)
        self.assertIsNone(path)


if __name__ == "__main__":
    unittest.main()
