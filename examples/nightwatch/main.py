import settings
from src.Nightwatch import Nightwatch

if __name__ == "__main__":
    game = Nightwatch(
        "Nightwatch",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
