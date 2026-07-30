import os
import subprocess
import sys
import unittest


class PackageInitTestCase(unittest.TestCase):
    def test_importing_any_gale_submodule_initializes_pygame(self) -> None:
        """
        A real game crashed with "pygame.error: font not initialized"
        building a settings.py-style FONTS dict, because nothing
        guaranteed pygame was initialized before that -- it only
        happened to work when some other module imported gale.game
        first. Run in a fresh interpreter (importing gale.input_handler
        only, never gale.game) to prove the guarantee doesn't depend on
        import order: gale/__init__.py itself initializes pygame the
        moment any gale submodule is imported.
        """
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from gale import input_handler\n"
                "import pygame\n"
                "font = pygame.font.Font(None, 16)\n"
                "print('ok')\n",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
