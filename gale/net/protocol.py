"""
This file contains the wire-level constants and helpers shared by every
piece of gale.net: the channel identifiers, the packet header format,
and the sequence number comparison used by the reliability layer.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import struct

# Maximum payload size (in bytes, after serialization) accepted for a
# single packet. gale.net does not fragment/reassemble large messages,
# so a game that needs to send more than this in one message should
# split it into several smaller messages itself.
MAX_PAYLOAD_SIZE: int = 1200

# Header layout: 1 byte channel id, 8 bytes connection token, 4 bytes
# sequence number, 4 bytes ack (last sequence number received from the
# peer), 4 bytes ack bitfield (whether each of the 32 sequence numbers
# right before ack was also received).
HEADER_FORMAT: str = "!BQIII"
HEADER_SIZE: int = struct.calcsize(HEADER_FORMAT)

SEQUENCE_MODULO: int = 1 << 32

# Reserved message types used internally by Server/Client for the
# connection handshake, heartbeat/RTT measurement, and reliable-channel
# ack flushing. A game's own message types should avoid this exact
# naming (double leading and trailing underscores) to stay out of the way.
CONNECT_REQUEST: str = "__connect_request__"
CONNECT_ACCEPTED: str = "__connect_accepted__"
PING: str = "__ping__"
PONG: str = "__pong__"
ACK: str = "__ack__"
DISCONNECT: str = "__disconnect__"


class Channel:
    """
    Identifies how a message should be delivered.

    - UNRELIABLE: sent once, may be lost or arrive out of order. Use it
      for data that is superseded by the next update anyway, such as a
      position snapshot sent every frame.
    - RELIABLE_ORDERED: guaranteed to arrive, and to be delivered to
      on_message callbacks in the same order it was sent. Use it for
      events where both matter, such as a chat log.
    - RELIABLE_UNORDERED: guaranteed to arrive, but may be delivered out
      of order. Cheaper than RELIABLE_ORDERED since it never has to
      hold a packet back waiting for an earlier one. Use it for events
      that must not be lost but are independent of each other, such as
      "a point was scored".
    """

    UNRELIABLE: int = 0
    RELIABLE_ORDERED: int = 1
    RELIABLE_UNORDERED: int = 2


def is_sequence_newer(a: int, b: int) -> bool:
    """
    Compare two 32-bit sequence numbers that wrap around, accounting
    for the wraparound: after the highest representable sequence number
    comes 0 again, so a plain a > b comparison would be wrong close to
    that wraparound point.

    :param a: A sequence number.
    :param b: A sequence number to compare against.
    :returns: Whether a is newer than b, assuming neither is more than half the sequence space ahead of the other (the standard assumption for this technique).
    """
    diff = (a - b) % SEQUENCE_MODULO
    return 0 < diff < (SEQUENCE_MODULO // 2)


def pack_header(
    channel: int, token: int, sequence: int, ack: int, ack_bitfield: int
) -> bytes:
    """
    :param channel: One of the Channel constants.
    :param token: The connection token for this peer.
    :param sequence: This packet's sequence number (per channel, per direction).
    :param ack: The last sequence number received from the peer on this channel.
    :param ack_bitfield: Bit i (0-indexed) set means sequence number (ack - 1 - i) was also received.
    :returns: The packed header bytes.
    """
    return struct.pack(
        HEADER_FORMAT,
        channel,
        token,
        sequence % SEQUENCE_MODULO,
        ack % SEQUENCE_MODULO,
        ack_bitfield,
    )


def unpack_header(data: bytes):
    """
    :param data: Raw packet bytes, at least HEADER_SIZE long.
    :returns: A tuple (channel, token, sequence, ack, ack_bitfield).
    :raises struct.error: If data is shorter than HEADER_SIZE.
    """
    return struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
