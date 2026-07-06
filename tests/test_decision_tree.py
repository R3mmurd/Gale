import unittest
from unittest.mock import patch

from gale.ai.decision_tree import (
    ActionNode,
    DecisionNode,
    DecisionTree,
    RandomDecisionNode,
)


class DecisionNodeTestCase(unittest.TestCase):
    def test_picks_true_branch(self) -> None:
        tree = DecisionTree(
            DecisionNode(
                test=lambda agent: agent > 0,
                true_branch=ActionNode(lambda agent: "positive"),
                false_branch=ActionNode(lambda agent: "non_positive"),
            )
        )
        self.assertEqual(tree.make_decision(1), "positive")

    def test_picks_false_branch(self) -> None:
        tree = DecisionTree(
            DecisionNode(
                test=lambda agent: agent > 0,
                true_branch=ActionNode(lambda agent: "positive"),
                false_branch=ActionNode(lambda agent: "non_positive"),
            )
        )
        self.assertEqual(tree.make_decision(-1), "non_positive")

    def test_nested_decision_nodes(self) -> None:
        tree = DecisionTree(
            DecisionNode(
                test=lambda agent: agent > 10,
                true_branch=ActionNode(lambda agent: "big"),
                false_branch=DecisionNode(
                    test=lambda agent: agent > 0,
                    true_branch=ActionNode(lambda agent: "small"),
                    false_branch=ActionNode(lambda agent: "non_positive"),
                ),
            )
        )
        self.assertEqual(tree.make_decision(20), "big")
        self.assertEqual(tree.make_decision(5), "small")
        self.assertEqual(tree.make_decision(-5), "non_positive")


class RandomDecisionNodeTestCase(unittest.TestCase):
    def test_uses_weights_to_choose_a_branch(self) -> None:
        node = RandomDecisionNode(
            [
                (ActionNode(lambda agent: "a"), 1),
                (ActionNode(lambda agent: "b"), 0),
            ]
        )
        with patch("random.choices", return_value=[node.branches[0]]) as choices:
            result = node.make_decision(None)
        choices.assert_called_once_with(node.branches, weights=node.weights, k=1)
        self.assertEqual(result, "a")
