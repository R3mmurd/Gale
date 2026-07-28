import unittest

import pygame

from gale.text import Text, render_text


class RenderTextTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.font.init()
        self.font = pygame.font.Font(None, 16)
        self.surface = pygame.Surface((200, 100))

    def test_render_at_top_left_by_default(self) -> None:
        render_text(self.surface, "Hi", self.font, 10, 20, (255, 255, 255))

    def test_render_centered(self) -> None:
        render_text(
            self.surface, "Hi", self.font, 100, 50, (255, 255, 255), center=True
        )

    def test_render_with_background_color(self) -> None:
        render_text(
            self.surface,
            "Hi",
            self.font,
            0,
            0,
            (255, 255, 255),
            bgcolor=(0, 0, 0),
        )

    def test_render_shadowed_does_not_raise(self) -> None:
        render_text(self.surface, "Hi", self.font, 0, 0, (255, 255, 255), shadowed=True)


class TextTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.font.init()
        self.font = pygame.font.Font(None, 16)
        self.surface = pygame.Surface((200, 100))

    def test_render_at_top_left_positions_the_rect(self) -> None:
        text = Text("Hi", self.font, 10, 20, (255, 255, 255))
        text.render(self.surface)
        self.assertEqual(text.rect.x, 10)
        self.assertEqual(text.rect.y, 20)

    def test_render_centered_positions_the_rect_center(self) -> None:
        text = Text("Hi", self.font, 100, 50, (255, 255, 255), center=True)
        text.render(self.surface)
        self.assertEqual(text.rect.center, (100, 50))

    def test_moving_x_and_y_updates_the_rendered_position(self) -> None:
        text = Text("Hi", self.font, 0, 0, (255, 255, 255))
        text.x = 30
        text.y = 40
        text.render(self.surface)
        self.assertEqual(text.rect.topleft, (30, 40))

    def test_shadowed_text_prerenders_the_shadow_surface(self) -> None:
        text = Text("Hi", self.font, 0, 0, (255, 255, 255), shadowed=True)
        self.assertTrue(hasattr(text, "shadow_text"))
        text.render(self.surface)  # should not raise

    def test_non_shadowed_text_has_no_shadow_surface(self) -> None:
        text = Text("Hi", self.font, 0, 0, (255, 255, 255))
        self.assertFalse(hasattr(text, "shadow_text"))


if __name__ == "__main__":
    unittest.main()
