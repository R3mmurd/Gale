import unittest

from gale.physics.shapes import BoxShape, CircleShape, PolygonShape


class CircleShapeTestCase(unittest.TestCase):
    def test_defaults(self) -> None:
        shape = CircleShape(radius=10)
        self.assertEqual(shape.radius, 10)
        self.assertEqual(shape.density, 1.0)
        self.assertEqual(shape.friction, 0.3)
        self.assertEqual(shape.restitution, 0.0)
        self.assertFalse(shape.is_sensor)
        self.assertEqual(shape.offset, (0, 0))

    def test_explicit_values(self) -> None:
        shape = CircleShape(
            radius=5,
            density=2,
            friction=0.1,
            restitution=0.8,
            is_sensor=True,
            offset=(1, 2),
        )
        self.assertEqual(
            (shape.density, shape.friction, shape.restitution), (2, 0.1, 0.8)
        )
        self.assertTrue(shape.is_sensor)
        self.assertEqual(shape.offset, (1, 2))


class BoxShapeTestCase(unittest.TestCase):
    def test_defaults(self) -> None:
        shape = BoxShape(width=20, height=10)
        self.assertEqual((shape.width, shape.height), (20, 10))
        self.assertEqual(shape.density, 1.0)
        self.assertFalse(shape.is_sensor)


class PolygonShapeTestCase(unittest.TestCase):
    def test_defaults(self) -> None:
        points = [(0, -10), (10, 10), (-10, 10)]
        shape = PolygonShape(points)
        self.assertEqual(shape.points, points)
        self.assertEqual(shape.density, 1.0)

    def test_points_are_copied(self) -> None:
        points = [(0, 0), (1, 1)]
        shape = PolygonShape(points)
        points.append((2, 2))
        self.assertEqual(len(shape.points), 2)


if __name__ == "__main__":
    unittest.main()
