import http.server
import json
import logging
import threading
import unittest

from gale.log.discord_webhook_handler import DiscordWebhookHandler


class _CapturingHandler(http.server.BaseHTTPRequestHandler):
    received = {}

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)
        _CapturingHandler.received["body"] = json.loads(body)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args) -> None:
        pass


class DiscordWebhookHandlerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        _CapturingHandler.received = {}
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _CapturingHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.handle_request, daemon=True)
        self.thread.start()

        self.handler = DiscordWebhookHandler(
            f"http://127.0.0.1:{self.port}/webhook", username="test_game", timeout=2.0
        )
        self.logger = logging.getLogger("test_discord")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False

    def tearDown(self) -> None:
        self.logger.removeHandler(self.handler)
        self.thread.join(timeout=2.0)
        self.server.server_close()

    def test_posts_message_content_and_username(self) -> None:
        self.logger.warning("low fuel")
        self.thread.join(timeout=2.0)

        body = _CapturingHandler.received["body"]
        self.assertEqual(body["content"], "low fuel")
        self.assertEqual(body["username"], "test_game")

    def test_truncates_content_to_discords_limit(self) -> None:
        handler = DiscordWebhookHandler(f"http://127.0.0.1:{self.port}/webhook")
        long_message = "x" * 3000
        record = logging.LogRecord(
            "test_discord", logging.INFO, __file__, 1, long_message, None, None
        )
        handler.emit(record)
        self.thread.join(timeout=2.0)

        body = _CapturingHandler.received["body"]
        self.assertEqual(len(body["content"]), 2000)


if __name__ == "__main__":
    unittest.main()
