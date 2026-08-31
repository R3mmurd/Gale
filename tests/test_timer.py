import unittest

from gale.timer import Timer


class DummyTarget:
    def __init__(self, x: float = 0.0) -> None:
        self.x = x


class EveryTestCase(unittest.TestCase):
    def test_fires_every_interval(self) -> None:
        calls = []
        Timer.every(1.0, lambda: calls.append(1))
        Timer.update(0.5)
        self.assertEqual(len(calls), 0)
        Timer.update(0.5)
        self.assertEqual(len(calls), 1)
        Timer.update(1.0)
        self.assertEqual(len(calls), 2)

    def test_only_fires_once_per_update_even_if_dt_covers_multiple_periods(
        self,
    ) -> None:
        # Every.update() checks its accumulated timer once per call,
        # not in a catch-up loop -- a single update() covering several
        # periods' worth of dt still only fires once.
        calls = []
        Timer.every(1.0, lambda: calls.append(1))
        Timer.update(2.5)
        self.assertEqual(len(calls), 1)

    def test_leftover_time_carries_into_the_next_update(self) -> None:
        calls = []
        Timer.every(1.0, lambda: calls.append(1))
        Timer.update(2.5)
        Timer.update(0.5)
        self.assertEqual(len(calls), 2)

    def test_limit_removes_the_item_and_calls_on_finish(self) -> None:
        calls = []
        finished = []
        Timer.every(
            1.0, lambda: calls.append(1), limit=2, on_finish=lambda: finished.append(1)
        )
        Timer.update(1.0)
        Timer.update(1.0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(finished), 1)
        self.assertEqual(len(Timer.items), 0)

        Timer.update(1.0)
        self.assertEqual(len(calls), 2)


class AfterTestCase(unittest.TestCase):
    def test_fires_once_after_the_delay(self) -> None:
        calls = []
        Timer.after(1.0, lambda: calls.append(1))
        Timer.update(0.5)
        self.assertEqual(len(calls), 0)
        Timer.update(0.5)
        self.assertEqual(len(calls), 1)
        Timer.update(10.0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(Timer.items), 0)


class TweenTestCase(unittest.TestCase):
    def test_interpolates_towards_the_final_value(self) -> None:
        target = DummyTarget(x=0.0)
        Timer.tween(1.0, [(target, {"x": 10.0})])
        Timer.update(0.5)
        self.assertAlmostEqual(target.x, 5.0)
        Timer.update(0.5)
        self.assertAlmostEqual(target.x, 10.0)

    def test_calls_on_finish_and_removes_itself(self) -> None:
        target = DummyTarget()
        finished = []
        Timer.tween(1.0, [(target, {"x": 10.0})], on_finish=lambda: finished.append(1))
        Timer.update(1.0)
        self.assertEqual(len(finished), 1)
        self.assertEqual(len(Timer.items), 0)

    def test_overshoot_snaps_exactly_to_the_final_value(self) -> None:
        target = DummyTarget()
        Timer.tween(1.0, [(target, {"x": 10.0})])
        Timer.update(5.0)
        self.assertEqual(target.x, 10.0)

    def test_unknown_ease_function_raises(self) -> None:
        self.assertRaises(
            RuntimeError,
            Timer.tween,
            1.0,
            [(DummyTarget(), {"x": 1.0})],
            "not_a_real_ease_function",
        )

    def test_multiple_objects_and_attributes(self) -> None:
        a = DummyTarget(x=0.0)
        b = DummyTarget(x=100.0)
        Timer.tween(1.0, [(a, {"x": 10.0}), (b, {"x": 0.0})])
        Timer.update(1.0)
        self.assertEqual(a.x, 10.0)
        self.assertEqual(b.x, 0.0)


class TimerControlTestCase(unittest.TestCase):
    def test_pause_stops_every_item_from_updating(self) -> None:
        calls = []
        Timer.every(1.0, lambda: calls.append(1))
        Timer.pause()
        Timer.update(2.0)
        self.assertEqual(len(calls), 0)

    def test_resume_continues_updating(self) -> None:
        calls = []
        Timer.every(1.0, lambda: calls.append(1))
        Timer.pause()
        Timer.update(2.0)
        Timer.resume()
        Timer.update(1.0)
        self.assertEqual(len(calls), 1)

    def test_clear_removes_every_item_and_unpauses(self) -> None:
        Timer.every(1.0, lambda: None)
        Timer.pause()
        Timer.clear()
        self.assertEqual(len(Timer.items), 0)
        self.assertFalse(Timer.paused)

    def test_remove_marks_an_item_for_removal_on_next_update(self) -> None:
        item = Timer.after(10.0, lambda: None)
        item.remove()
        Timer.update(0.0)
        self.assertEqual(len(Timer.items), 0)

    def test_finish_replaces_the_on_finish_callback(self) -> None:
        calls = []
        item = Timer.after(1.0, lambda: calls.append("original"))
        item.finish(lambda: calls.append("replaced"))
        Timer.update(1.0)
        self.assertEqual(calls, ["replaced"])


class DuringTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Timer.clear()

    def tearDown(self) -> None:
        Timer.clear()

    def test_calls_function_with_dt_and_progress_every_update(self) -> None:
        calls = []
        Timer.during(2.0, lambda dt, progress: calls.append((dt, progress)))
        Timer.update(0.5)
        Timer.update(0.5)
        self.assertEqual(calls, [(0.5, 0.25), (0.5, 0.5)])

    def test_progress_is_clamped_to_1_and_on_finish_runs_once(self) -> None:
        calls = []
        finished = []
        Timer.during(
            1.0,
            lambda dt, progress: calls.append(progress),
            on_finish=lambda: finished.append(1),
        )
        Timer.update(1.5)
        self.assertEqual(calls, [1.0])
        self.assertEqual(len(finished), 1)
        self.assertEqual(len(Timer.items), 0)

    def test_stops_being_called_after_it_finishes(self) -> None:
        calls = []
        Timer.during(1.0, lambda dt, progress: calls.append(1))
        Timer.update(1.0)
        Timer.update(1.0)
        self.assertEqual(len(calls), 1)


class TimerProgressTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Timer.clear()

    def tearDown(self) -> None:
        Timer.clear()

    def test_progress_starts_at_zero(self) -> None:
        item = Timer.after(2.0, lambda: None)
        self.assertEqual(item.progress, 0.0)

    def test_progress_reflects_elapsed_fraction(self) -> None:
        item = Timer.after(2.0, lambda: None)
        Timer.update(0.5)
        self.assertAlmostEqual(item.progress, 0.25)

    def test_progress_never_exceeds_one(self) -> None:
        target = DummyTarget()
        item = Timer.tween(1.0, [(target, {"x": 10.0})])
        Timer.update(5.0)
        self.assertEqual(item.progress, 1.0)

    def test_progress_is_one_for_a_non_positive_time(self) -> None:
        item = Timer.after(0.0, lambda: None)
        self.assertEqual(item.progress, 1.0)


class TimerPerItemPauseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Timer.clear()

    def tearDown(self) -> None:
        Timer.clear()

    def test_pausing_one_item_does_not_affect_others(self) -> None:
        calls_a = []
        calls_b = []
        item_a = Timer.every(1.0, lambda: calls_a.append(1))
        Timer.every(1.0, lambda: calls_b.append(1))

        item_a.pause()
        Timer.update(1.0)

        self.assertEqual(calls_a, [])
        self.assertEqual(calls_b, [1])

    def test_resuming_an_item_lets_it_update_again(self) -> None:
        calls = []
        item = Timer.every(1.0, lambda: calls.append(1))
        item.pause()
        Timer.update(1.0)
        item.resume()
        Timer.update(1.0)
        self.assertEqual(calls, [1])


class TimerGroupTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Timer.clear()

    def tearDown(self) -> None:
        Timer.clear()

    def test_pausing_a_group_only_stops_items_in_that_group(self) -> None:
        enemy_calls = []
        ui_calls = []
        Timer.every(1.0, lambda: enemy_calls.append(1), group="enemies")
        Timer.every(1.0, lambda: ui_calls.append(1), group="ui")

        Timer.pause(group="enemies")
        Timer.update(1.0)

        self.assertEqual(enemy_calls, [])
        self.assertEqual(ui_calls, [1])

    def test_resuming_a_group_lets_it_update_again(self) -> None:
        calls = []
        Timer.every(1.0, lambda: calls.append(1), group="enemies")
        Timer.pause(group="enemies")
        Timer.update(1.0)
        Timer.resume(group="enemies")
        Timer.update(1.0)
        self.assertEqual(calls, [1])

    def test_ungrouped_items_are_unaffected_by_a_group_pause(self) -> None:
        calls = []
        Timer.every(1.0, lambda: calls.append(1))
        Timer.pause(group="enemies")
        Timer.update(1.0)
        self.assertEqual(calls, [1])

    def test_ignore_global_pause_keeps_a_group_running_while_everything_else_stops(
        self,
    ) -> None:
        gameplay_calls = []
        ui_calls = []
        Timer.every(1.0, lambda: gameplay_calls.append(1))
        Timer.every(1.0, lambda: ui_calls.append(1), ignore_global_pause=True)

        Timer.pause()
        Timer.update(1.0)

        self.assertEqual(gameplay_calls, [])
        self.assertEqual(ui_calls, [1])

    def test_group_pause_still_applies_even_with_ignore_global_pause(self) -> None:
        calls = []
        Timer.every(
            1.0,
            lambda: calls.append(1),
            group="ui",
            ignore_global_pause=True,
        )
        Timer.pause(group="ui")
        Timer.update(1.0)
        self.assertEqual(calls, [])

    def test_clear_with_a_group_only_removes_that_groups_items(self) -> None:
        Timer.every(1.0, lambda: None, group="enemies")
        Timer.every(1.0, lambda: None, group="ui")
        Timer.every(1.0, lambda: None)

        Timer.clear(group="enemies")

        groups = {item.group for item in Timer.items}
        self.assertEqual(groups, {"ui", None})

    def test_clear_with_a_group_also_unpauses_that_group(self) -> None:
        Timer.every(1.0, lambda: None, group="enemies")
        Timer.pause(group="enemies")
        Timer.clear(group="enemies")
        self.assertNotIn("enemies", Timer.paused_groups)

    def test_clear_without_a_group_still_clears_everything_and_every_group_pause(
        self,
    ) -> None:
        Timer.every(1.0, lambda: None, group="enemies")
        Timer.pause(group="enemies")
        Timer.clear()
        self.assertEqual(len(Timer.items), 0)
        self.assertEqual(len(Timer.paused_groups), 0)

    def test_group_can_be_any_hashable_object_not_just_a_string(self) -> None:
        class Owner:
            pass

        owner = Owner()
        calls = []
        Timer.every(1.0, lambda: calls.append(1), group=owner)
        Timer.clear(group=owner)
        self.assertEqual(len(Timer.items), 0)


if __name__ == "__main__":
    unittest.main()
