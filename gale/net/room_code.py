"""
gale.net.room_code: encode a host/port pair as a short, human-typeable
code (e.g. "7QK3M-2XHDR" with the default format) instead of making
players share a raw IP and port. This is a pure, local, symmetric
encoding: there is no matchmaking/relay server involved, and no
dependency on Server/Client — a Client still connects directly to the
decoded (host, port).

The default format (Crockford base32, grouped 5-5) is a sane default
for "read it over voice chat" room codes, but every part of it -
alphabet, group size, separator - is configurable per game through
RoomCodeFormat, so a game can match whatever house style it wants
(e.g. lowercase, 3-3-3 groups, no separator at all).

See docs/examples/net.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math
import re
import socket
import struct
from dataclasses import dataclass
from typing import Tuple

# Crockford base32: digits + uppercase letters, excluding I, L, O, U to
# avoid confusion with 1, 1, 0, and V when read or typed by hand.
DEFAULT_ALPHABET: str = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
DEFAULT_GROUP_SIZE: int = 5
DEFAULT_GROUP_SEPARATOR: str = "-"

# A host (32-bit IPv4) plus a port (16-bit) pack into 48 bits.
_ADDRESS_BITS: int = 48
_PORT_BITS: int = 16
_PORT_MASK: int = (1 << _PORT_BITS) - 1


class RoomCodeError(ValueError):
    """Raised when a string isn't a valid room code for a given format."""


@dataclass(frozen=True)
class RoomCodeFormat:
    """
    How a room code is rendered: which characters it can use, how many
    of them are grouped together, and what separates the groups. Two
    RoomCodeFormat instances with the same alphabet and group_size
    round-trip each other's codes regardless of group_separator, since
    decoding strips every group_separator character before decoding.

    Usage example:

        # "7qk3-m2x-hdr" style: lowercase, 4-3-3 groups, dash-separated.
        my_format = RoomCodeFormat(
            alphabet="0123456789abcdefghjkmnpqrstvwxyz",
            group_size=4,
        )
    """

    alphabet: str = DEFAULT_ALPHABET
    group_size: int = DEFAULT_GROUP_SIZE
    group_separator: str = DEFAULT_GROUP_SEPARATOR

    def __post_init__(self) -> None:
        if len(self.alphabet) < 2:
            raise ValueError("alphabet must have at least 2 characters")

        if len(set(self.alphabet)) != len(self.alphabet):
            raise ValueError("alphabet must not contain repeated characters")

        if self.group_size < 1:
            raise ValueError("group_size must be at least 1")

    @property
    def char_count(self) -> int:
        """
        :returns: How many characters, in this format's alphabet, are needed to represent any (host, port) pair.
        """
        base = len(self.alphabet)
        return math.ceil(_ADDRESS_BITS * math.log(2) / math.log(base))


DEFAULT_FORMAT = RoomCodeFormat()


def encode(host: str, port: int, fmt: RoomCodeFormat = DEFAULT_FORMAT) -> str:
    """
    :param host: An IPv4 address (e.g. "203.0.113.7") or a resolvable hostname.
    :param port: A UDP/TCP port, between 0 and 65535.
    :param fmt: The format to render the code in. The default value is DEFAULT_FORMAT ("XXXXX-XXXXX", Crockford base32).
    :returns: A short code that decode() can turn back into (host, port).
    """
    if not 0 <= port <= 0xFFFF:
        raise ValueError(f"port must be between 0 and 65535, got {port}")

    packed = _pack(host, port)
    raw = _encode_int(packed, fmt)
    groups = [raw[i : i + fmt.group_size] for i in range(0, len(raw), fmt.group_size)]
    return fmt.group_separator.join(groups)


def decode(code: str, fmt: RoomCodeFormat = DEFAULT_FORMAT) -> Tuple[str, int]:
    """
    :param code: A code produced by encode() with the same fmt (whitespace, group_separator, and, for a same-case alphabet, letter case are all ignored).
    :param fmt: The format code was rendered in. The default value is DEFAULT_FORMAT.
    :returns: The (host, port) pair encode() was given.
    :raises RoomCodeError: If code contains a character outside fmt.alphabet.
    """
    cleaned = _normalize(code, fmt)
    value = _decode_int(cleaned, fmt)
    return _unpack(value)


def _normalize(code: str, fmt: RoomCodeFormat) -> str:
    cleaned = re.sub(r"\s+", "", code.strip())

    if fmt.group_separator:
        cleaned = cleaned.replace(fmt.group_separator, "")

    if fmt.alphabet == fmt.alphabet.upper():
        cleaned = cleaned.upper()
    elif fmt.alphabet == fmt.alphabet.lower():
        cleaned = cleaned.lower()

    return cleaned


def _pack(host: str, port: int) -> int:
    try:
        packed_ip = struct.unpack("!I", socket.inet_aton(host))[0]
    except OSError:
        resolved = socket.gethostbyname(host)
        packed_ip = struct.unpack("!I", socket.inet_aton(resolved))[0]

    return (packed_ip << _PORT_BITS) | port


def _unpack(value: int) -> Tuple[str, int]:
    port = value & _PORT_MASK
    packed_ip = value >> _PORT_BITS
    host = socket.inet_ntoa(struct.pack("!I", packed_ip))
    return host, port


def _encode_int(value: int, fmt: RoomCodeFormat) -> str:
    base = len(fmt.alphabet)
    digits = []

    for _ in range(fmt.char_count):
        digits.append(fmt.alphabet[value % base])
        value //= base

    return "".join(reversed(digits))


def _decode_int(chars: str, fmt: RoomCodeFormat) -> int:
    base = len(fmt.alphabet)
    value = 0

    for char in chars:
        try:
            index = fmt.alphabet.index(char)
        except ValueError:
            raise RoomCodeError(
                f"{char!r} is not a valid character for this room code format"
            ) from None

        value = value * base + index

    return value
