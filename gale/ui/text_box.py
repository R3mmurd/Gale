"""
This file contains the implementation of the classes TextBox, a
paginated block of text advanced by click/Enter (RPG-dialogue style),
and PaginatedTextBox, the same paginated text but navigated with
explicit Previous/Next buttons instead.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import random
from typing import Callable, List, Optional, Tuple

import pygame

from gale.input_handler import MouseClickData
from gale.text import Text

from .button import Button
from .container import Container
from .theme import Theme, get_default_theme
from .widget import Widget


class TextBox(Widget):
    """
    A paginated block of text, such as dialogue or an in-game hint.
    advance() moves to the next page (on a mouse click or on_confirm),
    or, on the last page, hides the box and calls on_close. This is
    the click-or-Enter-to-continue style used by RPG dialogue, where
    the player doesn't need to navigate backward.

    For content the player pages through with explicit "Previous"/"Next"
    buttons instead (e.g. a rules or help screen), use next_page() and
    previous_page() directly, or wrap this in a PaginatedTextBox, which
    also wires up and enables/disables those buttons for you.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        font: Optional[pygame.font.Font] = None,
        lines_per_page: int = 3,
        on_close: Optional[Callable[[], None]] = None,
        theme: Optional[Theme] = None,
    ) -> None:
        """
        :param x: The box's x position.
        :param y: The box's y position.
        :param width: The box's width, used to word-wrap the text.
        :param height: The box's height.
        :param text: The full text to page through.
        :param font: The font used to render and measure the text. The default value is None, so theme.font is used.
        :param lines_per_page: How many wrapped lines are shown per page. The default value is 3.
        :param on_close: Called with no arguments once the last page is advanced past. The default value is None.
        :param theme: This widget's own theme. The default value is None.
        """
        super().__init__(x, y, width, height, theme=theme)
        self._font = font
        self.lines_per_page: int = lines_per_page
        self.on_close: Optional[Callable[[], None]] = on_close
        self._pages: List[List[str]] = self._paginate(text)
        self.page_index: int = 0

    def _paginate(self, text: str) -> List[List[str]]:
        font = self._font if self._font is not None else self.theme.font
        wrapped = self._wrap(text, font)
        pages = [
            wrapped[i : i + self.lines_per_page]
            for i in range(0, len(wrapped), self.lines_per_page)
        ]
        return pages or [[]]

    def _wrap(self, text: str, font: pygame.font.Font) -> List[str]:
        max_width = self.width - 2 * self.theme.padding
        lines: List[str] = []

        for paragraph in text.split("\n"):
            current = ""

            for word in paragraph.split(" "):
                candidate = f"{current} {word}".strip()

                if current and font.size(candidate)[0] > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate

            lines.append(current)

        return lines

    @property
    def finished(self) -> bool:
        return self.page_index >= len(self._pages) - 1

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def has_next_page(self) -> bool:
        return self.page_index < len(self._pages) - 1

    @property
    def has_previous_page(self) -> bool:
        return self.page_index > 0

    def advance(self) -> None:
        if self.finished:
            self.visible = False

            if self.on_close is not None:
                self.on_close()

            return

        self.page_index += 1

    def next_page(self) -> bool:
        """
        Move to the next page, if any, without the auto-close behavior
        of advance(). Meant to back a "Next" button.

        :returns: Whether there was a next page to move to.
        """
        if not self.has_next_page:
            return False

        self.page_index += 1
        return True

    def previous_page(self) -> bool:
        """
        Move back to the previous page, if any. Meant to back a
        "Previous" button.

        :returns: Whether there was a previous page to move back to.
        """
        if not self.has_previous_page:
            return False

        self.page_index -= 1
        return True

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)

        if self.theme.border_width > 0:
            pygame.draw.rect(
                surface, self.theme.border_color, self.rect, self.theme.border_width
            )

        font = self._font if self._font is not None else self.theme.font
        line_height = font.get_linesize()

        for i, line in enumerate(self._pages[self.page_index]):
            text_obj = Text(
                line,
                font,
                self.x + self.theme.padding,
                self.y + self.theme.padding + i * line_height,
                self.theme.text_color,
            )
            text_obj.render(surface)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released:
            self.advance()

        return True

    def on_confirm(self) -> bool:
        if not self.enabled:
            return False

        self.advance()
        return True


