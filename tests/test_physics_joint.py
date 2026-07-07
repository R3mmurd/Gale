import unittest

from gale.physics.shapes import BoxShape, CircleShape
from gale.physics.world import World


class RevoluteJointTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 0))
        self.anchor = self.world.create_static_body(0, 0)
        self.arm = self.world.create_dynamic_body(100, 0, BoxShape(60, 10))

    def test_motor_properties_round_trip(self) -> None:
        joint = self.world.create_revolute_joint(self.anchor, self.arm, (0, 0))
        joint.enable_motor = True
        joint.motor_speed = 2.0
        joint.max_motor_torque = 500
        self.assertTrue(joint.enable_motor)
        self.assertAlmostEqual(joint.motor_speed, 2.0)
        self.assertAlmostEqual(joint.max_motor_torque, 500)

    def test_motorized_joint_rotates_the_arm(self) -> None:
        joint = self.world.create_revolute_joint(self.anchor, self.arm, (0, 0))
        joint.enable_motor = True
        joint.motor_speed = 5.0
        joint.max_motor_torque = 10000
        start_angle = joint.angle

        for _ in range(60):
            self.world.update(1 / 60)

        self.assertNotAlmostEqual(joint.angle, start_angle, places=2)

    def test_destroy_joint(self) -> None:
        joint = self.world.create_revolute_joint(self.anchor, self.arm, (0, 0))
        self.world.destroy_joint(joint)
        # Bodies should now be free to separate without the constraint;
        # absence of an exception is the main thing being verified.
        self.world.update(1 / 60)


class WheelJointTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.world = World(gravity=(0, 900))
        self.chassis = self.world.create_dynamic_body(200, 200, BoxShape(60, 20))
        self.wheel = self.world.create_dynamic_body(
            220, 220, CircleShape(radius=10, friction=1.0)
        )

    def test_spring_properties_round_trip(self) -> None:
        joint = self.world.create_wheel_joint(
            self.chassis,
            self.wheel,
            self.wheel.position,
            frequencyHz=4,
            dampingRatio=0.7,
        )
        self.assertAlmostEqual(joint.frequency, 4.0, places=2)
        self.assertAlmostEqual(joint.damping_ratio, 0.7, places=2)

    def test_wheel_stays_attached_to_chassis(self) -> None:
        joint = self.world.create_wheel_joint(
            self.chassis,
            self.wheel,
            self.wheel.position,
            frequencyHz=4,
            dampingRatio=0.7,
        )
        start_distance = (self.chassis.position - self.wheel.position).length()

        for _ in range(120):
            self.world.update(1 / 60)

        end_distance = (self.chassis.position - self.wheel.position).length()
        # The suspension can stretch/compress a little, but the wheel
        # should stay roughly the same distance from the chassis, not
        # fall away freely under gravity.
        self.assertLess(abs(end_distance - start_distance), 15)

    def test_motor_drives_the_wheel(self) -> None:
        joint = self.world.create_wheel_joint(
            self.chassis,
            self.wheel,
            self.wheel.position,
            frequencyHz=4,
            dampingRatio=0.7,
        )
        joint.enable_motor = True
        joint.motor_speed = -20
        joint.max_motor_torque = 1000

        for _ in range(30):
            self.world.update(1 / 60)

        self.assertLess(self.wheel.angular_velocity, 0)


if __name__ == "__main__":
    unittest.main()
