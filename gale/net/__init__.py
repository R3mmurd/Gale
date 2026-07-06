"""
gale.net: a pure-Python, pygame-free toolkit to build multiplayer
games over UDP, for LAN or internet play, with a hand-rolled
reliability layer (no dependency on a third-party networking library).

See docs/examples/net.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .client import Client
from .discovery import ServerInfo, discover_lan_servers
from .peer import Peer
from .protocol import Channel
from .serialization import json_deserialize, json_serialize
from .server import Server

__all__ = [
    "Channel",
    "Client",
    "Peer",
    "Server",
    "ServerInfo",
    "discover_lan_servers",
    "json_deserialize",
    "json_serialize",
]
