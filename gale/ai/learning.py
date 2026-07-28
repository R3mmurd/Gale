"""
This file contains two lightweight models an agent can use to build up
knowledge about another agent (typically the player) from observed
behavior, instead of having its reactions hand-scripted: a
NaiveBayesClassifier to predict a discrete label (e.g. "aggressive" vs
"defensive" play style) from a set of features, and an NGramPredictor
to predict the next action in a sequence from how often it has
followed the same recent actions before (e.g. anticipating whether the
player is about to dodge left, dodge right, or attack).

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from collections import Counter, deque
from typing import Any, Deque, Dict, Hashable, Optional, Tuple


class NaiveBayesClassifier:
    """
    A naive Bayes classifier over discrete features: learns
    P(label) and P(feature_value | label) from observed examples, then
    predicts the label maximizing their product (assuming features are
    independent given the label, the "naive" assumption) for a new set
    of features.

    Usage example:

        model = NaiveBayesClassifier()
        model.observe("aggressive", {"approach_speed": "fast", "range": "melee"})
        model.observe("defensive", {"approach_speed": "slow", "range": "ranged"})
        model.predict({"approach_speed": "fast", "range": "melee"})  # "aggressive"
    """

    def __init__(self) -> None:
        self._label_counts: Counter = Counter()
        self._feature_counts: Dict[Hashable, Counter] = {}

    def observe(self, label: Hashable, features: Dict[str, Any]) -> None:
        """
        Record one labeled example.

        :param label: The label this example belongs to.
        :param features: Feature name -> discrete value pairs observed alongside label.
        """
        self._label_counts[label] += 1

        for name, value in features.items():
            self._feature_counts.setdefault((name, value), Counter())[label] += 1

    def predict(self, features: Dict[str, Any]) -> Optional[Hashable]:
        """
        :param features: Feature name -> discrete value pairs to classify.
        :returns: The label with the highest estimated posterior probability given features, or None if no example has been observed yet.
        """
        if not self._label_counts:
            return None

        total = sum(self._label_counts.values())
        best_label: Optional[Hashable] = None
        best_score = -1.0

        for label, label_count in self._label_counts.items():
            score = label_count / total

            for name, value in features.items():
                counts = self._feature_counts.get((name, value))
                # Laplace smoothing: an unseen (feature, label) pair
                # gets a small non-zero probability instead of forcing
                # the whole product to 0.
                seen = counts[label] if counts else 0
                score *= (seen + 1) / (label_count + 2)

            if score > best_score:
                best_score = score
                best_label = label

        return best_label


class NGramPredictor:
    """
    Predicts the next action in a sequence from how often it has
    followed the same n-1 most recent actions before, learned online
    from observe(). Useful to anticipate a player's next move (e.g. in
    a fighting game or a stealth encounter) well enough to react to a
    pattern without the player realizing they've fallen into one.

    Usage example:

        predictor = NGramPredictor(n=3)
        for action in ["dodge_left", "attack", "dodge_left", "attack"]:
            predictor.observe(action)
        predictor.predict_next()  # "dodge_left", the most common
                                   # follow-up seen after ["dodge_left", "attack"]
    """

    def __init__(self, n: int = 3) -> None:
        """
        :param n: Size of the n-gram: the (n - 1) most recent actions are used as context to predict the next one. The default value is 3.
        """
        self.n: int = n
        self._history: Deque[Hashable] = deque(maxlen=n - 1)
        self._counts: Dict[Tuple[Hashable, ...], Counter] = {}

    def observe(self, action: Hashable) -> None:
        """
        Record that action happened right after the current history,
        then append it to the history for the next call.

        :param action: The action observed.
        """
        context = tuple(self._history)
        self._counts.setdefault(context, Counter())[action] += 1
        self._history.append(action)

    def predict_next(self) -> Optional[Hashable]:
        """
        :returns: The action most often observed right after the current history, or None if this exact context has never been seen before.
        """
        counts = self._counts.get(tuple(self._history))

        if not counts:
            return None

        return counts.most_common(1)[0][0]

    def reset_history(self) -> None:
        """
        Clear the current context (e.g. at the start of a new
        encounter) without discarding what has been learned.
        """
        self._history.clear()
