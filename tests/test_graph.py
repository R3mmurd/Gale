import unittest

from gale.ai.graph import CycleError, DependencyGraph, Graph, NavGraph, StateGraph


class GraphTestCase(unittest.TestCase):
    def test_add_node(self) -> None:
        graph = Graph()
        graph.add_node("a")
        self.assertTrue(graph.has_node("a"))
        self.assertIn("a", graph)
        self.assertEqual(len(graph), 1)

    def test_undirected_edge_is_added_both_ways(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b", 5)
        self.assertTrue(graph.has_edge("a", "b"))
        self.assertTrue(graph.has_edge("b", "a"))
        self.assertEqual(graph.get_weight("a", "b"), 5)
        self.assertEqual(graph.get_weight("b", "a"), 5)

    def test_directed_edge_is_added_one_way(self) -> None:
        graph = Graph(directed=True)
        graph.add_edge("a", "b", 5)
        self.assertTrue(graph.has_edge("a", "b"))
        self.assertFalse(graph.has_edge("b", "a"))

    def test_default_weight(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b")
        self.assertEqual(graph.get_weight("a", "b"), 1.0)

    def test_neighbors_and_weighted_neighbors(self) -> None:
        graph = Graph(directed=True)
        graph.add_edge("a", "b", 2)
        graph.add_edge("a", "c", 3)
        self.assertEqual(set(graph.neighbors("a")), {"b", "c"})
        self.assertEqual(set(graph.weighted_neighbors("a")), {("b", 2), ("c", 3)})

    def test_remove_node_removes_connected_edges(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.remove_node("b")
        self.assertFalse(graph.has_node("b"))
        self.assertFalse(graph.has_edge("a", "b"))
        self.assertFalse(graph.has_edge("c", "b"))
        self.assertTrue(graph.has_node("a"))
        self.assertTrue(graph.has_node("c"))

    def test_remove_edge(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b")
        graph.remove_edge("a", "b")
        self.assertFalse(graph.has_edge("a", "b"))
        self.assertFalse(graph.has_edge("b", "a"))

    def test_edges_property_undirected_yields_each_edge_once(self) -> None:
        graph = Graph()
        graph.add_edge("a", "b", 1)
        graph.add_edge("b", "c", 2)
        edges = {(min(s, t), max(s, t), w) for s, t, w in graph.edges}
        self.assertEqual(edges, {("a", "b", 1), ("b", "c", 2)})

    def test_edges_property_directed_yields_every_edge(self) -> None:
        graph = Graph(directed=True)
        graph.add_edge("a", "b", 1)
        graph.add_edge("b", "a", 2)
        self.assertEqual(set(graph.edges), {("a", "b", 1), ("b", "a", 2)})


class NavGraphTestCase(unittest.TestCase):
    def test_default_weight_is_euclidean_distance(self) -> None:
        graph = NavGraph()
        graph.add_edge((0, 0), (3, 4))
        self.assertAlmostEqual(graph.get_weight((0, 0), (3, 4)), 5.0)

    def test_weight_can_be_overridden(self) -> None:
        graph = NavGraph()
        graph.add_edge((0, 0), (3, 4), weight=100)
        self.assertEqual(graph.get_weight((0, 0), (3, 4)), 100)


class DependencyGraphTestCase(unittest.TestCase):
    def test_topological_sort_respects_dependencies(self) -> None:
        graph = DependencyGraph()
        graph.add_dependency("wheels", depends_on="rubber")
        graph.add_dependency("car", depends_on="wheels")
        graph.add_dependency("car", depends_on="engine")

        order = graph.topological_sort()

        self.assertLess(order.index("rubber"), order.index("wheels"))
        self.assertLess(order.index("wheels"), order.index("car"))
        self.assertLess(order.index("engine"), order.index("car"))

    def test_topological_sort_raises_on_cycle(self) -> None:
        graph = DependencyGraph()
        graph.add_dependency("a", depends_on="b")
        graph.add_dependency("b", depends_on="a")

        with self.assertRaises(CycleError):
            graph.topological_sort()

    def test_has_cycle(self) -> None:
        acyclic = DependencyGraph()
        acyclic.add_dependency("b", depends_on="a")
        self.assertFalse(acyclic.has_cycle())

        cyclic = DependencyGraph()
        cyclic.add_dependency("a", depends_on="b")
        cyclic.add_dependency("b", depends_on="a")
        self.assertTrue(cyclic.has_cycle())


class StateGraphTestCase(unittest.TestCase):
    def test_expand_builds_full_reachable_graph(self) -> None:
        # A tiny state space: 0 -> 1 -> 2 (a dead end) and 0 -> 3.
        transitions = {
            0: [(1, 1), (3, 1)],
            1: [(2, 1)],
            2: [],
            3: [],
        }

        graph = StateGraph.expand(0, lambda state: transitions[state])

        self.assertEqual(set(graph.nodes), {0, 1, 2, 3})
        self.assertTrue(graph.has_edge(0, 1))
        self.assertTrue(graph.has_edge(0, 3))
        self.assertTrue(graph.has_edge(1, 2))
        self.assertTrue(graph.directed)
