"""
gale.conf: a lazily-loaded, overridable settings object, the same role
django.conf plays for Django (and the reason for the name: so it never
collides with a project's own settings.py, which "gale.settings"
would).

`from gale.conf import settings` gives you a single object with every
setting gale.game.Game understands (see gale.conf.global_settings for
the full list and their defaults). On first access, it tries `import
settings` -- the project's own top-level settings.py, importable
because gale games are always run from their own directory -- and
looks up each attribute there first, falling back to
gale.conf.global_settings for anything the project doesn't define.
This also means a project's settings.py can define its own extra
settings (asset dicts, gameplay constants, ...) and read them back the
same way, with no special declaration needed.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from types import ModuleType
from typing import Any, Optional

from . import global_settings


class Settings:
    """
    See the module docstring. Usage example:

        # settings.py, next to main.py
        WINDOW_WIDTH = 1280
        WINDOW_HEIGHT = 720
        PLAYER_SPEED = 200

        # main.py
        from gale.conf import settings

        settings.WINDOW_WIDTH   # 1280: the project's own override
        settings.FPS            # 60: gale.conf.global_settings' default
        settings.PLAYER_SPEED   # 200: a project-specific setting, not
                                 # declared anywhere in gale itself
    """

    def __init__(self) -> None:
        self._project_settings: Optional[ModuleType] = None
        self._loaded: bool = False

    def _load(self) -> None:
        if self._loaded:
            return

        self._loaded = True

        try:
            import settings as project_settings

            self._project_settings = project_settings
        except ImportError:
            self._project_settings = None

    def __getattr__(self, name: str) -> Any:
        self._load()

        if self._project_settings is not None and hasattr(self._project_settings, name):
            return getattr(self._project_settings, name)

        if hasattr(global_settings, name):
            return getattr(global_settings, name)

        raise AttributeError(
            f"Setting {name!r} is not defined in the project's settings.py "
            "nor in gale.conf.global_settings"
        )


settings = Settings()
