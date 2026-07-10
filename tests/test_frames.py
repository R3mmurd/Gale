import unittest

import pygame
from pygame.surface import Surface

from gale.frames import generate_frames


class AnimationTestCase(unittest.TestCase):
    def test_frame_generation(self) -> None:
        result = generate_frames(Surface((80, 160)), 16, 16)
        self.assertEqual(len(result), 50)

    def test_frame_generation_with_margin_and_spacing(self) -> None:
        # margin=1, spacing=1, 2x2 tiles of 16x16: 1 + 16 + 1 + 16 + 1 = 35
        result = generate_frames(Surface((35, 35)), 16, 16, margin=1, spacing=1)
        self.assertEqual(
            result,
            [
                pygame.Rect(1, 1, 16, 16),
                pygame.Rect(18, 1, 16, 16),
                pygame.Rect(1, 18, 16, 16),
                pygame.Rect(18, 18, 16, 16),
            ],
        )
