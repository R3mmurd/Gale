"""
This file contains the implementation of an observer-pattern-based
input handler.

Author: Alejandro Mujica
"""
from typing import Tuple, Union, TypeVar, NoReturn, Dict, List, Optional

import pygame

INPUT_EVENTS: Tuple[int, int, int, int, int, int] = (
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
    pygame.MOUSEWHEEL,
    pygame.MOUSEMOTION,
)


class InvalidListenerException(Exception):
    pass


class KeyboardData:
    """
    Group the data associated to a keyboad input event.
    """

    def __init__(
        self, pressed: bool, released: bool, modifier: int, unicode: str
    ) -> None:
        self.pressed: bool = pressed
        self.released: bool = released
        self.modifier: int = modifier
        self.unicode: str = unicode


class MouseClickData:
    """
    Group the data associated to a mouse click event.
    """

    def __init__(
        self, pressed: bool, released: bool, button: int, position: Tuple[int, int]
    ) -> None:
        self.pressed: bool = pressed
        self.released: bool = released
        self.button: int = button
        self.position: Tuple[int, int] = position


class MouseWheelData:
    """
    Group the data associated to a mouse wheel event.
    """

    def __init__(self, flipped: bool) -> None:
        self.flipped: bool = flipped


class MouseMotionData:
    """
    Group the data associated to a mouse motion event.
    """

    def __init__(
        self, position: Tuple[int, int], buttons: Tuple[int, int, int]
    ) -> None:
        self.position: Tuple[int, int] = position
        self.buttons: Tuple[int, int, int] = buttons


InputData = TypeVar(
    "InputData",
    bound=Union[KeyboardData, MouseClickData, MouseWheelData, MouseMotionData],
)


class InputListener:
    """
    This is an interface to any class that need to be an
    input listener.
    """

    def on_input(self, input_id: str, input_data: InputData) -> NoReturn:
        raise NotImplementedError()


