import unittest

from gale.event import EventBus, EventEmitter, Signal


class RecordingListener:
    def __init__(self) -> None:
        self.calls = []

    def __call__(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))


class SignalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.signal = Signal()

    def test_starts_empty(self) -> None:
        self.assertEqual(len(self.signal), 0)

    def test_connect_increases_length(self) -> None:
        self.signal.connect(RecordingListener())
        self.assertEqual(len(self.signal), 1)

    def test_emit_calls_listener_with_args_and_kwargs(self) -> None:
        listener = RecordingListener()
        self.signal.connect(listener)
        self.signal.emit(1, 2, name="hero")
        self.assertEqual(listener.calls, [((1, 2), {"name": "hero"})])

    def test_emit_with_no_listeners_does_not_raise(self) -> None:
        self.signal.emit("anything")

    def test_multiple_listeners_are_called_in_connection_order_by_default(
        self,
    ) -> None:
        order = []
        self.signal.connect(lambda: order.append("first"))
        self.signal.connect(lambda: order.append("second"))
        self.signal.connect(lambda: order.append("third"))
        self.signal.emit()
        self.assertEqual(order, ["first", "second", "third"])

    def test_higher_priority_listeners_are_called_first(self) -> None:
        order = []
        self.signal.connect(lambda: order.append("low"), priority=0)
        self.signal.connect(lambda: order.append("high"), priority=10)
        self.signal.connect(lambda: order.append("medium"), priority=5)
        self.signal.emit()
        self.assertEqual(order, ["high", "medium", "low"])

    def test_equal_priority_preserves_connection_order(self) -> None:
        order = []
        self.signal.connect(lambda: order.append("a"), priority=1)
        self.signal.connect(lambda: order.append("b"), priority=1)
        self.signal.connect(lambda: order.append("c"), priority=1)
        self.signal.emit()
        self.assertEqual(order, ["a", "b", "c"])

    def test_connecting_the_same_listener_twice_raises(self) -> None:
        listener = RecordingListener()
        self.signal.connect(listener)
        with self.assertRaises(ValueError):
            self.signal.connect(listener)

    def test_is_connected(self) -> None:
        listener = RecordingListener()
        self.assertFalse(self.signal.is_connected(listener))
        self.signal.connect(listener)
        self.assertTrue(self.signal.is_connected(listener))

    def test_disconnect_stops_future_emits_from_reaching_listener(self) -> None:
        listener = RecordingListener()
        self.signal.connect(listener)
        self.signal.disconnect(listener)
        self.signal.emit()
        self.assertEqual(listener.calls, [])
        self.assertEqual(len(self.signal), 0)

    def test_disconnecting_an_unconnected_listener_is_a_silent_no_op(self) -> None:
        self.signal.disconnect(RecordingListener())

    def test_once_listener_fires_exactly_once(self) -> None:
        listener = RecordingListener()
        self.signal.connect(listener, once=True)
        self.signal.emit(1)
        self.signal.emit(2)
        self.assertEqual(listener.calls, [((1,), {})])
        self.assertEqual(len(self.signal), 0)

    def test_once_listener_is_disconnected_before_being_invoked(self) -> None:
        """A once listener is removed before it runs, so it can safely
        reconnect itself (or something else) from inside its own
        callback without immediately re-triggering itself."""
        calls = []

        def listener() -> None:
            calls.append("ran")
            self.assertFalse(self.signal.is_connected(listener))
            self.signal.connect(listener, once=True)

        self.signal.connect(listener, once=True)
        self.signal.emit()
        self.signal.emit()
        self.assertEqual(calls, ["ran", "ran"])

    def test_clear_disconnects_every_listener(self) -> None:
        self.signal.connect(RecordingListener())
        self.signal.connect(RecordingListener())
        self.signal.clear()
        self.assertEqual(len(self.signal), 0)

    def test_listener_disconnecting_itself_during_emit_does_not_break_dispatch(
        self,
    ) -> None:
        order = []

        def self_disconnecting() -> None:
            order.append("self")
            self.signal.disconnect(self_disconnecting)

        self.signal.connect(self_disconnecting)
        self.signal.connect(lambda: order.append("after"))
        self.signal.emit()
        self.assertEqual(order, ["self", "after"])
        self.assertEqual(len(self.signal), 1)

    def test_listener_disconnecting_a_not_yet_called_listener_skips_it(
        self,
    ) -> None:
        order = []

        def disconnects_victim() -> None:
            order.append("disconnector")
            self.signal.disconnect(victim)

        def victim() -> None:
            order.append("victim")

        self.signal.connect(disconnects_victim, priority=1)
        self.signal.connect(victim, priority=0)
        self.signal.emit()
        self.assertEqual(order, ["disconnector"])

    def test_listener_connecting_a_new_listener_during_emit_does_not_call_it_this_time(
        self,
    ) -> None:
        order = []
        late_listener = RecordingListener()

        def connector() -> None:
            order.append("connector")
            self.signal.connect(late_listener)

        self.signal.connect(connector)
        self.signal.emit()
        self.assertEqual(order, ["connector"])
        self.assertEqual(late_listener.calls, [])

        self.signal.emit()
        self.assertEqual(len(late_listener.calls), 1)

    def test_a_raising_listener_does_not_stop_the_rest_from_being_called(
        self,
    ) -> None:
        order = []

        def broken() -> None:
            order.append("broken")
            raise RuntimeError("boom")

        self.signal.connect(broken)
        self.signal.connect(lambda: order.append("after"))

        with self.assertLogs("gale.event", level="ERROR"):
            self.signal.emit()

        self.assertEqual(order, ["broken", "after"])

    def test_a_raising_listener_does_not_propagate_out_of_emit(self) -> None:
        def broken() -> None:
            raise RuntimeError("boom")

        self.signal.connect(broken)

        with self.assertLogs("gale.event", level="ERROR"):
            self.signal.emit()


class EventEmitterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.emitter = EventEmitter()

    def test_on_and_emit(self) -> None:
        listener = RecordingListener()
        self.emitter.on("score", listener)
        self.emitter.emit("score", 10)
        self.assertEqual(listener.calls, [((10,), {})])

    def test_events_are_independent_namespaces(self) -> None:
        score_listener = RecordingListener()
        death_listener = RecordingListener()
        self.emitter.on("score", score_listener)
        self.emitter.on("death", death_listener)
        self.emitter.emit("score", 10)
        self.assertEqual(score_listener.calls, [((10,), {})])
        self.assertEqual(death_listener.calls, [])

    def test_emit_on_event_name_with_no_listeners_does_not_raise(self) -> None:
        self.emitter.emit("nothing_listens_here")

    def test_off_before_any_on_is_a_silent_no_op(self) -> None:
        self.emitter.off("never_registered", RecordingListener())

    def test_off_removes_listener(self) -> None:
        listener = RecordingListener()
        self.emitter.on("score", listener)
        self.emitter.off("score", listener)
        self.emitter.emit("score", 10)
        self.assertEqual(listener.calls, [])

    def test_once_fires_only_once(self) -> None:
        listener = RecordingListener()
        self.emitter.once("score", listener)
        self.emitter.emit("score", 1)
        self.emitter.emit("score", 2)
        self.assertEqual(listener.calls, [((1,), {})])

    def test_is_on(self) -> None:
        listener = RecordingListener()
        self.assertFalse(self.emitter.is_on("score", listener))
        self.emitter.on("score", listener)
        self.assertTrue(self.emitter.is_on("score", listener))

    def test_has_listeners(self) -> None:
        listener = RecordingListener()
        self.assertFalse(self.emitter.has_listeners("score"))
        self.emitter.on("score", listener)
        self.assertTrue(self.emitter.has_listeners("score"))
        self.emitter.off("score", listener)
        self.assertFalse(self.emitter.has_listeners("score"))

    def test_clear_one_event_name_leaves_others_untouched(self) -> None:
        score_listener = RecordingListener()
        death_listener = RecordingListener()
        self.emitter.on("score", score_listener)
        self.emitter.on("death", death_listener)
        self.emitter.clear("score")
        self.emitter.emit("score", 10)
        self.emitter.emit("death")
        self.assertEqual(score_listener.calls, [])
        self.assertEqual(death_listener.calls, [((), {})])

    def test_clear_with_no_event_name_clears_everything(self) -> None:
        score_listener = RecordingListener()
        death_listener = RecordingListener()
        self.emitter.on("score", score_listener)
        self.emitter.on("death", death_listener)
        self.emitter.clear()
        self.emitter.emit("score", 10)
        self.emitter.emit("death")
        self.assertEqual(score_listener.calls, [])
        self.assertEqual(death_listener.calls, [])

    def test_signal_returns_the_same_instance_for_the_same_event_name(self) -> None:
        self.assertIs(self.emitter.signal("score"), self.emitter.signal("score"))

    def test_signal_reflects_listeners_registered_through_on(self) -> None:
        listener = RecordingListener()
        self.emitter.on("score", listener)
        self.assertTrue(self.emitter.signal("score").is_connected(listener))

    def test_combines_with_another_class_through_multiple_inheritance(self) -> None:
        class Entity:
            def __init__(self, name: str) -> None:
                self.name = name

        class Actor(EventEmitter, Entity):
            def __init__(self, name: str) -> None:
                super().__init__(name)

        listener = RecordingListener()
        actor = Actor("hero")
        actor.on("death", listener)

        self.assertEqual(actor.name, "hero")
        actor.emit("death")
        self.assertEqual(len(listener.calls), 1)

    def test_separate_emitters_do_not_share_listeners(self) -> None:
        other = EventEmitter()
        listener = RecordingListener()
        self.emitter.on("score", listener)
        other.emit("score", 10)
        self.assertEqual(listener.calls, [])


