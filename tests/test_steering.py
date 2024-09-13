import unittest

import pygame

from gale import steering


class Agent:
    def __init__(
        self,
        position: pygame.Vector2,
        velocity: pygame.Vector2,
        max_speed: float,
        angle: float = 0,
    ) -> None:
        self.position = position
        self.velocity = velocity
        self.max_speed = max_speed
        self.angle = angle


class SeekTestCase(unittest.TestCase):

    def test_seek(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        target = Agent(pygame.Vector2(1, 1), pygame.Vector2(0, 0), 1)
        seek = steering.Seek(agent, target)
        result = seek.calculate()
        self.assertEqual(pygame.Vector2(0.7071067811865476, 0.7071067811865476), result)


class FleeTestCase(unittest.TestCase):

    def test_flee(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        target = Agent(pygame.Vector2(1, 1), pygame.Vector2(0, 0), 1)
        flee = steering.Flee(agent, target)
        result = flee.calculate()
        self.assertEqual(pygame.Vector2(-0.707106, -0.707106), result)


class ArrivalTestCase(unittest.TestCase):

    def test_arrival(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        target = Agent(pygame.Vector2(1, 1), pygame.Vector2(0, 0), 1)
        arrival = steering.Arrival(agent, target, 1)
        result = arrival.calculate()
        self.assertEqual(result, pygame.Vector2(0.707106, 0.707106))


class WanderTestCase(unittest.TestCase):

    def test_wander(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        wander = steering.Wander(agent, 1, 1, 1)
        result = wander.calculate()
        self.assertEqual(result, pygame.Vector2(0.924646, 0.380828))


class PursueTestCase(unittest.TestCase):

    def test_pursue(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        target = Agent(pygame.Vector2(1, 1), pygame.Vector2(0, 0), 1)
        pursue = steering.Pursue(agent, target)
        result = pursue.calculate()
        self.assertEqual(result, pygame.Vector2(0.707106, 0.707106))


class EvadeTestCase(unittest.TestCase):

    def test_evade(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        target = Agent(pygame.Vector2(1, 1), pygame.Vector2(0, 0), 1)
        evade = steering.Evade(agent, target)
        result = evade.calculate()
        self.assertEqual(result, pygame.Vector2(-0.707106, -0.707106))


class AvoidTestCase(unittest.TestCase):

    def test_avoid(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        obstacles = [Agent(pygame.Vector2(1, 1), pygame.Vector2(0, 0), 1)]
        avoid = steering.Avoid(agent, obstacles)
        result = avoid.calculate()
        self.assertEqual(result, pygame.Vector2(-0.707107, -0.707107))


class FollowPathTestCase(unittest.TestCase):

    def test_follow_path(self) -> None:
        agent = Agent(pygame.Vector2(0, 0), pygame.Vector2(0, 0), 1)
        path = [pygame.Vector2(1, 1), pygame.Vector2(2, 2)]
        follow_path = steering.FollowPath(agent, path)
        result = follow_path.calculate()
        self.assertEqual(result, pygame.Vector2(0.707107, 0.707107))