class PaginatedTextBox(Container):
    """
    A TextBox paired with "Previous"/"Next" buttons docked under it,
    for content the player pages through at their own pace instead of
    a click/Enter-to-continue dialogue (e.g. an instructions or help
    screen). The buttons are kept in sync every update(): disabled on
    the first/last page instead of wrapping around, and this never
    auto-hides itself the way TextBox.advance() does on its own —
    close it explicitly (e.g. from a Window's close button) if needed.

    Usage example:

        help_box = PaginatedTextBox(160, 90, 320, 220, long_help_text)
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        font: Optional[pygame.font.Font] = None,
        lines_per_page: int = 3,
        button_height: int = 28,
        button_width: int = 96,
        previous_label: str = "Previous",
        next_label: str = "Next",
        theme: Optional[Theme] = None,
        visible: bool = True,
    ) -> None:
        """
        :param x: The widget's x position.
        :param y: The widget's y position.
        :param width: The widget's width, used to word-wrap the text and lay out the buttons.
        :param height: The widget's total height, shared between the text box and the buttons row.
        :param text: The full text to page through.
        :param font: The font used to render and measure the text. The default value is None, so theme.font is used.
        :param lines_per_page: How many wrapped lines are shown per page. The default value is 3.
        :param button_height: The height of the Previous/Next buttons, in pixels. The default value is 28.
        :param button_width: The width of the Previous/Next buttons, in pixels. The default value is 96.
        :param previous_label: The label of the "go back" button. The default value is "Previous".
        :param next_label: The label of the "go forward" button. The default value is "Next".
        :param theme: This widget's own theme, also handed down to the text box and buttons unless they're given their own. The default value is None.
        :param visible: Whether the widget (and everything in it) is drawn/updated/reachable by input. The default value is True.
        """
        theme_obj = theme if theme is not None else get_default_theme()
        padding = theme_obj.padding
        text_box_height = height - button_height - padding

        self.text_box = TextBox(
            x,
            y,
            width,
            text_box_height,
            text,
            font=font,
            lines_per_page=lines_per_page,
            theme=theme,
        )
        self.previous_button = Button(
            x,
            y + text_box_height + padding,
            button_width,
            button_height,
            previous_label,
            on_click=self._go_previous,
            theme=theme,
        )
        self.next_button = Button(
            x + width - button_width,
            y + text_box_height + padding,
            button_width,
            button_height,
            next_label,
            on_click=self._go_next,
            theme=theme,
        )
        super().__init__(
            x,
            y,
            width,
            height,
            children=[self.text_box, self.previous_button, self.next_button],
            theme=theme,
            visible=visible,
        )
        self._sync_buttons()

    def _go_previous(self) -> None:
        self.text_box.previous_page()
        self._sync_buttons()

    def _go_next(self) -> None:
        self.text_box.next_page()
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        self.previous_button.enabled = self.text_box.has_previous_page
        self.next_button.enabled = self.text_box.has_next_page

    def update(self, dt: float) -> None:
        super().update(dt)
        self._sync_buttons()


class TypewriterTextBox(TextBox):
    """
    A TextBox that reveals its text progressively character by character,
    popular in RPG dialogues.
    advance() will instantly reveal all text on the current page if it is
    still typing, or move to the next page if the text is fully revealed.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        font: Optional[pygame.font.Font] = None,
        lines_per_page: int = 3,
        on_close: Optional[Callable[[], None]] = None,
        theme: Optional[Theme] = None,
        chars_per_second: float = 40.0,
        sounds: Optional[List[pygame.mixer.Sound]] = None,
        on_char_typed: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        :param x: The box's x position.
        :param y: The box's y position.
        :param width: The box's width, used to word-wrap the text.
        :param height: The box's height.
        :param text: The full text to page through.
        :param font: The font used to render and measure the text. The default value is None, so theme.font is used.
        :param lines_per_page: How many wrapped lines are shown per page. The default value is 3.
        :param on_close: Called with no arguments once the last page is advanced past. The default value is None.
        :param theme: This widget's own theme. The default value is None.
        :param chars_per_second: The typing speed in characters per second. The default value is 40.0.
        :param sounds: A list of pygame.mixer.Sound objects. One will be played randomly when a non-space character is typed. The default value is None.
        :param on_char_typed: A callback function invoked with each individual character string as it is revealed. The default value is None.
        """
        super().__init__(
            x,
            y,
            width,
            height,
            text,
            font=font,
            lines_per_page=lines_per_page,
            on_close=on_close,
            theme=theme,
        )
        self.chars_per_second: float = chars_per_second
        self.sounds: Optional[List[pygame.mixer.Sound]] = sounds
        self.on_char_typed: Optional[Callable[[str], None]] = on_char_typed
        self.char_index: float = 0.0
        self.total_chars_on_page: int = 0
        self._calculate_page_chars()

    def set_text(self, text: str) -> None:
        """
        Replace the current text, reset pagination, and restart the typewriter effect.
        """
        self._pages = self._paginate(text)
        self.page_index = 0
        self.char_index = 0.0
        self._calculate_page_chars()

    def _calculate_page_chars(self) -> None:
        if self.page_index < len(self._pages):
            self.total_chars_on_page = sum(
                len(line) for line in self._pages[self.page_index]
            )
        else:
            self.total_chars_on_page = 0

    def update(self, dt: float) -> None:
        if self.char_index < self.total_chars_on_page:
            old_index = int(self.char_index)
            self.char_index += self.chars_per_second * dt
            new_index = int(self.char_index)

            if new_index > old_index:
                full_text = "".join(self._pages[self.page_index])
                if old_index < len(full_text):
                    revealed = full_text[old_index:new_index]

                    if self.on_char_typed is not None:
                        for c in revealed:
                            self.on_char_typed(c)

                    if any(not c.isspace() for c in revealed):
                        if self.sounds:
                            random.choice(self.sounds).play()

    @property
    def is_typing(self) -> bool:
        return self.char_index < self.total_chars_on_page

    def advance(self) -> None:
        if self.is_typing:
            self.char_index = float(self.total_chars_on_page)
        else:
            super().advance()
            self.char_index = 0.0
            self._calculate_page_chars()

    def next_page(self) -> bool:
        if self.is_typing:
            self.char_index = float(self.total_chars_on_page)
            return False

        res = super().next_page()
        if res:
            self.char_index = 0.0
            self._calculate_page_chars()
        return res

    def previous_page(self) -> bool:
        res = super().previous_page()
        if res:
            self.char_index = 0.0
            self._calculate_page_chars()
        return res

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        pygame.draw.rect(surface, self.theme.background_color, self.rect)

        if self.theme.border_width > 0:
            pygame.draw.rect(
                surface, self.theme.border_color, self.rect, self.theme.border_width
            )

        font = self._font if self._font is not None else self.theme.font
        line_height = font.get_linesize()

        if self.page_index >= len(self._pages):
            return

        chars_to_render = int(self.char_index)

        for i, line in enumerate(self._pages[self.page_index]):
            if chars_to_render <= 0:
                break

            if len(line) <= chars_to_render:
                text_to_render = line
                chars_to_render -= len(line)
            else:
                text_to_render = line[:chars_to_render]
                chars_to_render = 0

            text_obj = Text(
                text_to_render,
                font,
                self.x + self.theme.padding,
                self.y + self.theme.padding + i * line_height,
                self.theme.text_color,
            )
            text_obj.render(surface)
