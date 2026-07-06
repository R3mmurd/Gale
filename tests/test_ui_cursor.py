import unittest

import pygame

from gale.ui.cursor import Cursor


class CursorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.display.init()
        pygame.display.set_mode((32, 32))
        self.image = pygame.Surface((8, 8))
        self.cursor = Cursor(self.image, hotspot=(2, 2))

    def tearDown(self) -> None:
        pygame.display.quit()

    def test_starts_visible(self) -> None:
        self.assertTrue(self.cursor.visible)

    def test_hide_and_show(self) -> None:
        self.cursor.hide()
        self.assertFalse(self.cursor.visible)
        self.cursor.show()
        self.assertTrue(self.cursor.visible)

    def test_render_skips_when_hidden(self) -> None:
        surface = pygame.Surface((32, 32))
        self.cursor.hide()
        # Should not raise, and should not blit anything.
        self.cursor.render(surface, (10, 10))


if __name__ == "__main__":
    unittest.main()
