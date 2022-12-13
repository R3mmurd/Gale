"""
This file contains the implementation of an observer-pattern-based
input handler.

Author: Alejandro Mujica
"""

from enum import Enum

import pygame

INPUT_EVENTS = (
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
    pygame.MOUSEWHEEL,
    pygame.MOUSEMOTION
)

class InputListener:
    """
    This is an interface to any class that need to be an
    input listener.
    """
    def on_input(self, input_id, input_data):
        raise NotImplementedError
    

class InvalidListenerException(Exception):
    pass


class KeyboardData:
    """
    Group the data associated to a keyboad input event.
    """
    def __init__(self, pressed, released, modifier, unicode):
        self.pressed = pressed
        self.released = released
        self.modifier = modifier
        self.unicode = unicode


class MouseClickData:
    """
    Group the data associated to a mouse click event.
    """
    def __init__(self, pressed, released, button, position):
        self.pressed = pressed
        self.released = released
        self.button = button
        self.position = position


class MouseWheelData:
    """
    Group the data associated to a mouse wheel event.
    """
    def __init__(self, flipped):
        self.flipped = flipped


class MouseMotionData:
    """
    Group the data associated to a mouse motion event.
    """
    def __init__(self, position, buttons) -> None:
        self.position = position
        self.buttons = buttons

