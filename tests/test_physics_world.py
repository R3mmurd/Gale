import unittest

from gale.physics.body_type import BodyType
from gale.physics.shapes import BoxShape, CircleShape
from gale.physics.world import World


class BodyCreationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 900))

    def test_create_each_body_type(self) -> None:
        static = self.world.create_static_body(10, 20)
        dynamic = self.world.create_dynamic_body(30, 40)
        kinematic = self.world.create_kinematic_body(50, 60)
        self.assertEqual(static.body_type, BodyType.STATIC)
        self.assertEqual(dynamic.body_type, BodyType.DYNAMIC)
        self.assertEqual(kinematic.body_type, BodyType.KINEMATIC)
        self.assertAlmostEqual(static.position.x, 10, places=3)
        self.assertAlmostEqual(dynamic.position.y, 40, places=3)

    def test_shape_attached_immediately(self) -> None:
        body = self.world.create_dynamic_body(0, 0, CircleShape(radius=10))
        # No direct fixture accessor, but a second overlapping body
        # should register a contact, proving a fixture exists.
        other = self.world.create_dynamic_body(0, 0, CircleShape(radius=10))
        self.world.fixed_update()
        self.assertIn(other, body.touching_bodies)

    def test_destroy_body(self) -> None:
        body = self.world.create_dynamic_body(0, 0, CircleShape(radius=10))
        body.destroy()
        # No direct way to assert it's gone except that further use
        # doesn't crash the world stepping.
        self.world.update(1 / 60)


class FixedTimestepTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 900), fixed_timestep=1 / 60)

    def test_static_body_never_moves(self) -> None:
        body = self.world.create_static_body(100, 100, BoxShape(10, 10))
        for _ in range(60):
            self.world.update(1 / 60)
        self.assertAlmostEqual(body.position.x, 100, places=3)
        self.assertAlmostEqual(body.position.y, 100, places=3)

    def test_dynamic_body_falls_under_gravity(self) -> None:
        body = self.world.create_dynamic_body(100, 0, CircleShape(radius=5))
        start_y = body.position.y
        self.world.update(1.0)
        self.assertGreater(body.position.y, start_y)

    def test_kinematic_body_moves_exactly_per_velocity(self) -> None:
        body = self.world.create_kinematic_body(0, 0, BoxShape(10, 10))
        body.set_velocity(50, 0)
        self.world.update(1.0)
        # update(1.0)'s accumulator resolves to either 59 or 60 fixed
        # steps of 1/60s depending on float rounding right at that
        # exact boundary (1/60 isn't exactly representable) — both are
        # correct, so the tolerance covers one step's worth of motion
        # (50px/s / 60 ~= 0.83px) plus margin.
        self.assertAlmostEqual(body.position.x, 50, delta=1.0)

    def test_accumulator_counts_fixed_updates_correctly(self) -> None:
        calls = []
        original = self.world.fixed_update
        self.world.fixed_update = lambda: (calls.append(1), original())[1]

        # Several small dts that individually don't reach one
        # fixed_timestep (1/60 ~= 0.0167) should still accumulate.
        for _ in range(10):
            self.world.update(0.005)

        # 10 * 0.005 = 0.05s -> floor(0.05 / (1/60)) = 3 fixed steps.
        self.assertEqual(len(calls), 3)

    def test_fixed_update_is_public_and_directly_callable(self) -> None:
        body = self.world.create_dynamic_body(100, 0, CircleShape(radius=5))
        start_y = body.position.y
        self.world.fixed_update()
        self.assertGreater(body.position.y, start_y)


class CollisionCallbackTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 0))

    def test_begin_and_end_fire(self) -> None:
        begins = []
        ends = []
        self.world.on_collision_begin(lambda a, b: begins.append((a, b)))
        self.world.on_collision_end(lambda a, b: ends.append((a, b)))

        a = self.world.create_static_body(0, 0, CircleShape(radius=10, is_sensor=True))
        b = self.world.create_dynamic_body(0, 0, CircleShape(radius=10))
        b.set_velocity(100, 0)

        for _ in range(120):
            self.world.update(1 / 60)

        self.assertGreaterEqual(len(begins), 1)
        self.assertGreaterEqual(len(ends), 1)
        self.assertEqual({begins[0][0], begins[0][1]}, {a, b})


if __name__ == "__main__":
    unittest.main()
