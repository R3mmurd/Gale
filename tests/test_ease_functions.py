import math
import unittest

from gale.ease_functions import EASE_FUNCTIONS, ease_in_out_back, ease_out_bounce


class EaseFunctionsTestCase(unittest.TestCase):
    def test_every_function_starts_at_zero_and_ends_at_one(self) -> None:
        for name, function in EASE_FUNCTIONS.items():
            with self.subTest(ease_function=name):
                self.assertAlmostEqual(function(0.0), 0.0, places=6)
                self.assertAlmostEqual(function(1.0), 1.0, places=6)

    def test_every_function_is_finite_across_the_domain(self) -> None:
        samples = [i / 20 for i in range(21)]

        for name, function in EASE_FUNCTIONS.items():
            for t in samples:
                with self.subTest(ease_function=name, t=t):
                    value = function(t)
                    self.assertTrue(math.isfinite(value))

    def test_linear_is_the_identity(self) -> None:
        linear = EASE_FUNCTIONS["linear"]
        self.assertEqual(linear(0.25), 0.25)
        self.assertEqual(linear(0.75), 0.75)

    def test_in_functions_start_slower_than_linear(self) -> None:
        # A pure "in_*" easing (not "in_out_*", which passes exactly
        # through the midpoint by construction) should still be below
        # the midpoint at t=0.5 -- it starts slow, only catching up
        # near the end -- except "in_back"/"in_elastic", which
        # intentionally overshoot below 0 first.
        for name, function in EASE_FUNCTIONS.items():
            if (
                name.startswith("in_")
                and "out" not in name
                and "back" not in name
                and "elastic" not in name
            ):
                with self.subTest(ease_function=name):
                    self.assertLess(function(0.5), 0.5)

    def test_out_back_overshoots_past_one_before_settling(self) -> None:
        out_back = EASE_FUNCTIONS["out_back"]
        self.assertGreater(max(out_back(i / 10) for i in range(11)), 1.0)

    def test_in_out_back_is_symmetric_around_the_midpoint(self) -> None:
        self.assertAlmostEqual(
            ease_in_out_back(0.25), 1 - ease_in_out_back(0.75), places=6
        )

    def test_out_bounce_reaches_exactly_one_at_the_end(self) -> None:
        self.assertEqual(ease_out_bounce(1.0), 1.0)


if __name__ == "__main__":
    unittest.main()
