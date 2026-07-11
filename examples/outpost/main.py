import settings
from src.Outpost import Outpost

if __name__ == "__main__":
    game = Outpost(
        "Outpost",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
