import unittest

from gale.game import Game


class RecordingGame(Game):
    def init(self) -> None:
        self.fixed_update_calls = 0
        self.update_calls = 0

    def fixed_update(self) -> None:
        self.fixed_update_calls += 1

    def update(self, dt: float) -> None:
        self.update_calls += 1


class GameTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.game = RecordingGame(fixed_timestep=1.0 / 60.0)

    def test_fixed_update_runs_as_many_times_as_the_accumulated_time_covers(
        self,
    ) -> None:
        self.game._Game__update(1.0 / 60.0 * 3.5)
        self.assertEqual(self.game.fixed_update_calls, 3)
        self.assertEqual(self.game.update_calls, 1)

    def test_fixed_update_does_not_run_before_a_full_timestep_accumulates(
        self,
    ) -> None:
        self.game._Game__update(1.0 / 60.0 * 0.5)
        self.assertEqual(self.game.fixed_update_calls, 0)
        self.assertEqual(self.game.update_calls, 1)

    def test_leftover_time_carries_over_between_calls(self) -> None:
        self.game._Game__update(1.0 / 60.0 * 0.5)
        self.game._Game__update(1.0 / 60.0 * 0.5)
        self.assertEqual(self.game.fixed_update_calls, 1)
        self.assertEqual(self.game.update_calls, 2)


if __name__ == "__main__":
    unittest.main()
