"""
gale.net: a pure-Python, pygame-free toolkit to build multiplayer
games over UDP, for LAN or internet play, with a hand-rolled
reliability layer (no dependency on a third-party networking library),
LAN discovery, and configurable-format room codes (encode/decode) for
sharing a host/port pair as a short, human-typeable string.

See docs/examples/net.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .client import Client
from .discovery import ServerInfo, discover_lan_servers
from .peer import Peer
from .protocol import Channel
from .room_code import DEFAULT_FORMAT, RoomCodeError, RoomCodeFormat, decode, encode
from .serialization import json_deserialize, json_serialize
from .server import Server

__all__ = [
    "Channel",
    "Client",
    "DEFAULT_FORMAT",
    "Peer",
    "RoomCodeError",
    "RoomCodeFormat",
    "Server",
    "ServerInfo",
    "decode",
    "discover_lan_servers",
    "encode",
    "json_deserialize",
    "json_serialize",
]
