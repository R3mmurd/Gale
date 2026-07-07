import unittest

from gale.physics.shapes import BoxShape, CircleShape
from gale.physics.world import World


class BodyPropertiesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 0))

    def test_position_round_trips_through_pixels(self) -> None:
        body = self.world.create_dynamic_body(123, 45)
        self.assertAlmostEqual(body.position.x, 123, places=4)
        self.assertAlmostEqual(body.position.y, 45, places=4)

    def test_set_velocity_and_read_back(self) -> None:
        body = self.world.create_dynamic_body(0, 0)
        body.set_velocity(100, -50)
        self.assertAlmostEqual(body.velocity.x, 100, places=2)
        self.assertAlmostEqual(body.velocity.y, -50, places=2)

    def test_velocity_property_setter(self) -> None:
        body = self.world.create_dynamic_body(0, 0)
        body.velocity = (10, 20)
        self.assertAlmostEqual(body.velocity.x, 10, places=2)
        self.assertAlmostEqual(body.velocity.y, 20, places=2)

    def test_apply_impulse_changes_velocity(self) -> None:
        body = self.world.create_dynamic_body(0, 0, CircleShape(radius=10))
        self.assertEqual(body.velocity.y, 0)
        body.apply_impulse(0, -1000)
        self.assertLess(body.velocity.y, 0)

    def test_user_data_round_trips(self) -> None:
        body = self.world.create_dynamic_body(0, 0)
        body.user_data = {"kind": "player"}
        self.assertEqual(body.user_data, {"kind": "player"})


class TouchingBodiesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 0))

    def test_not_touching_when_far_apart(self) -> None:
        a = self.world.create_dynamic_body(0, 0, CircleShape(radius=5))
        b = self.world.create_dynamic_body(1000, 1000, CircleShape(radius=5))
        self.world.fixed_update()
        self.assertEqual(a.touching_bodies, [])
        self.assertEqual(b.touching_bodies, [])

    def test_touching_when_overlapping(self) -> None:
        a = self.world.create_static_body(0, 0, CircleShape(radius=5))
        b = self.world.create_dynamic_body(0, 0, CircleShape(radius=5))
        self.world.fixed_update()
        self.assertIn(b, a.touching_bodies)
        self.assertIn(a, b.touching_bodies)

    def test_stops_touching_after_moving_away(self) -> None:
        a = self.world.create_static_body(0, 0, CircleShape(radius=5))
        b = self.world.create_dynamic_body(0, 0, CircleShape(radius=5))
        self.world.fixed_update()
        self.assertIn(b, a.touching_bodies)

        b.position = (10000, 10000)
        self.world.fixed_update()
        self.assertNotIn(b, a.touching_bodies)


class AddFixtureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 0))

    def test_add_box_after_creation(self) -> None:
        body = self.world.create_dynamic_body(0, 0)
        body.add_box(BoxShape(20, 20))
        other = self.world.create_dynamic_body(0, 0, CircleShape(radius=5))
        self.world.fixed_update()
        self.assertIn(other, body.touching_bodies)


if __name__ == "__main__":
    unittest.main()
