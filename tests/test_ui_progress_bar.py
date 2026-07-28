import unittest

import pygame

from gale.ui.progress_bar import ProgressBar
from gale.ui.theme import Theme


class ProgressBarTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.theme = Theme(
            background_color=pygame.Color(10, 10, 10),
            border_color=pygame.Color(20, 20, 20),
            border_width=1,
            accent_color=pygame.Color(90, 200, 255),
        )

    def test_defaults(self) -> None:
        bar = ProgressBar(0, 0, 100, 10)
        self.assertEqual(bar.value, 0)
        self.assertEqual(bar.max_value, 100)

    def test_half_filled_bar_fills_half_its_width(self) -> None:
        bar = ProgressBar(0, 0, 100, 10, value=50, max_value=100, theme=self.theme)
        surface = pygame.Surface((100, 10))
        bar.render(surface)
        self.assertEqual(surface.get_at((10, 5))[:3], (90, 200, 255))
        self.assertEqual(surface.get_at((90, 5))[:3], (10, 10, 10))

    def test_full_bar_fills_the_entire_width(self) -> None:
        bar = ProgressBar(0, 0, 100, 10, value=100, max_value=100, theme=self.theme)
        surface = pygame.Surface((100, 10))
        bar.render(surface)
        self.assertEqual(surface.get_at((95, 5))[:3], (90, 200, 255))

    def test_value_above_max_is_clamped_to_full(self) -> None:
        bar = ProgressBar(0, 0, 100, 10, value=1000, max_value=100, theme=self.theme)
        surface = pygame.Surface((100, 10))
        bar.render(surface)
        self.assertEqual(surface.get_at((95, 5))[:3], (90, 200, 255))

    def test_negative_value_is_clamped_to_empty(self) -> None:
        bar = ProgressBar(0, 0, 100, 10, value=-50, max_value=100, theme=self.theme)
        surface = pygame.Surface((100, 10))
        bar.render(surface)
        self.assertEqual(surface.get_at((5, 5))[:3], (10, 10, 10))

    def test_zero_max_value_does_not_raise_and_stays_empty(self) -> None:
        bar = ProgressBar(0, 0, 100, 10, value=10, max_value=0, theme=self.theme)
        surface = pygame.Surface((100, 10))
        bar.render(surface)
        self.assertEqual(surface.get_at((5, 5))[:3], (10, 10, 10))

    def test_custom_fill_color_overrides_theme_accent(self) -> None:
        bar = ProgressBar(
            0, 0, 100, 10, value=50, color=pygame.Color(255, 0, 0), theme=self.theme
        )
        surface = pygame.Surface((100, 10))
        bar.render(surface)
        self.assertEqual(surface.get_at((10, 5))[:3], (255, 0, 0))

    def test_hidden_bar_does_not_render(self) -> None:
        bar = ProgressBar(0, 0, 100, 10, value=100, theme=self.theme)
        bar.visible = False
        surface = pygame.Surface((100, 10))
        surface.fill((1, 2, 3))
        bar.render(surface)
        self.assertEqual(surface.get_at((10, 5))[:3], (1, 2, 3))


if __name__ == "__main__":
    unittest.main()
