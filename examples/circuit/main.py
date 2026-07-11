import settings
from src.Circuit import Circuit

if __name__ == "__main__":
    game = Circuit(
        "Circuit",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
