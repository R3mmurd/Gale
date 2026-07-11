"""
This file contains the implementation of the class PredictionBuffer, a
small recipe for client-side prediction and server reconciliation: a
client applies its own inputs immediately (instead of waiting for a
round trip to the server) so movement feels instant, keeps a record of
each predicted input/state pair, and later replays whatever inputs the
server has not yet acknowledged on top of the authoritative state it
sends back, so the client ends up in the same place the server would
have put it while still feeling responsive.

Like gale.net's other recipes (see gale.net.interpolation), this is
kept generic over plain, JSON-serializable state and input payloads:
gale.net has no notion of "physics" or "entities", it only moves bytes
and tracks time, so this module only ever deals in plain dicts and a
game-supplied apply_input function.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, List, NamedTuple

from .protocol import is_sequence_newer

ApplyInput = Callable[[Dict[str, Any], Dict[str, Any], float], Dict[str, Any]]


class _Record(NamedTuple):
    sequence: int
    input_payload: Dict[str, Any]
    dt: float
    predicted_state: Dict[str, Any]


class PredictionBuffer:
    """
    Buffers a client's own predicted inputs/states so they can be
    replayed on top of an authoritative state sent back by the server
    (client-side prediction + server reconciliation).

    Usage example:

        buffer = PredictionBuffer()

        # Every local frame, after applying input `payload` for `dt`
        # seconds and predicting the resulting state:
        sequence += 1
        predicted_state = apply_input(current_state, payload, dt)
        buffer.record(sequence, payload, dt, predicted_state)
        client.send("input", {"sequence": sequence, **payload})

        # When the server reports how far it got:
        def on_snapshot(payload):
            state = buffer.reconcile(
                payload["last_processed_sequence"],
                payload["state"],
                apply_input,
            )
            # `state` is where the client should render from now;
            # smoothly correcting towards it (rather than snapping)
            # to hide any discrepancy with what was predicted before
            # is left to the game, the same way gale.net leaves the
            # amount of snapshot-interpolation delay to the game (see
            # gale.net.interpolation).

    apply_input has the signature (state, input_payload, dt) ->
    new_state, and must be a pure function of its arguments (no
    reliance on wall-clock time, randomness, or outside state) since it
    is replayed after the fact, possibly several times per reconcile()
    call.
    """

    def __init__(self) -> None:
        self._records: List[_Record] = []

    @property
    def pending_count(self) -> int:
        """
        :returns: The number of recorded inputs not yet discarded by reconcile(), i.e. still awaiting server acknowledgement.
        """
        return len(self._records)

    def record(
        self,
        sequence: int,
        input_payload: Dict[str, Any],
        predicted_state: Dict[str, Any],
        dt: float = 0.0,
    ) -> None:
        """
        Store an input and the state predicted from applying it,
        keyed by sequence number, to be replayed later if the server's
        authoritative state does not already account for it.

        :param sequence: This input's sequence number. Must increase from one call to the next (matching the sequence the game sends to the server alongside the input).
        :param input_payload: The input applied this frame.
        :param predicted_state: The state that resulted from applying input_payload locally. Not used by reconcile() itself (it always replays from the authoritative state), but useful for the game to inspect/compare.
        :param dt: Time elapsed, in seconds, over which input_payload was applied. Replayed unchanged by reconcile(). The default value is 0.0.
        """
        self._records.append(_Record(sequence, input_payload, dt, predicted_state))

    def reconcile(
        self,
        last_processed_sequence: int,
        authoritative_state: Dict[str, Any],
        apply_input: ApplyInput,
    ) -> Dict[str, Any]:
        """
        Discard every recorded input the server has already accounted
        for (sequence <= last_processed_sequence), then replay every
        remaining, unacknowledged input on top of authoritative_state,
        in the order it was recorded.

        :param last_processed_sequence: The highest input sequence number the server had already processed when it produced authoritative_state.
        :param authoritative_state: The state the server computed after processing inputs up through last_processed_sequence.
        :param apply_input: Function (state, input_payload, dt) -> new_state, applied once per remaining buffered input, in order.
        :returns: The reconciled state: authoritative_state with every unacknowledged input replayed on top of it.
        """
        self._records = [
            record
            for record in self._records
            if is_sequence_newer(record.sequence, last_processed_sequence)
        ]

        state = authoritative_state

        for record in self._records:
            state = apply_input(state, record.input_payload, record.dt)

        return state
