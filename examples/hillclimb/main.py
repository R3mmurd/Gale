import settings
from src.Hillclimb import Hillclimb

if __name__ == "__main__":
    game = Hillclimb(
        "Hillclimb",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
