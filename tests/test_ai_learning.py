import unittest

from gale.ai.learning import NaiveBayesClassifier, NGramPredictor


class NaiveBayesClassifierTestCase(unittest.TestCase):
    def test_predicts_none_without_observations(self) -> None:
        model = NaiveBayesClassifier()
        self.assertIsNone(model.predict({"approach_speed": "fast"}))

    def test_predicts_the_matching_label(self) -> None:
        model = NaiveBayesClassifier()

        for _ in range(10):
            model.observe("aggressive", {"approach_speed": "fast", "range": "melee"})
            model.observe("defensive", {"approach_speed": "slow", "range": "ranged"})

        self.assertEqual(
            model.predict({"approach_speed": "fast", "range": "melee"}),
            "aggressive",
        )
        self.assertEqual(
            model.predict({"approach_speed": "slow", "range": "ranged"}),
            "defensive",
        )


class NGramPredictorTestCase(unittest.TestCase):
    def test_predicts_none_for_unseen_context(self) -> None:
        predictor = NGramPredictor(n=3)
        self.assertIsNone(predictor.predict_next())

    def test_predicts_the_most_common_follow_up(self) -> None:
        predictor = NGramPredictor(n=3)
        sequence = ["dodge_left", "attack"] * 5 + ["dodge_right", "attack"]

        for action in sequence:
            predictor.observe(action)

        predictor.reset_history()
        predictor.observe("dodge_left")
        predictor.observe("attack")
        self.assertEqual(predictor.predict_next(), "dodge_left")

    def test_reset_history_clears_context_but_keeps_learned_counts(self) -> None:
        predictor = NGramPredictor(n=2)
        predictor.observe("a")
        predictor.observe("b")
        # The empty context (before "a") already predicts "a"; jump
        # into a context that was never observed to check it's None.
        predictor.observe("c")
        self.assertIsNone(predictor.predict_next())
        predictor.reset_history()
        predictor.observe("a")
        self.assertEqual(predictor.predict_next(), "b")


if __name__ == "__main__":
    unittest.main()
