"""
Every setting gale.conf.settings falls back to when a project's own
settings.py doesn't define it -- the full list of what gale.game.Game
reads from settings, with the same default values Game itself used to
hardcode directly in its constructor. Mirrors the role
django.conf.global_settings plays for Django: a project only needs to
define what it wants to change.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

TITLE = None
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# None means "match WINDOW_WIDTH/WINDOW_HEIGHT", the same dynamic
# fallback Game itself used to apply directly -- set an explicit value
# in a project's settings.py to emulate a different resolution instead.
VIRTUAL_WIDTH = None
VIRTUAL_HEIGHT = None
FPS = 60
FIXED_TIMESTEP = 1.0 / 60.0

# gale.save.SaveManager's defaults. SAVE_DIR is relative to the
# project's own working directory, the same convention gale-admin's
# generated settings.py already uses for assets/.
SAVE_DIR = "saves"
SAVE_VERSION = 1
SAVE_FILE_EXTENSION = "sav"
