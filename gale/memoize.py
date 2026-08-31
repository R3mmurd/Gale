"""
This file contains Memoized (wraps a function, caching its return
value per distinct positional/keyword argument combination) and the
class Memo, a process-wide registry managing every Memoized created
through Memo.memoize -- the same shape gale.timer's Timer manages
Every/After/Tween: call Memo.update(dt) once a frame to age every
registered cache.

A Memoized's ttl decides what "cached" means, all driven by game time
(dt) rather than the wall clock, so it pauses along with the rest of
the game instead of expiring while a menu is open:

- ttl=None (the default): cached forever, exactly like
  functools.lru_cache, until clear()/invalidate() is called
  explicitly. Prefer plain functools.lru_cache for this case unless
  you specifically want it to live in Memo's registry (so
  Memo.clear() can drop it along with every ttl-based cache, on a
  level unload, say).
- ttl=0: valid only for the remainder of the current frame -- however
  many times it's called before the next update(dt), the wrapped
  function runs once. Useful for a query several independent systems
  might ask for in the same frame (the nearest enemy, a pathfinding
  cost), the same "guard on the frame counter" trick Unity/Godot code
  reaches for by hand.
- ttl=N (seconds): cached for up to N seconds of game time -- useful
  for anything a game can afford to have go stale for a moment (an
  AI's last line-of-sight check, a UI's damage-number aggregation),
  trading a bit of staleness for not recomputing every single call.
  Unlike functools.lru_cache, entries actually expire, so decorating
  an instance method doesn't pin that instance in memory forever.

See docs/examples/memoize.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import functools

from typing import Any, Callable, Dict, List, Optional, Tuple


class Memoized:
    """
    Wraps a function, caching its return value per distinct
    positional/keyword argument combination. Usable directly
    (``Memoized(fn)``) or as a bare decorator (``@Memoized``);
    ``Memo.memoize`` builds one too, additionally registering it so
    Memo.update(dt) ages it automatically, and is the one that also
    accepts ttl as a decorator factory (``@Memo.memoize(ttl=...)``).
    """

    def __init__(
        self, function: Callable[..., Any], ttl: Optional[float] = None
    ) -> None:
        """
        :param function: The function whose return value is cached.
        :param ttl: How many seconds of accumulated update(dt) a cached entry stays valid for. The default value is None, meaning an entry never expires on its own. 0 means an entry is valid only until the next update(dt), however many times it's called before then.
        :raises ValueError: If ttl is negative.
        """
        if ttl is not None and ttl < 0:
            raise ValueError(f"ttl must not be negative, got {ttl!r}")

        functools.update_wrapper(self, function)
        self.function = function
        self.ttl = ttl
        self._entries: Dict[Any, Tuple[Any, float]] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        key = self._make_key(args, kwargs)
        entry = self._entries.get(key)

        if entry is not None:
            value, age = entry
            if self.ttl is None or age <= self.ttl:
                return value

        value = self.function(*args, **kwargs)
        self._entries[key] = (value, 0.0)
        return value

    def __get__(
        self, instance: Any, owner: Optional[type] = None
    ) -> Callable[..., Any]:
        if instance is None:
            return self

        return functools.partial(self, instance)

    def update(self, dt: float) -> None:
        """Age every cached entry by dt, dropping whichever now exceed ttl. A no-op when ttl is None -- a forever cache never expires."""
        if self.ttl is None:
            return

        expired = []

        for key, (value, age) in self._entries.items():
            age += dt
            if age > self.ttl:
                expired.append(key)
            else:
                self._entries[key] = (value, age)

        for key in expired:
            del self._entries[key]

    def invalidate(self, *args: Any, **kwargs: Any) -> None:
        """Drop the single cached entry for this exact call, if any."""
        self._entries.pop(self._make_key(args, kwargs), None)

    def clear(self) -> None:
        """Drop every cached entry, forcing the next call for any arguments to recompute."""
        self._entries = {}

    @staticmethod
    def _make_key(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
        return (args, tuple(sorted(kwargs.items())))

    def __len__(self) -> int:
        return len(self._entries)


class Memo:
    """Process-wide registry of every Memoized created through Memo.memoize -- call Memo.update(dt) once a frame to age all of them."""

    items: List[Memoized] = []
    paused: bool = False

    @classmethod
    def update(cls, dt: float) -> None:
        if cls.paused:
            return

        for item in cls.items:
            item.update(dt)

    @classmethod
    def memoize(
        cls,
        function: Optional[Callable[..., Any]] = None,
        *,
        ttl: Optional[float] = None,
    ):
        """
        :param function: The function to wrap. When omitted, returns a decorator instead (``@Memo.memoize(ttl=...)``).
        :param ttl: Forwarded to Memoized. The default value is None.
        :returns: A Memoized already registered with this class, so Memo.update(dt)/pause()/resume()/clear() reach it.
        """

        def register(fn: Callable[..., Any]) -> Memoized:
            memoized = Memoized(fn, ttl=ttl)
            cls.items.append(memoized)
            return memoized

        if function is not None:
            return register(function)

        return register

    @classmethod
    def clear(cls) -> None:
        cls.items = []
        cls.paused = False

    @classmethod
    def pause(cls) -> None:
        cls.paused = True

    @classmethod
    def resume(cls) -> None:
        cls.paused = False
