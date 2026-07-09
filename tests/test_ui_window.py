import unittest

from gale.ui.label import Label
from gale.ui.window import Window


class WindowTestCase(unittest.TestCase):
    def test_closable_by_default_creates_close_button(self) -> None:
        window = Window(0, 0, 200, 150)
        self.assertIsNotNone(window.close_button)
        self.assertIn(window.close_button, window.children)

    def test_close_button_docked_top_right(self) -> None:
        window = Window(10, 20, 200, 150, close_button_size=20)
        padding = window.theme.padding
        self.assertEqual(window.close_button.x, 10 + 200 - 20 - padding)
        self.assertEqual(window.close_button.y, 20 + padding)

    def test_not_closable_has_no_close_button(self) -> None:
        window = Window(0, 0, 200, 150, closable=False)
        self.assertIsNone(window.close_button)

    def test_clicking_close_button_hides_window_and_calls_on_close(self) -> None:
        closed = []
        window = Window(0, 0, 200, 150, on_close=lambda: closed.append(True))
        window.close_button.on_click()
        self.assertFalse(window.visible)
        self.assertEqual(closed, [True])

    def test_close_can_be_called_directly_even_when_not_closable(self) -> None:
        closed = []
        window = Window(
            0, 0, 200, 150, closable=False, on_close=lambda: closed.append(True)
        )
        window.close()
        self.assertFalse(window.visible)
        self.assertEqual(closed, [True])

    def test_title_adds_a_label_child(self) -> None:
        window = Window(0, 0, 200, 150, title="Inventory")
        labels = [child for child in window.children if isinstance(child, Label)]
        self.assertEqual(len(labels), 1)

    def test_no_title_adds_no_label_child(self) -> None:
        window = Window(0, 0, 200, 150)
        labels = [child for child in window.children if isinstance(child, Label)]
        self.assertEqual(len(labels), 0)

    def test_extra_children_are_kept(self) -> None:
        extra = Label(0, 0, "Hello")
        window = Window(0, 0, 200, 150, children=[extra])
        self.assertIn(extra, window.children)


if __name__ == "__main__":
    unittest.main()
