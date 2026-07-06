`← Back to the main README <../../README.rst>`_

gale.ai
========

``gale.ai`` provides small, composable pieces to build autonomous
characters (vehicles, people, animals, or any kind of creature): a
``Kinematic`` body, steering behaviors, a behavior tree, a decision
tree, and generic graphs with search algorithms (for pathfinding and
beyond). They are combined through the ``Agent`` class, but you can also
use each piece on its own.

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

Graphs
------

``gale.ai.graph`` provides a generic ``Graph`` (nodes connected by
weighted edges, directed or not), plus three specializations built on
top of it:

- ``NavGraph``: nodes are 2D positions (waypoints); an edge's weight
  defaults to the euclidean distance between the positions it connects.
- ``DependencyGraph``: a directed graph of prerequisite/build-order
  relationships (skill trees, quest chains, build pipelines), with
  ``topological_sort`` and ``has_cycle``.
- ``StateGraph``: a directed graph of a state space (every reachable
  configuration of a puzzle and the moves between them). Since the full
  state space is normally too large to write out by hand,
  ``StateGraph.expand`` builds it automatically from a starting state
  and a function that yields the valid transitions out of any state.

.. code-block:: python

   from gale.ai.graph import DependencyGraph, NavGraph

   # NavGraph: pathfinding waypoints, weights default to distance.
   nav_graph = NavGraph()
   nav_graph.add_edge((0, 0), (100, 0))
   nav_graph.add_edge((100, 0), (100, 100))
   nav_graph.add_edge((0, 0), (0, 100), weight=1000)  # a slow, hazardous shortcut

   # DependencyGraph: a tiny skill tree.
   skills = DependencyGraph()
   skills.add_dependency("fireball", depends_on="magic_missile")
   skills.add_dependency("meteor", depends_on="fireball")
   build_order = skills.topological_sort()  # e.g. ["magic_missile", "fireball", "meteor"]

Search algorithms
------------------

``gale.ai.search`` provides ``depth_first_search``, ``breadth_first_search``,
``dijkstra``, and ``a_star``. All four share the same signature,
``search(start, goal, graph_or_neighbors_fn, ...)``, and return the list
of nodes from ``start`` to ``goal`` (both included), or ``None`` if
``goal`` is unreachable. ``graph_or_neighbors_fn`` can be a ``Graph`` (or
any of its subclasses above) or a plain callable
``node -> iterable of (neighbor, weight)`` pairs, so these functions work
just as well over an implicit graph you never materialize.

.. code-block:: python

   import math

   from gale.ai.graph import NavGraph
   from gale.ai.search import a_star, dijkstra, path_cost

   nav_graph = NavGraph()
   nav_graph.add_edge((0, 0), (100, 0))
   nav_graph.add_edge((100, 0), (100, 100))

   def heuristic(node, goal):
       return math.hypot(goal[0] - node[0], goal[1] - node[1])

   path = a_star((0, 0), (100, 100), nav_graph, heuristic)
   total_distance = path_cost(nav_graph, path)

A path found this way is a sequence of waypoints, which pairs naturally
with the steering behaviors above — for instance, ``Seek`` (or
``Arrive`` for the last waypoint) towards each point in turn, advancing
to the next one once the character gets close enough.

``depth_first_search`` and ``breadth_first_search`` ignore weights (they
only care about the number of edges), while ``dijkstra`` and ``a_star``
find the cheapest path by total weight — ``a_star`` additionally takes a
``heuristic(node, goal)`` callable to focus the search towards the goal
instead of expanding outward evenly, which is faster as long as the
heuristic never overestimates the real remaining cost.

These functions aren't limited to spatial pathfinding — any state-space
problem works too. Here they solve the Towers of Hanoi optimally by
searching a ``StateGraph`` built from the puzzle's legal moves:

.. code-block:: python

   from gale.ai.graph import StateGraph
   from gale.ai.search import breadth_first_search


   def hanoi_successors(state):
       # state is a tuple of 3 tuples (one per peg) listing disk sizes
       # from bottom to top.
       for source in range(3):
           if not state[source]:
               continue

           disk = state[source][-1]

           for target in range(3):
               if target == source:
                   continue

               if state[target] and state[target][-1] < disk:
                   continue

               next_state = list(state)
               next_state[source] = state[source][:-1]
               next_state[target] = state[target] + (disk,)
               yield tuple(next_state), 1


   n = 3
   start = (tuple(range(n, 0, -1)), (), ())
   goal = ((), (), tuple(range(n, 0, -1)))

   graph = StateGraph.expand(start, hanoi_successors)
   solution = breadth_first_search(start, goal, graph)
   print(len(solution) - 1)  # 7 moves: optimal for 3 disks (2**n - 1)
