import os
import tempfile
import unittest

from click.testing import CliRunner

from gale.management.gale_admin import create_project


class CreateProjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_creates_the_expected_layout(self) -> None:
        result = self.runner.invoke(create_project, ["demo_game"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists("demo_game/main.py"))
        self.assertTrue(os.path.exists("demo_game/settings.py"))
        self.assertTrue(os.path.exists("demo_game/README.md"))
        self.assertTrue(os.path.exists("demo_game/src/demo_game.py"))

        for directory in ("sounds", "graphics", "fonts"):
            self.assertTrue(os.path.isdir(f"demo_game/assets/{directory}"))

    def test_settings_declares_the_project_title(self) -> None:
        self.runner.invoke(create_project, ["demo_game"])
        contents = open("demo_game/settings.py").read()
        self.assertIn("TITLE = 'Demo Game'", contents)

    def test_main_does_not_pass_settings_to_the_game_constructor(self) -> None:
        """
        main.py should rely on Game resolving its configuration from
        gale.conf.settings (which in turn reads settings.py) instead
        of passing it through explicitly -- see gale/conf.
        """
        self.runner.invoke(create_project, ["demo_game"])
        contents = open("demo_game/main.py").read()
        self.assertNotIn("import settings", contents)
        self.assertIn("DemoGame()", contents)

    def test_generated_project_actually_runs(self) -> None:
        self.runner.invoke(create_project, ["demo_game"])
        os.chdir("demo_game")

        import importlib
        import sys

        sys.path.insert(0, os.getcwd())

        try:
            module = importlib.import_module("src.demo_game")
            game = module.DemoGame()
            self.assertEqual(game.title, "Demo Game")
            self.assertEqual(game.window_width, 1280)
            self.assertEqual(game.virtual_width, 320)
        finally:
            sys.path.remove(os.getcwd())
            sys.modules.pop("src.demo_game", None)
            sys.modules.pop("src", None)
            sys.modules.pop("settings", None)

    def test_already_existing_project_is_not_overwritten(self) -> None:
        self.runner.invoke(create_project, ["demo_game"])
        result = self.runner.invoke(create_project, ["demo_game"])
        self.assertIn("already exists", result.output)


if __name__ == "__main__":
    unittest.main()
