import unittest

import pygame

from gale.input_handler import MouseClickData
from gale.ui.checkbox import Checkbox


def click_data(released: bool) -> MouseClickData:
    event_type = pygame.MOUSEBUTTONUP if released else pygame.MOUSEBUTTONDOWN
    return MouseClickData(pygame.event.Event(event_type, button=1, pos=(0, 0)))


class CheckboxTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.changes = []
        self.checkbox = Checkbox(
            0, 0, 20, on_change=lambda checked: self.changes.append(checked)
        )

    def test_starts_unchecked_by_default(self) -> None:
        self.assertFalse(self.checkbox.checked)

    def test_can_start_checked(self) -> None:
        checkbox = Checkbox(0, 0, 20, checked=True)
        self.assertTrue(checkbox.checked)

    def test_toggle_flips_state_and_fires_on_change(self) -> None:
        self.checkbox.toggle()
        self.assertTrue(self.checkbox.checked)
        self.assertEqual(self.changes, [True])

        self.checkbox.toggle()
        self.assertFalse(self.checkbox.checked)
        self.assertEqual(self.changes, [True, False])

    def test_toggle_without_on_change_does_not_raise(self) -> None:
        checkbox = Checkbox(0, 0, 20)
        checkbox.toggle()
        self.assertTrue(checkbox.checked)

    def test_click_inside_on_release_toggles(self) -> None:
        self.assertTrue(
            self.checkbox.on_mouse_click((10, 10), click_data(released=True))
        )
        self.assertEqual(self.changes, [True])

    def test_click_inside_on_press_does_not_toggle_yet(self) -> None:
        self.assertTrue(
            self.checkbox.on_mouse_click((10, 10), click_data(released=False))
        )
        self.assertEqual(self.changes, [])

    def test_click_outside_does_not_consume(self) -> None:
        self.assertFalse(
            self.checkbox.on_mouse_click((500, 500), click_data(released=True))
        )
        self.assertEqual(self.changes, [])

    def test_confirm_toggles(self) -> None:
        self.assertTrue(self.checkbox.on_confirm())
        self.assertEqual(self.changes, [True])

    def test_disabled_does_not_toggle(self) -> None:
        self.checkbox.enabled = False
        self.assertFalse(
            self.checkbox.on_mouse_click((10, 10), click_data(released=True))
        )
        self.assertFalse(self.checkbox.on_confirm())
        self.assertEqual(self.changes, [])

    def test_render_does_not_raise_when_checked_and_focused(self) -> None:
        self.checkbox.checked = True
        self.checkbox.focused = True
        surface = pygame.Surface((20, 20))
        self.checkbox.render(surface)

    def test_render_skips_hidden_widget(self) -> None:
        self.checkbox.visible = False
        surface = pygame.Surface((20, 20))
        self.checkbox.render(surface)  # should not raise, and draws nothing


if __name__ == "__main__":
    unittest.main()
