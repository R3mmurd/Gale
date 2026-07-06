import unittest

from gale.ui.theme import Theme, get_default_theme, set_default_theme
from gale.ui.widget import Widget


class ThemeFallbackTestCase(unittest.TestCase):
    def test_widget_without_theme_uses_default(self) -> None:
        widget = Widget(0, 0, 10, 10)
        self.assertIs(widget.theme, get_default_theme())

    def test_widget_with_explicit_theme_keeps_it(self) -> None:
        theme = Theme()
        widget = Widget(0, 0, 10, 10, theme=theme)
        self.assertIs(widget.theme, theme)

    def test_default_theme_swap_propagates_live(self) -> None:
        widget = Widget(0, 0, 10, 10)
        original_default = get_default_theme()

        try:
            new_theme = Theme()
            set_default_theme(new_theme)
            self.assertIs(widget.theme, new_theme)
        finally:
            set_default_theme(original_default)


if __name__ == "__main__":
    unittest.main()
