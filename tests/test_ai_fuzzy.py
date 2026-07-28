import unittest

from gale.ai.fuzzy import (
    FuzzyRule,
    FuzzyRuleSet,
    FuzzyVariable,
    LeftShoulderSet,
    RightShoulderSet,
    TrapezoidalSet,
    TriangularSet,
    fuzzy_and,
    fuzzy_or,
)


class TriangularSetTestCase(unittest.TestCase):
    def test_peak_has_full_membership(self) -> None:
        fuzzy_set = TriangularSet(0, 10, 20)
        self.assertEqual(fuzzy_set.membership(10), 1.0)

    def test_outside_range_has_zero_membership(self) -> None:
        fuzzy_set = TriangularSet(0, 10, 20)
        self.assertEqual(fuzzy_set.membership(-5), 0.0)
        self.assertEqual(fuzzy_set.membership(25), 0.0)

    def test_midpoint_has_half_membership(self) -> None:
        fuzzy_set = TriangularSet(0, 10, 20)
        self.assertAlmostEqual(fuzzy_set.membership(5), 0.5)


class TrapezoidalSetTestCase(unittest.TestCase):
    def test_plateau_has_full_membership(self) -> None:
        fuzzy_set = TrapezoidalSet(0, 10, 20, 30)
        self.assertEqual(fuzzy_set.membership(15), 1.0)

    def test_rising_edge_is_linear(self) -> None:
        fuzzy_set = TrapezoidalSet(0, 10, 20, 30)
        self.assertAlmostEqual(fuzzy_set.membership(5), 0.5)


class ShoulderSetTestCase(unittest.TestCase):
    def test_left_shoulder_is_full_below_peak(self) -> None:
        fuzzy_set = LeftShoulderSet(10, 20)
        self.assertEqual(fuzzy_set.membership(0), 1.0)
        self.assertEqual(fuzzy_set.membership(20), 0.0)

    def test_right_shoulder_is_full_above_peak(self) -> None:
        fuzzy_set = RightShoulderSet(10, 20)
        self.assertEqual(fuzzy_set.membership(30), 1.0)
        self.assertEqual(fuzzy_set.membership(10), 0.0)


class FuzzyAndOrTestCase(unittest.TestCase):
    def test_and_is_minimum(self) -> None:
        self.assertEqual(fuzzy_and(0.3, 0.7, 0.5), 0.3)

    def test_or_is_maximum(self) -> None:
        self.assertEqual(fuzzy_or(0.3, 0.7, 0.5), 0.7)


class FuzzyVariableTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.distance = FuzzyVariable(
            "distance",
            domain=(0, 100),
            sets={
                "near": LeftShoulderSet(10, 30),
                "far": RightShoulderSet(50, 90),
            },
        )

    def test_fuzzify_returns_a_degree_per_set(self) -> None:
        degrees = self.distance.fuzzify(5)
        self.assertEqual(degrees["near"], 1.0)
        self.assertEqual(degrees["far"], 0.0)

    def test_defuzzify_of_symmetric_degrees_centers_the_domain(self) -> None:
        symmetric = FuzzyVariable(
            "symmetric",
            domain=(0, 100),
            sets={
                "low": LeftShoulderSet(0, 100),
                "high": RightShoulderSet(0, 100),
            },
        )
        value = symmetric.defuzzify({"low": 1.0, "high": 1.0})
        self.assertAlmostEqual(value, 50, delta=2)

    def test_defuzzify_with_no_degrees_returns_domain_midpoint(self) -> None:
        self.assertEqual(self.distance.defuzzify({}), 50)


class FuzzyRuleSetTestCase(unittest.TestCase):
    def test_evaluate_aggregates_rules_by_max(self) -> None:
        rules = FuzzyRuleSet(
            [
                FuzzyRule(lambda d: 0.3, "alertness", "high"),
                FuzzyRule(lambda d: 0.7, "alertness", "high"),
                FuzzyRule(lambda d: 0.2, "alertness", "low"),
            ]
        )
        output = rules.evaluate({})
        self.assertEqual(output["alertness"]["high"], 0.7)
        self.assertEqual(output["alertness"]["low"], 0.2)

    def test_evaluate_uses_fuzzified_inputs(self) -> None:
        distance = FuzzyVariable(
            "distance", (0, 100), {"near": LeftShoulderSet(10, 30)}
        )
        rules = FuzzyRuleSet(
            [FuzzyRule(lambda d: d["distance"]["near"], "alertness", "high")]
        )
        output = rules.evaluate({"distance": distance.fuzzify(0)})
        self.assertEqual(output["alertness"]["high"], 1.0)


if __name__ == "__main__":
    unittest.main()
