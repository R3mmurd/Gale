import unittest

import pygame

from gale.input_handler import MouseClickData
from gale.ui.text_box import PaginatedTextBox, TextBox


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

    def test_next_page_does_not_auto_close(self) -> None:
        self.assertTrue(self.text_box.next_page())
        self.assertEqual(self.text_box.page_index, 1)
        self.assertFalse(self.text_box.next_page())
        self.assertEqual(self.text_box.page_index, 1)
        self.assertTrue(self.text_box.visible)
        self.assertEqual(self.closed, [])

    def test_previous_page(self) -> None:
        self.assertFalse(self.text_box.previous_page())
        self.text_box.next_page()
        self.assertTrue(self.text_box.previous_page())
        self.assertEqual(self.text_box.page_index, 0)

    def test_has_next_and_previous_page(self) -> None:
        self.assertFalse(self.text_box.has_previous_page)
        self.assertTrue(self.text_box.has_next_page)
        self.text_box.next_page()
        self.assertTrue(self.text_box.has_previous_page)
        self.assertFalse(self.text_box.has_next_page)


class PaginatedTextBoxTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.box = PaginatedTextBox(
            0, 0, 500, 100, "Line1\nLine2\nLine3\nLine4", lines_per_page=2
        )

    def test_previous_button_starts_disabled(self) -> None:
        self.assertFalse(self.box.previous_button.enabled)
        self.assertTrue(self.box.next_button.enabled)

    def test_next_button_advances_and_disables_at_last_page(self) -> None:
        self.box.next_button.on_click()
        self.assertEqual(self.box.text_box.page_index, 1)
        self.assertTrue(self.box.previous_button.enabled)
        self.assertFalse(self.box.next_button.enabled)

    def test_previous_button_goes_back(self) -> None:
        self.box.next_button.on_click()
        self.box.previous_button.on_click()
        self.assertEqual(self.box.text_box.page_index, 0)
        self.assertFalse(self.box.previous_button.enabled)
        self.assertTrue(self.box.next_button.enabled)

    def test_does_not_auto_close(self) -> None:
        self.box.next_button.on_click()
        self.assertTrue(self.box.visible)
        self.assertTrue(self.box.text_box.visible)


if __name__ == "__main__":
    unittest.main()
