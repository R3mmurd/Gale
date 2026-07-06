import time
import unittest

from gale.net.client import Client
from gale.net.protocol import Channel
from gale.net.server import Server

STEP: float = 0.01


def pump(*endpoints, until, deadline: float = 3.0) -> bool:
    """
    Repeatedly call update(STEP) on every endpoint until until() returns
    a truthy value or deadline seconds have elapsed. Returns whether
    until() succeeded.
    """
    start = time.monotonic()

    while time.monotonic() - start < deadline:
        for endpoint in endpoints:
            endpoint.update(STEP)

        if until():
            return True

        time.sleep(STEP)

    return False


class ServerClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.server = Server(port=0, timeout=1.0, heartbeat_interval=0.05)
        self.client = Client(timeout=1.0)
        self.client.heartbeat_interval = 0.05

    def tearDown(self) -> None:
        self.client.close()
        self.server.close()

    def test_connect(self) -> None:
        self.client.connect("127.0.0.1", self.server.port)
        connected = pump(self.server, self.client, until=lambda: self.client.connected)
        self.assertTrue(connected)
        self.assertEqual(len(self.server.get_peers()), 1)

    def test_unreliable_message_delivery(self) -> None:
        received = []
        self.server.on_message("ping", lambda peer, payload: received.append(payload))
        self.client.connect("127.0.0.1", self.server.port)
        pump(self.server, self.client, until=lambda: self.client.connected)

        self.client.send("ping", {"n": 1}, channel=Channel.UNRELIABLE)
        pump(self.server, self.client, until=lambda: len(received) == 1)
        self.assertEqual(received, [{"n": 1}])

    def test_reliable_ordered_delivery(self) -> None:
        received = []
        self.server.on_message("event", lambda peer, payload: received.append(payload))
        self.client.connect("127.0.0.1", self.server.port)
        pump(self.server, self.client, until=lambda: self.client.connected)

        for i in range(5):
            self.client.send("event", {"n": i}, channel=Channel.RELIABLE_ORDERED)

        pump(self.server, self.client, until=lambda: len(received) == 5)
        self.assertEqual([payload["n"] for payload in received], [0, 1, 2, 3, 4])

    def test_server_to_client_reliable_unordered(self) -> None:
        received = []
        self.client.on_message("score", lambda payload: received.append(payload))
        self.client.connect("127.0.0.1", self.server.port)
        pump(self.server, self.client, until=lambda: self.client.connected)

        self.server.broadcast(
            "score", {"points": 10}, channel=Channel.RELIABLE_UNORDERED
        )
        pump(self.server, self.client, until=lambda: len(received) == 1)
        self.assertEqual(received, [{"points": 10}])

    def test_rtt_is_measured(self) -> None:
        self.client.connect("127.0.0.1", self.server.port)
        pump(self.server, self.client, until=lambda: self.client.connected)
        pump(
            self.server,
            self.client,
            until=lambda: self.client.get_rtt() is not None
            and self.client.get_rtt() > 0,
        )
        self.assertGreater(self.client.get_rtt(), 0)

        peer = self.server.get_peers()[0]
        pump(
            self.server,
            self.client,
            until=lambda: self.server.get_rtt(peer.peer_id) > 0,
        )
        self.assertGreater(self.server.get_rtt(peer.peer_id), 0)

    def test_disconnect_notifies_server(self) -> None:
        disconnected = []
        self.server.on_disconnect(lambda peer: disconnected.append(peer.peer_id))
        self.client.connect("127.0.0.1", self.server.port)
        pump(self.server, self.client, until=lambda: self.client.connected)

        self.client.disconnect()
        pump(self.server, until=lambda: len(disconnected) == 1, deadline=1.0)
        self.assertEqual(len(disconnected), 1)

    def test_connect_failed_when_server_unreachable(self) -> None:
        failed = []
        client = Client(timeout=1.0)
        client.on_connect_failed(lambda reason: failed.append(reason))
        client.connect("127.0.0.1", 1, timeout=0.2)
        pump(client, until=lambda: len(failed) == 1, deadline=1.0)
        client.close()
        self.assertEqual(len(failed), 1)


if __name__ == "__main__":
    unittest.main()
