import unittest

import pygame

from gale.input_handler import (
    InputHandler,
    KEY_a,
    KEY_s,
    MOD_CTRL,
    MOD_NONE,
    MOD_SHIFT,
)


def keydown(key: int, mod: int = MOD_NONE) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode="")


class InputHandlerKeyComboTestCase(unittest.TestCase):
    def setUp(self) -> None:
        InputHandler.input_binding["keyboard"] = {}
        InputHandler.listeners = []
        self.received = []
        InputHandler.register_listener(self)

    def on_input(self, input_id: str, input_data) -> None:
        self.received.append(input_id)

    def test_plain_binding_ignores_unbound_modifiers(self) -> None:
        InputHandler.set_keyboard_action(KEY_a, "plain")
        InputHandler.handle_input(keydown(KEY_a))
        InputHandler.handle_input(keydown(KEY_a, MOD_SHIFT))
        self.assertEqual(self.received, ["plain", "plain"])

    def test_combo_binding_requires_exact_modifiers(self) -> None:
        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.handle_input(keydown(KEY_s, MOD_CTRL))
        InputHandler.handle_input(keydown(KEY_s, MOD_NONE))
        self.assertEqual(self.received, ["save"])

    def test_more_specific_combo_takes_precedence(self) -> None:
        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.set_keyboard_action(
            KEY_s, "save_as", modifiers=MOD_CTRL | MOD_SHIFT
        )
        InputHandler.handle_input(keydown(KEY_s, MOD_CTRL))
        InputHandler.handle_input(keydown(KEY_s, MOD_CTRL | MOD_SHIFT))
        self.assertEqual(self.received, ["save", "save_as"])

    def test_combo_only_binding_does_not_fall_back(self) -> None:
        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.handle_input(keydown(KEY_s, MOD_NONE))
        self.assertEqual(self.received, [])

    def test_combo_triggers_holding_only_one_side_of_the_modifier(self) -> None:
        # MOD_CTRL (like every MOD_* constant) is the combination of its
        # left and right variants (KMOD_LCTRL | KMOD_RCTRL), but pygame
        # only ever reports whichever single side is physically held,
        # never that combined value. A binding registered with MOD_CTRL
        # must still fire from a real, single-sided Ctrl press.
        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.handle_input(keydown(KEY_s, pygame.KMOD_LCTRL))
        InputHandler.handle_input(keydown(KEY_s, pygame.KMOD_RCTRL))
        self.assertEqual(self.received, ["save", "save"])

    def test_combo_ignores_lock_keys(self) -> None:
        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.handle_input(
            keydown(KEY_s, pygame.KMOD_LCTRL | pygame.KMOD_CAPS | pygame.KMOD_NUM)
        )
        self.assertEqual(self.received, ["save"])

    def test_combo_does_not_trigger_with_a_different_modifier(self) -> None:
        InputHandler.set_keyboard_action(KEY_s, "save", modifiers=MOD_CTRL)
        InputHandler.handle_input(keydown(KEY_s, pygame.KMOD_LALT))
        self.assertEqual(self.received, [])
