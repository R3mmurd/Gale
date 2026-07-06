`← Back to the main README <../../README.rst>`_

gale.ai
========

``gale.ai`` provides small, composable pieces to build autonomous
characters (vehicles, people, animals, or any kind of creature): a
``Kinematic`` body, steering behaviors, a behavior tree, and a decision
tree. They are combined through the ``Agent`` class, but you can also use
each piece on its own.

Steering only
-------------

A wandering agent driven only by a steering behavior:

.. code-block:: python

   from gale.ai.agent import Agent
   from gale.ai.steering import Wander

   agent = Agent(x=100, y=100, max_speed=120)
   agent.set_steering_behavior(Wander(agent.kinematic))

   # In your game loop:
   agent.update(dt)

Other steering behaviors (``Seek``, ``Flee``, ``Arrive``, ``Pursue``,
``Evade``, ``Separation``, ``ObstacleAvoidance``, ...) work the same way:
build one with the character's ``Kinematic`` and whatever target it needs,
then pass it to ``set_steering_behavior``. Use ``BlendedSteering`` or
``PrioritySteering`` to combine several of them.

Behavior tree
-------------

An agent whose steering is decided by a behavior tree, so it chases a
player when close and wanders otherwise:

.. code-block:: python

   from gale.ai.agent import Agent
   from gale.ai.behavior_tree import Action, BehaviorTree, Condition, Selector, Sequence, Status
   from gale.ai.steering import Kinematic, Pursue, Wander

   player = Kinematic()
   wander = None


   def close_to_player(agent) -> bool:
       return (player.position - agent.kinematic.position).length() < 150


   def chase(agent, dt) -> Status:
       agent.set_steering_behavior(Pursue(agent.kinematic, player))
       return Status.RUNNING


   def patrol(agent, dt) -> Status:
       agent.set_steering_behavior(wander)
       return Status.RUNNING


   agent = Agent(x=0, y=0, max_speed=120)
   wander = Wander(agent.kinematic)
   agent.set_brain(
       BehaviorTree(
           Selector(
               [
                   Sequence([Condition(close_to_player), Action(chase)]),
                   Action(patrol),
               ]
           )
       )
   )

   # In your game loop:
   agent.update(dt)

Decision tree
-------------

The same decision could be expressed with a ``DecisionTree`` instead of a
behavior tree:

.. code-block:: python

   from gale.ai.decision_tree import ActionNode, DecisionNode, DecisionTree

   agent.set_brain(
       DecisionTree(
           DecisionNode(
               test=close_to_player,
               true_branch=ActionNode(lambda agent: chase(agent, 0)),
               false_branch=ActionNode(lambda agent: patrol(agent, 0)),
           )
       )
   )

Using it with Factory
----------------------

Since ``Agent`` accepts ``x`` and ``y`` as its first two constructor
arguments, it plugs directly into ``gale.factory.Factory``:

.. code-block:: python

   from gale.ai.agent import Agent
   from gale.factory import Factory

   agent_factory = Factory(Agent)
   agent = agent_factory.create(50, 50, {"max_speed": 150})
