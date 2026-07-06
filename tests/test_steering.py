import math
import unittest

import pygame

from gale.ai.steering import (
    Align,
    Arrive,
    BlendedSteering,
    Evade,
    Flee,
    Kinematic,
    Obstacle,
    ObstacleAvoidance,
    PrioritySteering,
    Pursue,
    Seek,
    Separation,
    SteeringOutput,
    VelocityMatch,
    Wander,
)


class KinematicTestCase(unittest.TestCase):
    def test_update_integrates_position_and_velocity(self) -> None:
        character = Kinematic(0, 0, max_speed=100)
        character.update(SteeringOutput(linear=(10, 0)), 1)
        self.assertEqual(character.velocity.x, 10)
        self.assertEqual(character.position.x, 0)
        character.update(SteeringOutput(), 1)
        self.assertEqual(character.position.x, 10)

    def test_velocity_is_clamped_to_max_speed(self) -> None:
        character = Kinematic(0, 0, max_speed=5)
        character.update(SteeringOutput(linear=(100, 0)), 1)
        self.assertAlmostEqual(character.velocity.length(), 5)

    def test_vector_to_orientation_of_zero_vector_is_zero(self) -> None:
        self.assertEqual(Kinematic.vector_to_orientation(pygame.Vector2(0, 0)), 0)


class SeekFleeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.character = Kinematic(0, 0, max_acceleration=10)
        self.target = Kinematic(10, 0)

    def test_seek_accelerates_towards_target(self) -> None:
        steering = Seek(self.character, self.target).get_steering()
        self.assertAlmostEqual(steering.linear.x, 10)
        self.assertAlmostEqual(steering.linear.y, 0)

    def test_flee_accelerates_away_from_target(self) -> None:
        steering = Flee(self.character, self.target).get_steering()
        self.assertAlmostEqual(steering.linear.x, -10)

    def test_seek_on_top_of_target_does_not_accelerate(self) -> None:
        steering = Seek(self.character, Kinematic(0, 0)).get_steering()
        self.assertEqual(steering.linear.length(), 0)


class ArriveTestCase(unittest.TestCase):
    def test_arrive_stops_within_target_radius(self) -> None:
        character = Kinematic(0, 0, max_speed=100, max_acceleration=100)
        target = Kinematic(1, 0)
        steering = Arrive(character, target, target_radius=5).get_steering()
        self.assertEqual(steering.linear.length(), 0)

    def test_arrive_slows_down_within_slow_radius(self) -> None:
        character = Kinematic(0, 0, max_speed=100, max_acceleration=1000)
        target = Kinematic(10, 0)
        steering = Arrive(
            character, target, target_radius=1, slow_radius=100
        ).get_steering()
        self.assertGreater(steering.linear.x, 0)


class AlignTestCase(unittest.TestCase):
    def test_align_returns_zero_within_target_radius(self) -> None:
        character = Kinematic(0, 0, orientation=0)
        target = Kinematic(0, 0, orientation=0.001)
        steering = Align(character, target, target_radius=0.05).get_steering()
        self.assertEqual(steering.angular, 0)

    def test_align_rotates_towards_shortest_path(self) -> None:
        character = Kinematic(0, 0, orientation=0)
        target = Kinematic(0, 0, orientation=math.pi - 0.1)
        steering = Align(character, target).get_steering()
        self.assertGreater(steering.angular, 0)


class VelocityMatchTestCase(unittest.TestCase):
    def test_matches_target_velocity(self) -> None:
        character = Kinematic(0, 0, max_acceleration=1000)
        target = Kinematic(0, 0)
        target.velocity.x = 50
        steering = VelocityMatch(character, target, time_to_target=0.5).get_steering()
        self.assertAlmostEqual(steering.linear.x, 100)


class PursueEvadeTestCase(unittest.TestCase):
    def test_pursue_targets_predicted_position(self) -> None:
        character = Kinematic(0, 0, max_acceleration=10)
        target = Kinematic(10, 0)
        target.velocity.y = 10
        pursue = Pursue(character, target, max_prediction=1)
        steering = pursue.get_steering()
        self.assertGreater(steering.linear.y, 0)

    def test_evade_moves_away_from_predicted_position(self) -> None:
        character = Kinematic(0, 0, max_acceleration=10)
        target = Kinematic(10, 0)
        evade = Evade(character, target, max_prediction=1)
        steering = evade.get_steering()
        self.assertLess(steering.linear.x, 0)


class WanderTestCase(unittest.TestCase):
    def test_wander_produces_non_zero_acceleration(self) -> None:
        character = Kinematic(0, 0, max_acceleration=50)
        wander = Wander(character)
        steering = wander.get_steering(0.1)
        self.assertGreater(steering.linear.length(), 0)


class SeparationTestCase(unittest.TestCase):
    def test_separation_pushes_away_from_close_targets(self) -> None:
        character = Kinematic(0, 0, max_acceleration=100)
        close = Kinematic(1, 0)
        far = Kinematic(1000, 0)
        steering = Separation(
            character, [character, close, far], threshold=50
        ).get_steering()
        self.assertLess(steering.linear.x, 0)


class ObstacleAvoidanceTestCase(unittest.TestCase):
    def test_avoids_obstacle_ahead(self) -> None:
        character = Kinematic(0, 0, max_acceleration=100)
        character.velocity.x = 10
        obstacle = Obstacle(20, 0, radius=5)
        steering = ObstacleAvoidance(
            character, [obstacle], avoid_margin=5, lookahead=100
        ).get_steering()
        self.assertGreater(steering.linear.length(), 0)

    def test_ignores_obstacle_out_of_the_way(self) -> None:
        character = Kinematic(0, 0, max_acceleration=100)
        character.velocity.x = 10
        obstacle = Obstacle(20, 100, radius=5)
        steering = ObstacleAvoidance(
            character, [obstacle], avoid_margin=5, lookahead=100
        ).get_steering()
        self.assertEqual(steering.linear.length(), 0)


class BlendedAndPriorityTestCase(unittest.TestCase):
    def test_blended_steering_sums_weighted_outputs(self) -> None:
        character = Kinematic(0, 0, max_acceleration=1000)
        target = Kinematic(10, 0)
        blended = BlendedSteering(
            character,
            [
                (Seek(character, target), 0.25),
                (Seek(character, target), 0.25),
            ],
        )
        plain = Seek(character, target).get_steering()
        steering = blended.get_steering()
        self.assertAlmostEqual(steering.linear.x, plain.linear.x * 0.5)

    def test_blended_steering_clamps_to_max_acceleration(self) -> None:
        character = Kinematic(0, 0, max_acceleration=1000)
        target = Kinematic(10, 0)
        blended = BlendedSteering(
            character,
            [
                (Seek(character, target), 1),
                (Seek(character, target), 1),
            ],
        )
        steering = blended.get_steering()
        self.assertAlmostEqual(steering.linear.length(), character.max_acceleration)

    def test_priority_steering_falls_back_to_next_group(self) -> None:
        character = Kinematic(0, 0, max_acceleration=100)
        target = Kinematic(0, 0)  # on top of character: zero output
        fallback_target = Kinematic(10, 0)
        priority = PrioritySteering(
            character,
            [
                [(Seek(character, target), 1)],
                [(Seek(character, fallback_target), 1)],
            ],
        )
        steering = priority.get_steering()
        self.assertGreater(steering.linear.length(), 0)
