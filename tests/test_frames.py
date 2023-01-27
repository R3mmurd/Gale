import unittest
from typing import Tuple

from gale.frames import generate_frames


class SpriteSheetSimulation:
    def get_size(self) -> Tuple[int, int]:
        return 80, 160


class AnimationTestCase(unittest.TestCase):
    def test_frame_generation(self) -> None:
        result = generate_frames(SpriteSheetSimulation(), 16, 16)
        # Ten rows by five columns
        self.assertEqual(len(result), 50)
