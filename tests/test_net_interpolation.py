import unittest
from unittest.mock import patch

from gale.net.interpolation import SnapshotInterpolator, lag_compensated_position


class SnapshotInterpolatorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.interpolator = SnapshotInterpolator()

    def test_sample_with_no_snapshots_returns_none(self) -> None:
        self.assertIsNone(self.interpolator.sample(0.0))

    def test_sample_before_first_returns_first_snapshot(self) -> None:
        with patch("time.monotonic", return_value=10.0):
            self.interpolator.add({"x": 1})

        with patch("time.monotonic", return_value=20.0):
            self.interpolator.add({"x": 2})

        self.assertEqual(self.interpolator.sample(0.0), {"x": 1})

    def test_sample_after_last_returns_last_snapshot(self) -> None:
        with patch("time.monotonic", return_value=10.0):
            self.interpolator.add({"x": 1})

        with patch("time.monotonic", return_value=20.0):
            self.interpolator.add({"x": 2})

        self.assertEqual(self.interpolator.sample(100.0), {"x": 2})

    def test_sample_interpolates_between_bracketing_snapshots(self) -> None:
        with patch("time.monotonic", return_value=0.0):
            self.interpolator.add({"x": 0.0})

        with patch("time.monotonic", return_value=10.0):
            self.interpolator.add({"x": 10.0})

        self.assertEqual(self.interpolator.sample(5.0), {"x": 5.0})

    def test_sample_interpolates_nested_dict_fields(self) -> None:
        with patch("time.monotonic", return_value=0.0):
            self.interpolator.add({"position": {"x": 0.0, "y": 0.0}, "speed": 0.0})

        with patch("time.monotonic", return_value=10.0):
            self.interpolator.add({"position": {"x": 10.0, "y": 20.0}, "speed": 100.0})

        result = self.interpolator.sample(2.5)
        self.assertEqual(result["position"], {"x": 2.5, "y": 5.0})
        self.assertEqual(result["speed"], 25.0)

    def test_single_snapshot_always_returned(self) -> None:
        with patch("time.monotonic", return_value=5.0):
            self.interpolator.add({"x": 42.0})

        self.assertEqual(self.interpolator.sample(0.0), {"x": 42.0})
        self.assertEqual(self.interpolator.sample(100.0), {"x": 42.0})


class LagCompensatedPositionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.history = SnapshotInterpolator()

        with patch("time.monotonic", return_value=0.0):
            self.history.add({"position": {"x": 0.0}})

        with patch("time.monotonic", return_value=10.0):
            self.history.add({"position": {"x": 10.0}})

    def test_empty_history_returns_none(self) -> None:
        empty = SnapshotInterpolator()
        self.assertIsNone(lag_compensated_position(empty, 0.1, now=10.0))

    def test_rewinds_to_past_state(self) -> None:
        result = lag_compensated_position(self.history, rewind_time=5.0, now=10.0)
        self.assertEqual(result, {"position": {"x": 5.0}})

    def test_field_path_drills_into_state(self) -> None:
        result = lag_compensated_position(
            self.history, rewind_time=5.0, field_path=("position", "x"), now=10.0
        )
        self.assertEqual(result, 5.0)

    def test_defaults_now_to_time_monotonic(self) -> None:
        with patch("time.monotonic", return_value=10.0):
            result = lag_compensated_position(self.history, rewind_time=10.0)

        self.assertEqual(result, {"position": {"x": 0.0}})


if __name__ == "__main__":
    unittest.main()
