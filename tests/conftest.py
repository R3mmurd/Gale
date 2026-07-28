import pytest

from gale.conf import settings as conf_settings


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
