"""
This file contains a decision tree implementation, a simple alternative
to behavior trees to model the decision making of autonomous characters
as a sequence of yes/no questions that lead to an action.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import random

from typing import Any, Callable, Sequence, Tuple


class DecisionTreeNode:
    """
    Base class for any node of a decision tree.
    """

    def make_decision(self, agent: Any) -> Any:
        """
        Evaluate this node.

        :param agent: The agent this decision tree belongs to.
        :returns: Whatever the reached leaf of the tree returns.
        """
        raise NotImplementedError()


class ActionNode(DecisionTreeNode):
    """
    Leaf node of a decision tree. It represents the outcome of the
    decision-making process.
    """

    def __init__(self, action: Callable[[Any], Any]) -> None:
        """
        :param action: Callable that receives the agent and returns the result of this decision.
        """
        self.action: Callable[[Any], Any] = action

    def make_decision(self, agent: Any) -> Any:
        return self.action(agent)


class DecisionNode(DecisionTreeNode):
    """
    Node that decides which one of two branches to evaluate, based on a
    test performed over the agent.
    """

    def __init__(
        self,
        test: Callable[[Any], bool],
        true_branch: DecisionTreeNode,
        false_branch: DecisionTreeNode,
    ) -> None:
        """
        :param test: Callable that receives the agent and returns a bool.
        :param true_branch: Branch evaluated when the test returns True.
        :param false_branch: Branch evaluated when the test returns False.
        """
        self.test: Callable[[Any], bool] = test
        self.true_branch: DecisionTreeNode = true_branch
        self.false_branch: DecisionTreeNode = false_branch

    def make_decision(self, agent: Any) -> Any:
        branch = self.true_branch if self.test(agent) else self.false_branch
        return branch.make_decision(agent)


class RandomDecisionNode(DecisionTreeNode):
    """
    Node that picks one of several branches at random, according to
    given weights. Useful to make characters less predictable.
    """

    def __init__(self, branches: Sequence[Tuple[DecisionTreeNode, float]]) -> None:
        """
        :param branches: Sequence of pairs (branch, weight) to choose from.
        """
        self.branches: Sequence[DecisionTreeNode] = [branch for branch, _ in branches]
        self.weights: Sequence[float] = [weight for _, weight in branches]

    def make_decision(self, agent: Any) -> Any:
        branch = random.choices(self.branches, weights=self.weights, k=1)[0]
        return branch.make_decision(agent)


class DecisionTree:
    """
    Wraps a root node so that it can be conveniently evaluated as a
    whole.

    Usage example:

        tree = DecisionTree(
            DecisionNode(
                test=lambda agent: agent.health < 0.3,
                true_branch=ActionNode(lambda agent: agent.flee()),
                false_branch=ActionNode(lambda agent: agent.attack()),
            )
        )
        tree.make_decision(agent)
    """

    def __init__(self, root: DecisionTreeNode) -> None:
        """
        :param root: The root node of the tree.
        """
        self.root: DecisionTreeNode = root

    def make_decision(self, agent: Any) -> Any:
        """
        Evaluate the tree from its root.

        :param agent: The agent this tree belongs to.
        :returns: Whatever the reached leaf of the tree returns.
        """
        return self.root.make_decision(agent)
