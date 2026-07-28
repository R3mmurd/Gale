import unittest

from gale.math_util import EPSILON, real_equal


class RealEqualTestCase(unittest.TestCase):
    def test_identical_values_are_equal(self) -> None:
        self.assertTrue(real_equal(1.0, 1.0))

    def test_values_within_epsilon_are_equal(self) -> None:
        self.assertTrue(real_equal(1.0, 1.0 + EPSILON / 2))

    def test_values_beyond_epsilon_are_not_equal(self) -> None:
        self.assertFalse(real_equal(1.0, 1.0 + EPSILON * 10))

    def test_negative_difference_is_handled(self) -> None:
        self.assertTrue(real_equal(1.0, 1.0 - EPSILON / 2))


if __name__ == "__main__":
    unittest.main()
