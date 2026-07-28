import unittest

from gale.ai.behavior_tree import BehaviorTree, Status
from gale.ai.decision_tree import DecisionTree
from gale.ai.scripting import Registry, build_behavior_tree, build_decision_tree


class BuildBehaviorTreeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        self.registry.register_condition(
            "enemy_visible", lambda agent: agent["enemy_visible"]
        )
        self.registry.register_action(
            "attack",
            lambda agent, dt: (
                Status.SUCCESS if agent["enemy_visible"] else Status.FAILURE
            ),
        )
        self.registry.register_action("patrol", lambda agent, dt: Status.SUCCESS)

    def test_selector_falls_back_to_patrol(self) -> None:
        spec = {
            "type": "selector",
            "children": [
                {
                    "type": "sequence",
                    "children": [
                        {"type": "condition", "name": "enemy_visible"},
                        {"type": "action", "name": "attack"},
                    ],
                },
                {"type": "action", "name": "patrol"},
            ],
        }
        tree = BehaviorTree(build_behavior_tree(spec, self.registry))
        status = tree.tick({"enemy_visible": False}, 0.1)
        self.assertEqual(status, Status.SUCCESS)

    def test_decorator_wraps_its_child(self) -> None:
        spec = {"type": "inverter", "child": {"type": "action", "name": "patrol"}}
        tree = BehaviorTree(build_behavior_tree(spec, self.registry))
        self.assertEqual(tree.tick({}, 0.1), Status.FAILURE)

    def test_repeater_and_cooldown_build_correctly(self) -> None:
        repeater_spec = {
            "type": "repeater",
            "child": {"type": "action", "name": "patrol"},
            "times": 2,
        }
        cooldown_spec = {
            "type": "cooldown",
            "child": {"type": "action", "name": "patrol"},
            "duration": 1.0,
        }
        BehaviorTree(build_behavior_tree(repeater_spec, self.registry))
        BehaviorTree(build_behavior_tree(cooldown_spec, self.registry))

    def test_unrecognized_type_raises(self) -> None:
        self.assertRaises(
            KeyError, build_behavior_tree, {"type": "nonsense"}, self.registry
        )


class BuildDecisionTreeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Registry()
        self.registry.register_condition(
            "low_health", lambda agent: agent["health"] < 20
        )
        self.registry.register_action("flee", lambda agent, dt: "flee")
        self.registry.register_action("attack", lambda agent, dt: "attack")

    def test_decision_node_picks_the_right_branch(self) -> None:
        spec = {
            "type": "decision",
            "test": "low_health",
            "true": {"type": "action", "name": "flee"},
            "false": {"type": "action", "name": "attack"},
        }
        tree = DecisionTree(build_decision_tree(spec, self.registry))
        self.assertEqual(tree.make_decision({"health": 10}), "flee")
        self.assertEqual(tree.make_decision({"health": 100}), "attack")

    def test_random_node_only_returns_a_declared_branch(self) -> None:
        spec = {
            "type": "random",
            "branches": [
                [{"type": "action", "name": "flee"}, 0.5],
                [{"type": "action", "name": "attack"}, 0.5],
            ],
        }
        tree = DecisionTree(build_decision_tree(spec, self.registry))

        for _ in range(20):
            self.assertIn(tree.make_decision({}), ("flee", "attack"))

    def test_unrecognized_type_raises(self) -> None:
        self.assertRaises(
            KeyError, build_decision_tree, {"type": "nonsense"}, self.registry
        )


if __name__ == "__main__":
    unittest.main()
