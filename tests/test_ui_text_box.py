import unittest

import pygame

from gale.input_handler import MouseClickData
from gale.ui.text_box import TextBox


def click_data(released: bool) -> MouseClickData:
    event_type = pygame.MOUSEBUTTONUP if released else pygame.MOUSEBUTTONDOWN
    return MouseClickData(pygame.event.Event(event_type, button=1, pos=(0, 0)))


class TextBoxTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.closed = []
        # A wide box and short, newline-separated lines means the wrap
        # logic never has to split a line, keeping pagination predictable.
        self.text_box = TextBox(
            0,
            0,
            500,
            100,
            "Line1\nLine2\nLine3\nLine4",
            lines_per_page=2,
            on_close=lambda: self.closed.append(True),
        )

    def test_starts_on_first_page(self) -> None:
        self.assertEqual(self.text_box.page_index, 0)
        self.assertFalse(self.text_box.finished)

    def test_advance_moves_to_next_page(self) -> None:
        self.text_box.advance()
        self.assertEqual(self.text_box.page_index, 1)
        self.assertTrue(self.text_box.finished)

    def test_advance_past_last_page_closes(self) -> None:
        self.text_box.advance()
        self.text_box.advance()
        self.assertFalse(self.text_box.visible)
        self.assertEqual(self.closed, [True])

    def test_click_advances(self) -> None:
        self.text_box.on_mouse_click((10, 10), click_data(released=True))
        self.assertEqual(self.text_box.page_index, 1)


if __name__ == "__main__":
    unittest.main()
