import unittest

from gale.save.serialization import json_deserialize, json_serialize


class JsonSaveSerializationTestCase(unittest.TestCase):
    def test_round_trip(self) -> None:
        envelope = {"version": 1, "data": {"hp": 80}}
        data = json_serialize(envelope)
        self.assertEqual(json_deserialize(data), envelope)

    def test_deserialize_invalid_json_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b"not json")

    def test_deserialize_invalid_utf8_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b"\xff\xfe")

    def test_deserialize_wrong_shape_raises_value_error(self) -> None:
        self.assertRaises(ValueError, json_deserialize, b"[1, 2, 3]")


if __name__ == "__main__":
    unittest.main()
