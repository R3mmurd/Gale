import unittest

import pygame

from gale.ai.targeting import (
    ballistic_position,
    iterative_targeting_angle,
    predict_intercept_time,
    simulate_drag_trajectory,
)


class PredictInterceptTimeTestCase(unittest.TestCase):
    def test_stationary_target_is_intercepted_at_distance_over_speed(self) -> None:
        t = predict_intercept_time(
            pygame.Vector2(0, 0), pygame.Vector2(100, 0), pygame.Vector2(0, 0), 50
        )
        self.assertAlmostEqual(t, 2.0)

    def test_none_when_target_outruns_the_projectile(self) -> None:
        t = predict_intercept_time(
            pygame.Vector2(0, 0), pygame.Vector2(100, 0), pygame.Vector2(1000, 0), 10
        )
        self.assertIsNone(t)

    def test_none_with_non_positive_speed(self) -> None:
        t = predict_intercept_time(
            pygame.Vector2(0, 0), pygame.Vector2(100, 0), pygame.Vector2(0, 0), 0
        )
        self.assertIsNone(t)

    def test_moving_target_is_intercepted_ahead_of_its_current_position(self) -> None:
        t = predict_intercept_time(
            pygame.Vector2(0, 0), pygame.Vector2(100, 0), pygame.Vector2(0, 10), 50
        )
        self.assertIsNotNone(t)
        self.assertGreater(t, 2.0)


class BallisticPositionTestCase(unittest.TestCase):
    def test_matches_free_fall_formula(self) -> None:
        origin = pygame.Vector2(0, 0)
        velocity = pygame.Vector2(10, 0)
        gravity = pygame.Vector2(0, 100)
        position = ballistic_position(origin, velocity, gravity, t=2)
        self.assertAlmostEqual(position.x, 20)
        self.assertAlmostEqual(position.y, 200)


class SimulateDragTrajectoryTestCase(unittest.TestCase):
    def test_returns_steps_plus_one_points(self) -> None:
        trajectory = simulate_drag_trajectory(
            pygame.Vector2(0, 0),
            pygame.Vector2(10, 0),
            pygame.Vector2(0, 10),
            drag=0.1,
            dt=0.1,
            steps=5,
        )
        self.assertEqual(len(trajectory), 6)
        self.assertEqual(trajectory[0], pygame.Vector2(0, 0))

    def test_zero_drag_falls_faster_over_time(self) -> None:
        no_drag = simulate_drag_trajectory(
            pygame.Vector2(0, 0),
            pygame.Vector2(10, 0),
            pygame.Vector2(0, 50),
            drag=0.0,
            dt=0.1,
            steps=10,
        )
        with_drag = simulate_drag_trajectory(
            pygame.Vector2(0, 0),
            pygame.Vector2(10, 0),
            pygame.Vector2(0, 50),
            drag=2.0,
            dt=0.1,
            steps=10,
        )
        self.assertGreater(no_drag[-1].y, with_drag[-1].y)


class IterativeTargetingAngleTestCase(unittest.TestCase):
    def test_none_when_origin_equals_target(self) -> None:
        angle = iterative_targeting_angle(
            pygame.Vector2(0, 0), pygame.Vector2(0, 0), 100, pygame.Vector2(0, 50)
        )
        self.assertIsNone(angle)

    def test_finds_an_angle_that_lands_reasonably_close(self) -> None:
        origin = pygame.Vector2(0, 0)
        target = pygame.Vector2(200, 0)
        gravity = pygame.Vector2(0, 100)
        angle = iterative_targeting_angle(
            origin, target, speed=150, gravity=gravity, iterations=12
        )
        self.assertIsNotNone(angle)

        import math

        # Rotate the found angle (relative to the straight line to the
        # target) back into world space to check it actually lands
        # near the target.
        base = math.atan2((target - origin).y, (target - origin).x)
        world_direction = pygame.Vector2(math.cos(base + angle), math.sin(base + angle))
        trajectory = simulate_drag_trajectory(
            origin, world_direction * 150, gravity, drag=0.0, dt=1 / 60, steps=300
        )
        closest = min(trajectory, key=lambda p: (p - target).length())
        self.assertLess((closest - target).length(), 20)


if __name__ == "__main__":
    unittest.main()
