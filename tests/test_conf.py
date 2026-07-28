import sys
import types
import unittest

from gale.conf import Settings, global_settings


class SettingsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._had_settings_module = "settings" in sys.modules
        self._original_settings_module = sys.modules.get("settings")

    def tearDown(self) -> None:
        if self._had_settings_module:
            sys.modules["settings"] = self._original_settings_module
        else:
            sys.modules.pop("settings", None)

    def _install_project_settings(self, **values) -> None:
        module = types.ModuleType("settings")

        for name, value in values.items():
            setattr(module, name, value)

        sys.modules["settings"] = module

    def test_falls_back_to_global_settings_without_a_project_settings_module(
        self,
    ) -> None:
        sys.modules.pop("settings", None)
        settings = Settings()
        self.assertEqual(settings.WINDOW_WIDTH, global_settings.WINDOW_WIDTH)
        self.assertEqual(settings.FPS, global_settings.FPS)

    def test_project_settings_overrides_global_settings(self) -> None:
        self._install_project_settings(WINDOW_WIDTH=1280)
        settings = Settings()
        self.assertEqual(settings.WINDOW_WIDTH, 1280)
        self.assertEqual(settings.FPS, global_settings.FPS)

    def test_project_settings_can_define_extra_settings(self) -> None:
        self._install_project_settings(PLAYER_SPEED=250)
        settings = Settings()
        self.assertEqual(settings.PLAYER_SPEED, 250)

    def test_undefined_setting_raises(self) -> None:
        sys.modules.pop("settings", None)
        settings = Settings()
        self.assertRaises(AttributeError, getattr, settings, "NOT_A_REAL_SETTING")

    def test_missing_project_settings_module_is_not_an_error(self) -> None:
        sys.modules.pop("settings", None)
        settings = Settings()
        self.assertEqual(settings.WINDOW_HEIGHT, global_settings.WINDOW_HEIGHT)


if __name__ == "__main__":
    unittest.main()
