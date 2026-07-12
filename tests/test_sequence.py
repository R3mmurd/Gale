import unittest
from types import SimpleNamespace

from gale.sequence import Sequence, Step, StepGroup


class RecordingStep(Step):
    def __init__(self, name, log, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.log = log

    def enter(self, *args, **kwargs):
        super().enter(*args, **kwargs)
        self.log.append(f"{self.name}:enter")

    def exit(self):
        self.log.append(f"{self.name}:exit")

    def update(self, dt):
        self.log.append(f"{self.name}:update")

    def render(self, surface):
        self.log.append(f"{self.name}:render")


class StepTestCase(unittest.TestCase):
    def test_duration_completes_after_elapsed_time(self):
        step = Step(duration=1.0)
        step.enter()
        step._tick(0.6)
        self.assertFalse(step.is_complete())
        step._tick(0.5)
        self.assertTrue(step.is_complete())

    def test_never_completes_without_duration_or_input(self):
        step = Step()
        step.enter()
        step._tick(1000.0)
        self.assertFalse(step.is_complete())

    def test_advance_on_input_completes_on_matching_press(self):
        step = Step(advance_on_input="confirm")
        step.enter()
        step.on_input("move_left", SimpleNamespace(pressed=True))
        self.assertFalse(step.is_complete())
        step.on_input("confirm", SimpleNamespace(pressed=False))
        self.assertFalse(step.is_complete())
        step.on_input("confirm", SimpleNamespace(pressed=True))
        self.assertTrue(step.is_complete())

    def test_enter_resets_bookkeeping(self):
        step = Step(duration=1.0)
        step.enter()
        step._tick(1.0)
        self.assertTrue(step.is_complete())
        step.enter()
        self.assertFalse(step.is_complete())


class StepGroupTestCase(unittest.TestCase):
    def test_require_all_waits_for_every_child(self):
        group = StepGroup([Step(duration=1.0), Step(duration=2.0)])
        group.enter()
        group.update(1.5)
        self.assertFalse(group.is_complete())
        group.update(1.0)
        self.assertTrue(group.is_complete())

    def test_require_any_completes_on_first_child(self):
        group = StepGroup([Step(duration=1.0), Step(duration=5.0)], require_all=False)
        group.enter()
        group.update(1.0)
        self.assertTrue(group.is_complete())

    def test_own_duration_forces_completion_regardless_of_children(self):
        group = StepGroup([Step(duration=5.0)], duration=0.5)
        group.enter()
        group._tick(0.5)
        self.assertTrue(group.is_complete())

    def test_finished_children_are_not_ticked_again(self):
        log = []
        group = StepGroup(
            [
                RecordingStep("a", log, duration=1.0),
                RecordingStep("b", log, duration=2.0),
            ]
        )
        group.enter()
        group.update(1.0)
        log.clear()
        group.update(1.0)
        self.assertNotIn("a:update", log)
        self.assertIn("b:update", log)

    def test_on_input_forwarded_to_every_child(self):
        group = StepGroup(
            [Step(advance_on_input="confirm"), Step(advance_on_input="confirm")]
        )
        group.enter()
        group.on_input("confirm", SimpleNamespace(pressed=True))
        self.assertTrue(group.is_complete())


class SequenceTestCase(unittest.TestCase):
    def test_enters_first_step_immediately(self):
        log = []
        Sequence([RecordingStep("a", log, duration=1.0)])
        self.assertEqual(log, ["a:enter"])

    def test_advances_through_steps_in_order(self):
        log = []
        sequence = Sequence(
            [
                RecordingStep("a", log, duration=1.0),
                RecordingStep("b", log, duration=1.0),
            ]
        )
        log.clear()
        sequence.update(1.0)
        self.assertEqual(log, ["a:update", "a:exit", "b:enter"])

    def test_on_finished_called_once_when_steps_run_out(self):
        finished = []
        sequence = Sequence(
            [Step(duration=1.0)], on_finished=lambda: finished.append(1)
        )
        sequence.update(1.0)
        self.assertEqual(finished, [1])
        self.assertTrue(sequence.finished)
        sequence.update(1.0)
        self.assertEqual(finished, [1])

    def test_empty_sequence_finishes_immediately(self):
        finished = []
        sequence = Sequence([], on_finished=lambda: finished.append(1))
        self.assertTrue(sequence.finished)
        self.assertEqual(finished, [1])

    def test_render_delegates_to_current_step(self):
        log = []
        sequence = Sequence([RecordingStep("a", log, duration=1.0)])
        log.clear()
        sequence.render(None)
        self.assertEqual(log, ["a:render"])

    def test_on_input_delegates_to_current_step(self):
        sequence = Sequence([Step(advance_on_input="confirm")])
        sequence.on_input("confirm", SimpleNamespace(pressed=True))
        self.assertTrue(sequence.current.is_complete())

    def test_skip_current_advances_early(self):
        log = []
        sequence = Sequence(
            [RecordingStep("a", log, duration=100.0), RecordingStep("b", log)]
        )
        sequence.skip_current()
        self.assertEqual(sequence.index, 1)
        self.assertEqual(sequence.current.name, "b")


if __name__ == "__main__":
    unittest.main()
