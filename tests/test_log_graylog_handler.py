import json
import logging
import socket
import time
import unittest

from gale.log.graylog_handler import GraylogHandler


class GraylogHandlerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiver.bind(("127.0.0.1", 0))
        self.receiver.settimeout(2.0)
        port = self.receiver.getsockname()[1]

        self.handler = GraylogHandler("127.0.0.1", port, source="test-host")
        self.logger = logging.getLogger("test_graylog")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False

    def tearDown(self) -> None:
        self.logger.removeHandler(self.handler)
        self.handler.close()
        self.receiver.close()

    def _receive_payload(self) -> dict:
        data, _ = self.receiver.recvfrom(4096)
        return json.loads(data.decode("utf-8"))

    def test_sends_valid_gelf_payload(self) -> None:
        self.logger.info("hello graylog")
        payload = self._receive_payload()

        self.assertEqual(payload["version"], "1.1")
        self.assertEqual(payload["host"], "test-host")
        self.assertEqual(payload["short_message"], "hello graylog")
        self.assertEqual(payload["level"], 6)
        self.assertIn("timestamp", payload)
        self.assertEqual(payload["_logger"], "test_graylog")

    def test_maps_levels_to_syslog_severity(self) -> None:
        self.logger.error("something broke")
        payload = self._receive_payload()
        self.assertEqual(payload["level"], 3)

    def test_extra_fields_become_underscore_prefixed(self) -> None:
        self.logger.info("player scored", extra={"player_id": 7, "points": 100})
        payload = self._receive_payload()
        self.assertEqual(payload["_player_id"], 7)
        self.assertEqual(payload["_points"], 100)

    def test_reserved_attributes_are_not_duplicated_as_extra_fields(self) -> None:
        self.logger.info("plain message")
        payload = self._receive_payload()
        self.assertNotIn("_module", payload)
        self.assertNotIn("_lineno", payload)


if __name__ == "__main__":
    unittest.main()
