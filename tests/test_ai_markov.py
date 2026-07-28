import unittest

from gale.ai.markov import MarkovChain, MarkovState, MarkovStateMachine


class MarkovChainTestCase(unittest.TestCase):
    def test_next_state_only_returns_states_with_a_transition(self) -> None:
        chain = MarkovChain()
        chain.add_transition("idle", "patrol", 1.0)
        self.assertEqual(chain.next_state("idle"), "patrol")

    def test_missing_state_raises(self) -> None:
        chain = MarkovChain()
        self.assertRaises(KeyError, chain.next_state, "unknown")

    def test_weighted_choice_only_returns_declared_targets(self) -> None:
        chain = MarkovChain()
        chain.add_transition("idle", "patrol", 0.9)
        chain.add_transition("idle", "investigate", 0.1)

        for _ in range(20):
            self.assertIn(chain.next_state("idle"), ("patrol", "investigate"))


class MarkovStateMachineTestCase(unittest.TestCase):
    def test_starts_in_the_given_state(self) -> None:
        chain = MarkovChain()
        machine = MarkovStateMachine(
            chain, {"idle": MarkovState("idle", duration=1.0)}, start="idle"
        )
        self.assertEqual(machine.current.name, "idle")

    def test_transitions_once_the_current_state_completes(self) -> None:
        chain = MarkovChain()
        chain.add_transition("idle", "patrol", 1.0)
        machine = MarkovStateMachine(
            chain,
            {
                "idle": MarkovState("idle", duration=1.0),
                "patrol": MarkovState("patrol", duration=5.0),
            },
            start="idle",
        )
        machine.update(1.5)
        self.assertEqual(machine.current.name, "patrol")

    def test_stays_in_the_same_state_before_it_completes(self) -> None:
        chain = MarkovChain()
        chain.add_transition("idle", "patrol", 1.0)
        machine = MarkovStateMachine(
            chain,
            {
                "idle": MarkovState("idle", duration=2.0),
                "patrol": MarkovState("patrol", duration=5.0),
            },
            start="idle",
        )
        machine.update(0.5)
        self.assertEqual(machine.current.name, "idle")


if __name__ == "__main__":
    unittest.main()
