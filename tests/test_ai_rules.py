import unittest

from gale.ai.rules import Rule, RuleEngine


class RuleEngineTestCase(unittest.TestCase):
    def test_fires_the_highest_priority_applicable_rule(self) -> None:
        engine = RuleEngine(
            [
                Rule(
                    "flee",
                    lambda m: m["health"] < 20,
                    lambda m: m.update(goal="flee"),
                    priority=10,
                ),
                Rule(
                    "attack",
                    lambda m: m["enemy_visible"],
                    lambda m: m.update(goal="attack"),
                    priority=5,
                ),
            ],
            {"health": 100, "enemy_visible": True},
        )
        fired = engine.run()
        self.assertEqual(fired, ["attack"])
        self.assertEqual(engine.working_memory["goal"], "attack")

    def test_higher_priority_rule_wins_when_both_apply(self) -> None:
        engine = RuleEngine(
            [
                Rule(
                    "flee",
                    lambda m: m["health"] < 20,
                    lambda m: m.update(goal="flee"),
                    priority=10,
                ),
                Rule(
                    "attack",
                    lambda m: m["enemy_visible"],
                    lambda m: m.update(goal="attack"),
                    priority=5,
                ),
            ],
            {"health": 10, "enemy_visible": True},
        )
        engine.run()
        self.assertEqual(engine.working_memory["goal"], "flee")

    def test_stops_when_no_rule_applies(self) -> None:
        engine = RuleEngine(
            [Rule("attack", lambda m: m.get("enemy_visible", False), lambda m: None)],
            {},
        )
        fired = engine.run()
        self.assertEqual(fired, [])

    def test_stops_at_a_steady_state_instead_of_looping_to_max_iterations(
        self,
    ) -> None:
        engine = RuleEngine(
            [Rule("patrol", lambda m: True, lambda m: m.update(goal="patrol"))]
        )
        fired = engine.run(max_iterations=100)
        self.assertEqual(fired, ["patrol"])


if __name__ == "__main__":
    unittest.main()
