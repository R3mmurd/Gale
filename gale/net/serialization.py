"""
This file contains the default message serializer/deserializer used by
gale.net's Server and Client. Both are plain functions, and both are
accepted as constructor parameters, so a game that needs a more compact
wire format (for a latency-critical action game, say) can swap them out
without changing anything else.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
from typing import Any, Callable, Dict, Tuple

Serializer = Callable[[str, Dict[str, Any]], bytes]
Deserializer = Callable[[bytes], Tuple[str, Dict[str, Any]]]


def json_serialize(message_type: str, payload: Dict[str, Any]) -> bytes:
    """
    :param message_type: The message type/name.
    :param payload: The message's data.
    :returns: The UTF-8 encoded JSON representation of {"type": message_type, "payload": payload}.
    """
    return json.dumps({"type": message_type, "payload": payload}).encode("utf-8")


def json_deserialize(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    :param data: Bytes produced by json_serialize (or a wire-compatible encoder).
    :returns: A tuple (message_type, payload).
    :raises ValueError: If data is not valid JSON or does not have the expected shape.
    """
    try:
        decoded = json.loads(data.decode("utf-8"))
        return decoded["type"], decoded["payload"]
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"Malformed message: {error}") from error