class EventBusTestCase(unittest.TestCase):
    def setUp(self) -> None:
        EventBus.clear()

    def tearDown(self) -> None:
        EventBus.clear()

    def test_on_and_emit_without_instantiation(self) -> None:
        listener = RecordingListener()
        EventBus.on("wolves_killed", listener)
        EventBus.emit("wolves_killed", 1)
        self.assertEqual(listener.calls, [((1,), {})])

    def test_state_is_shared_across_every_caller(self) -> None:
        listener_a = RecordingListener()
        listener_b = RecordingListener()
        EventBus.on("wolves_killed", listener_a)
        EventBus.on("wolves_killed", listener_b)

        EventBus.emit("wolves_killed", 1)

        self.assertEqual(listener_a.calls, [((1,), {})])
        self.assertEqual(listener_b.calls, [((1,), {})])

    def test_off(self) -> None:
        listener = RecordingListener()
        EventBus.on("wolves_killed", listener)
        EventBus.off("wolves_killed", listener)
        EventBus.emit("wolves_killed", 1)
        self.assertEqual(listener.calls, [])

    def test_once(self) -> None:
        listener = RecordingListener()
        EventBus.once("wolves_killed", listener)
        EventBus.emit("wolves_killed", 1)
        EventBus.emit("wolves_killed", 2)
        self.assertEqual(listener.calls, [((1,), {})])

    def test_is_on_and_has_listeners(self) -> None:
        listener = RecordingListener()
        self.assertFalse(EventBus.is_on("wolves_killed", listener))
        self.assertFalse(EventBus.has_listeners("wolves_killed"))
        EventBus.on("wolves_killed", listener)
        self.assertTrue(EventBus.is_on("wolves_killed", listener))
        self.assertTrue(EventBus.has_listeners("wolves_killed"))

    def test_clear_resets_every_event(self) -> None:
        listener = RecordingListener()
        EventBus.on("wolves_killed", listener)
        EventBus.clear()
        EventBus.emit("wolves_killed", 1)
        self.assertEqual(listener.calls, [])

    def test_signal_exposes_the_underlying_signal(self) -> None:
        listener = RecordingListener()
        EventBus.on("wolves_killed", listener)
        self.assertTrue(EventBus.signal("wolves_killed").is_connected(listener))


if __name__ == "__main__":
    unittest.main()
