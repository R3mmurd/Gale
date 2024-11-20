"""
This module contains a simple event system.
"""


class Event:
    """
    This class represents an event.
    """

    handlers: dict[str | int, list[callable]] = {}

    @classmethod
    def on(cls, event_id: str | int, handler: callable) -> None:
        """
        Register a handler for an event.
        :param event_id: The event id.
        :param handler: The handler function.
        """
        if event_id not in cls.handlers:
            cls.handlers[event_id] = []
        cls.handlers[event_id].append(handler)

    @classmethod
    def remove(cls, event_id: str | int, handler: callable) -> None:
        """
        Remove a handler for an event.
        :param event_id: The event id.
        :param handler: The handler function.
        """
        if event_id in cls.handlers:
            cls.handlers[event_id].remove(handler)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all handlers.
        """
        cls.handlers = {}

    @classmethod
    def remove_event(cls, event_id: str | int) -> None:
        """
        Remove an event.
        :param event_id: The event id.
        """
        if event_id in cls.handlers:
            del cls.handlers[event_id]

    @classmethod
    def dispatch(cls, event_id: str | int, *args: any, **kwargs: any) -> None:
        """
        Dispatch an event.
        :param event_id: The event id.
        """
        if event_id in cls.handlers:
            for handler in cls.handlers[event_id]:
                handler(*args, **kwargs)
