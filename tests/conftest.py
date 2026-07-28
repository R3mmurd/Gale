import pytest

from gale.conf import settings as conf_settings
from gale.input_handler import InputHandler
from gale.timer import Timer


@pytest.fixture(autouse=True)
def _reset_gale_conf_settings_cache():
    """
    gale.conf.settings is a shared, lazily-loaded singleton: once
    something reads a setting from it (e.g. any Game() instantiated
    without every argument explicit), it caches whichever "settings"
    module happened to be importable at that moment for the rest of
    the process. Reset it around every test so one test's Game()
    (or a project settings.py a test temporarily installs into
    sys.modules) never leaks into another's.
    """
    conf_settings._loaded = False
    conf_settings._project_settings = None
    yield
    conf_settings._loaded = False
    conf_settings._project_settings = None


@pytest.fixture(autouse=True)
def _reset_input_handler_and_timer_state():
    """
    InputHandler.listeners/gamepads and Timer.items/paused are also
    process-wide, class-level shared state: any Game (or Agent, or a
    test constructing one directly) registers itself with
    InputHandler on __init__, and most tests never call quit() to
    unregister -- so without a reset, listeners/timers from one test
    would otherwise keep piling up and firing throughout the rest of
    the suite.
    """
    InputHandler.listeners = []
    InputHandler.gamepads = {}
    Timer.items = []
    Timer.paused = False
    yield
    InputHandler.listeners = []
    InputHandler.gamepads = {}
    Timer.items = []
    Timer.paused = False
