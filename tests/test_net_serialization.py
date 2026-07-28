import unittest

from gale.net.serialization import json_deserialize, json_serialize


class JsonSerializationTestCase(unittest.TestCase):
    def test_round_trip(self) -> None:
        data = json_serialize("hello", {"name": "Ada"})
        message_type, payload = json_deserialize(data)
        self.assertEqual(message_type, "hello")
        self.assertEqual(payload, {"name": "Ada"})

    def test_deserialize_invalid_json_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b"not json")

    def test_deserialize_invalid_utf8_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b"\xff\xfe")

    def test_deserialize_missing_keys_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b'{"type": "hello"}')

    def test_deserialize_wrong_shape_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b"[1, 2, 3]")


if __name__ == "__main__":
    unittest.main()
