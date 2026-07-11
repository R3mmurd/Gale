import unittest
from unittest.mock import patch

from gale.state import StateMachine, BaseState, HierarchicalState


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


class WalkingState(BaseState):
    def enter(self, speed: int = 1) -> None:
        self.speed = speed


class LookingAroundState(BaseState):
    pass


class PatrolState(HierarchicalState):
    def __init__(self, state_machine: StateMachine) -> None:
        super().__init__(
            state_machine,
            substates={"walking": WalkingState, "looking_around": LookingAroundState},
            initial_substate="walking",
        )


class InnerLeafState(BaseState):
    pass


class InnerHierarchicalState(HierarchicalState):
    def __init__(self, state_machine: StateMachine) -> None:
        super().__init__(
            state_machine,
            substates={"leaf": InnerLeafState},
            initial_substate="leaf",
        )


class OuterHierarchicalState(HierarchicalState):
    def __init__(self, state_machine: StateMachine) -> None:
        super().__init__(
            state_machine,
            substates={"inner": InnerHierarchicalState},
            initial_substate="inner",
        )


class HierarchicalStateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.state_machine = StateMachine({"patrol": PatrolState})

    def test_enter_selects_initial_substate(self) -> None:
        self.state_machine.change("patrol")
        self.assertIsInstance(
            self.state_machine.current.substate_machine.current, WalkingState
        )

    def test_enter_forwards_args_to_initial_substate(self) -> None:
        self.state_machine.change("patrol", speed=5)
        self.assertEqual(self.state_machine.current.substate_machine.current.speed, 5)

    def test_update_delegates_to_current_substate(self) -> None:
        self.state_machine.change("patrol")
        with patch.object(WalkingState, "update", return_value=None) as update_method:
            self.state_machine.update(0.1)
        update_method.assert_called_once_with(0.1)

    def test_render_delegates_to_current_substate(self) -> None:
        self.state_machine.change("patrol")
        with patch.object(WalkingState, "render", return_value=None) as render_method:
            self.state_machine.render("a surface")
        render_method.assert_called_once_with("a surface")

    def test_on_input_delegates_to_current_substate(self) -> None:
        self.state_machine.change("patrol")
        with patch.object(
            WalkingState, "on_input", return_value=None
        ) as on_input_method:
            self.state_machine.on_input("look", "data")
        on_input_method.assert_called_once_with("look", "data")

    def test_change_substate_switches_current_substate(self) -> None:
        self.state_machine.change("patrol")
        self.state_machine.current.change_substate("looking_around")
        self.assertIsInstance(
            self.state_machine.current.substate_machine.current, LookingAroundState
        )

    def test_change_substate_calls_exit_and_enter(self) -> None:
        self.state_machine.change("patrol")
        with patch.object(
            WalkingState, "exit", return_value=None
        ) as exit_method, patch.object(
            LookingAroundState, "enter", return_value=None
        ) as enter_method:
            self.state_machine.current.change_substate("looking_around")
        exit_method.assert_called_once()
        enter_method.assert_called_once()

    def test_two_level_hierarchy_dispatches_update_to_leaf(self) -> None:
        state_machine = StateMachine({"outer": OuterHierarchicalState})
        state_machine.change("outer")
        with patch.object(InnerLeafState, "update", return_value=None) as update_method:
            state_machine.update(0.1)
        update_method.assert_called_once_with(0.1)
