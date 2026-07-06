import unittest

from gale.net.protocol import (
    HEADER_SIZE,
    SEQUENCE_MODULO,
    Channel,
    is_sequence_newer,
    pack_header,
    unpack_header,
)


class SequenceComparisonTestCase(unittest.TestCase):
    def test_plain_newer(self) -> None:
        self.assertTrue(is_sequence_newer(5, 3))
        self.assertFalse(is_sequence_newer(3, 5))

    def test_equal_is_not_newer(self) -> None:
        self.assertFalse(is_sequence_newer(5, 5))

    def test_wraparound(self) -> None:
        highest = SEQUENCE_MODULO - 1
        wrapped = 0
        self.assertTrue(is_sequence_newer(wrapped, highest))
        self.assertFalse(is_sequence_newer(highest, wrapped))


class HeaderPackingTestCase(unittest.TestCase):
    def test_round_trip(self) -> None:
        data = pack_header(Channel.RELIABLE_ORDERED, 123456789, 42, 41, 0b101)
        self.assertEqual(len(data), HEADER_SIZE)
        channel, token, sequence, ack, ack_bitfield = unpack_header(data)
        self.assertEqual(channel, Channel.RELIABLE_ORDERED)
        self.assertEqual(token, 123456789)
        self.assertEqual(sequence, 42)
        self.assertEqual(ack, 41)
        self.assertEqual(ack_bitfield, 0b101)

    def test_sequence_is_wrapped_when_packing(self) -> None:
        data = pack_header(Channel.UNRELIABLE, 0, SEQUENCE_MODULO + 3, 0, 0)
        _, _, sequence, _, _ = unpack_header(data)
        self.assertEqual(sequence, 3)


if __name__ == "__main__":
    unittest.main()
