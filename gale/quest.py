"""
This file contains a generic, customizable-per-game quest system built
on top of gale.sequence: Objective (one trackable goal, completed by
progress events, a duration, an input, or a custom condition -- pick
whichever combination fits), Stage (a StepGroup of Objectives, one
phase of a quest), Quest (a Sequence of Stages), and QuestLog (tracks
every quest a game has registered, starts/advances them, and
broadcasts progress events to whichever are active).

None of this hardcodes what an objective actually means: a game
defines its own objective keys ("wolves_killed", "herbs_collected",
...) and reports progress by calling QuestLog.notify(key, amount) from
wherever that event actually happens (an enemy's on_death, a pickup's
on_collected, ...) -- exactly the "coordinate through shared state, not
direct references" shape gale.ai.blackboard already names a quest
system as an example user of, and the two compose naturally (a
Blackboard observer can call notify() to bridge the two). Objectives
that don't fit a simple progress counter (checking an inventory, a
Blackboard flag, ...) are just a matter of subclassing Objective and
overriding is_complete.

See docs/examples/quest.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, List, Optional

from .input_handler import InputData
from .sequence import Sequence, Step, StepGroup


class Objective(Step):
    """
    One trackable goal within a quest Stage. By default it completes
    once enough matching progress events have been reported (see
    notify), but it's a Step underneath, so duration/advance_on_input
    work here too (an objective that's just "wait a moment" or "press
    a key to confirm" needs no progress tracking at all), and
    subclassing to override is_complete covers anything else.

    Usage example:

        Objective("wolves_killed", "Defeat 3 wolves in the forest", target=3)
    """

    def __init__(
        self,
        key: Optional[str] = None,
        description: str = "",
        target: int = 1,
        **kwargs: Any,
    ) -> None:
        """
        :param key: The progress-event name this objective listens for (see notify). The default value is None, meaning it never advances from progress events, only from duration/advance_on_input/a subclass's own is_complete.
        :param description: Human-readable text a game's quest log UI can show for this objective.
        :param target: How many matching progress events complete this objective. The default value is 1.
        """
        super().__init__(**kwargs)
        self.key: Optional[str] = key
        self.description: str = description
        self.target: int = target
        self.progress: int = 0

    def notify(self, key: str, amount: int) -> None:
        """
        :param key: The progress-event name being reported.
        :param amount: How much progress to add if key matches this objective's own key.
        """
        if self.key is not None and key == self.key:
            self.progress = min(self.target, self.progress + amount)

    def is_complete(self) -> bool:
        if self.key is not None and self.progress >= self.target:
            return True

        return super().is_complete()


class Stage(StepGroup):
    """
    One phase of a Quest: a group of Objectives (or nested Stages)
    tracked together, completed once all of them are -- or any one,
    with require_all=False (e.g. "reach the gate OR find the secret
    passage").
    """

    def notify(self, key: str, amount: int) -> None:
        """
        :param key: The progress-event name being reported.
        :param amount: How much progress to report to every Objective (or nested Stage) in this stage.
        """
        for step in self.steps:
            if isinstance(step, (Objective, Stage)):
                step.notify(key, amount)


class Quest(Sequence):
    """
    A questline: a Sequence of Stages, tracked as a whole under a
    quest_id/title a game's quest log UI can show. Not meant to be
    driven directly most of the time -- see QuestLog, which manages
    every quest a game has and routes notify()/update()/on_input() to
    whichever are active.

    Usage example:

        Quest(
            "defeat_the_wolves",
            "Wolf Trouble",
            [Stage([Objective("wolves_killed", "Defeat 3 wolves", target=3)])],
        )
    """

    def __init__(
        self,
        quest_id: str,
        title: str,
        stages: List[Stage],
        on_completed: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        :param quest_id: Unique identifier for this quest, used by QuestLog to look it up.
        :param title: Human-readable title a game's quest log UI can show.
        :param stages: The stages this quest progresses through, in order.
        :param on_completed: Called once, with no arguments, when the last stage completes. The default value is None.
        """
        self.quest_id: str = quest_id
        self.title: str = title
        super().__init__(stages, on_finished=on_completed)

    def notify(self, key: str, amount: int) -> None:
        """
        :param key: The progress-event name being reported.
        :param amount: How much progress to report to the current stage.
        """
        if self.current is not None:
            self.current.notify(key, amount)

    @property
    def current_stage(self) -> Optional[Stage]:
        """
        :returns: The stage currently in progress, or None once the quest is finished.
        """
        return self.current


class QuestLog:
    """
    Tracks every quest a game has registered: which are active,
    completed, or not yet started, and broadcasts progress events (see
    notify) to whichever are currently active. A game usually keeps one
    QuestLog for the whole session/save file.

    Usage example:

        log = QuestLog()
        log.register(Quest("defeat_the_wolves", "Wolf Trouble", [...]))
        log.start("defeat_the_wolves")

        # Wherever a wolf dies:
        log.notify("wolves_killed", 1)

        # Every frame (only active quests actually do anything):
        log.update(dt)
    """

    def __init__(self) -> None:
        self._quests: Dict[str, Quest] = {}
        self._active: List[str] = []
        self._completed: List[str] = []

    def register(self, quest: Quest) -> None:
        """
        :param quest: The quest to make available to start() later.
        """
        self._quests[quest.quest_id] = quest

    def start(self, quest_id: str) -> None:
        """
        Activates a registered quest. Does nothing if it's already
        active or completed.

        :param quest_id: A previously registered quest to activate.
        :raises KeyError: If quest_id was never registered.
        """
        if quest_id not in self._quests:
            raise KeyError(quest_id)

        if quest_id not in self._active and quest_id not in self._completed:
            self._active.append(quest_id)

    def get(self, quest_id: str) -> Quest:
        """
        :param quest_id: A previously registered quest.
        :returns: That Quest, whatever its current status.
        :raises KeyError: If quest_id was never registered.
        """
        return self._quests[quest_id]

    def is_active(self, quest_id: str) -> bool:
        """
        :param quest_id: A previously registered quest.
        :returns: Whether it's currently in progress.
        """
        return quest_id in self._active

    def is_completed(self, quest_id: str) -> bool:
        """
        :param quest_id: A previously registered quest.
        :returns: Whether it has already finished.
        """
        return quest_id in self._completed

    def active_quests(self) -> List[Quest]:
        """
        :returns: Every currently active quest, in the order they were started.
        """
        return [self._quests[quest_id] for quest_id in self._active]

    def notify(self, key: str, amount: int = 1) -> None:
        """
        Reports progress on an event to every currently active quest.

        :param key: The progress-event name being reported (e.g. "wolves_killed").
        :param amount: How much progress to add. The default value is 1.
        """
        for quest_id in self._active:
            self._quests[quest_id].notify(key, amount)

    def update(self, dt: float) -> None:
        """
        Updates every active quest, moving any that just finished
        their last stage into the completed list.

        :param dt: Time elapsed (in seconds) since the last update.
        """
        for quest_id in list(self._active):
            quest = self._quests[quest_id]
            quest.update(dt)

            if quest.finished:
                self._active.remove(quest_id)
                self._completed.append(quest_id)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        Forwards input to every currently active quest (for objectives
        using advance_on_input).

        :param input_id: The string that describes the input.
        :param input_data: Data associated to the input type.
        """
        for quest_id in self._active:
            self._quests[quest_id].on_input(input_id, input_data)
