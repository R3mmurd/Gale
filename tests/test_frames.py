import unittest

from pygame.surface import Surface

from gale.frames import generate_frames


class AnimationTestCase(unittest.TestCase):
    def test_frame_generation(self) -> None:
        result = generate_frames(Surface((80, 160)), 16, 16)
        self.assertEqual(len(result), 50)
