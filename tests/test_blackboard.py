import unittest

from gale.ai.blackboard import Blackboard


class BlackboardTestCase(unittest.TestCase):
    def test_get_returns_default_when_unset(self) -> None:
        blackboard = Blackboard()
        self.assertIsNone(blackboard.get("missing"))
        self.assertEqual(blackboard.get("missing", "fallback"), "fallback")

    def test_set_and_get(self) -> None:
        blackboard = Blackboard()
        blackboard.set("score", 10)
        self.assertEqual(blackboard.get("score"), 10)

    def test_initial_values(self) -> None:
        blackboard = Blackboard({"is_alerted": False})
        self.assertFalse(blackboard.get("is_alerted"))

    def test_has_and_contains(self) -> None:
        blackboard = Blackboard()
        self.assertFalse(blackboard.has("key"))
        self.assertNotIn("key", blackboard)
        blackboard.set("key", 1)
        self.assertTrue(blackboard.has("key"))
        self.assertIn("key", blackboard)

    def test_erase(self) -> None:
        blackboard = Blackboard({"key": 1})
        blackboard.erase("key")
        self.assertFalse(blackboard.has("key"))
        # Erasing an already-absent key does nothing (no exception).
        blackboard.erase("key")

    def test_clear_removes_every_key(self) -> None:
        blackboard = Blackboard({"a": 1, "b": 2})
        blackboard.clear()
        self.assertFalse(blackboard.has("a"))
        self.assertFalse(blackboard.has("b"))

    def test_observer_is_called_on_change(self) -> None:
        blackboard = Blackboard()
        calls = []
        blackboard.observe("hp", lambda key, old, new: calls.append((key, old, new)))
        blackboard.set("hp", 100)
        blackboard.set("hp", 80)
        self.assertEqual(calls, [("hp", None, 100), ("hp", 100, 80)])

    def test_observer_is_not_called_when_value_does_not_change(self) -> None:
        blackboard = Blackboard({"hp": 100})
        calls = []
        blackboard.observe("hp", lambda key, old, new: calls.append((key, old, new)))
        blackboard.set("hp", 100)
        self.assertEqual(calls, [])

    def test_observer_only_fires_for_its_own_key(self) -> None:
        blackboard = Blackboard()
        calls = []
        blackboard.observe("hp", lambda key, old, new: calls.append(key))
        blackboard.set("mana", 50)
        self.assertEqual(calls, [])

    def test_multiple_observers_for_the_same_key(self) -> None:
        blackboard = Blackboard()
        calls = []
        blackboard.observe("hp", lambda key, old, new: calls.append("a"))
        blackboard.observe("hp", lambda key, old, new: calls.append("b"))
        blackboard.set("hp", 100)
        self.assertEqual(calls, ["a", "b"])

    def test_stop_observing(self) -> None:
        blackboard = Blackboard()
        calls = []
        observer = lambda key, old, new: calls.append(1)
        blackboard.observe("hp", observer)
        blackboard.stop_observing("hp", observer)
        blackboard.set("hp", 100)
        self.assertEqual(calls, [])

    def test_stop_observing_unknown_observer_raises(self) -> None:
        blackboard = Blackboard()
        blackboard.observe("hp", lambda key, old, new: None)
        with self.assertRaises(ValueError):
            blackboard.stop_observing("hp", lambda key, old, new: None)
