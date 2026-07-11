import math
import unittest

import pygame

from gale.ai.blackboard import Blackboard
from gale.ai.perception import AlertLevel, Perception, VisionCone, has_line_of_sight
from gale.ai.steering import Kinematic


class HasLineOfSightTestCase(unittest.TestCase):
    def test_no_obstacles_is_always_visible(self) -> None:
        self.assertTrue(has_line_of_sight(pygame.Vector2(0, 0), pygame.Vector2(100, 0)))

    def test_clear_segment_is_visible(self) -> None:
        wall = pygame.Rect(0, 50, 100, 20)
        self.assertTrue(
            has_line_of_sight(pygame.Vector2(0, 0), pygame.Vector2(100, 0), [wall])
        )

    def test_blocked_segment_is_not_visible(self) -> None:
        wall = pygame.Rect(50, -10, 10, 20)
        self.assertFalse(
            has_line_of_sight(pygame.Vector2(0, 0), pygame.Vector2(100, 0), [wall])
        )


class VisionConeCanSeePointTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = Kinematic(0, 0, orientation=0)
        self.cone = VisionCone(
            self.guard, range_near=50, range_far=200, half_angle=math.radians(30)
        )

    def test_point_ahead_within_range_and_angle_is_visible(self) -> None:
        self.assertTrue(self.cone.can_see_point(pygame.Vector2(100, 0)))

    def test_point_outside_angle_is_not_visible(self) -> None:
        self.assertFalse(self.cone.can_see_point(pygame.Vector2(0, 100)))

    def test_point_outside_far_range_is_not_visible(self) -> None:
        self.assertFalse(self.cone.can_see_point(pygame.Vector2(300, 0)))

    def test_point_blocked_by_obstacle_is_not_visible(self) -> None:
        wall = pygame.Rect(40, -10, 10, 20)
        self.assertFalse(
            self.cone.can_see_point(pygame.Vector2(100, 0), obstacles=[wall])
        )

    def test_origin_point_is_visible(self) -> None:
        self.assertTrue(self.cone.can_see_point(pygame.Vector2(0, 0)))

    def test_cone_follows_kinematic_orientation(self) -> None:
        self.guard.orientation = math.pi / 2
        self.assertTrue(self.cone.can_see_point(pygame.Vector2(0, 100)))
        self.assertFalse(self.cone.can_see_point(pygame.Vector2(100, 0)))


class VisionConeAwarenessGainTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = Kinematic(0, 0, orientation=0)
        self.cone = VisionCone(
            self.guard, range_near=50, range_far=200, half_angle=math.radians(30)
        )

    def test_full_gain_within_near_range(self) -> None:
        gain = self.cone.awareness_gain(pygame.Vector2(30, 0), dt=1.0)
        self.assertAlmostEqual(gain, 1.0)

    def test_reduced_gain_within_far_band(self) -> None:
        gain = self.cone.awareness_gain(pygame.Vector2(125, 0), dt=1.0)
        self.assertTrue(0 < gain < 1.0)

    def test_gain_decreases_towards_far_range(self) -> None:
        near_far_gain = self.cone.awareness_gain(pygame.Vector2(60, 0), dt=1.0)
        far_gain = self.cone.awareness_gain(pygame.Vector2(190, 0), dt=1.0)
        self.assertGreater(near_far_gain, far_gain)

    def test_no_gain_outside_range(self) -> None:
        gain = self.cone.awareness_gain(pygame.Vector2(300, 0), dt=1.0)
        self.assertEqual(gain, 0.0)

    def test_no_gain_when_blocked(self) -> None:
        wall = pygame.Rect(40, -10, 10, 20)
        gain = self.cone.awareness_gain(
            pygame.Vector2(100, 0), dt=1.0, obstacles=[wall]
        )
        self.assertEqual(gain, 0.0)

    def test_no_gain_outside_angle(self) -> None:
        gain = self.cone.awareness_gain(pygame.Vector2(0, 100), dt=1.0)
        self.assertEqual(gain, 0.0)


class PerceptionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = Kinematic(0, 0, orientation=0)
        self.cone = VisionCone(
            self.guard, range_near=50, range_far=200, half_angle=math.radians(30)
        )
        self.blackboard = Blackboard()
        self.perception = Perception(
            [self.cone],
            self.blackboard,
            decay_rate=0.5,
            suspicious_threshold=0.3,
            alerted_threshold=1.0,
        )

    def test_builds_up_to_alerted_when_target_stays_visible(self) -> None:
        target = pygame.Vector2(30, 0)

        for _ in range(5):
            level = self.perception.update(1.0, target)

        self.assertEqual(level, AlertLevel.ALERTED)
        self.assertEqual(self.blackboard.get("alert_level"), AlertLevel.ALERTED)

    def test_becomes_suspicious_before_alerted(self) -> None:
        target = pygame.Vector2(100, 0)
        level = self.perception.update(1.0, target)
        self.assertEqual(level, AlertLevel.SUSPICIOUS)

    def test_stays_unaware_when_never_seen(self) -> None:
        target = pygame.Vector2(0, 100)
        level = self.perception.update(1.0, target)
        self.assertEqual(level, AlertLevel.UNAWARE)
        self.assertFalse(self.blackboard.has("last_known_target_position"))

    def test_awareness_decays_when_target_lost(self) -> None:
        target = pygame.Vector2(30, 0)
        self.perception.update(1.0, target)
        self.assertGreater(self.perception.awareness, 0)

        hidden_target = pygame.Vector2(0, 100)
        self.perception.update(1.0, hidden_target)
        self.assertLess(self.perception.awareness, 1.0)

    def test_writes_last_known_target_position_while_alerted(self) -> None:
        target = pygame.Vector2(30, 0)
        self.perception.update(1.0, target)
        self.assertEqual(
            self.blackboard.get("last_known_target_position"), pygame.Vector2(30, 0)
        )

    def test_writes_awareness_key(self) -> None:
        target = pygame.Vector2(30, 0)
        self.perception.update(1.0, target)
        self.assertEqual(self.blackboard.get("awareness"), self.perception.awareness)


if __name__ == "__main__":
    unittest.main()
