import settings
from src.Futsal import Futsal

if __name__ == "__main__":
    game = Futsal(
        "Futsal",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
