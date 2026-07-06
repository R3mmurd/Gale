import unittest

import pygame

from gale.input_handler import MouseClickData
from gale.ui.button import Button
from gale.ui.container import Container
from gale.ui.list_view import ListView
from gale.ui.panel import Panel


def click_data(released: bool) -> MouseClickData:
    event_type = pygame.MOUSEBUTTONUP if released else pygame.MOUSEBUTTONDOWN
    return MouseClickData(pygame.event.Event(event_type, button=1, pos=(0, 0)))


class ContainerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.clicked_a = []
        self.clicked_b = []
        self.button_a = Button(
            0, 0, 50, 50, "A", on_click=lambda: self.clicked_a.append(True)
        )
        self.button_b = Button(
            0, 0, 50, 50, "B", on_click=lambda: self.clicked_b.append(True)
        )
        self.container = Container(
            0, 0, 100, 100, children=[self.button_a, self.button_b]
        )

    def test_first_child_is_focused_initially(self) -> None:
        self.assertTrue(self.button_a.focused)
        self.assertFalse(self.button_b.focused)

    def test_top_most_overlapping_child_wins_click(self) -> None:
        # button_b was added after button_a, so it is on top and overlaps
        # the same rect entirely.
        self.container.on_mouse_click((25, 25), click_data(released=True))
        self.assertEqual(self.clicked_a, [])
        self.assertEqual(self.clicked_b, [True])

    def test_click_moves_focus(self) -> None:
        self.container.on_mouse_click((25, 25), click_data(released=True))
        self.assertFalse(self.button_a.focused)
        self.assertTrue(self.button_b.focused)

    def test_confirm_forwards_to_focused_child(self) -> None:
        self.container.on_confirm()
        self.assertEqual(self.clicked_a, [True])
        self.assertEqual(self.clicked_b, [])

    def test_navigate_moves_focus_when_unconsumed(self) -> None:
        self.assertTrue(self.container.on_navigate((0, 1)))
        self.assertFalse(self.button_a.focused)
        self.assertTrue(self.button_b.focused)

    def test_remove_child_drops_it_from_dispatch(self) -> None:
        self.container.remove_child(self.button_b)
        self.container.on_mouse_click((25, 25), click_data(released=True))
        self.assertEqual(self.clicked_a, [True])
        self.assertEqual(self.clicked_b, [])


class NestedPanelListViewFocusTestCase(unittest.TestCase):
    """
    Regression test: a decorative Panel must never steal keyboard
    focus from the interactive ListView beside it, since
    Container([Panel(...), ListView(...)]) is gale.ui's canonical menu
    composition (Panel as background chrome, ListView as the actual
    selectable items).
    """

    def test_panel_is_not_focusable_but_list_view_is(self) -> None:
        selected = []
        list_view = ListView(
            8, 8, 84, 84, items=[("Go", lambda: selected.append("Go"))]
        )
        panel = Panel(0, 0, 100, 100)
        menu = Container(0, 0, 100, 100, children=[panel, list_view])

        self.assertFalse(panel.focused)
        self.assertTrue(list_view.focused)

        self.assertTrue(menu.on_confirm())
        self.assertEqual(selected, ["Go"])

    def test_focus_skips_decorative_siblings_at_the_root_too(self) -> None:
        from gale.ui.label import Label

        selected = []
        list_view = ListView(
            8, 8, 84, 84, items=[("Go", lambda: selected.append("Go"))]
        )
        menu = Container(0, 0, 100, 100, children=[Panel(0, 0, 100, 100), list_view])
        root = Container(0, 0, 100, 100, children=[Label(0, 0, "Title"), menu])

        self.assertTrue(menu.focused)
        self.assertTrue(root.on_confirm())
        self.assertEqual(selected, ["Go"])


if __name__ == "__main__":
    unittest.main()
