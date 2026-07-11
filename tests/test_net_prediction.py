import unittest

from gale.net.prediction import PredictionBuffer


def apply_input(state, input_payload, dt):
    return {"x": state["x"] + input_payload.get("dx", 0) * dt}


class PredictionBufferTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.buffer = PredictionBuffer()

    def test_empty_buffer_reconciles_to_authoritative_state(self) -> None:
        authoritative_state = {"x": 5}
        result = self.buffer.reconcile(0, authoritative_state, apply_input)
        self.assertEqual(result, {"x": 5})
        self.assertEqual(self.buffer.pending_count, 0)

    def test_record_tracks_pending_count(self) -> None:
        self.buffer.record(1, {"dx": 1}, {"x": 1}, dt=1.0)
        self.buffer.record(2, {"dx": 1}, {"x": 2}, dt=1.0)
        self.assertEqual(self.buffer.pending_count, 2)

    def test_reconcile_replays_only_unacknowledged_inputs(self) -> None:
        self.buffer.record(1, {"dx": 1}, {"x": 1}, dt=1.0)
        self.buffer.record(2, {"dx": 1}, {"x": 2}, dt=1.0)
        self.buffer.record(3, {"dx": 1}, {"x": 3}, dt=1.0)

        # Server says it processed up through sequence 1, and the
        # authoritative state already reflects that input.
        result = self.buffer.reconcile(1, {"x": 1}, apply_input)

        # Only inputs 2 and 3 should have been replayed on top of the
        # authoritative state.
        self.assertEqual(result, {"x": 3})
        self.assertEqual(self.buffer.pending_count, 2)

    def test_reconcile_discards_acknowledged_sequences(self) -> None:
        self.buffer.record(1, {"dx": 1}, {"x": 1}, dt=1.0)
        self.buffer.record(2, {"dx": 1}, {"x": 2}, dt=1.0)

        self.buffer.reconcile(2, {"x": 2}, apply_input)
        self.assertEqual(self.buffer.pending_count, 0)

    def test_reconcile_corrects_a_missed_input(self) -> None:
        # Client predicted using dx=1, but the server determined the
        # actual effective input differed (e.g. was clamped), so the
        # authoritative state after sequence 1 is different from what
        # the client predicted.
        self.buffer.record(1, {"dx": 1}, {"x": 1}, dt=1.0)
        self.buffer.record(2, {"dx": 1}, {"x": 2}, dt=1.0)

        result = self.buffer.reconcile(1, {"x": 0}, apply_input)
        # Replaying sequence 2's input (dx=1, dt=1.0) on top of the
        # corrected authoritative state of 0.
        self.assertEqual(result, {"x": 1})

    def test_reconcile_with_no_pending_records_after_ack(self) -> None:
        self.buffer.record(1, {"dx": 1}, {"x": 1}, dt=1.0)
        self.buffer.reconcile(1, {"x": 1}, apply_input)
        result = self.buffer.reconcile(1, {"x": 1}, apply_input)
        self.assertEqual(result, {"x": 1})
        self.assertEqual(self.buffer.pending_count, 0)


if __name__ == "__main__":
    unittest.main()
