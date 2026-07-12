import unittest

from gale.quest import Objective, Quest, QuestLog, Stage


class ObjectiveTestCase(unittest.TestCase):
    def test_completes_once_target_progress_reported(self):
        objective = Objective("wolves_killed", "Defeat 3 wolves", target=3)
        objective.enter()
        objective.notify("wolves_killed", 1)
        objective.notify("wolves_killed", 1)
        self.assertFalse(objective.is_complete())
        objective.notify("wolves_killed", 1)
        self.assertTrue(objective.is_complete())

    def test_progress_does_not_overshoot_target(self):
        objective = Objective("herbs", "Collect herbs", target=2)
        objective.notify("herbs", 10)
        self.assertEqual(objective.progress, 2)

    def test_ignores_non_matching_keys(self):
        objective = Objective("herbs", "Collect herbs", target=1)
        objective.notify("wolves_killed", 5)
        self.assertEqual(objective.progress, 0)

    def test_without_key_only_duration_or_input_complete_it(self):
        objective = Objective(description="Wait a moment", duration=1.0)
        objective.enter()
        objective.notify("anything", 100)
        objective._tick(1.0)
        self.assertTrue(objective.is_complete())


class StageTestCase(unittest.TestCase):
    def test_completes_once_every_objective_does(self):
        stage = Stage(
            [
                Objective("wolves_killed", "Defeat 3 wolves", target=3),
                Objective("herbs", "Collect 2 herbs", target=2),
            ]
        )
        stage.enter()
        stage.notify("wolves_killed", 3)
        self.assertFalse(stage.is_complete())
        stage.notify("herbs", 2)
        self.assertTrue(stage.is_complete())

    def test_require_all_false_completes_on_first_objective(self):
        stage = Stage(
            [
                Objective("gate", "Reach the gate", target=1),
                Objective("passage", "Find the secret passage", target=1),
            ],
            require_all=False,
        )
        stage.enter()
        stage.notify("passage", 1)
        self.assertTrue(stage.is_complete())


class QuestTestCase(unittest.TestCase):
    def test_advances_through_stages_and_completes(self):
        completed = []
        quest = Quest(
            "wolf_trouble",
            "Wolf Trouble",
            [
                Stage([Objective("wolves_killed", "Defeat 3 wolves", target=3)]),
                Stage([Objective("report", "Report back", target=1)]),
            ],
            on_completed=lambda: completed.append(True),
        )

        quest.notify("wolves_killed", 3)
        quest.update(0.0)
        self.assertIs(quest.current_stage, quest.steps[1])

        quest.notify("report", 1)
        quest.update(0.0)
        self.assertTrue(quest.finished)
        self.assertEqual(completed, [True])

    def test_notify_only_reaches_current_stage(self):
        quest = Quest(
            "two_stage",
            "Two Stage",
            [
                Stage([Objective("a", "A", target=1)]),
                Stage([Objective("a", "A", target=1)]),
            ],
        )
        # Both stages listen for the same key, but only stage 0 is current.
        quest.notify("a", 1)
        self.assertTrue(quest.steps[0].is_complete())
        self.assertEqual(quest.steps[1].steps[0].progress, 0)


class QuestLogTestCase(unittest.TestCase):
    def setUp(self):
        self.log = QuestLog()
        self.quest = Quest(
            "wolf_trouble",
            "Wolf Trouble",
            [Stage([Objective("wolves_killed", "Defeat 3 wolves", target=3)])],
        )
        self.log.register(self.quest)

    def test_start_unknown_quest_raises(self):
        with self.assertRaises(KeyError):
            self.log.start("does_not_exist")

    def test_notify_only_reaches_active_quests(self):
        self.log.notify("wolves_killed", 1)
        self.assertEqual(self.quest.current_stage.steps[0].progress, 0)

        self.log.start("wolf_trouble")
        self.log.notify("wolves_killed", 1)
        self.assertEqual(self.quest.current_stage.steps[0].progress, 1)

    def test_update_moves_finished_quest_to_completed(self):
        self.log.start("wolf_trouble")
        self.log.notify("wolves_killed", 3)
        self.log.update(0.0)
        self.assertFalse(self.log.is_active("wolf_trouble"))
        self.assertTrue(self.log.is_completed("wolf_trouble"))

    def test_starting_twice_is_a_no_op(self):
        self.log.start("wolf_trouble")
        self.log.start("wolf_trouble")
        self.assertEqual(self.log.active_quests(), [self.quest])

    def test_get_returns_registered_quest(self):
        self.assertIs(self.log.get("wolf_trouble"), self.quest)


if __name__ == "__main__":
    unittest.main()
