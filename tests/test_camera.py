import unittest

import pygame

from gale.camera import Camera


class CameraTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = Camera(0, 0, 100, 100)

    def test_follow(self) -> None:
        self.camera.attach_to(pygame.Vector2(10, 20))
        self.camera.update()
        self.assertEqual(-40, self.camera.x)
        self.assertEqual(-30, self.camera.y)

    def test_collision_boundaries(self):
        self.camera.set_collision_boundaries(pygame.Rect(0, 0, 200, 200))
        self.camera.attach_to(pygame.Vector2(10, 20))
        self.camera.update()
        self.assertEqual(0, self.camera.x)
        self.assertEqual(0, self.camera.y)
        self.camera.attach_to(pygame.Vector2(190, 190))
        self.camera.update()
        self.assertEqual(100, self.camera.x)
        self.assertEqual(100, self.camera.y)
