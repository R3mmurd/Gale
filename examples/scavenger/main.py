import settings
from src.Scavenger import Scavenger

if __name__ == "__main__":
    game = Scavenger(
        "Scavenger",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
