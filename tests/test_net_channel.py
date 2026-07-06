import unittest

from gale.net.channel import (
    ACK_WINDOW,
    MAX_IN_FLIGHT,
    MAX_RETRANSMIT_ATTEMPTS,
    ReliableReceiver,
    ReliableSender,
)


class ReliableSenderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.sender = ReliableSender()

    def test_next_increments(self) -> None:
        self.assertEqual(self.sender.next(), 0)
        self.assertEqual(self.sender.next(), 1)

    def test_acknowledge_removes_pending(self) -> None:
        seq = self.sender.next()
        self.sender.track(seq, b"payload", now=0.0)
        due, gave_up = self.sender.due_for_retransmit(now=0.0, rtt=0.1)
        self.assertEqual(due, [])
        self.assertFalse(gave_up)

        self.sender.acknowledge(seq, 0)
        due, _ = self.sender.due_for_retransmit(now=10.0, rtt=0.1)
        self.assertEqual(due, [])

    def test_acknowledge_via_bitfield(self) -> None:
        seq = self.sender.next()
        self.sender.track(seq, b"payload", now=0.0)
        later_seq = self.sender.next()
        self.sender.track(later_seq, b"payload2", now=0.0)

        # later_seq acked directly; seq acked through bit 0 of the bitfield.
        self.sender.acknowledge(later_seq, 0b1)
        due, _ = self.sender.due_for_retransmit(now=10.0, rtt=0.1)
        self.assertEqual(due, [])

    def test_retransmits_after_timeout(self) -> None:
        seq = self.sender.next()
        self.sender.track(seq, b"payload", now=0.0)
        due, gave_up = self.sender.due_for_retransmit(now=1.0, rtt=0.1)
        self.assertEqual(due, [(seq, b"payload")])
        self.assertFalse(gave_up)

    def test_gives_up_after_max_attempts(self) -> None:
        seq = self.sender.next()
        self.sender.track(seq, b"payload", now=0.0)
        now = 0.0

        for _ in range(MAX_RETRANSMIT_ATTEMPTS):
            due, gave_up = self.sender.due_for_retransmit(now=now, rtt=0.01)
            self.assertFalse(gave_up)
            now += 1.0

        due, gave_up = self.sender.due_for_retransmit(now=now, rtt=0.01)
        self.assertTrue(gave_up)
        self.assertEqual(due, [])

    def test_overflow(self) -> None:
        for _ in range(MAX_IN_FLIGHT + 1):
            seq = self.sender.next()
            self.sender.track(seq, b"x", now=0.0)

        self.assertTrue(self.sender.is_overflowing())


class ReliableReceiverUnorderedTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.receiver = ReliableReceiver(ordered=False)

    def test_delivers_immediately(self) -> None:
        self.assertEqual(self.receiver.receive(0, b"a"), [b"a"])
        self.assertEqual(self.receiver.receive(2, b"c"), [b"c"])
        self.assertEqual(self.receiver.receive(1, b"b"), [b"b"])

    def test_drops_duplicates(self) -> None:
        self.receiver.receive(0, b"a")
        self.assertEqual(self.receiver.receive(0, b"a"), [])

    def test_ack_reflects_bitfield(self) -> None:
        self.receiver.receive(0, b"a")
        self.receiver.receive(2, b"c")
        ack, bitfield = self.receiver.build_ack()
        self.assertEqual(ack, 2)
        # sequence 1 (ack - 1 - 0) missing, sequence 0 (ack - 1 - 1) present.
        self.assertFalse(bitfield & (1 << 0))
        self.assertTrue(bitfield & (1 << 1))


class ReliableReceiverOrderedTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.receiver = ReliableReceiver(ordered=True)

    def test_delivers_in_order_when_received_in_order(self) -> None:
        self.assertEqual(self.receiver.receive(0, b"a"), [b"a"])
        self.assertEqual(self.receiver.receive(1, b"b"), [b"b"])

    def test_buffers_out_of_order_packets(self) -> None:
        self.assertEqual(self.receiver.receive(1, b"b"), [])
        self.assertEqual(self.receiver.receive(0, b"a"), [b"a", b"b"])

    def test_drops_duplicate_of_already_delivered(self) -> None:
        self.receiver.receive(0, b"a")
        self.assertEqual(self.receiver.receive(0, b"a"), [])

    def test_ack_window_bound(self) -> None:
        self.assertLessEqual(ACK_WINDOW, 32)


if __name__ == "__main__":
    unittest.main()
