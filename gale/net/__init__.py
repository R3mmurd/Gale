"""
gale.net: a pure-Python, pygame-free toolkit to build multiplayer
games over UDP, for LAN or internet play, with a hand-rolled
reliability layer (no dependency on a third-party networking library),
LAN discovery, configurable-format room codes (encode/decode) for
sharing a host/port pair as a short, human-typeable string, and
optional building blocks for client-side prediction/server
reconciliation (PredictionBuffer) and entity interpolation/lag
compensation (SnapshotInterpolator, lag_compensated_position).

See docs/examples/net.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .client import Client
from .discovery import ServerInfo, discover_lan_servers
from .interpolation import SnapshotInterpolator, lag_compensated_position
from .peer import Peer
from .prediction import PredictionBuffer
from .protocol import Channel
from .room_code import DEFAULT_FORMAT, RoomCodeError, RoomCodeFormat, decode, encode
from .serialization import json_deserialize, json_serialize
from .server import Server

__all__ = [
    "Channel",
    "Client",
    "DEFAULT_FORMAT",
    "Peer",
    "PredictionBuffer",
    "RoomCodeError",
    "RoomCodeFormat",
    "Server",
    "ServerInfo",
    "SnapshotInterpolator",
    "decode",
    "discover_lan_servers",
    "encode",
    "json_deserialize",
    "json_serialize",
    "lag_compensated_position",
]