KEY_0: int = pygame.K_0
KEY_1: int = pygame.K_1
KEY_2: int = pygame.K_2
KEY_3: int = pygame.K_3
KEY_4: int = pygame.K_4
KEY_5: int = pygame.K_5
KEY_6: int = pygame.K_6
KEY_7: int = pygame.K_7
KEY_8: int = pygame.K_8
KEY_9: int = pygame.K_9
KEY_AC_BACK: int = pygame.K_AC_BACK
KEY_AMPERSAND: int = pygame.K_AMPERSAND
KEY_ASTERISK: int = pygame.K_ASTERISK
KEY_AT: int = pygame.K_AT
KEY_BACKQUOTE: int = pygame.K_BACKQUOTE
KEY_BACKSLASH: int = pygame.K_BACKSLASH
KEY_BACKSPACE: int = pygame.K_BACKSPACE
KEY_BREAK: int = pygame.K_BREAK
KEY_CAPSLOCK: int = pygame.K_CAPSLOCK
KEY_CARET: int = pygame.K_CARET
KEY_CLEAR: int = pygame.K_CLEAR
KEY_COLON: int = pygame.K_COLON
KEY_COMMA: int = pygame.K_COMMA
KEY_CURRENCYSUBUNIT: int = pygame.K_CURRENCYSUBUNIT
KEY_CURRENCYUNIT: int = pygame.K_CURRENCYUNIT
KEY_DELETE: int = pygame.K_DELETE
KEY_DOLLAR: int = pygame.K_DOLLAR
KEY_DOWN: int = pygame.K_DOWN
KEY_END: int = pygame.K_END
KEY_EQUALS: int = pygame.K_EQUALS
KEY_ESCAPE: int = pygame.K_ESCAPE
KEY_EURO: int = pygame.K_EURO
KEY_EXCLAIM: int = pygame.K_EXCLAIM
KEY_F1: int = pygame.K_F1
KEY_F10: int = pygame.K_F10
KEY_F11: int = pygame.K_F11
KEY_F12: int = pygame.K_F12
KEY_F13: int = pygame.K_F13
KEY_F14: int = pygame.K_F14
KEY_F15: int = pygame.K_F15
KEY_F2: int = pygame.K_F2
KEY_F3: int = pygame.K_F3
KEY_F4: int = pygame.K_F4
KEY_F5: int = pygame.K_F5
KEY_F6: int = pygame.K_F6
KEY_F7: int = pygame.K_F7
KEY_F8: int = pygame.K_F8
KEY_F9: int = pygame.K_F9
KEY_GREATER: int = pygame.K_GREATER
KEY_HASH: int = pygame.K_HASH
KEY_HELP: int = pygame.K_HELP
KEY_HOME: int = pygame.K_HOME
KEY_INSERT: int = pygame.K_INSERT
KEY_KP0: int = pygame.K_KP0
KEY_KP1: int = pygame.K_KP1
KEY_KP2: int = pygame.K_KP2
KEY_KP3: int = pygame.K_KP3
KEY_KP4: int = pygame.K_KP4
KEY_KP5: int = pygame.K_KP5
KEY_KP6: int = pygame.K_KP6
KEY_KP7: int = pygame.K_KP7
KEY_KP8: int = pygame.K_KP8
KEY_KP9: int = pygame.K_KP9
KEY_KP_0: int = pygame.K_KP_0
KEY_KP_1: int = pygame.K_KP_1
KEY_KP_2: int = pygame.K_KP_2
KEY_KP_3: int = pygame.K_KP_3
KEY_KP_4: int = pygame.K_KP_4
KEY_KP_5: int = pygame.K_KP_5
KEY_KP_6: int = pygame.K_KP_6
KEY_KP_7: int = pygame.K_KP_7
KEY_KP_8: int = pygame.K_KP_8
KEY_KP_9: int = pygame.K_KP_9
KEY_KP_DIVIDE: int = pygame.K_KP_DIVIDE
KEY_KP_ENTER: int = pygame.K_KP_ENTER
KEY_KP_EQUALS: int = pygame.K_KP_EQUALS
KEY_KP_MINUS: int = pygame.K_KP_MINUS
KEY_KP_MULTIPLY: int = pygame.K_KP_MULTIPLY
KEY_KP_PERIOD: int = pygame.K_KP_PERIOD
KEY_KP_PLUS: int = pygame.K_KP_PLUS
KEY_LALT: int = pygame.K_LALT
KEY_LCTRL: int = pygame.K_LCTRL
KEY_LEFT: int = pygame.K_LEFT
KEY_LEFTBRACKET: int = pygame.K_LEFTBRACKET
KEY_LEFTPAREN: int = pygame.K_LEFTPAREN
KEY_LESS: int = pygame.K_LESS
KEY_LGUI: int = pygame.K_LGUI
KEY_LMETA: int = pygame.K_LMETA
KEY_LSHIFT: int = pygame.K_LSHIFT
KEY_LSUPER: int = pygame.K_LSUPER
KEY_MENU: int = pygame.K_MENU
KEY_MINUS: int = pygame.K_MINUS
KEY_MODE: int = pygame.K_MODE
KEY_NUMLOCK: int = pygame.K_NUMLOCK
KEY_NUMLOCKCLEAR: int = pygame.K_NUMLOCKCLEAR
KEY_PAGEDOWN: int = pygame.K_PAGEDOWN
KEY_PAGEUP: int = pygame.K_PAGEUP
KEY_PAUSE: int = pygame.K_PAUSE
KEY_PERCENT: int = pygame.K_PERCENT
KEY_PERIOD: int = pygame.K_PERIOD
KEY_PLUS: int = pygame.K_PLUS
KEY_POWER: int = pygame.K_POWER
KEY_PRINT: int = pygame.K_PRINT
KEY_PRINTSCREEN: int = pygame.K_PRINTSCREEN
KEY_QUESTION: int = pygame.K_QUESTION
KEY_QUOTE: int = pygame.K_QUOTE
KEY_QUOTEDBL: int = pygame.K_QUOTEDBL
KEY_RALT: int = pygame.K_RALT
KEY_RCTRL: int = pygame.K_RCTRL
KEY_RETURN: int = pygame.K_RETURN
KEY_RGUI: int = pygame.K_RGUI
KEY_RIGHT: int = pygame.K_RIGHT
KEY_RIGHTBRACKET: int = pygame.K_RIGHTBRACKET
KEY_RIGHTPAREN: int = pygame.K_RIGHTPAREN
KEY_RMETA: int = pygame.K_RMETA
KEY_RSHIFT: int = pygame.K_RSHIFT
KEY_RSUPER: int = pygame.K_RSUPER
KEY_SCROLLLOCK: int = pygame.K_SCROLLLOCK
KEY_SCROLLOCK: int = pygame.K_SCROLLOCK
KEY_SEMICOLON: int = pygame.K_SEMICOLON
KEY_SLASH: int = pygame.K_SLASH
KEY_SPACE: int = pygame.K_SPACE
KEY_SYSREQ: int = pygame.K_SYSREQ
KEY_TAB: int = pygame.K_TAB
KEY_UNDERSCORE: int = pygame.K_UNDERSCORE
KEY_UNKNOWN: int = pygame.K_UNKNOWN
KEY_UP: int = pygame.K_UP
KEY_a: int = pygame.K_a
KEY_b: int = pygame.K_b
KEY_c: int = pygame.K_c
KEY_d: int = pygame.K_d
KEY_e: int = pygame.K_e
KEY_f: int = pygame.K_f
KEY_g: int = pygame.K_g
KEY_h: int = pygame.K_h
KEY_i: int = pygame.K_i
KEY_j: int = pygame.K_j
KEY_k: int = pygame.K_k
KEY_l: int = pygame.K_l
KEY_m: int = pygame.K_m
KEY_n: int = pygame.K_n
KEY_o: int = pygame.K_o
KEY_p: int = pygame.K_p
KEY_q: int = pygame.K_q
KEY_r: int = pygame.K_r
KEY_s: int = pygame.K_s
KEY_t: int = pygame.K_t
KEY_u: int = pygame.K_u
KEY_v: int = pygame.K_v
KEY_w: int = pygame.K_w
KEY_x: int = pygame.K_x
KEY_y: int = pygame.K_y
KEY_z: int = pygame.K_z
MOUSE_BUTTON_1: int = 1
MOUSE_BUTTON_2: int = 2
MOUSE_BUTTON_3: int = 3
MOUSE_MOTION_UP: Tuple[int, int] = (0, -1)
MOUSE_MOTION_RIGHT: Tuple[int, int] = (1, 0)
MOUSE_MOTION_DOWN: Tuple[int, int] = (0, 1)
MOUSE_MOTION_LEFT: Tuple[int, int] = (-1, 0)
MOUSE_WHEEL_UP: Tuple[int, int] = (0, -1)
MOUSE_WHEEL_RIGHT: Tuple[int, int] = (1, 0)
MOUSE_WHEEL_DOWN: Tuple[int, int] = (0, 1)
MOUSE_WHEEL_LEFT: Tuple[int, int] = (-1, 0)


