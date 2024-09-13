import unittest
from unittest.mock import Mock

from gale.event import Event


class EventTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Event.handlers = {}

    def test_on(self) -> None:
        def handler(*args: any, **kwargs: any) -> None:
            pass

        Event.on("event", handler)
        self.assertIn("event", Event.handlers)
        self.assertIn(handler, Event.handlers["event"])

    def test_remove(self) -> None:
        def handler(*args: any, **kwargs: any) -> None:
            pass

        Event.on("event", handler)
        Event.remove("event", handler)
        self.assertNotIn(handler, Event.handlers["event"])

    @staticmethod
    def test_dispatch() -> None:
        handler_mock = Mock()
        Event.on("event", handler_mock)
        Event.dispatch("event")
        handler_mock.assert_called_once()

    @staticmethod
    def test_dispatch_multiple_handlers() -> None:
        handler_mock = Mock()
        handler_mock2 = Mock()
        Event.on("event", handler_mock)
        Event.on("event", handler_mock2)
        Event.dispatch("event")
        handler_mock.assert_called_once()
        handler_mock2.assert_called_once()

    @staticmethod
    def test_dispatch_with_args() -> None:
        handler_mock = Mock()
        Event.on("event", handler_mock)
        Event.dispatch("event", 1, 2, 3)
        handler_mock.assert_called_once_with(1, 2, 3)

    @staticmethod
    def test_no_dispatch() -> None:
        handler_mock = Mock()
        Event.on("event", handler_mock)
        Event.dispatch("another_event")
        handler_mock.assert_not_called()
