import os
import tempfile
import unittest

from click.testing import CliRunner

from gale.management.gale_admin import create_project, create_state


class CreateStateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        self.runner.invoke(create_project, ["demo_game"])
        os.chdir(os.path.join(self._tmp.name, "demo_game"))

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_creates_state_file_and_package(self) -> None:
        result = self.runner.invoke(create_state, ["menu"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists("src/states/__init__.py"))
        self.assertTrue(os.path.exists("src/states/menu_state.py"))

        contents = open("src/states/menu_state.py").read()
        self.assertIn("class MenuState(BaseState):", contents)

    def test_normalizes_name_regardless_of_casing(self) -> None:
        self.runner.invoke(create_state, ["menu"])
        result = self.runner.invoke(create_state, ["MenuState"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("already exists", result.output)

    def test_appends_state_suffix_when_missing(self) -> None:
        self.runner.invoke(create_state, ["game_over"])
        self.assertTrue(os.path.exists("src/states/game_over_state.py"))
        contents = open("src/states/game_over_state.py").read()
        self.assertIn("class GameOverState(BaseState):", contents)

    def test_requires_a_src_directory(self) -> None:
        os.chdir(self._tmp.name)
        result = self.runner.invoke(create_state, ["menu"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No 'src' directory found", result.output)
        self.assertFalse(os.path.exists("src"))


if __name__ == "__main__":
    unittest.main()
