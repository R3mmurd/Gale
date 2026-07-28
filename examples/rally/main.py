from src.Rally import Rally

if __name__ == "__main__":
    # Rally takes every gale.game.Game argument (title, window
    # size, ...) straight from settings.py / gale.conf.global_settings,
    # so there's no need to pass any of them here -- see settings.py.
    game = Rally()
    game.exec()
