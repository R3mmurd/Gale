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


if __name__ == "__main__":
    unittest.main()
