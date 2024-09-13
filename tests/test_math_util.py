import unittest

from gale import math_util


class MathUtilTestCase(unittest.TestCase):
    def test_real_equal(self):
        self.assertTrue(math_util.real_equal(0.1, 0.1))
        self.assertTrue(math_util.real_equal(0.1, 0.1 + math_util.EPSILON / 2))
        self.assertTrue(math_util.real_equal(0.1, 0.1 - math_util.EPSILON / 2))
        self.assertFalse(math_util.real_equal(0.1, 0.1 + math_util.EPSILON * 2))
        self.assertFalse(math_util.real_equal(0.1, 0.1 - math_util.EPSILON * 2))
        self.assertTrue(math_util.real_equal(0.0, 0.0))
        self.assertTrue(math_util.real_equal(0.0, math_util.EPSILON / 2))
        self.assertTrue(math_util.real_equal(0.0, -math_util.EPSILON / 2))
        self.assertFalse(math_util.real_equal(0.0, math_util.EPSILON * 2))
        self.assertFalse(math_util.real_equal(0.0, -math_util.EPSILON * 2))
