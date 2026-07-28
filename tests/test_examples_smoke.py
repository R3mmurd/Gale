"""
A regression net for examples/*: each one is its own standalone
project (its own settings.py, its own src/ package), never imported by
gale's own test suite otherwise, so a change to gale.game/gale.conf (or
anything else every example happens to lean on) could silently break
every one of them with zero automated signal -- which is exactly what
happened by hand, repeatedly, while building the settings system and
the pygame subsystem init fix. This just imports each one and runs its
update loop for a handful of frames headlessly (requires
SDL_VIDEODRIVER=dummy, and for examples/space_trip specifically,
SDL_AUDIODRIVER=dummy too, since it loads real sound files -- both are
already set by CI and by .pre-commit-config.yaml's local test hook).
"""

import importlib
import os
import sys
import unittest

from gale.conf import settings as conf_settings
from gale.management.gale_admin import to_pascal_case

EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)


def _example_slugs():
    return sorted(
        name
        for name in os.listdir(EXAMPLES_DIR)
        if os.path.isdir(os.path.join(EXAMPLES_DIR, name))
        and not name.startswith((".", "__"))
    )


class ExamplesSmokeTestCase(unittest.TestCase):
    def _run_example(self, slug: str) -> None:
        class_name = to_pascal_case(slug)
        example_dir = os.path.join(EXAMPLES_DIR, slug)
        original_cwd = os.getcwd()
        original_sys_path = list(sys.path)

        os.chdir(example_dir)
        sys.path.insert(0, example_dir)
        # gale.conf.settings caches whichever "settings" module it
        # first finds; each example needs its own, so force a fresh
        # lookup instead of reusing the previous example's.
        conf_settings._loaded = False
        conf_settings._project_settings = None

        try:
            module = importlib.import_module(f"src.{class_name}")
            game_class = getattr(module, class_name)
            game = game_class()

            for _ in range(5):
                game._Game__update(1.0 / 60.0)
        finally:
            os.chdir(original_cwd)
            sys.path[:] = original_sys_path

            for name in list(sys.modules):
                if name == "settings" or name == "src" or name.startswith("src."):
                    del sys.modules[name]

    def test_every_example_starts_and_runs_headlessly(self) -> None:
        slugs = _example_slugs()
        self.assertGreater(len(slugs), 0, "no example projects found under examples/")

        for slug in slugs:
            with self.subTest(example=slug):
                self._run_example(slug)


if __name__ == "__main__":
    unittest.main()
