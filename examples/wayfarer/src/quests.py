from typing import Callable, Optional

from gale.quest import Objective, Quest, QuestLog, Stage


def build_quest_log(
    on_wolf_trouble_completed: Optional[Callable[[], None]],
) -> QuestLog:
    """
    Builds the QuestLog for a fresh play session, registering
    "wolf_trouble" but not starting it -- PlayState.enter() does that
    once the intro cutscene has handed off into free-roam play.

    :param on_wolf_trouble_completed: Called once, with no arguments, when the quest's last stage completes -- PlayState uses it to transition into the victory cutscene.
    """
    log = QuestLog()
    log.register(
        Quest(
            "wolf_trouble",
            "Wolf Trouble",
            [
                Stage(
                    [
                        Objective("herbs_collected", "Collect 2 herbs", target=2),
                        Objective("wolf_defeated", "Defeat the wolf", target=1),
                    ]
                ),
                Stage([Objective("reported", "Report back to the Elder", target=1)]),
            ],
            on_completed=on_wolf_trouble_completed,
        )
    )
    return log
