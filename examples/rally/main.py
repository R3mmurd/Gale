import settings
from src.Rally import Rally

if __name__ == "__main__":
    game = Rally(
        "Rally",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
