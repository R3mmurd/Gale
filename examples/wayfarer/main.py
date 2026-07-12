import settings
from src.Wayfarer import Wayfarer

if __name__ == "__main__":
    game = Wayfarer(
        "Wayfarer",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
