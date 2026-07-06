"""
This file contains the hand-rolled reliability layer used by
gale.net's RELIABLE_ORDERED and RELIABLE_UNORDERED channels: an
outgoing side that tracks unacked packets and retransmits them, and an
incoming side that deduplicates packets and (for the ordered channel)
buffers out-of-order ones until the gap is filled.

UNRELIABLE traffic does not go through either of these: it is just
sent once, with no tracking at all.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Dict, List, Optional, Tuple

from .protocol import SEQUENCE_MODULO, is_sequence_newer

# How many times an unacked packet is retransmitted before the peer is
# considered unreachable and gets disconnected.
MAX_RETRANSMIT_ATTEMPTS: int = 10

# How many packets can be in flight (sent but not yet acked) for a
# single (peer, channel) pair before the peer is disconnected, so a
# peer that stops acking can't grow this buffer without bound.
MAX_IN_FLIGHT: int = 256

# How many past sequence numbers are still checked for dedup/acking.
# Matches the 32 bits available in the ack bitfield.
ACK_WINDOW: int = 32

# Retransmit timeout is derived from the smoothed RTT; this is the
# floor used until a peer has an RTT estimate at all (i.e. right after
# connecting, before the first heartbeat reply comes back).
DEFAULT_RTT: float = 0.1


class ReliableSender:
    """
    Tracks packets sent on one (peer, channel) pair that are waiting
    to be acked, and decides when they should be retransmitted.
    """

    def __init__(self) -> None:
        self.next_sequence: int = 0
        # sequence -> (payload_bytes, last_sent_time, attempts)
        self._pending: Dict[int, Tuple[bytes, float, int]] = {}

    def is_overflowing(self) -> bool:
        """
        :returns: Whether too many packets are in flight, unacked, on this channel. The caller should treat this peer as unreachable.
        """
        return len(self._pending) > MAX_IN_FLIGHT

    def next(self) -> int:
        """
        :returns: The next sequence number to use for a new packet, advancing the internal counter.
        """
        sequence = self.next_sequence
        self.next_sequence = (self.next_sequence + 1) % SEQUENCE_MODULO
        return sequence

    def track(self, sequence: int, payload: bytes, now: float) -> None:
        """
        Register a just-sent packet so it can be retransmitted if it
        is not acked in time.

        :param sequence: The packet's sequence number.
        :param payload: The serialized message bytes (without the header).
        :param now: The current time, in seconds.
        """
        self._pending[sequence] = (payload, now, 1)

    def acknowledge(self, ack: int, ack_bitfield: int) -> None:
        """
        Drop every pending packet the peer has confirmed receiving,
        either directly (sequence == ack) or through the bitfield
        (sequence in the ACK_WINDOW packets right before ack).

        :param ack: The highest sequence number the peer says it received.
        :param ack_bitfield: Bit i set means sequence (ack - 1 - i) was also received.
        """
        self._pending.pop(ack, None)

        for i in range(ACK_WINDOW):
            if ack_bitfield & (1 << i):
                sequence = (ack - 1 - i) % SEQUENCE_MODULO
                self._pending.pop(sequence, None)

    def due_for_retransmit(
        self, now: float, rtt: float
    ) -> Tuple[List[Tuple[int, bytes]], bool]:
        """
        :param now: The current time, in seconds.
        :param rtt: The peer's current smoothed round-trip time, in seconds, used to size the retransmit timeout.
        :returns: A tuple (packets, gave_up). packets is the list of (sequence, payload) pairs that should be resent now. gave_up is True if some packet exceeded MAX_RETRANSMIT_ATTEMPTS, meaning the caller should disconnect this peer.
        """
        timeout = 2 * (rtt if rtt > 0 else DEFAULT_RTT)
        due: List[Tuple[int, bytes]] = []
        gave_up = False

        for sequence, (payload, last_sent_time, attempts) in list(
            self._pending.items()
        ):
            if now - last_sent_time < timeout * attempts:
                continue

            if attempts >= MAX_RETRANSMIT_ATTEMPTS:
                del self._pending[sequence]
                gave_up = True
                continue

            self._pending[sequence] = (payload, now, attempts + 1)
            due.append((sequence, payload))

        return due, gave_up


class ReliableReceiver:
    """
    Tracks packets received on one (peer, channel) pair: deduplicates
    them and, for the ordered channel, holds out-of-order packets back
    until the ones before them arrive.
    """

    def __init__(self, ordered: bool) -> None:
        self.ordered: bool = ordered
        self.highest_received: Optional[int] = None
        self._seen: Dict[int, bool] = {}
        self._next_expected: int = 0
        self._reorder_buffer: Dict[int, bytes] = {}

    def receive(self, sequence: int, payload: bytes) -> List[bytes]:
        """
        :param sequence: The received packet's sequence number.
        :param payload: The received packet's payload bytes.
        :returns: The list of payloads (possibly empty, possibly more than one) that should now be delivered to on_message callbacks, in delivery order.
        """
        if sequence in self._seen:
            return []

        if self.highest_received is None or is_sequence_newer(
            sequence, self.highest_received
        ):
            self.highest_received = sequence

        self._seen[sequence] = True
        self._prune_seen()

        if not self.ordered:
            return [payload]

        if sequence != self._next_expected and not is_sequence_newer(
            sequence, self._next_expected
        ):
            # Already delivered (or too old to ever deliver); drop it.
            return []

        self._reorder_buffer[sequence] = payload
        ready: List[bytes] = []

        while self._next_expected in self._reorder_buffer:
            ready.append(self._reorder_buffer.pop(self._next_expected))
            self._next_expected = (self._next_expected + 1) % SEQUENCE_MODULO

        return ready

    def build_ack(self) -> Tuple[int, int]:
        """
        :returns: A tuple (ack, ack_bitfield) describing what has been received so far, to be sent back to the peer.
        """
        if self.highest_received is None:
            return 0, 0

        bitfield = 0

        for i in range(ACK_WINDOW):
            sequence = (self.highest_received - 1 - i) % SEQUENCE_MODULO

            if sequence in self._seen:
                bitfield |= 1 << i

        return self.highest_received, bitfield

    def _prune_seen(self) -> None:
        if self.highest_received is None:
            return

        cutoff = ACK_WINDOW * 4

        for sequence in list(self._seen):
            distance = (self.highest_received - sequence) % SEQUENCE_MODULO

            if distance > cutoff:
                del self._seen[sequence]
