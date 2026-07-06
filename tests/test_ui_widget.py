import unittest

from gale.ui.widget import Widget


class WidgetHitTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.widget = Widget(10, 10, 20, 20)

    def test_contains_inside_point(self) -> None:
        self.assertTrue(self.widget.contains((15, 15)))

    def test_contains_outside_point(self) -> None:
        self.assertFalse(self.widget.contains((100, 100)))

    def test_on_mouse_motion_sets_hovered(self) -> None:
        self.widget.on_mouse_motion((15, 15))
        self.assertTrue(self.widget.hovered)
        self.widget.on_mouse_motion((100, 100))
        self.assertFalse(self.widget.hovered)

    def test_default_input_hooks_do_not_consume(self) -> None:
        self.assertFalse(self.widget.on_confirm())
        self.assertFalse(self.widget.on_navigate((0, 1)))


if __name__ == "__main__":
    unittest.main()
