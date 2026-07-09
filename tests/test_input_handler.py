import unittest

import pygame

from gale.input_handler import (
    GAMEPAD_AXIS_LEFT_X,
    GAMEPAD_BUTTON_A,
    GAMEPAD_BUTTON_B,
    InputHandler,
    KEY_a,
    KEY_s,
    MOD_CTRL,
    MOD_NONE,
    MOD_SHIFT,
    apply_deadzone,
)


def keydown(key: int, mod: int = MOD_NONE) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode="")


def gamepad_button_down(button: int, instance_id: int = 0) -> pygame.event.Event:
    return pygame.event.Event(
        pygame.CONTROLLERBUTTONDOWN, instance_id=instance_id, button=button
    )


def gamepad_axis_motion(
    axis: int, value: float, instance_id: int = 0
) -> pygame.event.Event:
    return pygame.event.Event(
        pygame.CONTROLLERAXISMOTION, instance_id=instance_id, axis=axis, value=value
    )


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


class InputHandlerGamepadTestCase(unittest.TestCase):
    def setUp(self) -> None:
        InputHandler.input_binding["gamepad_button"] = {}
        InputHandler.input_binding["gamepad_axis"] = {}
        InputHandler.gamepads = {}
        InputHandler.listeners = []
        self.received = []
        InputHandler.register_listener(self)

    def on_input(self, input_id: str, input_data) -> None:
        self.received.append((input_id, input_data))

    def test_button_binding_matches_any_gamepad_by_default(self) -> None:
        InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_A, "jump")
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_A, instance_id=0))
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_A, instance_id=1))
        self.assertEqual([i for i, _ in self.received], ["jump", "jump"])

    def test_button_binding_can_be_restricted_to_one_gamepad(self) -> None:
        InputHandler.set_gamepad_button_action(
            GAMEPAD_BUTTON_A, "p1_jump", gamepad_id=1
        )
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_A, instance_id=0))
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_A, instance_id=1))
        self.assertEqual([i for i, _ in self.received], ["p1_jump"])

    def test_specific_gamepad_binding_takes_precedence_over_wildcard(self) -> None:
        InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_B, "any_special")
        InputHandler.set_gamepad_button_action(
            GAMEPAD_BUTTON_B, "p1_special", gamepad_id=1
        )
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_B, instance_id=0))
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_B, instance_id=1))
        self.assertEqual([i for i, _ in self.received], ["any_special", "p1_special"])

    def test_button_data_reports_pressed_and_gamepad_id(self) -> None:
        InputHandler.set_gamepad_button_action(GAMEPAD_BUTTON_A, "jump")
        InputHandler.handle_input(gamepad_button_down(GAMEPAD_BUTTON_A, instance_id=3))
        _, data = self.received[0]
        self.assertTrue(data.pressed)
        self.assertFalse(data.released)
        self.assertEqual(data.gamepad_id, 3)

    def test_axis_binding_matches_any_gamepad_by_default(self) -> None:
        InputHandler.set_gamepad_axis_action(GAMEPAD_AXIS_LEFT_X, "move_x")
        InputHandler.handle_input(gamepad_axis_motion(GAMEPAD_AXIS_LEFT_X, 0.75))
        _, data = self.received[0]
        self.assertEqual(data.value, 0.75)

    def test_axis_binding_can_be_restricted_to_one_gamepad(self) -> None:
        InputHandler.set_gamepad_axis_action(
            GAMEPAD_AXIS_LEFT_X, "p1_move_x", gamepad_id=1
        )
        InputHandler.handle_input(
            gamepad_axis_motion(GAMEPAD_AXIS_LEFT_X, 0.5, instance_id=0)
        )
        InputHandler.handle_input(
            gamepad_axis_motion(GAMEPAD_AXIS_LEFT_X, -0.5, instance_id=1)
        )
        self.assertEqual([i for i, _ in self.received], ["p1_move_x"])

    def test_axis_value_normalizes_raw_sdl_int_range(self) -> None:
        InputHandler.set_gamepad_axis_action(GAMEPAD_AXIS_LEFT_X, "move_x")
        InputHandler.handle_input(gamepad_axis_motion(GAMEPAD_AXIS_LEFT_X, -32768))
        _, data = self.received[0]
        self.assertEqual(data.value, -1.0)

    def test_device_added_and_removed_track_connected_gamepads(self) -> None:
        InputHandler.handle_input(
            pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=99)
        )
        self.assertNotIn(99, InputHandler.gamepads)


class ApplyDeadzoneTestCase(unittest.TestCase):
    def test_snaps_small_values_to_zero(self) -> None:
        self.assertEqual(apply_deadzone(0.05), 0.0)
        self.assertEqual(apply_deadzone(-0.1), 0.0)

    def test_keeps_values_past_the_threshold(self) -> None:
        self.assertEqual(apply_deadzone(0.5), 0.5)
        self.assertEqual(apply_deadzone(-0.9), -0.9)

    def test_custom_threshold(self) -> None:
        self.assertEqual(apply_deadzone(0.2, threshold=0.3), 0.0)
        self.assertEqual(apply_deadzone(0.4, threshold=0.3), 0.4)
