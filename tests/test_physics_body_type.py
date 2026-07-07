import unittest

from gale.physics.body_type import BodyType


class BodyTypeTestCase(unittest.TestCase):
    def test_constants_are_distinct(self) -> None:
        values = {BodyType.STATIC, BodyType.DYNAMIC, BodyType.KINEMATIC}
        self.assertEqual(len(values), 3)


if __name__ == "__main__":
    unittest.main()
