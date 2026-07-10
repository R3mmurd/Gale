import settings
from src.Lantern import Lantern

if __name__ == "__main__":
    game = Lantern(
        "Lantern",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
