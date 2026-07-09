import unittest

import pygame

from gale.camera import Camera


class Target:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class CameraTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.camera = Camera(800, 600)

    def test_offset_centers_the_viewport_on_x_y(self) -> None:
        self.assertEqual(self.camera.offset, (-400.0, -300.0))

    def test_world_to_screen_at_center(self) -> None:
        self.assertEqual(self.camera.world_to_screen((0, 0)), (400.0, 300.0))

    def test_screen_to_world_is_the_inverse_of_world_to_screen(self) -> None:
        point = (123.0, 456.0)
        self.assertEqual(
            self.camera.screen_to_world(self.camera.world_to_screen(point)), point
        )

    def test_zoom_scales_world_to_screen(self) -> None:
        self.camera.zoom = 2.0
        self.assertEqual(self.camera.world_to_screen((0, 0)), (400.0, 300.0))
        self.assertEqual(self.camera.world_to_screen((100, 0)), (600.0, 300.0))

    def test_apply_translates_and_scales_a_rect(self) -> None:
        self.camera.zoom = 2.0
        rect = pygame.Rect(10, 10, 20, 20)
        applied = self.camera.apply(rect)
        self.assertEqual(applied.size, (40, 40))

    def test_follow_snaps_by_default(self) -> None:
        target = Target(1000, 500)
        self.camera.follow(target)
        self.camera.update(1 / 60)
        self.assertEqual((self.camera.x, self.camera.y), (1000, 500))

    def test_follow_with_rate_moves_gradually(self) -> None:
        target = Target(1000, 0)
        self.camera.follow(target, rate=6.0)
        self.camera.update(1 / 60)
        self.assertGreater(self.camera.x, 0)
        self.assertLess(self.camera.x, 1000)

    def test_follow_with_rate_converges_over_time(self) -> None:
        target = Target(1000, 0)
        self.camera.follow(target, rate=6.0)
        for _ in range(600):
            self.camera.update(1 / 60)
        self.assertAlmostEqual(self.camera.x, 1000, delta=1.0)

    def test_unfollow_stops_tracking(self) -> None:
        target = Target(1000, 500)
        self.camera.follow(target)
        self.camera.unfollow()
        self.camera.update(1 / 60)
        self.assertEqual((self.camera.x, self.camera.y), (0.0, 0.0))

    def test_shake_offsets_and_decays_to_zero(self) -> None:
        self.camera.shake(50, 1.0)
        self.camera.update(0.1)
        offset_x, offset_y = self.camera._shake_offset
        self.assertTrue(abs(offset_x) <= 50 and abs(offset_y) <= 50)
        self.camera.update(1.0)
        self.assertEqual(self.camera._shake_offset, (0.0, 0.0))

    def test_bounds_clamp_camera_position(self) -> None:
        self.camera.bounds = pygame.Rect(0, 0, 1000, 1000)
        self.camera.x = 2000
        self.camera.y = 2000
        self.camera.update(1 / 60)
        self.assertEqual(self.camera.x, 1000 - 400)
        self.assertEqual(self.camera.y, 1000 - 300)

    def test_bounds_smaller_than_viewport_center_camera(self) -> None:
        self.camera.bounds = pygame.Rect(0, 0, 200, 100)
        self.camera.x = 2000
        self.camera.update(1 / 60)
        self.assertEqual(self.camera.x, 100.0)
        self.assertEqual(self.camera.y, 50.0)

    def test_bounds_do_not_clamp_when_camera_already_inside(self) -> None:
        self.camera.bounds = pygame.Rect(0, 0, 10000, 10000)
        self.camera.x = 5000
        self.camera.y = 5000
        self.camera.update(1 / 60)
        self.assertEqual((self.camera.x, self.camera.y), (5000, 5000))


if __name__ == "__main__":
    unittest.main()
