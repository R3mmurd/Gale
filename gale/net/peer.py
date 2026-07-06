"""
This file contains the implementation of the class Peer, the
Server-side handle to a connected Client.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Tuple


class Peer:
    """
    Represents one connected client, from the Server's point of view.

    Usage example:

        for peer in server.get_peers():
            print(peer.peer_id, peer.address, peer.rtt)
    """

    def __init__(self, peer_id: int, address: Tuple[str, int], token: int) -> None:
        """
        :param peer_id: Unique id assigned to this peer by the Server that created it.
        :param address: The peer's (host, port) address.
        :param token: Random connection token used to reject packets spoofing this peer's address.
        """
        self.peer_id: int = peer_id
        self.address: Tuple[str, int] = address
        self.token: int = token
        self.rtt: float = 0.0
        self.last_seen: float = 0.0
        self.connected: bool = True

    def update_rtt(self, sample: float) -> None:
        """
        Fold a new round-trip-time sample into the smoothed estimate
        using an exponential moving average.

        :param sample: The latest measured round-trip time, in seconds.
        """
        if self.rtt == 0.0:
            self.rtt = sample
        else:
            self.rtt = 0.875 * self.rtt + 0.125 * sample
