import unittest
from unittest.mock import patch

from gale.command import Command, CommandBindings, CommandControlled


class RecordingCommand(Command):
    def __init__(self) -> None:
        self.calls = []

    def execute(self, receiver, dt: float = 0.0) -> None:
        self.calls.append((receiver, dt))


class FakeInputData:
    def __init__(self, pressed: bool = False, released: bool = False) -> None:
        self.pressed = pressed
        self.released = released


class AxisLikeInputData:
    """Stands in for something like GamepadAxisData, which has neither
    pressed nor released."""

    def __init__(self, value: float) -> None:
        self.value = value


class CommandTestCase(unittest.TestCase):
    def test_command_is_not_instantiable_directly(self) -> None:
        with self.assertRaises(NotImplementedError):
            Command().execute(object())

    def test_call_delegates_to_execute(self) -> None:
        command = RecordingCommand()
        receiver = object()
        command(receiver, 0.5)
        self.assertEqual(command.calls, [(receiver, 0.5)])

    def test_call_defaults_dt_to_zero(self) -> None:
        command = RecordingCommand()
        receiver = object()
        command(receiver)
        self.assertEqual(command.calls, [(receiver, 0.0)])


class CommandBindingsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.bindings = CommandBindings()
        self.press = RecordingCommand()
        self.release = RecordingCommand()
        self.bindings.bind("jump", press=self.press, release=self.release)
        self.receiver = object()

    def test_dispatch_press(self) -> None:
        self.bindings.dispatch(self.receiver, "jump", FakeInputData(pressed=True), 0.1)
        self.assertEqual(self.press.calls, [(self.receiver, 0.1)])
        self.assertEqual(self.release.calls, [])

    def test_dispatch_release(self) -> None:
        self.bindings.dispatch(self.receiver, "jump", FakeInputData(released=True), 0.1)
        self.assertEqual(self.release.calls, [(self.receiver, 0.1)])
        self.assertEqual(self.press.calls, [])

    def test_dispatch_ignores_unregistered_input_id(self) -> None:
        self.bindings.dispatch(self.receiver, "duck", FakeInputData(pressed=True))
        self.assertEqual(self.press.calls, [])
        self.assertEqual(self.release.calls, [])

    def test_dispatch_ignores_press_or_release_left_unbound(self) -> None:
        self.bindings.bind("shoot", press=self.press)
        self.bindings.dispatch(self.receiver, "shoot", FakeInputData(released=True))
        self.assertEqual(self.press.calls, [])

    def test_dispatch_does_not_fail_without_pressed_or_released_attributes(
        self,
    ) -> None:
        self.bindings.dispatch(self.receiver, "jump", AxisLikeInputData(value=0.8))
        self.assertEqual(self.press.calls, [])
        self.assertEqual(self.release.calls, [])


class CommandControlledTestCase(unittest.TestCase):
    def test_registers_itself_with_input_handler(self) -> None:
        with patch("gale.command.InputHandler") as mock_input_handler:
            controlled = CommandControlled(CommandBindings())
            mock_input_handler.register_listener.assert_called_once_with(controlled)

    def test_on_input_dispatches_through_command_bindings(self) -> None:
        bindings = CommandBindings()
        press = RecordingCommand()
        bindings.bind("jump", press=press)

        with patch("gale.command.InputHandler"):
            controlled = CommandControlled(bindings)

        controlled.on_input("jump", FakeInputData(pressed=True))
        self.assertEqual(press.calls, [(controlled, 0.0)])

    def test_combines_with_another_class_through_multiple_inheritance(self) -> None:
        class Entity:
            def __init__(self, name: str) -> None:
                self.name = name

        class Player(CommandControlled, Entity):
            def __init__(self, command_bindings: CommandBindings, name: str) -> None:
                super().__init__(command_bindings, name)

        bindings = CommandBindings()
        press = RecordingCommand()
        bindings.bind("jump", press=press)

        with patch("gale.command.InputHandler"):
            player = Player(bindings, "hero")

        self.assertEqual(player.name, "hero")
        player.on_input("jump", FakeInputData(pressed=True))
        self.assertEqual(press.calls, [(player, 0.0)])
