"""
This file contains InputHandler, an observer-pattern-based dispatcher
mapping keyboard (including modifier combos), mouse (clicks, wheel,
motion), and gamepad (buttons, axes, hotplug) input to named actions,
notifying every registered InputListener when one fires — plus every
KEY_*/MOUSE_*/GAMEPAD_* constant and *Data class involved.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Tuple, Union, TypeVar, NoReturn, Dict, List, Optional, Type

import pygame

INPUT_EVENTS: Tuple[int, ...] = (
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
    pygame.MOUSEWHEEL,
    pygame.MOUSEMOTION,
    pygame.CONTROLLERBUTTONDOWN,
    pygame.CONTROLLERBUTTONUP,
    pygame.CONTROLLERAXISMOTION,
    pygame.CONTROLLERDEVICEADDED,
    pygame.CONTROLLERDEVICEREMOVED,
)

# Modifier keys that can be combined with a regular key to build a key
# combo, for instance, MOD_CTRL | MOD_SHIFT to represent Ctrl + Shift.
MOD_NONE: int = pygame.KMOD_NONE
MOD_SHIFT: int = pygame.KMOD_SHIFT
MOD_CTRL: int = pygame.KMOD_CTRL
MOD_ALT: int = pygame.KMOD_ALT
MOD_META: int = pygame.KMOD_META

# Modifiers that gale takes into account to resolve key combos. Lock keys
# such as Caps Lock or Num Lock are intentionally ignored.
_COMBINABLE_MODIFIERS: Tuple[int, int, int, int] = (
    MOD_SHIFT,
    MOD_CTRL,
    MOD_ALT,
    MOD_META,
)


def _normalize_modifiers(raw_modifiers: int) -> int:
    """
    Each MOD_* constant (e.g. MOD_CTRL) is actually the combination of
    its left and right variants (e.g. KMOD_LCTRL | KMOD_RCTRL), but a
    real key press only ever reports whichever single side was held,
    never that combined value. This maps a raw pygame modifier state
    to the combination of MOD_* constants a binding could have been
    registered with, so holding either (or both) side of a modifier
    matches a binding requiring it.
    """
    normalized = 0

    for family in _COMBINABLE_MODIFIERS:
        if raw_modifiers & family:
            normalized |= family

    return normalized


class InvalidListenerException(Exception):
    pass


class KeyboardData:
    """
    Group the data associated to a keyboad input event.
    """

    def __init__(self, event: pygame.event.Event) -> None:
        self.pressed: bool = event.type == pygame.KEYDOWN
        self.released: bool = event.type == pygame.KEYUP
        self.modifier: int = event.mod
        self.unicode: str = event.unicode
        self.key: int = event.key

    @staticmethod
    def get_action_key(event: pygame.event.Event) -> Tuple[int, int]:
        return (_normalize_modifiers(event.mod), event.key)

    @staticmethod
    def get_action_name():
        return "keyboard"


class MouseClickData:
    """
    Group the data associated to a mouse click event.
    """

    def __init__(self, event: pygame.event.Event) -> None:
        self.pressed: bool = event.type == pygame.MOUSEBUTTONDOWN
        self.released: bool = event.type == pygame.MOUSEBUTTONUP
        self.button: int = event.button
        self.position: Tuple[int, int] = event.pos

    @staticmethod
    def get_action_key(event: pygame.event.Event) -> int:
        return event.button

    @staticmethod
    def get_action_name():
        return "mouse_click"


class MouseWheelData:
    """
    Group the data associated to a mouse wheel event.
    """

    def __init__(self, event: pygame.event.Event) -> None:
        self.flipped: bool = event.flipped

    @staticmethod
    def get_action_key(event: pygame.event.Event) -> Tuple[int, int]:
        return event.x, event.y

    @staticmethod
    def get_action_name():
        return "mouse_wheel"


class MouseMotionData:
    """
    Group the data associated to a mouse motion event.
    """

    def __init__(self, event: pygame.event.Event) -> None:
        self.position: Tuple[int, int] = event.pos
        self.buttons: Tuple[int, int, int] = event.buttons

    @staticmethod
    def get_action_key(event: pygame.event.Event) -> Tuple[int, int]:
        return event.rel

    @staticmethod
    def get_action_name():
        return "mouse_motion"


class GamepadButtonData:
    """
    Group the data associated to a gamepad button event. Uses SDL's
    "game controller" abstraction (pygame's CONTROLLER* events, not
    the lower-level, per-device JOY* ones), so button meaning (A, B,
    the D-pad, the shoulders...) is consistent across controller
    brands (Xbox, PlayStation, generic...) instead of varying by raw
    button index.
    """

    def __init__(self, event: pygame.event.Event) -> None:
        self.pressed: bool = event.type == pygame.CONTROLLERBUTTONDOWN
        self.released: bool = event.type == pygame.CONTROLLERBUTTONUP
        self.button: int = event.button
        self.gamepad_id: int = event.instance_id

    @staticmethod
    def get_action_key(event: pygame.event.Event) -> Tuple[int, int]:
        return (event.instance_id, event.button)

    @staticmethod
    def get_action_name():
        return "gamepad_button"


class GamepadAxisData:
    """
    Group the data associated to a gamepad axis motion event (an
    analog stick or a trigger). Fired continuously as the axis moves,
    the same way MouseMotionData is: bind it once with
    set_gamepad_axis_action and read value every time it is notified,
    rather than expecting a single discrete event.
    """

    def __init__(self, event: pygame.event.Event) -> None:
        value = event.value
        # Most pygame builds already normalize this to [-1.0, 1.0]
        # ([0.0, 1.0] for a trigger), but fall back to normalizing the
        # raw SDL int16 range ([-32768, 32767]) in case a given build
        # doesn't, so games never have to special-case this themselves.
        self.value: float = value if abs(value) <= 1.0 else value / 32768.0
        self.axis: int = event.axis
        self.gamepad_id: int = event.instance_id

    @staticmethod
    def get_action_key(event: pygame.event.Event) -> Tuple[int, int]:
        return (event.instance_id, event.axis)

    @staticmethod
    def get_action_name():
        return "gamepad_axis"


InputData = TypeVar(
    "InputData",
    bound=Union[
        KeyboardData,
        MouseClickData,
        MouseWheelData,
        MouseMotionData,
        GamepadButtonData,
        GamepadAxisData,
    ],
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

GAMEPAD_BUTTON_A: int = pygame.CONTROLLER_BUTTON_A
GAMEPAD_BUTTON_B: int = pygame.CONTROLLER_BUTTON_B
GAMEPAD_BUTTON_X: int = pygame.CONTROLLER_BUTTON_X
GAMEPAD_BUTTON_Y: int = pygame.CONTROLLER_BUTTON_Y
GAMEPAD_BUTTON_BACK: int = pygame.CONTROLLER_BUTTON_BACK
GAMEPAD_BUTTON_GUIDE: int = pygame.CONTROLLER_BUTTON_GUIDE
GAMEPAD_BUTTON_START: int = pygame.CONTROLLER_BUTTON_START
GAMEPAD_BUTTON_LEFTSTICK: int = pygame.CONTROLLER_BUTTON_LEFTSTICK
GAMEPAD_BUTTON_RIGHTSTICK: int = pygame.CONTROLLER_BUTTON_RIGHTSTICK
GAMEPAD_BUTTON_LEFTSHOULDER: int = pygame.CONTROLLER_BUTTON_LEFTSHOULDER
GAMEPAD_BUTTON_RIGHTSHOULDER: int = pygame.CONTROLLER_BUTTON_RIGHTSHOULDER
GAMEPAD_BUTTON_DPAD_UP: int = pygame.CONTROLLER_BUTTON_DPAD_UP
GAMEPAD_BUTTON_DPAD_DOWN: int = pygame.CONTROLLER_BUTTON_DPAD_DOWN
GAMEPAD_BUTTON_DPAD_LEFT: int = pygame.CONTROLLER_BUTTON_DPAD_LEFT
GAMEPAD_BUTTON_DPAD_RIGHT: int = pygame.CONTROLLER_BUTTON_DPAD_RIGHT

GAMEPAD_AXIS_LEFT_X: int = pygame.CONTROLLER_AXIS_LEFTX
GAMEPAD_AXIS_LEFT_Y: int = pygame.CONTROLLER_AXIS_LEFTY
GAMEPAD_AXIS_RIGHT_X: int = pygame.CONTROLLER_AXIS_RIGHTX
GAMEPAD_AXIS_RIGHT_Y: int = pygame.CONTROLLER_AXIS_RIGHTY
GAMEPAD_AXIS_TRIGGER_LEFT: int = pygame.CONTROLLER_AXIS_TRIGGERLEFT
GAMEPAD_AXIS_TRIGGER_RIGHT: int = pygame.CONTROLLER_AXIS_TRIGGERRIGHT


def apply_deadzone(value: float, threshold: float = 0.15) -> float:
    """
    Analog sticks rarely rest at exactly 0.0 (a bit of drift is
    normal), so a raw GamepadAxisData.value is usually run through
    this before acting on it.

    :param value: A raw axis value, typically GamepadAxisData.value.
    :param threshold: Values whose magnitude is at or below this are snapped to 0.0. The default value is 0.15.
    :returns: 0.0 if abs(value) <= threshold, otherwise value unchanged.
    """
    return 0.0 if abs(value) <= threshold else value


class InputHandler:
    """
    This class is to handle inputs.

    It has an input_binding dictionary where you need to add the desired input
    associate to an input id by keeping the following rules:

    - Any pair ((modifiers, key), input_id) should be added to input_binding["keyboard"].
    - Any pair (mouse_button, input_id) should be added to input_binding["mouse_click"].
    - Any pair (mouse_wheel, input_id) should be added to input_binding["mouse_wheel"].
    - Any pair (mouse_motion, input_id) should be added to input_binding["mouse_motion"].
    - Any pair ((gamepad_id, button), input_id) should be added to input_binding["gamepad_button"].
    - Any pair ((gamepad_id, axis), input_id) should be added to input_binding["gamepad_axis"].

    Keyboard bindings support combos with the modifier keys Shift, Ctrl, Alt,
    and Meta (also known as Super/Windows/Command key). Use set_keyboard_action
    passing a combination of MOD_SHIFT, MOD_CTRL, MOD_ALT, and/or MOD_META
    (joined with the bitwise or operator) through the modifiers argument, for
    instance:

        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.set_keyboard_action(
            KEY_s, "save_as", modifiers=MOD_CTRL | MOD_SHIFT
        )

    A binding registered without modifiers (the default) is triggered
    regardless of which modifiers are held, as long as there is no more
    specific binding matching the exact combo that is currently pressed.

    Gamepads need one extra call, once at startup, to be recognized at
    all (see init_gamepads); once that's done, a game with a single
    local player typically leaves gamepad_id as None on every binding
    (the default), matching input from whichever gamepad is plugged
    in. Local multiplayer instead binds the same button/axis to a
    different action_id per player by passing each player's own
    gamepad_id (see GamepadButtonData.gamepad_id/GamepadAxisData.gamepad_id
    to find out which gamepad a given event came from in the first
    place, e.g. while prompting "press A on your gamepad" during setup).
    """

    INPUT_DATA_TABLE: Dict[int, Type] = {
        pygame.KEYDOWN: KeyboardData,
        pygame.KEYUP: KeyboardData,
        pygame.MOUSEBUTTONUP: MouseClickData,
        pygame.MOUSEBUTTONDOWN: MouseClickData,
        pygame.MOUSEMOTION: MouseMotionData,
        pygame.MOUSEWHEEL: MouseWheelData,
        pygame.CONTROLLERBUTTONDOWN: GamepadButtonData,
        pygame.CONTROLLERBUTTONUP: GamepadButtonData,
        pygame.CONTROLLERAXISMOTION: GamepadAxisData,
    }

    input_binding: Dict[str, Dict] = {
        KeyboardData.get_action_name(): {},
        MouseClickData.get_action_name(): {},
        MouseWheelData.get_action_name(): {},
        MouseMotionData.get_action_name(): {},
        GamepadButtonData.get_action_name(): {},
        GamepadAxisData.get_action_name(): {},
    }

    # Every currently connected gamepad, keyed by the instance_id
    # GamepadButtonData/GamepadAxisData events report. A reference has
    # to be kept alive here for as long as the gamepad is connected,
    # or pygame/SDL closes the underlying device and stops sending
    # events for it.
    gamepads: Dict[int, "pygame.joystick.JoystickType"] = {}

    listeners: List[InputListener] = []

    @classmethod
    def init_gamepads(cls) -> None:
        """
        Open every currently connected gamepad, and start reacting to
        CONTROLLERDEVICEADDED/CONTROLLERDEVICEREMOVED so gamepads
        plugged in or unplugged later are picked up/dropped
        automatically too. Call this once at startup, before any
        gamepad input is expected to work (uninitialized, gamepad
        events are never generated at all).
        """
        pygame.joystick.init()

        for device_index in range(pygame.joystick.get_count()):
            cls._open_gamepad(device_index)

    @classmethod
    def _open_gamepad(cls, device_index: int) -> None:
        gamepad = pygame.joystick.Joystick(device_index)
        cls.gamepads[gamepad.get_instance_id()] = gamepad

    @classmethod
    def _close_gamepad(cls, instance_id: int) -> None:
        cls.gamepads.pop(instance_id, None)

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
        for l in cls.listeners.copy():
            l.on_input(action_id, action_data)

    @classmethod
    def set_keyboard_action(
        cls, key: int, action_id: str, modifiers: int = MOD_NONE
    ) -> None:
        """
        Bind a keyboard key, optionally combined with modifiers, to an action.

        :param key: The key code (one of the KEY_* constants).
        :param action_id: The identifier of the action to notify.
        :param modifiers: A combination (bitwise or) of MOD_SHIFT, MOD_CTRL, MOD_ALT, and/or MOD_META that must be held for this binding to trigger. By default, MOD_NONE, meaning that the binding triggers regardless of the modifiers held, unless a more specific combo is also bound to the same key.
        """
        cls.input_binding[KeyboardData.get_action_name()][
            (_normalize_modifiers(modifiers), key)
        ] = action_id

    @classmethod
    def set_mouse_click_action(cls, button: int, action_id: str) -> None:
        cls.input_binding[MouseClickData.get_action_name()][button] = action_id

    @classmethod
    def set_mouse_wheel_action(cls, direction: Tuple[int, int], action_id: str) -> None:
        cls.input_binding[MouseWheelData.get_action_name()][direction] = action_id

    @classmethod
    def set_mouse_motion_action(
        cls, direction: Optional[Tuple[int, int]], action_id: str
    ) -> None:
        """
        :param direction: One of the MOUSE_MOTION_* constants, matched only when the raw motion is exactly that unit vector. Pass None instead to register a wildcard fired for every motion event that does not match a more specific direction binding (the usual choice for continuous mouse tracking, such as hovering over a widget in gale.ui, since real motion deltas rarely equal exactly (0, -1) and friends).
        :param action_id: The identifier of the action to notify.
        """
        cls.input_binding[MouseMotionData.get_action_name()][direction] = action_id

    @classmethod
    def set_gamepad_button_action(
        cls, button: int, action_id: str, gamepad_id: Optional[int] = None
    ) -> None:
        """
        :param button: One of the GAMEPAD_BUTTON_* constants.
        :param action_id: The identifier of the action to notify.
        :param gamepad_id: Restrict this binding to a single gamepad (its GamepadButtonData.gamepad_id, from an earlier event, e.g. while prompting a player to press a button during local co-op setup). The default value is None, matching this button on every connected gamepad, unless a more specific binding for the same button also exists for whichever gamepad triggered the event.
        """
        cls.input_binding[GamepadButtonData.get_action_name()][
            (gamepad_id, button)
        ] = action_id

    @classmethod
    def set_gamepad_axis_action(
        cls, axis: int, action_id: str, gamepad_id: Optional[int] = None
    ) -> None:
        """
        :param axis: One of the GAMEPAD_AXIS_* constants.
        :param action_id: The identifier of the action to notify.
        :param gamepad_id: Restrict this binding to a single gamepad. The default value is None, matching this axis on every connected gamepad, unless a more specific binding for the same axis also exists for whichever gamepad triggered the event. See set_gamepad_button_action for the local co-op use case this is for.
        """
        cls.input_binding[GamepadAxisData.get_action_name()][
            (gamepad_id, axis)
        ] = action_id

    @classmethod
    def handle_input(cls, event: pygame.event.Event) -> None:
        if event.type == pygame.CONTROLLERDEVICEADDED:
            cls._open_gamepad(event.device_index)
            return

        if event.type == pygame.CONTROLLERDEVICEREMOVED:
            cls._close_gamepad(event.instance_id)
            return

        data_class: Optional[Type] = cls.INPUT_DATA_TABLE.get(event.type)

        if data_class is None:
            return

        bindings = cls.input_binding[data_class.get_action_name()]
        action_key = data_class.get_action_key(event)
        action: Optional[str] = bindings.get(action_key)

        if action is None and data_class is KeyboardData and action_key[0] != MOD_NONE:
            # No binding matched the exact combo of modifiers held, fall
            # back to a plain binding for the key without modifiers.
            action = bindings.get((MOD_NONE, action_key[1]))
        elif action is None and data_class is MouseMotionData:
            # No binding matched this exact relative motion vector, fall
            # back to the wildcard registered (if any) via
            # set_mouse_motion_action(None, action_id).
            action = bindings.get(None)
        elif (
            action is None
            and data_class in (GamepadButtonData, GamepadAxisData)
            and action_key[0] is not None
        ):
            # No binding matched this exact gamepad, fall back to a
            # binding for the button/axis on any gamepad.
            action = bindings.get((None, action_key[1]))

        if action is not None:
            data = data_class(event)
            cls.notify(action, data)