class Key(Enum):
    KEY_0 = pygame.K_0
    KEY_1 = pygame.K_1
    KEY_2 = pygame.K_2
    KEY_3 = pygame.K_3
    KEY_4 = pygame.K_4
    KEY_5 = pygame.K_5
    KEY_6 = pygame.K_6
    KEY_7 = pygame.K_7
    KEY_8 = pygame.K_8
    KEY_9 = pygame.K_9
    KEY_AC_BACK = pygame.K_AC_BACK
    KEY_AMPERSAND = pygame.K_AMPERSAND
    KEY_ASTERISK = pygame.K_ASTERISK
    KEY_AT = pygame.K_AT
    KEY_BACKQUOTE = pygame.K_BACKQUOTE
    KEY_BACKSLASH = pygame.K_BACKSLASH
    KEY_BACKSPACE = pygame.K_BACKSPACE
    KEY_BREAK = pygame.K_BREAK
    KEY_CAPSLOCK = pygame.K_CAPSLOCK
    KEY_CARET = pygame.K_CARET
    KEY_CLEAR = pygame.K_CLEAR
    KEY_COLON = pygame.K_COLON
    KEY_COMMA = pygame.K_COMMA
    KEY_CURRENCYSUBUNIT = pygame.K_CURRENCYSUBUNIT
    KEY_CURRENCYUNIT = pygame.K_CURRENCYUNIT
    KEY_DELETE = pygame.K_DELETE
    KEY_DOLLAR = pygame.K_DOLLAR
    KEY_DOWN = pygame.K_DOWN
    KEY_END = pygame.K_END
    KEY_EQUALS = pygame.K_EQUALS
    KEY_ESCAPE = pygame.K_ESCAPE
    KEY_EURO = pygame.K_EURO
    KEY_EXCLAIM = pygame.K_EXCLAIM
    KEY_F1 = pygame.K_F1
    KEY_F10 = pygame.K_F10
    KEY_F11 = pygame.K_F11
    KEY_F12 = pygame.K_F12
    KEY_F13 = pygame.K_F13
    KEY_F14 = pygame.K_F14
    KEY_F15 = pygame.K_F15
    KEY_F2 = pygame.K_F2
    KEY_F3 = pygame.K_F3
    KEY_F4 = pygame.K_F4
    KEY_F5 = pygame.K_F5
    KEY_F6 = pygame.K_F6
    KEY_F7 = pygame.K_F7
    KEY_F8 = pygame.K_F8
    KEY_F9 = pygame.K_F9
    KEY_GREATER = pygame.K_GREATER
    KEY_HASH = pygame.K_HASH
    KEY_HELP = pygame.K_HELP
    KEY_HOME = pygame.K_HOME
    KEY_INSERT = pygame.K_INSERT
    KEY_KP0 = pygame.K_KP0
    KEY_KP1 = pygame.K_KP1
    KEY_KP2 = pygame.K_KP2
    KEY_KP3 = pygame.K_KP3
    KEY_KP4 = pygame.K_KP4
    KEY_KP5 = pygame.K_KP5
    KEY_KP6 = pygame.K_KP6
    KEY_KP7 = pygame.K_KP7
    KEY_KP8 = pygame.K_KP8
    KEY_KP9 = pygame.K_KP9
    KEY_KP_0 = pygame.K_KP_0
    KEY_KP_1 = pygame.K_KP_1
    KEY_KP_2 = pygame.K_KP_2
    KEY_KP_3 = pygame.K_KP_3
    KEY_KP_4 = pygame.K_KP_4
    KEY_KP_5 = pygame.K_KP_5
    KEY_KP_6 = pygame.K_KP_6
    KEY_KP_7 = pygame.K_KP_7
    KEY_KP_8 = pygame.K_KP_8
    KEY_KP_9 = pygame.K_KP_9
    KEY_KP_DIVIDE = pygame.K_KP_DIVIDE
    KEY_KP_ENTER = pygame.K_KP_ENTER
    KEY_KP_EQUALS = pygame.K_KP_EQUALS
    KEY_KP_MINUS = pygame.K_KP_MINUS
    KEY_KP_MULTIPLY = pygame.K_KP_MULTIPLY
    KEY_KP_PERIOD = pygame.K_KP_PERIOD
    KEY_KP_PLUS = pygame.K_KP_PLUS
    KEY_LALT = pygame.K_LALT
    KEY_LCTRL = pygame.K_LCTRL
    KEY_LEFT = pygame.K_LEFT
    KEY_LEFTBRACKET = pygame.K_LEFTBRACKET
    KEY_LEFTPAREN = pygame.K_LEFTPAREN
    KEY_LESS = pygame.K_LESS
    KEY_LGUI = pygame.K_LGUI
    KEY_LMETA = pygame.K_LMETA
    KEY_LSHIFT = pygame.K_LSHIFT
    KEY_LSUPER = pygame.K_LSUPER
    KEY_MENU = pygame.K_MENU
    KEY_MINUS = pygame.K_MINUS
    KEY_MODE = pygame.K_MODE
    KEY_NUMLOCK = pygame.K_NUMLOCK
    KEY_NUMLOCKCLEAR = pygame.K_NUMLOCKCLEAR
    KEY_PAGEDOWN = pygame.K_PAGEDOWN
    KEY_PAGEUP = pygame.K_PAGEUP
    KEY_PAUSE = pygame.K_PAUSE
    KEY_PERCENT = pygame.K_PERCENT
    KEY_PERIOD = pygame.K_PERIOD
    KEY_PLUS = pygame.K_PLUS
    KEY_POWER = pygame.K_POWER
    KEY_PRINT = pygame.K_PRINT
    KEY_PRINTSCREEN = pygame.K_PRINTSCREEN
    KEY_QUESTION = pygame.K_QUESTION
    KEY_QUOTE = pygame.K_QUOTE
    KEY_QUOTEDBL = pygame.K_QUOTEDBL
    KEY_RALT = pygame.K_RALT
    KEY_RCTRL = pygame.K_RCTRL
    KEY_RETURN = pygame.K_RETURN
    KEY_RGUI = pygame.K_RGUI
    KEY_RIGHT = pygame.K_RIGHT
    KEY_RIGHTBRACKET = pygame.K_RIGHTBRACKET
    KEY_RIGHTPAREN = pygame.K_RIGHTPAREN
    KEY_RMETA = pygame.K_RMETA
    KEY_RSHIFT = pygame.K_RSHIFT
    KEY_RSUPER = pygame.K_RSUPER
    KEY_SCROLLLOCK = pygame.K_SCROLLLOCK
    KEY_SCROLLOCK = pygame.K_SCROLLOCK
    KEY_SEMICOLON = pygame.K_SEMICOLON
    KEY_SLASH = pygame.K_SLASH
    KEY_SPACE = pygame.K_SPACE
    KEY_SYSREQ = pygame.K_SYSREQ
    KEY_TAB = pygame.K_TAB
    KEY_UNDERSCORE = pygame.K_UNDERSCORE
    KEY_UNKNOWN = pygame.K_UNKNOWN
    KEY_UP = pygame.K_UP
    KEY_a = pygame.K_a
    KEY_b = pygame.K_b
    KEY_c = pygame.K_c
    KEY_d = pygame.K_d
    KEY_e = pygame.K_e
    KEY_f = pygame.K_f
    KEY_g = pygame.K_g
    KEY_h = pygame.K_h
    KEY_i = pygame.K_i
    KEY_j = pygame.K_j
    KEY_k = pygame.K_k
    KEY_l = pygame.K_l
    KEY_m = pygame.K_m
    KEY_n = pygame.K_n
    KEY_o = pygame.K_o
    KEY_p = pygame.K_p
    KEY_q = pygame.K_q
    KEY_r = pygame.K_r
    KEY_s = pygame.K_s
    KEY_t = pygame.K_t
    KEY_u = pygame.K_u
    KEY_v = pygame.K_v
    KEY_w = pygame.K_w
    KEY_x = pygame.K_x
    KEY_y = pygame.K_y
    KEY_z = pygame.K_z

