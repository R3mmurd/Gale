import unittest

from gale.ai.behavior_tree import (
    Action,
    BehaviorTree,
    Condition,
    Cooldown,
    Inverter,
    Parallel,
    Repeater,
    Selector,
    Sequence,
    Status,
    UntilFailure,
    UntilSuccess,
)


def always(status: Status):
    return lambda agent, dt: status


class SequenceTestCase(unittest.TestCase):
    def test_succeeds_when_all_children_succeed(self) -> None:
        node = Sequence(
            [Action(always(Status.SUCCESS)), Action(always(Status.SUCCESS))]
        )
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)

    def test_fails_as_soon_as_a_child_fails(self) -> None:
        calls = []
        node = Sequence(
            [
                Action(always(Status.SUCCESS)),
                Action(always(Status.FAILURE)),
                Action(lambda agent, dt: calls.append(1) or Status.SUCCESS),
            ]
        )
        self.assertEqual(node.tick(None, 0), Status.FAILURE)
        self.assertEqual(calls, [])

    def test_resumes_running_child_on_next_tick(self) -> None:
        calls = []

        def counting_action(agent, dt):
            calls.append(1)
            return Status.RUNNING if len(calls) < 2 else Status.SUCCESS

        node = Sequence([Action(counting_action)])
        self.assertEqual(node.tick(None, 0), Status.RUNNING)
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)
        self.assertEqual(len(calls), 2)


class SelectorTestCase(unittest.TestCase):
    def test_succeeds_as_soon_as_a_child_succeeds(self) -> None:
        calls = []
        node = Selector(
            [
                Action(always(Status.FAILURE)),
                Action(lambda agent, dt: calls.append(1) or Status.SUCCESS),
                Action(lambda agent, dt: calls.append(2) or Status.SUCCESS),
            ]
        )
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)
        self.assertEqual(calls, [1])

    def test_fails_when_all_children_fail(self) -> None:
        node = Selector(
            [Action(always(Status.FAILURE)), Action(always(Status.FAILURE))]
        )
        self.assertEqual(node.tick(None, 0), Status.FAILURE)


class ParallelTestCase(unittest.TestCase):
    def test_succeeds_when_success_threshold_is_met(self) -> None:
        node = Parallel(
            [Action(always(Status.SUCCESS)), Action(always(Status.RUNNING))],
            success_threshold=1,
        )
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)

    def test_fails_when_failure_threshold_is_met(self) -> None:
        node = Parallel(
            [Action(always(Status.FAILURE)), Action(always(Status.RUNNING))],
        )
        self.assertEqual(node.tick(None, 0), Status.FAILURE)

    def test_keeps_running_otherwise(self) -> None:
        node = Parallel(
            [Action(always(Status.RUNNING)), Action(always(Status.RUNNING))]
        )
        self.assertEqual(node.tick(None, 0), Status.RUNNING)

    def test_does_not_retick_a_child_that_already_finished(self) -> None:
        calls = []

        def fire_once(agent, dt):
            calls.append(1)
            return Status.SUCCESS

        node = Parallel(
            [Action(fire_once), Action(always(Status.RUNNING))], success_threshold=2
        )
        node.tick(None, 0)
        node.tick(None, 0)
        node.tick(None, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(node.tick(None, 0), Status.RUNNING)

    def test_relatches_children_after_it_resets(self) -> None:
        calls = []

        def fire_once(agent, dt):
            calls.append(1)
            return Status.SUCCESS

        node = Parallel([Action(fire_once), Action(always(Status.SUCCESS))])
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)
        self.assertEqual(len(calls), 2)


class DecoratorTestCase(unittest.TestCase):
    def test_inverter(self) -> None:
        self.assertEqual(
            Inverter(Action(always(Status.SUCCESS))).tick(None, 0), Status.FAILURE
        )
        self.assertEqual(
            Inverter(Action(always(Status.FAILURE))).tick(None, 0), Status.SUCCESS
        )
        self.assertEqual(
            Inverter(Action(always(Status.RUNNING))).tick(None, 0), Status.RUNNING
        )

    def test_repeater_with_fixed_times(self) -> None:
        node = Repeater(Action(always(Status.SUCCESS)), times=3)
        self.assertEqual(node.tick(None, 0), Status.RUNNING)
        self.assertEqual(node.tick(None, 0), Status.RUNNING)
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)

    def test_until_success(self) -> None:
        calls = []

        def action(agent, dt):
            calls.append(1)
            return Status.SUCCESS if len(calls) == 3 else Status.FAILURE

        node = UntilSuccess(Action(action))
        self.assertEqual(node.tick(None, 0), Status.RUNNING)
        self.assertEqual(node.tick(None, 0), Status.RUNNING)
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)

    def test_until_failure(self) -> None:
        node = UntilFailure(Action(always(Status.SUCCESS)))
        self.assertEqual(node.tick(None, 0), Status.RUNNING)

    def test_cooldown_blocks_child_until_duration_elapses(self) -> None:
        node = Cooldown(Action(always(Status.SUCCESS)), duration=1)
        self.assertEqual(node.tick(None, 0.5), Status.SUCCESS)
        self.assertEqual(node.tick(None, 0.1), Status.FAILURE)
        self.assertEqual(node.tick(None, 1), Status.FAILURE)
        self.assertEqual(node.tick(None, 0), Status.SUCCESS)


class ConditionTestCase(unittest.TestCase):
    def test_condition(self) -> None:
        self.assertEqual(Condition(lambda agent: True).tick(None, 0), Status.SUCCESS)
        self.assertEqual(Condition(lambda agent: False).tick(None, 0), Status.FAILURE)


class BehaviorTreeTestCase(unittest.TestCase):
    def test_tick_delegates_to_root(self) -> None:
        tree = BehaviorTree(Action(always(Status.SUCCESS)))
        self.assertEqual(tree.tick(None, 0), Status.SUCCESS)
