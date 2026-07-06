"""
This file contains LAN discovery: a small UDP broadcast protocol a
Client can use to find Servers running on the same local network,
without the player having to type an IP address. Deliberately
LAN-only (relies on IP broadcast, which routers do not forward) and
kept to tiny request/response packets, so it is not useful as an
amplification vector: a public, internet-facing dedicated server
should simply not call Server.enable_lan_discovery.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
import socket
import time
from typing import List, NamedTuple, Tuple

DISCOVERY_MAGIC: bytes = b"GALEDISC1"
DEFAULT_DISCOVERY_PORT: int = 9998
MAX_DISCOVERY_PACKET_SIZE: int = 512


class ServerInfo(NamedTuple):
    """
    Information about a Server found through LAN discovery.
    """

    name: str
    address: Tuple[str, int]
    player_count: int


def discover_lan_servers(
    discovery_port: int = DEFAULT_DISCOVERY_PORT, timeout: float = 1.0
) -> List[ServerInfo]:
    """
    Broadcast a discovery request on the local network and collect
    every reply that comes back within timeout seconds.

    :param discovery_port: The UDP port Servers are listening for discovery requests on (see Server.enable_lan_discovery). The default value is DEFAULT_DISCOVERY_PORT.
    :param timeout: How long to wait for replies, in seconds. The default value is 1.0.
    :returns: The list of ServerInfo found, one per replying Server.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.sendto(DISCOVERY_MAGIC, ("255.255.255.255", discovery_port))

        results: List[ServerInfo] = []
        deadline = time.monotonic() + timeout

        while True:
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                break

            sock.settimeout(remaining)

            try:
                data, address = sock.recvfrom(MAX_DISCOVERY_PACKET_SIZE)
            except socket.timeout:
                break

            if not data.startswith(DISCOVERY_MAGIC):
                continue

            try:
                info = json.loads(data[len(DISCOVERY_MAGIC) :].decode("utf-8"))
                results.append(
                    ServerInfo(
                        name=info["name"],
                        address=(address[0], info["port"]),
                        player_count=info["player_count"],
                    )
                )
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError):
                continue

        return results
    finally:
        sock.close()
