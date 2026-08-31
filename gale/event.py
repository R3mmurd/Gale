"""
gale.event: a lightweight, decoupled publish/subscribe toolkit --
Signal (a single, explicit event channel: connect/disconnect/emit,
priority-ordered, connect(..., once=True) for a listener that detaches
itself before it runs so it can safely reconnect from inside its own
callback), EventEmitter (a mixin/composable object owning any number
of ad hoc, string-named Signals created lazily on first use --
on/off/once/emit, the same shape knife.event and Godot's by-name
signal API use), and EventBus, a ready-to-use global EventEmitter
exposed as classmethods over a single module-level instance, the same
shape gale.input_handler.InputHandler already uses for its own
listeners -- for cross-module communication that shouldn't have to
route through a shared object reference (gale.quest broadcasting
"wolves_killed" for gale.ai or gale.ui to react to, without either one
importing the other).

Every emit snapshots its listener list before iterating, so a listener
that connects or disconnects another listener -- or itself -- from
inside its own callback never corrupts the dispatch (the same defense
InputHandler.notify already uses via listeners.copy()), and isolates
each listener's exceptions (logged through gale.log, never propagated)
so one broken subscriber can never break every other, independently
owned listener on the same event. That is a deliberately stricter
contract than InputHandler.notify's fail-fast one: InputHandler always
routes to a single active entity, while an event here is a fan-out to
an arbitrary number of unrelated listeners, the same guarantee
addEventListener and Unity's UnityEvent give a DOM/Inspector-wired
audience.

See docs/examples/event.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, List, NamedTuple, Optional

from gale.log import get_logger


class _ListenerEntry(NamedTuple):
    listener: Callable[..., Any]
    once: bool
    priority: int


class Signal:
    """
    A single event channel. Holds no notion of a name or an owner --
    just the list of listeners connected to it -- so it can be used
    directly as an attribute (``died = Signal()``) or driven
    dynamically by EventEmitter/EventBus.
    """

    def __init__(self) -> None:
        self._entries: List[_ListenerEntry] = []

    def connect(
        self,
        listener: Callable[..., Any],
        *,
        once: bool = False,
        priority: int = 0,
    ) -> None:
        """
        :param listener: A callable invoked with whatever positional/keyword arguments emit() is given.
        :param once: If True, listener is disconnected right before it runs its first time, so a single emit() call never reaches it twice. The default value is False.
        :param priority: Listeners with a higher priority run first; listeners sharing a priority run in the order they were connected. The default value is 0.
        :raises ValueError: If listener is already connected -- almost always a sign of a missing disconnect() paired with an enter()/setup() that runs more than once.
        """
        if self.is_connected(listener):
            raise ValueError(f"{listener!r} is already connected to this Signal")

        self._entries.append(_ListenerEntry(listener, once, priority))

    def disconnect(self, listener: Callable[..., Any]) -> None:
        """
        Remove listener. A silent no-op if it was never connected (or
        already disconnected), the same tolerance
        InputHandler.unregister_listener gives.
        """
        self._entries = [entry for entry in self._entries if entry.listener != listener]

    def is_connected(self, listener: Callable[..., Any]) -> bool:
        return any(entry.listener == listener for entry in self._entries)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        """
        Call every connected listener with args/kwargs, highest
        priority first (ties keep connection order). Snapshots the
        listener list up front, so a listener that connects or
        disconnects another listener (including itself) never
        corrupts this dispatch: a disconnected once listener is
        skipped if it hasn't run yet, and a newly connected listener
        only takes part in the next emit(). A listener that raises has
        the exception logged and dispatch continues -- one broken
        subscriber never stops the rest from being notified.
        """
        snapshot = sorted(self._entries, key=lambda entry: -entry.priority)

        for entry in snapshot:
            if not self.is_connected(entry.listener):
                continue

            if entry.once:
                self.disconnect(entry.listener)

            try:
                entry.listener(*args, **kwargs)
            except Exception:
                get_logger("event").exception(
                    "Unhandled exception in listener %r", entry.listener
                )

    def clear(self) -> None:
        self._entries = []

    def __len__(self) -> int:
        return len(self._entries)


class EventEmitter:
    """
    Mixin/composable object owning an open-ended set of string-named
    Signal channels, created lazily the first time each name is used.
    Combine it by multiple inheritance the way InputListener/
    CommandControlled are combined today, or hold one as a plain
    attribute wherever inheritance doesn't fit (a World, a QuestLog, a
    net Server/Client, ...).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._signals: Dict[str, Signal] = {}

    def signal(self, event_name: str) -> Signal:
        """
        The Signal backing event_name, creating it on first use.
        Exposed so callers that need it (len(), is_connected(), ...)
        don't have to go through on/off/emit for everything.
        """
        return self._signals.setdefault(event_name, Signal())

    def on(
        self,
        event_name: str,
        listener: Callable[..., Any],
        *,
        once: bool = False,
        priority: int = 0,
    ) -> None:
        self.signal(event_name).connect(listener, once=once, priority=priority)

    def once(
        self, event_name: str, listener: Callable[..., Any], *, priority: int = 0
    ) -> None:
        self.on(event_name, listener, once=True, priority=priority)

    def off(self, event_name: str, listener: Callable[..., Any]) -> None:
        """
        Silent no-op if event_name was never used, or listener was
        never connected to it.
        """
        signal = self._signals.get(event_name)

        if signal is not None:
            signal.disconnect(listener)

    def is_on(self, event_name: str, listener: Callable[..., Any]) -> bool:
        signal = self._signals.get(event_name)
        return signal is not None and signal.is_connected(listener)

    def has_listeners(self, event_name: str) -> bool:
        signal = self._signals.get(event_name)
        return signal is not None and len(signal) > 0

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """A silent no-op if nobody has ever connected to event_name."""
        signal = self._signals.get(event_name)

        if signal is not None:
            signal.emit(*args, **kwargs)

    def clear(self, event_name: Optional[str] = None) -> None:
        """
        :param event_name: The single event to disconnect every listener from. The default value is None, clearing every event this emitter owns.
        """
        if event_name is None:
            self._signals = {}
        elif event_name in self._signals:
            self._signals[event_name].clear()


