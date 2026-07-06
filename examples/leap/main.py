import settings
from src.Leap import Leap

if __name__ == "__main__":
    game = Leap(
        "Leap",
        settings.WINDOW_WIDTH,
        settings.WINDOW_HEIGHT,
        settings.VIRTUAL_WIDTH,
        settings.VIRTUAL_HEIGHT,
    )
    game.exec()
