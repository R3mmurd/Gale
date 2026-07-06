import threading
import time
import unittest

from gale.net.discovery import discover_lan_servers
from gale.net.server import Server


class DiscoveryTestCase(unittest.TestCase):
    def test_discover_finds_enabled_server(self) -> None:
        # A real game pumps Server.update() continuously from its own
        # process while a Client calls the (blocking) discover_lan_servers()
        # from a different one; a background thread reproduces that
        # concurrency for the test without needing a second process.
        server = Server(port=0)
        discovery_port = _free_udp_port()
        server.enable_lan_discovery("Rally Table", discovery_port=discovery_port)
        stop = threading.Event()

        def pump_server() -> None:
            while not stop.is_set():
                server.update(0.01)
                time.sleep(0.01)

        pump_thread = threading.Thread(target=pump_server, daemon=True)
        pump_thread.start()

        try:
            found = discover_lan_servers(discovery_port=discovery_port, timeout=1.0)

            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].name, "Rally Table")
            self.assertEqual(found[0].address[1], server.port)
            self.assertEqual(found[0].player_count, 0)
        finally:
            stop.set()
            pump_thread.join()
            server.close()

    def test_discover_finds_nothing_when_no_server_listening(self) -> None:
        discovery_port = _free_udp_port()
        found = discover_lan_servers(discovery_port=discovery_port, timeout=0.2)
        self.assertEqual(found, [])


def _free_udp_port() -> int:
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


if __name__ == "__main__":
    unittest.main()
