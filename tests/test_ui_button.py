import unittest

import pygame

from gale.input_handler import MouseClickData
from gale.ui.button import Button


def click_data(released: bool) -> MouseClickData:
    event_type = pygame.MOUSEBUTTONUP if released else pygame.MOUSEBUTTONDOWN
    return MouseClickData(pygame.event.Event(event_type, button=1, pos=(0, 0)))


class ButtonTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.clicked = []
        self.button = Button(
            0, 0, 100, 40, "Start", on_click=lambda: self.clicked.append(True)
        )

    def test_click_inside_on_release_fires(self) -> None:
        self.assertTrue(self.button.on_mouse_click((50, 20), click_data(released=True)))
        self.assertEqual(self.clicked, [True])

    def test_click_inside_on_press_does_not_fire_yet(self) -> None:
        self.assertTrue(
            self.button.on_mouse_click((50, 20), click_data(released=False))
        )
        self.assertEqual(self.clicked, [])

    def test_click_outside_does_not_consume(self) -> None:
        self.assertFalse(
            self.button.on_mouse_click((500, 500), click_data(released=True))
        )
        self.assertEqual(self.clicked, [])

    def test_confirm_fires(self) -> None:
        self.assertTrue(self.button.on_confirm())
        self.assertEqual(self.clicked, [True])

    def test_disabled_does_not_fire(self) -> None:
        self.button.enabled = False
        self.assertFalse(
            self.button.on_mouse_click((50, 20), click_data(released=True))
        )
        self.assertFalse(self.button.on_confirm())
        self.assertEqual(self.clicked, [])


if __name__ == "__main__":
    unittest.main()
