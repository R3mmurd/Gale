import unittest

import pygame

from gale.input_handler import KEY_BACKSPACE, KEY_LEFT, KEY_RETURN, KeyboardData
from gale.ui.text_input import TextInput


def key_data(key: int, unicode: str = "") -> KeyboardData:
    return KeyboardData(
        pygame.event.Event(
            pygame.KEYDOWN, key=key, mod=pygame.KMOD_NONE, unicode=unicode
        )
    )


class TextInputTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.submitted = []
        self.text_input = TextInput(
            0,
            0,
            200,
            32,
            initial_text="ab",
            on_submit=lambda text: self.submitted.append(text),
        )

    def test_typing_appends_at_cursor(self) -> None:
        self.text_input.handle_key(key_data(pygame.K_c, "c"))
        self.assertEqual(self.text_input.text, "abc")
        self.assertEqual(self.text_input.cursor_index, 3)

    def test_backspace_removes_before_cursor(self) -> None:
        self.text_input.handle_key(key_data(KEY_BACKSPACE))
        self.assertEqual(self.text_input.text, "a")
        self.assertEqual(self.text_input.cursor_index, 1)

    def test_left_then_insert(self) -> None:
        self.text_input.handle_key(key_data(KEY_LEFT))
        self.text_input.handle_key(key_data(pygame.K_x, "x"))
        self.assertEqual(self.text_input.text, "axb")

    def test_max_length_is_enforced(self) -> None:
        self.text_input.max_length = 2
        self.text_input.handle_key(key_data(pygame.K_c, "c"))
        self.assertEqual(self.text_input.text, "ab")

    def test_enter_submits(self) -> None:
        self.text_input.handle_key(key_data(KEY_RETURN))
        self.assertEqual(self.submitted, ["ab"])

    def test_wants_raw_keyboard(self) -> None:
        self.assertTrue(self.text_input.wants_raw_keyboard)


if __name__ == "__main__":
    unittest.main()
