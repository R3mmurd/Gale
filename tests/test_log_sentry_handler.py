import http.server
import json
import logging
import threading
import unittest

from gale.log.sentry_handler import SentryHandler


class _CapturingHandler(http.server.BaseHTTPRequestHandler):
    received = {}

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)
        _CapturingHandler.received["body"] = json.loads(body)
        _CapturingHandler.received["headers"] = dict(self.headers)
        _CapturingHandler.received["path"] = self.path
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args) -> None:
        pass


class SentryHandlerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        _CapturingHandler.received = {}
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _CapturingHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.handle_request, daemon=True)
        self.thread.start()

        self.handler = SentryHandler(
            f"http://public-key@127.0.0.1:{self.port}/42", timeout=2.0
        )
        self.logger = logging.getLogger("test_sentry")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False

    def tearDown(self) -> None:
        self.logger.removeHandler(self.handler)
        self.thread.join(timeout=2.0)
        self.server.server_close()

    def test_sends_event_to_store_endpoint(self) -> None:
        self.logger.error("boom")
        self.thread.join(timeout=2.0)

        self.assertEqual(_CapturingHandler.received["path"], "/api/42/store/")
        body = _CapturingHandler.received["body"]
        self.assertEqual(body["message"], "boom")
        self.assertEqual(body["level"], "error")
        self.assertEqual(body["logger"], "test_sentry")
        self.assertIn("event_id", body)

    def test_auth_header_carries_public_key(self) -> None:
        self.logger.warning("careful")
        self.thread.join(timeout=2.0)

        auth = _CapturingHandler.received["headers"]["X-Sentry-Auth"]
        self.assertIn("sentry_key=public-key", auth)


if __name__ == "__main__":
    unittest.main()
