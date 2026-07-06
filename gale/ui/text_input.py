"""
This file contains the implementation of the class TextInput.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, Optional, Tuple

import pygame

from gale.input_handler import (
    KEY_BACKSPACE,
    KEY_DELETE,
    KEY_LEFT,
    KEY_RETURN,
    KEY_RIGHT,
    KeyboardData,
    MouseClickData,
)
from gale.text import Text

from .theme import Theme
from .widget import Widget


class TextInput(Widget):
    """
    A single-line editable text field, for things like a player name,
    a chat message, or a server address/join code. Needs raw keyboard
    events rather than the confirm/navigate vocabulary, so its owner
    (typically UIManager) must call handle_key directly while this
    widget is focused (see wants_raw_keyboard).

    Limitation: built on pygame's KEYDOWN.unicode, so it only supports
    ASCII-range input, not full IME/composed-character entry. That is
    enough for names, chat, and join codes, but not for every language.

    Usage example:

        name_input = TextInput(40, 40, 240, 32, initial_text="Player", max_length=16)
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        initial_text: str = "",
        max_length: Optional[int] = None,
        font: Optional[pygame.font.Font] = None,
        on_submit: Optional[Callable[[str], None]] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The field's x position.
        :param y: The field's y position.
        :param width: The field's width.
        :param height: The field's height.
        :param initial_text: The starting text. The default value is "".
        :param max_length: Maximum number of characters accepted. The default value is None, meaning no limit.
        :param font: The font used to render the text. The default value is None, so theme.font is used.
        :param on_submit: Called with the current text when Enter is pressed. The default value is None.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, width, height, theme=theme)
        self.text: str = initial_text
        self.cursor_index: int = len(initial_text)
        self.max_length: Optional[int] = max_length
        self._font = font
        self.on_submit: Optional[Callable[[str], None]] = on_submit
        self.wants_raw_keyboard = True
        self.focusable = True

    def handle_key(self, data: KeyboardData) -> bool:
        """
        :param data: The keyboard event to react to. Only KEYDOWN events (data.pressed) cause a change.
        :returns: Whether the key was consumed.
        """
        if not self.enabled or not data.pressed:
            return False

        key = data.key

        if key == KEY_BACKSPACE:
            if self.cursor_index > 0:
                self.text = (
                    self.text[: self.cursor_index - 1] + self.text[self.cursor_index :]
                )
                self.cursor_index -= 1
        elif key == KEY_DELETE:
            self.text = (
                self.text[: self.cursor_index] + self.text[self.cursor_index + 1 :]
            )
        elif key == KEY_LEFT:
            self.cursor_index = max(0, self.cursor_index - 1)
        elif key == KEY_RIGHT:
            self.cursor_index = min(len(self.text), self.cursor_index + 1)
        elif key == KEY_RETURN:
            if self.on_submit is not None:
                self.on_submit(self.text)
        elif data.unicode and data.unicode.isprintable():
            if self.max_length is None or len(self.text) < self.max_length:
                self.text = (
                    self.text[: self.cursor_index]
                    + data.unicode
                    + self.text[self.cursor_index :]
                )
                self.cursor_index += 1

        return True

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)
        border_color = (
            self.theme.focus_color if self.focused else self.theme.border_color
        )
        pygame.draw.rect(
            surface, border_color, self.rect, max(1, self.theme.border_width)
        )

        font = self._font if self._font is not None else self.theme.font
        text_obj = Text(
            self.text,
            font,
            self.x + self.theme.padding,
            self.rect.centery - font.get_linesize() // 2,
            self.theme.text_color,
        )
        text_obj.render(surface)

        if self.focused:
            cursor_x = (
                self.x
                + self.theme.padding
                + font.size(self.text[: self.cursor_index])[0]
            )
            pygame.draw.line(
                surface,
                self.theme.text_color,
                (cursor_x, self.y + 4),
                (cursor_x, self.y + self.height - 4),
            )

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released:
            self.cursor_index = len(self.text)

        return True