class EventBus:
    """
    Ready-to-use global EventEmitter, exposed as classmethods over a
    single module-level instance -- the same shape InputHandler gives
    its own listeners -- for modules that want to publish/subscribe
    without sharing an object reference to do it.
    """

    _emitter = EventEmitter()

    @classmethod
    def signal(cls, event_name: str) -> Signal:
        return cls._emitter.signal(event_name)

    @classmethod
    def on(
        cls,
        event_name: str,
        listener: Callable[..., Any],
        *,
        once: bool = False,
        priority: int = 0,
    ) -> None:
        cls._emitter.on(event_name, listener, once=once, priority=priority)

    @classmethod
    def once(
        cls, event_name: str, listener: Callable[..., Any], *, priority: int = 0
    ) -> None:
        cls._emitter.once(event_name, listener, priority=priority)

    @classmethod
    def off(cls, event_name: str, listener: Callable[..., Any]) -> None:
        cls._emitter.off(event_name, listener)

    @classmethod
    def is_on(cls, event_name: str, listener: Callable[..., Any]) -> bool:
        return cls._emitter.is_on(event_name, listener)

    @classmethod
    def has_listeners(cls, event_name: str) -> bool:
        return cls._emitter.has_listeners(event_name)

    @classmethod
    def emit(cls, event_name: str, *args: Any, **kwargs: Any) -> None:
        cls._emitter.emit(event_name, *args, **kwargs)

    @classmethod
    def clear(cls, event_name: Optional[str] = None) -> None:
        cls._emitter.clear(event_name)
