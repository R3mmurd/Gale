import unittest

from gale.memoize import Memo, Memoized


class CountingFunction:
    """A callable that records every call it receives and returns a
    fresh, distinguishable value each time, so a test can tell a cache
    hit (same returned object) from a recompute (a new one)."""

    def __init__(self) -> None:
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return object()


class MemoizedForeverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.function = CountingFunction()
        self.memoized = Memoized(self.function)

    def test_calls_the_wrapped_function_on_first_call(self) -> None:
        self.memoized(1)
        self.assertEqual(len(self.function.calls), 1)

    def test_repeated_calls_with_the_same_args_reuse_the_cached_value(self) -> None:
        first = self.memoized(1, 2)
        second = self.memoized(1, 2)
        self.assertIs(first, second)
        self.assertEqual(len(self.function.calls), 1)

    def test_different_args_are_cached_separately(self) -> None:
        self.memoized(1)
        self.memoized(2)
        self.assertEqual(len(self.function.calls), 2)

    def test_kwargs_participate_in_the_cache_key(self) -> None:
        self.memoized(x=1)
        self.memoized(x=2)
        self.assertEqual(len(self.function.calls), 2)

    def test_kwargs_given_in_a_different_order_hit_the_same_cache_entry(self) -> None:
        first = self.memoized(a=1, b=2)
        second = self.memoized(b=2, a=1)
        self.assertIs(first, second)
        self.assertEqual(len(self.function.calls), 1)

    def test_update_never_expires_a_forever_cache(self) -> None:
        first = self.memoized(1)
        self.memoized.update(1_000_000.0)
        second = self.memoized(1)
        self.assertIs(first, second)
        self.assertEqual(len(self.function.calls), 1)

    def test_len_reflects_the_number_of_distinct_cached_calls(self) -> None:
        self.assertEqual(len(self.memoized), 0)
        self.memoized(1)
        self.memoized(2)
        self.assertEqual(len(self.memoized), 2)

    def test_clear_forces_every_entry_to_recompute(self) -> None:
        self.memoized(1)
        self.memoized(2)
        self.memoized.clear()
        self.assertEqual(len(self.memoized), 0)
        self.memoized(1)
        self.memoized(2)
        self.assertEqual(len(self.function.calls), 4)

    def test_invalidate_forces_only_the_matching_entry_to_recompute(self) -> None:
        self.memoized(1)
        self.memoized(2)
        self.memoized.invalidate(1)
        self.assertEqual(len(self.memoized), 1)
        self.memoized(1)
        self.memoized(2)
        self.assertEqual(len(self.function.calls), 3)

    def test_invalidating_an_uncached_call_is_a_silent_no_op(self) -> None:
        self.memoized.invalidate("never called")


class MemoizedTTLTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.function = CountingFunction()
        self.memoized = Memoized(self.function, ttl=2.0)

    def test_negative_ttl_raises(self) -> None:
        with self.assertRaises(ValueError):
            Memoized(self.function, ttl=-1.0)

    def test_reuses_the_cached_value_while_within_ttl(self) -> None:
        first = self.memoized(1)
        self.memoized.update(1.0)
        second = self.memoized(1)
        self.assertIs(first, second)
        self.assertEqual(len(self.function.calls), 1)

    def test_recomputes_once_accumulated_age_exceeds_ttl(self) -> None:
        first = self.memoized(1)
        self.memoized.update(1.0)
        self.memoized.update(1.5)
        second = self.memoized(1)
        self.assertIsNot(first, second)
        self.assertEqual(len(self.function.calls), 2)

    def test_entry_is_still_valid_exactly_at_the_ttl_boundary(self) -> None:
        first = self.memoized(1)
        self.memoized.update(2.0)
        second = self.memoized(1)
        self.assertIs(first, second)
        self.assertEqual(len(self.function.calls), 1)

    def test_a_recompute_resets_that_entrys_age_but_a_cache_hit_does_not(
        self,
    ) -> None:
        # ttl is an absolute window from the last recompute, not a
        # sliding one: a cache hit doesn't push expiry back out.
        self.memoized(1)
        self.memoized.update(1.5)
        self.memoized(1)  # still within ttl -- a hit, doesn't reset age
        self.memoized.update(1.0)  # total age 2.5 > ttl 2.0: expired
        self.memoized(1)  # recomputes, resetting age to 0
        self.memoized.update(1.5)  # only 1.5s since that recompute
        self.memoized(1)  # still within ttl -- another hit
        self.assertEqual(len(self.function.calls), 2)

    def test_different_arguments_expire_independently(self) -> None:
        self.memoized(1)
        self.memoized.update(1.5)
        self.memoized(2)
        self.memoized.update(1.0)
        # "1" is now 2.5s old (expired), "2" is 1.0s old (still fresh).
        self.memoized(1)
        self.memoized(2)
        self.assertEqual(len(self.function.calls), 3)

    def test_expired_entries_are_pruned_from_the_internal_cache(self) -> None:
        self.memoized(1)
        self.assertEqual(len(self.memoized), 1)
        self.memoized.update(3.0)
        self.assertEqual(len(self.memoized), 0)


class MemoizedFrameScopedTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.function = CountingFunction()
        self.memoized = Memoized(self.function, ttl=0.0)

    def test_repeated_calls_within_the_same_frame_share_one_computation(
        self,
    ) -> None:
        first = self.memoized(1)
        second = self.memoized(1)
        third = self.memoized(1)
        self.assertIs(first, second)
        self.assertIs(second, third)
        self.assertEqual(len(self.function.calls), 1)

    def test_any_update_at_all_invalidates_it_for_the_next_call(self) -> None:
        first = self.memoized(1)
        self.memoized.update(1 / 240)  # a tiny dt is still a new frame
        second = self.memoized(1)
        self.assertIsNot(first, second)
        self.assertEqual(len(self.function.calls), 2)


class MemoizedMethodTestCase(unittest.TestCase):
    def test_caches_per_instance(self) -> None:
        calls = []

        class Agent:
            def __init__(self, name: str) -> None:
                self.name = name

            @Memoized
            def expensive_lookup(self):
                calls.append(self.name)
                return self.name

        hero = Agent("hero")
        villain = Agent("villain")

        self.assertEqual(hero.expensive_lookup(), "hero")
        self.assertEqual(hero.expensive_lookup(), "hero")
        self.assertEqual(villain.expensive_lookup(), "villain")

        self.assertEqual(calls, ["hero", "villain"])

    def test_accessing_it_through_the_class_returns_the_memoized_itself(self) -> None:
        class Agent:
            @Memoized
            def expensive_lookup(self):
                return "value"

        self.assertIsInstance(Agent.expensive_lookup, Memoized)


class MemoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        Memo.clear()

    def tearDown(self) -> None:
        Memo.clear()

    def test_memoize_used_as_a_bare_decorator_wraps_the_function(self) -> None:
        calls = []

        @Memo.memoize
        def compute(x):
            calls.append(x)
            return x * 2

        self.assertEqual(compute(3), 6)
        self.assertEqual(compute(3), 6)
        self.assertEqual(calls, [3])
        self.assertIsInstance(compute, Memoized)

    def test_memoize_used_as_a_decorator_factory_accepts_ttl(self) -> None:
        calls = []

        @Memo.memoize(ttl=1.0)
        def compute(x):
            calls.append(x)
            return x * 2

        compute(3)
        Memo.update(0.5)
        compute(3)
        self.assertEqual(calls, [3])

        Memo.update(0.6)
        compute(3)
        self.assertEqual(calls, [3, 3])

    def test_update_ages_every_registered_memoized(self) -> None:
        calls_a = []
        calls_b = []

        @Memo.memoize(ttl=1.0)
        def a(x):
            calls_a.append(x)
            return x

        @Memo.memoize(ttl=1.0)
        def b(x):
            calls_b.append(x)
            return x

        a(1)
        b(1)
        Memo.update(1.5)
        a(1)
        b(1)
        self.assertEqual(calls_a, [1, 1])
        self.assertEqual(calls_b, [1, 1])

    def test_pause_stops_every_registered_memoized_from_aging(self) -> None:
        calls = []

        @Memo.memoize(ttl=1.0)
        def compute(x):
            calls.append(x)
            return x

        compute(1)
        Memo.pause()
        Memo.update(5.0)
        compute(1)
        self.assertEqual(calls, [1])

    def test_resume_continues_aging(self) -> None:
        calls = []

        @Memo.memoize(ttl=1.0)
        def compute(x):
            calls.append(x)
            return x

        compute(1)
        Memo.pause()
        Memo.update(5.0)
        Memo.resume()
        Memo.update(1.5)
        compute(1)
        self.assertEqual(calls, [1, 1])

    def test_clear_unregisters_every_memoized_and_unpauses(self) -> None:
        Memo.memoize(lambda x: x)
        Memo.pause()
        Memo.clear()
        self.assertEqual(len(Memo.items), 0)
        self.assertFalse(Memo.paused)


if __name__ == "__main__":
    unittest.main()
