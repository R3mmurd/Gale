import unittest

from gale.animation import Animation


class AnimationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.infinite_animation = Animation([1, 2, 3], 0.1)
        self.limited_animation = Animation([4, 5, 6], 0.2, 5)

    def test_initialization_infinite_loops(self) -> None:
        self.assertEqual(self.infinite_animation.get_current_frame(), 1)
        self.assertEqual(self.infinite_animation.interval, 0.1)
        self.assertListEqual(self.infinite_animation.frames, [1, 2, 3])
        self.assertIsNone(self.infinite_animation.loops)

    def test_initialization_limited_loops(self) -> None:
        self.assertEqual(self.limited_animation.get_current_frame(), 4)
        self.assertEqual(self.limited_animation.interval, 0.2)
        self.assertListEqual(self.limited_animation.frames, [4, 5, 6])
        self.assertEqual(self.limited_animation.loops, 5)

    def test_change_frame(self) -> None:
        self.infinite_animation.update(0.1)
        self.assertEqual(self.infinite_animation.get_current_frame(), 2)
        self.limited_animation.update(0.2)
        self.assertEqual(self.limited_animation.get_current_frame(), 5)
    
    def test_no_change_frame(self) -> None:
        self.infinite_animation.update(0.09)
        self.assertEqual(self.infinite_animation.get_current_frame(), 1)
        self.limited_animation.update(0.19)
        self.assertEqual(self.limited_animation.get_current_frame(), 4)
    
    def test_times_played(self) -> None:
        for _ in range(3):
            self.infinite_animation.update(0.1)
            self.limited_animation.update(0.2)
        self.assertEqual(self.infinite_animation.times_played, 0)
        self.assertEqual(self.limited_animation.times_played, 1)
    
    def test_loop(self) -> None:
        for _ in range(3):
            self.infinite_animation.update(0.1)
            self.limited_animation.update(0.2)
        self.assertEqual(self.infinite_animation.get_current_frame(), 1)
        self.assertEqual(self.limited_animation.get_current_frame(), 4)

    def test_loops(self) -> None:
        # 6 times played
        for _ in range(3 * 6 + 1):
            self.infinite_animation.update(0.1)
            self.limited_animation.update(0.2)
        self.assertEqual(self.infinite_animation.get_current_frame(), 2)
        self.assertEqual(self.limited_animation.get_current_frame(), 4)
