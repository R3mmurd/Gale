import unittest

import pygame

from gale.input_handler import KEY_RETURN, KeyboardData, MouseClickData, MouseMotionData
from gale.ui.button import Button
from gale.ui.container import Container
from gale.ui.manager import UIManager
from gale.ui.text_input import TextInput


def click_data(released: bool, pos=(0, 0)) -> MouseClickData:
    event_type = pygame.MOUSEBUTTONUP if released else pygame.MOUSEBUTTONDOWN
    return MouseClickData(pygame.event.Event(event_type, button=1, pos=pos))


def motion_data(pos=(0, 0)) -> MouseMotionData:
    return MouseMotionData(
        pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0))
    )


def key_data(key: int, pressed: bool = True) -> KeyboardData:
    event_type = pygame.KEYDOWN if pressed else pygame.KEYUP
    return KeyboardData(
        pygame.event.Event(event_type, key=key, mod=pygame.KMOD_NONE, unicode="")
    )


class UIManagerRescaleTestCase(unittest.TestCase):
    def test_rescale_converts_window_coordinates_to_virtual_ones(self) -> None:
        manager = UIManager(
            Container(0, 0, 100, 100),
            virtual_width=400,
            window_width=800,
            virtual_height=300,
            window_height=600,
        )
        self.assertEqual(manager._rescale((800, 600)), (400, 300))
        self.assertEqual(manager._rescale((0, 0)), (0, 0))


class UIManagerDispatchTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.clicked = []
        self.button = Button(
            0, 0, 100, 100, "Go", on_click=lambda: self.clicked.append(True)
        )
        self.container = Container(0, 0, 100, 100, children=[self.button])
        self.manager = UIManager(
            self.container,
            virtual_width=100,
            window_width=200,
            virtual_height=100,
            window_height=200,
        )

    def test_mouse_click_is_rescaled_before_reaching_the_root(self) -> None:
        # (100, 100) in window space rescales to (50, 50) in virtual
        # space, still inside the 100x100 button.
        self.manager.on_input("mouse_click", click_data(released=True, pos=(100, 100)))
        self.assertEqual(self.clicked, [True])

    def test_mouse_motion_is_forwarded_rescaled(self) -> None:
        # Just below the widget's bottom edge in virtual space.
        self.manager.on_input("mouse_motion", motion_data(pos=(20, 210)))
        self.assertFalse(self.button.hovered)

        self.manager.on_input("mouse_motion", motion_data(pos=(20, 20)))
        self.assertTrue(self.button.hovered)

    def test_confirm_action_invokes_focused_widget(self) -> None:
        self.manager.on_input("confirm", key_data(KEY_RETURN))
        self.assertEqual(self.clicked, [True])

    def test_keyboard_release_is_ignored(self) -> None:
        self.manager.on_input("confirm", key_data(KEY_RETURN, pressed=False))
        self.assertEqual(self.clicked, [])


class UIManagerNavigationTestCase(unittest.TestCase):
    def test_navigate_action_moves_focus(self) -> None:
        button_a = Button(0, 0, 50, 50, "A")
        button_b = Button(0, 60, 50, 50, "B")
        container = Container(0, 0, 100, 200, children=[button_a, button_b])
        manager = UIManager(
            container,
            virtual_width=100,
            window_width=100,
            virtual_height=200,
            window_height=200,
            navigate_actions={"move_down": (0, 1)},
        )

        self.assertTrue(button_a.focused)
        manager.on_input("move_down", key_data(pygame.K_DOWN))
        self.assertTrue(button_b.focused)
        self.assertFalse(button_a.focused)


class UIManagerRawKeyboardTestCase(unittest.TestCase):
    def test_raw_keyboard_input_reaches_the_deepest_focused_widget(self) -> None:
        text_input = TextInput(0, 0, 100, 20, initial_text="ab")
        container = Container(0, 0, 100, 100, children=[text_input])
        manager = UIManager(
            container,
            virtual_width=100,
            window_width=100,
            virtual_height=100,
            window_height=100,
        )

        manager.on_input("any_key", key_data(pygame.K_BACKSPACE))

        self.assertEqual(text_input.text, "a")

    def test_widgets_that_do_not_want_raw_keyboard_are_left_alone(self) -> None:
        clicked = []
        button = Button(0, 0, 50, 50, "A", on_click=lambda: clicked.append(True))
        container = Container(0, 0, 100, 100, children=[button])
        manager = UIManager(
            container,
            virtual_width=100,
            window_width=100,
            virtual_height=100,
            window_height=100,
        )

        manager.on_input("any_key", key_data(pygame.K_a))

        self.assertEqual(clicked, [])


class UIManagerUpdateRenderTestCase(unittest.TestCase):
    def test_update_and_render_delegate_to_root(self) -> None:
        container = Container(0, 0, 50, 50)
        manager = UIManager(
            container,
            virtual_width=50,
            window_width=50,
            virtual_height=50,
            window_height=50,
        )
        manager.update(0.1)
        surface = pygame.Surface((50, 50))
        manager.render(surface)


if __name__ == "__main__":
    unittest.main()
