import sys
import types
import unittest

from gale.game import Game
from gale.input_handler import InputHandler


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

    def test_zero_fixed_timestep_raises_instead_of_hanging(self) -> None:
        self.assertRaises(ValueError, RecordingGame, fixed_timestep=0)

    def test_negative_fixed_timestep_raises(self) -> None:
        self.assertRaises(ValueError, RecordingGame, fixed_timestep=-1.0 / 60.0)

    def test_quit_unregisters_from_input_handler(self) -> None:
        self.assertIn(self.game, InputHandler.listeners)
        self.game.quit()
        self.assertNotIn(self.game, InputHandler.listeners)


class GameSettingsResolutionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._had_settings_module = "settings" in sys.modules
        self._original_settings_module = sys.modules.get("settings")
        sys.modules.pop("settings", None)

    def tearDown(self) -> None:
        if self._had_settings_module:
            sys.modules["settings"] = self._original_settings_module
        else:
            sys.modules.pop("settings", None)

    def test_defaults_come_from_gale_conf_global_settings_without_a_project_settings_module(
        self,
    ) -> None:
        game = RecordingGame()
        self.assertEqual(game.window_width, 800)
        self.assertEqual(game.window_height, 600)
        self.assertEqual(game.virtual_width, 800)
        self.assertEqual(game.virtual_height, 600)
        self.assertEqual(game.fps, 60)
        self.assertAlmostEqual(game.fixed_timestep, 1.0 / 60.0)
        self.assertEqual(game.title, "Game")

    def test_project_settings_module_overrides_defaults(self) -> None:
        module = types.ModuleType("settings")
        module.TITLE = "My Game"
        module.WINDOW_WIDTH = 1280
        module.WINDOW_HEIGHT = 720
        module.VIRTUAL_WIDTH = 640
        sys.modules["settings"] = module

        game = RecordingGame()
        self.assertEqual(game.title, "My Game")
        self.assertEqual(game.window_width, 1280)
        self.assertEqual(game.window_height, 720)
        self.assertEqual(game.virtual_width, 640)
        # VIRTUAL_HEIGHT wasn't overridden: falls back to window_height.
        self.assertEqual(game.virtual_height, 720)

    def test_explicit_constructor_argument_wins_over_settings(self) -> None:
        module = types.ModuleType("settings")
        module.WINDOW_WIDTH = 1280
        sys.modules["settings"] = module

        game = RecordingGame(window_width=320)
        self.assertEqual(game.window_width, 320)


if __name__ == "__main__":
    unittest.main()
