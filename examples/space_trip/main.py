"""
This module was autogenerated by gale.
"""

import settings
from src.SpaceTrip import SpaceTrip

if __name__ == "__main__":
    game = SpaceTrip(
        "Space Trip",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
