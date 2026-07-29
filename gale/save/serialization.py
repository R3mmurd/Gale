"""
The default save-file serializer/deserializer used by SaveManager. Both
are plain functions, and both are accepted as constructor parameters,
so a game that needs a different format (a more compact binary one, an
encrypted one, a compressed one) can swap them out without changing
anything else -- the same pattern gale.net.serialization already uses
for Server/Client.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
from typing import Any, Callable, Dict

Serializer = Callable[[Dict[str, Any]], bytes]
Deserializer = Callable[[bytes], Dict[str, Any]]


def json_serialize(envelope: Dict[str, Any]) -> bytes:
    """
    :param envelope: A JSON-serializable dict (SaveManager's internal
        envelope: version, timestamps, metadata, and the game's data).
    :returns: The UTF-8 encoded JSON representation of envelope.
    """
    return json.dumps(envelope).encode("utf-8")


def json_deserialize(data: bytes) -> Dict[str, Any]:
    """
    :param data: Bytes produced by json_serialize (or a wire-compatible encoder).
    :returns: The decoded envelope dict.
    :raises ValueError: If data is not valid JSON or does not decode to a dict.
    """
    try:
        decoded = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Malformed save data: {error}") from error

    if not isinstance(decoded, dict):
        raise ValueError(
            f"Malformed save data: expected an object, got {type(decoded).__name__}"
        )

    return decoded
