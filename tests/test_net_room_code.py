import unittest

from gale.net.room_code import RoomCodeError, RoomCodeFormat, decode, encode


class RoomCodeTestCase(unittest.TestCase):
    def test_round_trips_with_default_format(self) -> None:
        code = encode("203.0.113.7", 40000)
        self.assertEqual(decode(code), ("203.0.113.7", 40000))

    def test_default_format_is_two_groups_of_five(self) -> None:
        code = encode("203.0.113.7", 40000)
        groups = code.split("-")
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]), 5)
        self.assertEqual(len(groups[1]), 5)

    def test_decode_ignores_whitespace_and_case(self) -> None:
        code = encode("192.168.1.10", 9000)
        messy = f" {code.lower().replace('-', ' ')} "
        self.assertEqual(decode(messy), ("192.168.1.10", 9000))

    def test_rejects_out_of_range_port(self) -> None:
        with self.assertRaises(ValueError):
            encode("127.0.0.1", 70000)

    def test_decode_raises_on_invalid_character(self) -> None:
        with self.assertRaises(RoomCodeError):
            decode("!!!!!-!!!!!")

    def test_custom_format_round_trips(self) -> None:
        custom = RoomCodeFormat(
            alphabet="0123456789abcdefghjkmnpqrstvwxyz",
            group_size=4,
            group_separator=".",
        )
        code = encode("192.168.1.10", 9000, custom)
        self.assertEqual(code, code.lower())
        self.assertEqual(decode(code, custom), ("192.168.1.10", 9000))

    def test_different_formats_round_trip_independently(self) -> None:
        custom = RoomCodeFormat(group_size=3, group_separator=" ")
        code = encode("10.0.0.1", 1234, custom)
        self.assertEqual(decode(code, custom), ("10.0.0.1", 1234))

    def test_resolves_hostnames(self) -> None:
        code = encode("localhost", 8080)
        self.assertEqual(decode(code), ("127.0.0.1", 8080))


if __name__ == "__main__":
    unittest.main()
