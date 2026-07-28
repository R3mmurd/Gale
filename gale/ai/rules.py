"""
This file contains a small forward-chaining, production-rule system:
Rule pairs a condition with an action and a priority, and RuleEngine
repeatedly fires the highest-priority applicable rule against a shared
working memory until none applies (or a maximum number of iterations is
reached), the same "IF condition THEN action" style used in classic
expert systems and rule-based game AI.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, Optional, Sequence

Condition = Callable[[Dict[str, Any]], bool]
RuleAction = Callable[[Dict[str, Any]], None]


class Rule:
    """
    A single production rule: condition is checked against the
    RuleEngine's working memory, and action is called when it's the
    highest-priority rule whose condition currently holds.

    Usage example:

        Rule(
            name="flee_when_low_health",
            condition=lambda memory: memory.get("health", 100) < 20,
            action=lambda memory: memory.__setitem__("goal", "flee"),
            priority=10,
        )
    """

    def __init__(
        self,
        name: str,
        condition: Condition,
        action: RuleAction,
        priority: float = 0.0,
    ) -> None:
        """
        :param name: Name of this rule.
        :param condition: Callable(working_memory) -> bool, checked every iteration.
        :param action: Callable(working_memory) invoked when this rule fires; expected to mutate working_memory.
        :param priority: Higher priority rules are considered before lower priority ones when more than one applies in the same iteration. The default value is 0.
        """
        self.name: str = name
        self.condition: Condition = condition
        self.action: RuleAction = action
        self.priority: float = priority


class RuleEngine:
    """
    Forward-chains a set of rules against a shared working memory: each
    call to run() re-evaluates every rule's condition, fires the
    single highest-priority rule that currently applies, and repeats
    (since firing a rule may make others applicable, or the same one
    inapplicable) until no rule applies or max_iterations is reached.

    Usage example:

        engine = RuleEngine([
            Rule("flee", lambda m: m["health"] < 20, lambda m: m.update(goal="flee"), priority=10),
            Rule("attack", lambda m: m["enemy_visible"], lambda m: m.update(goal="attack"), priority=5),
            Rule("patrol", lambda m: True, lambda m: m.update(goal="patrol"), priority=0),
        ])
        engine.working_memory.update(health=100, enemy_visible=True)
        fired = engine.run()  # ["attack"] -- only "attack" applies and firing it doesn't unlock another
    """

    def __init__(
        self,
        rules: Sequence[Rule],
        working_memory: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        :param rules: The rules to forward-chain over.
        :param working_memory: Initial working memory. The default value is an empty dict.
        """
        self.rules: Sequence[Rule] = rules
        self.working_memory: Dict[str, Any] = (
            {} if working_memory is None else working_memory
        )

    def run(self, max_iterations: int = 100) -> Sequence[str]:
        """
        :param max_iterations: Maximum number of rules to fire in this call, as a safeguard against rules that keep re-triggering each other forever.
        :returns: The name of each rule fired, in the order they fired. Stops early, before max_iterations, as soon as the same rule would fire again against an unchanged working_memory (a steady state reached), without firing it that extra time.
        """
        fired = []
        last_fired_name = None
        memory_after_last_fire = None

        for _ in range(max_iterations):
            applicable = [
                rule for rule in self.rules if rule.condition(self.working_memory)
            ]

            if not applicable:
                break

            best_rule = max(applicable, key=lambda rule: rule.priority)

            if (
                best_rule.name == last_fired_name
                and self.working_memory == memory_after_last_fire
            ):
                break

            best_rule.action(self.working_memory)
            fired.append(best_rule.name)
            last_fired_name = best_rule.name
            memory_after_last_fire = dict(self.working_memory)

        return fired
