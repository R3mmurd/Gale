"""
This file contains the implementation of the class Blackboard, a shared
key-value store to pass data between an agent's behavior tree/decision
tree nodes and any other system, the same role a Blackboard plays
alongside Behavior Trees in engines such as Unreal Engine.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Dict, List, Optional

Observer = Callable[[str, Any, Any], None]


class Blackboard:
    """
    A shared key-value store meant to be attached to an Agent (see
    gale.ai.agent) so its behavior tree/decision tree nodes, its
    steering behaviors, and any external system (a perception system, a
    quest system, another agent) can read and write data about it
    without having to wire up direct references to one another.

    For instance, a perception system can post the last known position
    of a player under the "last_seen_player_position" key, a Condition
    node can check whether "is_alerted" is set, and a Task node can set
    "patrol_point" for a Seek steering behavior to read on its next
    update — none of them need to know about each other, only about the
    blackboard and the keys they agree on.

    Usage example:

        blackboard = Blackboard({"is_alerted": False})
        blackboard.set("last_seen_player_position", (120, 80))
        blackboard.get("is_alerted")  # False
        blackboard.get("patrol_point", default=(0, 0))

        def on_alert_changed(key, old_value, new_value):
            print(f"{key} changed from {old_value} to {new_value}")

        blackboard.observe("is_alerted", on_alert_changed)
        blackboard.set("is_alerted", True)  # triggers on_alert_changed
    """

    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        """
        :param values: Initial key-value pairs. The default value is an empty blackboard.
        """
        self._values: Dict[str, Any] = dict(values) if values else {}
        self._observers: Dict[str, List[Observer]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        :param key: The key to look up.
        :param default: Value returned if key has not been set. The default value is None.
        :returns: The value stored under key, or default if it has not been set.
        """
        return self._values.get(key, default)

    def has(self, key: str) -> bool:
        """
        :param key: The key to look for.
        :returns: Whether key currently has a value set.
        """
        return key in self._values

    def set(self, key: str, value: Any) -> None:
        """
        Set key to value. If the stored value actually changes (or key
        did not have a value before), every observer registered for
        key via observe is notified.

        :param key: The key to set.
        :param value: The new value.
        """
        changed = key not in self._values or self._values[key] != value
        old_value = self._values.get(key)
        self._values[key] = value

        if changed:
            for observer in self._observers.get(key, []):
                observer(key, old_value, value)

    def erase(self, key: str) -> None:
        """
        Remove key and its value. Does nothing if key has no value set.
        Registered observers for key are kept.

        :param key: The key to remove.
        """
        self._values.pop(key, None)

    def clear(self) -> None:
        """
        Remove every key and its value. Registered observers are kept.
        """
        self._values.clear()

    def observe(self, key: str, observer: Observer) -> None:
        """
        Register observer to be called whenever key's stored value
        changes through set().

        :param key: The key to watch.
        :param observer: Callable invoked as observer(key, old_value, new_value). old_value is None if key had no value set before.
        """
        self._observers.setdefault(key, []).append(observer)

    def stop_observing(self, key: str, observer: Observer) -> None:
        """
        Unregister a callable previously registered with observe.

        :param key: The key that was being watched.
        :param observer: The exact callable passed to observe.
        :raises ValueError: If observer was not registered for key.
        """
        self._observers[key].remove(observer)

    def __contains__(self, key: str) -> bool:
        return self.has(key)
