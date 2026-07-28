import unittest

from gale.ai.goap import GoapAction, plan


class GoapPlanTestCase(unittest.TestCase):
    def test_empty_plan_when_goal_already_satisfied(self) -> None:
        result = plan({"has_wood": True}, {"has_wood": True}, [])
        self.assertEqual(result, [])

    def test_finds_a_single_action_plan(self) -> None:
        chop_wood = GoapAction(
            "chop_wood", preconditions={"has_axe": True}, effects={"has_wood": True}
        )
        result = plan(
            {"has_axe": True, "has_wood": False}, {"has_wood": True}, [chop_wood]
        )
        self.assertEqual(result, [chop_wood])

    def test_finds_a_multi_step_plan(self) -> None:
        get_axe = GoapAction("get_axe", preconditions={}, effects={"has_axe": True})
        chop_wood = GoapAction(
            "chop_wood", preconditions={"has_axe": True}, effects={"has_wood": True}
        )
        result = plan({"has_axe": False}, {"has_wood": True}, [get_axe, chop_wood])
        self.assertEqual(result, [get_axe, chop_wood])

    def test_prefers_the_cheaper_plan(self) -> None:
        cheap_path = GoapAction(
            "cheap", preconditions={}, effects={"has_wood": True}, cost=1.0
        )
        expensive_step_1 = GoapAction(
            "expensive_step_1",
            preconditions={},
            effects={"in_progress": True},
            cost=5.0,
        )
        expensive_step_2 = GoapAction(
            "expensive_step_2",
            preconditions={"in_progress": True},
            effects={"has_wood": True},
            cost=5.0,
        )
        result = plan(
            {},
            {"has_wood": True},
            [cheap_path, expensive_step_1, expensive_step_2],
        )
        self.assertEqual(result, [cheap_path])

    def test_none_when_goal_is_unreachable(self) -> None:
        result = plan({}, {"has_wood": True}, [])
        self.assertIsNone(result)

    def test_action_is_only_applicable_when_preconditions_hold(self) -> None:
        chop_wood = GoapAction(
            "chop_wood", preconditions={"has_axe": True}, effects={"has_wood": True}
        )
        self.assertFalse(chop_wood.is_applicable({"has_axe": False}))
        self.assertTrue(chop_wood.is_applicable({"has_axe": True}))

    def test_apply_does_not_mutate_the_input_state(self) -> None:
        chop_wood = GoapAction(
            "chop_wood", preconditions={}, effects={"has_wood": True}
        )
        state = {"has_wood": False}
        new_state = chop_wood.apply(state)
        self.assertEqual(state, {"has_wood": False})
        self.assertEqual(new_state, {"has_wood": True})


if __name__ == "__main__":
    unittest.main()