class Mouse(Enum):
    BUTTON_1 = 1
    BUTTON_2 = 2
    BUTTON_3 = 3
    MOTION_UP = (0, -1)
    MOTION_RIGHT = (1, 0)
    MOTION_DOWN = (0, 1)
    MOTION_LEFT = (-1, 0)
    WHEEL_UP = (0, -1)
    WHEEL_RIGHT = (1, 0)
    WHEEL_DOWN = (0, 1)
    WHEEL_LEFT = (-1, 0)


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
    input_binding = {
        "keyboard": {},
        "mouse_click": {},
        "mouse_wheel": {},
        "mouse_motion": {},
    }

    listeners = []

    @classmethod
    def register_listener(cls, listener):
        if not hasattr(listener, 'on_input'):
            raise InvalidListenerException("Listener should implement the method on_input(input_id, input_data)")
        cls.listeners.append(listener)

    @classmethod
    def unregister_listener(cls, listener):
        cls.listeners = [l for l in cls.listeners if l != listener]

    @classmethod
    def notify(cls, action, event):
        for l in cls.listeners:
            l.on_input(action, event)

    @classmethod
    def set_keyboard_action(cls, key, action_id):
        cls.input_binding["keyboard"][key] = action_id
    
    @classmethod
    def set_mouse_click_action(cls, key, action_id):
        cls.input_binding["mouse_click"][key] = action_id
    
    @classmethod
    def set_mouse_wheel_action(cls, key, action_id):
        cls.input_binding["mouse_wheel"][key] = action_id
    
    @classmethod
    def set_mouse_wheel_action(cls, key, action_id):
        cls.input_binding["mouse_motion"][key] = action_id

    @classmethod
    def handle_input(cls, event) -> None:
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            action = cls.input_binding["keyboard"].get(event.key)
            if action is not None:
                data = KeyboardData(
                    event.type == pygame.KEYDOWN,
                    event.type == pygame.KEYUP,
                    event.mod,
                    event.unicode,
                )
                cls.notify(action, data)
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            action = cls.input_binding["mouse_click"].get(event.button)
            if action is not None:
                data = MouseClickData(
                    event.type == pygame.MOUSEBUTTONDOWN,
                    event.type == pygame.MOUSEBUTTONUP,
                    event.button,
                    event.pos
                )
                cls.notify(action, data)
        elif event.type == pygame.MOUSEWHEEL:
            action = cls.input_binding.get("mouse_wheel").get((event.x, event.y))
            if action is not None:
                data = MouseWheelData(event.flipped)
                cls.notify(action, data)
        elif event.type == pygame.MOUSEMOTION:
            action = cls.input_binding.get("mouse_motion").get(event.rel)
            if action is not None:
                data = MouseMotionData(event.pos, event.buttons)
                cls.notify(action, data)
