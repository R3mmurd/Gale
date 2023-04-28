import unittest
from unittest.mock import patch

from gale.state import StateMachine, BaseState


class StateMachineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.state_machine = StateMachine({"one": BaseState, "two": BaseState})
        self.state_machine.change("one")

    def test_change_state_enter(self) -> None:
        with patch.object(BaseState, "enter", return_value=None) as enter_method:
            self.state_machine.change("two")
        enter_method.assert_called_once()

    def test_change_state_enter_with_params(self) -> None:
        with patch.object(BaseState, "enter", return_value=None) as enter_method:
            self.state_machine.change("two", x=10)
        enter_method.assert_called_once_with(x=10)

    def test_change_state_exit(self) -> None:
        with patch.object(BaseState, "exit", return_value=None) as exit_method:
            self.state_machine.change("two")
        exit_method.assert_called_once()

    def test_change_to_invalid_state_name(self) -> None:
        with self.assertRaises(KeyError):
            self.state_machine.change("three")

    def test_update(self) -> None:
        with patch.object(BaseState, "update", return_value=None) as update_method:
            self.state_machine.update(0.1)
        update_method.assert_called_once_with(0.1)

    def test__render(self) -> None:
        with patch.object(BaseState, "render", return_value=None) as render_method:
            self.state_machine.render("a surface")
        render_method.assert_called_once_with("a surface")