class InputHandler:
    """
    This class is to handle inputs.

    It has an input_binding dictionary where you need to add the desired input
    associate to an input id by keeping the following rules:

    - Any pair (key, input_id) should be added to input_binding["keyboard"].
    - Any pair (mouse_button, input_id) should be added to input_binding["mouse_click"].
    - Any pair (mouse_wheel, input_id) should be added to input_binding["mouse_wheel"].
    - Any pair (mouse_motion, input_id) should be added to input_binding["mouse_motion"].
    """

    input_binding: Dict[str, Union[Dict[int, str], Dict[Tuple[int, int], str]]] = {
        "keyboard": {},
        "mouse_click": {},
        "mouse_wheel": {},
        "mouse_motion": {},
    }

    listeners: List[InputListener] = []

    @classmethod
    def register_listener(cls, listener: InputListener) -> None:
        if not hasattr(listener, "on_input"):
            raise InvalidListenerException(
                "Listener should implement the method on_input(input_id, input_data)"
            )
        cls.listeners.append(listener)

    @classmethod
    def unregister_listener(cls, listener: InputListener) -> None:
        cls.listeners = [l for l in cls.listeners if l != listener]

    @classmethod
    def notify(cls, action_id: str, action_data: InputData) -> None:
        for l in cls.listeners:
            l.on_input(action_id, action_data)

    @classmethod
    def set_keyboard_action(cls, key: int, action_id: str) -> None:
        cls.input_binding["keyboard"][key] = action_id

    @classmethod
    def set_mouse_click_action(cls, button: int, action_id: str) -> None:
        cls.input_binding["mouse_click"][button] = action_id

    @classmethod
    def set_mouse_wheel_action(cls, direction: Tuple[int, int], action_id: str) -> None:
        cls.input_binding["mouse_wheel"][direction] = action_id

    @classmethod
    def set_mouse_wheel_action(cls, direction: Tuple[int, int], action_id: str) -> None:
        cls.input_binding["mouse_motion"][direction] = action_id

    @classmethod
    def handle_input(cls, event: pygame.event.Event) -> None:
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            action: Optional[str] = cls.input_binding["keyboard"].get(event.key)
            if action is not None:
                data = KeyboardData(
                    event.type == pygame.KEYDOWN,
                    event.type == pygame.KEYUP,
                    event.mod,
                    event.unicode,
                )
                cls.notify(action, data)
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            action: Optional[str] = cls.input_binding["mouse_click"].get(event.button)
            if action is not None:
                data = MouseClickData(
                    event.type == pygame.MOUSEBUTTONDOWN,
                    event.type == pygame.MOUSEBUTTONUP,
                    event.button,
                    event.pos,
                )
                cls.notify(action, data)
        elif event.type == pygame.MOUSEWHEEL:
            action: Optional[str] = cls.input_binding.get("mouse_wheel").get(
                (event.x, event.y)
            )
            if action is not None:
                data = MouseWheelData(event.flipped)
                cls.notify(action, data)
        elif event.type == pygame.MOUSEMOTION:
            action: Optional[str] = cls.input_binding.get("mouse_motion").get(event.rel)
            if action is not None:
                data = MouseMotionData(event.pos, event.buttons)
                cls.notify(action, data)
