import settings
from src.Skirmish import Skirmish

if __name__ == "__main__":
    game = Skirmish(
        "Skirmish",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
