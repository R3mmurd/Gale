import unittest

import pygame

from gale.input_handler import MouseClickData
from gale.ui.list_view import ListView


def click_data(released: bool) -> MouseClickData:
    event_type = pygame.MOUSEBUTTONUP if released else pygame.MOUSEBUTTONDOWN
    return MouseClickData(pygame.event.Event(event_type, button=1, pos=(0, 0)))


class ListViewTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.selected = []
        self.list_view = ListView(
            0,
            0,
            100,
            90,
            items=[
                ("Host", lambda: self.selected.append("Host")),
                ("Join", lambda: self.selected.append("Join")),
                ("Quit", lambda: self.selected.append("Quit")),
            ],
        )

    def test_navigate_down_wraps_around(self) -> None:
        self.assertEqual(self.list_view.selected_index, 0)
        self.list_view.on_navigate((0, 1))
        self.assertEqual(self.list_view.selected_index, 1)
        self.list_view.on_navigate((0, 1))
        self.assertEqual(self.list_view.selected_index, 2)
        self.list_view.on_navigate((0, 1))
        self.assertEqual(self.list_view.selected_index, 0)

    def test_navigate_up_wraps_around(self) -> None:
        self.list_view.on_navigate((0, -1))
        self.assertEqual(self.list_view.selected_index, 2)

    def test_confirm_invokes_selected_item(self) -> None:
        self.list_view.selected_index = 1
        self.assertTrue(self.list_view.on_confirm())
        self.assertEqual(self.selected, ["Join"])

    def test_mouse_motion_syncs_selection(self) -> None:
        self.list_view.on_mouse_motion((50, 65))  # third row (row height 30)
        self.assertEqual(self.list_view.selected_index, 2)

    def test_mouse_click_selects_and_invokes(self) -> None:
        self.list_view.on_mouse_click((50, 35), click_data(released=True))
        self.assertEqual(self.list_view.selected_index, 1)
        self.assertEqual(self.selected, ["Join"])


if __name__ == "__main__":
    unittest.main()
