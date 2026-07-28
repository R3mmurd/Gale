"""
This file contains a small data-driven "scripting" layer for AI: a
Registry of named actions/conditions/tests/weights, plus
build_behavior_tree and build_decision_tree, which recursively turn a
plain, JSON-friendly dict into a gale.ai.behavior_tree.BehaviorTree or
gale.ai.decision_tree.DecisionTree. This lets a designer describe an
agent's decision-making as data (hand-written, generated, or loaded
from a JSON file) instead of writing Python subclasses for every leaf,
without needing a custom text-based language and its own parser.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, List, Tuple

from .behavior_tree import (
    Action,
    Condition,
    Cooldown,
    Failer,
    Inverter,
    Node,
    Parallel,
    Repeater,
    Selector,
    Sequence,
    Succeeder,
    UntilFailure,
    UntilSuccess,
)
from .decision_tree import (
    ActionNode,
    DecisionNode,
    DecisionTreeNode,
    RandomDecisionNode,
)


class Registry:
    """
    Holds the named building blocks a behavior tree/decision tree spec
    can refer to by name instead of by direct Python reference: actions
    (agent, dt) -> Status/Any, conditions/tests (agent) -> bool, and
    named weights for RandomDecisionNode branches.

    Usage example:

        registry = Registry()
        registry.register_action("patrol", lambda agent, dt: agent.patrol(dt))
        registry.register_condition("enemy_visible", lambda agent: agent.can_see_enemy())
    """

    def __init__(self) -> None:
        self._actions: Dict[str, Callable[[Any, float], Any]] = {}
        self._conditions: Dict[str, Callable[[Any], bool]] = {}

    def register_action(self, name: str, function: Callable[[Any, float], Any]) -> None:
        """
        :param name: Name a spec can refer to this action by.
        :param function: Callable(agent, dt) implementing it.
        """
        self._actions[name] = function

    def register_condition(self, name: str, predicate: Callable[[Any], bool]) -> None:
        """
        :param name: Name a spec can refer to this condition by.
        :param predicate: Callable(agent) -> bool implementing it.
        """
        self._conditions[name] = predicate

    def get_action(self, name: str) -> Callable[[Any, float], Any]:
        """
        :param name: The name an action was registered with.
        :returns: The registered callable.
        :raises KeyError: If no action was registered under name.
        """
        return self._actions[name]

    def get_condition(self, name: str) -> Callable[[Any], bool]:
        """
        :param name: The name a condition was registered with.
        :returns: The registered callable.
        :raises KeyError: If no condition was registered under name.
        """
        return self._conditions[name]


_BEHAVIOR_COMPOSITES: Dict[str, type] = {
    "sequence": Sequence,
    "selector": Selector,
}
_BEHAVIOR_DECORATORS: Dict[str, type] = {
    "inverter": Inverter,
    "succeeder": Succeeder,
    "failer": Failer,
    "until_success": UntilSuccess,
    "until_failure": UntilFailure,
}


def build_behavior_tree(spec: Dict[str, Any], registry: Registry) -> Node:
    """
    Recursively build a behavior tree node from a spec such as:

        {
            "type": "selector",
            "children": [
                {"type": "sequence", "children": [
                    {"type": "condition", "name": "enemy_visible"},
                    {"type": "action", "name": "attack"},
                ]},
                {"type": "action", "name": "patrol"},
            ],
        }

    Recognized "type" values: "sequence"/"selector" (need "children": a
    list of specs), "parallel" (also accepts "success_threshold"/
    "failure_threshold"), "inverter"/"succeeder"/"failer"/
    "until_success"/"until_failure" (need "child": a single spec),
    "repeater" (needs "child", accepts "times"), "cooldown" (needs
    "child" and "duration"), "action" (needs "name", looked up in
    registry), "condition" (needs "name", looked up in registry).

    :param spec: The spec to build a node from.
    :param registry: Where "action"/"condition" names are looked up.
    :returns: The built Node. Wrap the result in gale.ai.behavior_tree.BehaviorTree to tick it.
    :raises KeyError: If spec's "type" is not one of the recognized values above, or an "action"/"condition" name is not registered.
    """
    node_type = spec["type"]

    if node_type in _BEHAVIOR_COMPOSITES:
        children = [build_behavior_tree(child, registry) for child in spec["children"]]
        return _BEHAVIOR_COMPOSITES[node_type](children)

    if node_type == "parallel":
        children = [build_behavior_tree(child, registry) for child in spec["children"]]
        return Parallel(
            children,
            success_threshold=spec.get("success_threshold"),
            failure_threshold=spec.get("failure_threshold"),
        )

    if node_type in _BEHAVIOR_DECORATORS:
        child = build_behavior_tree(spec["child"], registry)
        return _BEHAVIOR_DECORATORS[node_type](child)

    if node_type == "repeater":
        child = build_behavior_tree(spec["child"], registry)
        return Repeater(child, times=spec.get("times"))

    if node_type == "cooldown":
        child = build_behavior_tree(spec["child"], registry)
        return Cooldown(child, duration=spec["duration"])

    if node_type == "action":
        return Action(registry.get_action(spec["name"]))

    if node_type == "condition":
        return Condition(registry.get_condition(spec["name"]))

    raise KeyError(f"Unrecognized behavior tree node type: {node_type!r}")


def build_decision_tree(spec: Dict[str, Any], registry: Registry) -> DecisionTreeNode:
    """
    Recursively build a decision tree node from a spec such as:

        {
            "type": "decision",
            "test": "low_health",
            "true": {"type": "action", "name": "flee"},
            "false": {"type": "action", "name": "attack"},
        }

    Recognized "type" values: "decision" (needs "test", "true",
    "false"), "random" (needs "branches": a list of [spec, weight]
    pairs), "action" (needs "name", looked up in registry).

    :param spec: The spec to build a node from.
    :param registry: Where "test"/"action" names are looked up.
    :returns: The built DecisionTreeNode. Wrap the result in gale.ai.decision_tree.DecisionTree to evaluate it.
    :raises KeyError: If spec's "type" is not one of the recognized values above, or a "test"/"action" name is not registered.
    """
    node_type = spec["type"]

    if node_type == "decision":
        return DecisionNode(
            test=registry.get_condition(spec["test"]),
            true_branch=build_decision_tree(spec["true"], registry),
            false_branch=build_decision_tree(spec["false"], registry),
        )

    if node_type == "random":
        branches: List[Tuple[DecisionTreeNode, float]] = [
            (build_decision_tree(branch_spec, registry), weight)
            for branch_spec, weight in spec["branches"]
        ]
        return RandomDecisionNode(branches)

    if node_type == "action":
        # Registry actions have the (agent, dt) signature the behavior
        # tree Action leaf expects; ActionNode only passes agent, so
        # dt is fixed at 0 here -- the same "accepted but ignored"
        # convention DecisionTree.tick already uses.
        function = registry.get_action(spec["name"])
        return ActionNode(lambda agent, function=function: function(agent, 0))

    raise KeyError(f"Unrecognized decision tree node type: {node_type!r}")
