import unittest

from gale.state_machine import StateMachine, BaseState


class AState(BaseState):
    def enter(self) -> None:
        self.some_value = 10
    
    def update(self, dt: float) -> None:
        self.some_value += self.some_value * dt


class StateMachineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.state_machine = StateMachine({
            'one': AState
        })
        self.state_machine.change('one')
    
    def test_initialization(self) -> None:
        self.assertEqual(self.state_machine.current.some_value, 10)
    
    def test_update(self) -> None:
        self.state_machine.update(0.1)
        self.assertEqual(self.state_machine.current.some_value, 11)
    
    def test_change_to_invalid_state_name(self) -> None:
        with self.assertRaises(KeyError):
            self.state_machine.change('two')
