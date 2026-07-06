import unittest

from gale.ai.agent import Agent
from gale.ai.behavior_tree import Action, BehaviorTree, Status
from gale.ai.decision_tree import ActionNode, DecisionTree
from gale.ai.steering import Kinematic, Seek
from gale.factory import Factory


class AgentMovementTestCase(unittest.TestCase):
    def test_agent_moves_towards_target_with_seek(self) -> None:
        agent = Agent(x=0, y=0, max_speed=100, max_acceleration=100)
        target = Kinematic(100, 0)
        agent.set_steering_behavior(Seek(agent.kinematic, target))

        initial_distance = (target.position - agent.position).length()
        for _ in range(10):
            agent.update(0.1)

        self.assertLess((target.position - agent.position).length(), initial_distance)

    def test_agent_without_steering_behavior_does_not_accelerate(self) -> None:
        agent = Agent(x=0, y=0)
        agent.update(0.1)
        self.assertEqual(agent.velocity.length(), 0)
        self.assertEqual(agent.position.x, 0)

    def test_agent_faces_movement_direction(self) -> None:
        agent = Agent(x=0, y=0, orientation=0, max_speed=100, max_acceleration=100)
        target = Kinematic(0, 100)
        agent.set_steering_behavior(Seek(agent.kinematic, target))
        for _ in range(5):
            agent.update(0.1)
        self.assertGreater(agent.orientation, 0)

    def test_agent_is_compatible_with_factory(self) -> None:
        factory = Factory(Agent)
        agent = factory.create(5, 8, {"max_speed": 50})
        self.assertIsInstance(agent, Agent)
        self.assertEqual(agent.position.x, 5)
        self.assertEqual(agent.position.y, 8)
        self.assertEqual(agent.kinematic.max_speed, 50)


class AgentBrainTestCase(unittest.TestCase):
    def test_agent_runs_behavior_tree_brain(self) -> None:
        calls = []
        tree = BehaviorTree(
            Action(lambda agent, dt: calls.append(agent) or Status.SUCCESS)
        )
        agent = Agent()
        agent.set_brain(tree)
        agent.update(0.1)
        self.assertEqual(calls, [agent])

    def test_agent_runs_decision_tree_brain(self) -> None:
        calls = []
        tree = DecisionTree(ActionNode(lambda agent: calls.append(agent)))
        agent = Agent()
        agent.set_brain(tree)
        agent.update(0.1)
        self.assertEqual(calls, [agent])

    def test_agent_rejects_invalid_brain(self) -> None:
        agent = Agent()
        agent.set_brain(object())
        with self.assertRaises(TypeError):
            agent.update(0.1)
