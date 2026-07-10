import settings
from src.Planks import Planks

if __name__ == "__main__":
    game = Planks(
        "Planks",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
