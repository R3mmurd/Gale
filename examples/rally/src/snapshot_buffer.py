"""
A small recipe for smoothing remote state (the opponent's paddle, the
ball) over an unreliable, latency-bearing connection: buffer a few
recent, timestamped snapshots and interpolate between the two that
bracket the moment we want to render, instead of snapping straight to
whatever the latest UDP packet said (which looks jittery whenever
packets arrive unevenly).

This is deliberately local to this example, not part of gale.net: the
right amount of buffering/delay and the right shape to interpolate are
game-specific, so gale.net only gives you the primitives (timestamps,
per-peer RTT via Client.get_rtt()/Server.get_rtt()) and leaves this
part to the game.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

MAX_SNAPSHOTS: int = 16


class SnapshotBuffer:
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
        :param render_time: The moment (in time.monotonic() terms) to reconstruct the state for, typically now minus a small delay so there is usually a snapshot on either side of it to interpolate between.
        :returns: The interpolated data, or None if nothing has been added yet.
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
