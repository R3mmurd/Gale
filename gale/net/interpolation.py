"""
This file contains the implementation of the class SnapshotInterpolator,
a small recipe for smoothing remote state (an opponent's car, a ball)
received over an unreliable, latency-bearing connection: buffer a few
recent, timestamped snapshots and interpolate between the two that
bracket the moment you want to render, instead of snapping straight to
whatever the latest UDP packet said (which looks jittery whenever
packets arrive unevenly).

It also contains lag_compensated_position, a thin helper built on top
of SnapshotInterpolator for the other classic use of buffered snapshot
history: lag compensation. When a laggy client reports "I shot the
target", the server should check that hit against where the target was
in that client's view of the world (some time in the past), not where
it is right now.

Both are engine-agnostic, generic over plain, JSON-serializable state
dicts, and optional: gale.net only gives you the primitives (timestamps,
per-peer RTT via Client.get_rtt()/Server.get_rtt()) and leaves the right
amount of buffering/delay and the right shape to interpolate to the
game, the same way examples/rally's snapshot_buffer.py (which this
module generalizes) always has. Choosing how much to correct visible
discrepancies (snapping vs. smoothing) is likewise left to the game.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

MAX_SNAPSHOTS: int = 16


class SnapshotInterpolator:
    """
    Buffers timestamped snapshots of a single piece of remote state and
    reconstructs it at an arbitrary past moment by linearly
    interpolating between the two snapshots that bracket it.

    Usage example:

        history = SnapshotInterpolator()

        client.on_message(
            "snapshot", lambda payload: history.add(payload)
        )

        # Every render frame, rendering slightly in the past so there
        # is usually a snapshot on either side to interpolate between:
        render_time = time.monotonic() - interpolation_delay
        state = history.sample(render_time)

        if state is not None:
            draw_car(state["x"], state["y"], state["heading"])

    One SnapshotInterpolator holds the history for one remote entity; a
    game with several remote entities (other cars, other players) keeps
    one instance per entity.
    """

    def __init__(self) -> None:
        self._snapshots: List[Tuple[float, Dict[str, Any]]] = []

    def add(self, data: Dict[str, Any]) -> None:
        """
        :param data: A JSON-serializable dict of numeric (possibly nested) fields, stamped with the local arrival time.
        """
        self._snapshots.append((time.monotonic(), data))
        self._snapshots = self._snapshots[-MAX_SNAPSHOTS:]

    def sample(self, render_time: float) -> Optional[Dict[str, Any]]:
        """
        :param render_time: The moment (in time.monotonic() terms) to reconstruct the state for.
        :returns: The interpolated data, the oldest snapshot if render_time is at or before it, the newest snapshot if render_time is at or after it, or None if nothing has been added yet.
        """
        if not self._snapshots:
            return None

        if len(self._snapshots) == 1 or render_time <= self._snapshots[0][0]:
            return self._snapshots[0][1]

        for (t0, d0), (t1, d1) in zip(self._snapshots, self._snapshots[1:]):
            if t0 <= render_time <= t1:
                alpha = 0.0 if t1 == t0 else (render_time - t0) / (t1 - t0)
                return _lerp(d0, d1, alpha)

        return self._snapshots[-1][1]


def lag_compensated_position(
    history: SnapshotInterpolator,
    rewind_time: float,
    field_path: Optional[Sequence[str]] = None,
    now: Optional[float] = None,
) -> Optional[Any]:
    """
    Rewind a target's snapshot history back to how a (laggy) shooter
    perceived it, for server-side hit detection: instead of testing a
    shot against the target's current, authoritative position, test it
    against where the target was rewind_time seconds ago, which is
    approximately where the shooter actually saw it when they fired.

    rewind_time is typically the shooter's RTT / 2 (one-way trip from
    server to shooter) plus whatever interpolation delay the shooter's
    own SnapshotInterpolator/rendering uses.

    :param history: The target's snapshot history.
    :param rewind_time: How far back in time, in seconds, to rewind.
    :param field_path: Optional sequence of keys to drill into the sampled snapshot (e.g. ("position",) to get just the nested position dict). The default value is None, meaning the whole sampled snapshot is returned.
    :param now: The current time in time.monotonic() terms. The default value is None, meaning time.monotonic() is used.
    :returns: The target's interpolated state at the rewound moment (or the value at field_path within it), or None if history has no snapshots yet.
    """
    current_time = time.monotonic() if now is None else now
    state = history.sample(current_time - rewind_time)

    if state is None:
        return None

    if field_path is None:
        return state

    value: Any = state

    for key in field_path:
        value = value[key]

    return value


def _lerp(a: Dict[str, Any], b: Dict[str, Any], alpha: float) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    for key, value in a.items():
        other = b[key]
        result[key] = (
            _lerp(value, other, alpha)
            if isinstance(value, dict)
            else value + (other - value) * alpha
        )

    return result
