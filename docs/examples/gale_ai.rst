`← Back to the main README <../../README.rst>`_

gale.ai
========

``gale.ai`` provides small, composable pieces to build autonomous
characters (vehicles, people, animals, or any kind of creature): a
``Kinematic`` body, steering behaviors, a behavior tree, a decision
tree, a shared Blackboard, and generic graphs with search algorithms
(for pathfinding and beyond). They are combined through the ``Agent``
class, but you can also use each piece on its own.

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

Other steering behaviors (``Seek``, ``Flee``, ``Arrive``, ``Align``,
``Face``, ``LookWhereYoureGoing``, ``VelocityMatch``, ``Pursue``,
``Evade``, ``Separation``, ``CollisionAvoidance``, ``ObstacleAvoidance``,
``WallAvoidance``, ``PathFollow``, ...) work the same way: build one
with the character's ``Kinematic`` and whatever target it needs, then
pass it to ``set_steering_behavior``.

Combining steering
-------------------

Several behaviors can drive the same character at once:

- ``BlendedSteering``: sums every behavior's output, weighted, then
  clamps the result to the character's limits. Good for behaviors
  meant to blend smoothly, e.g. a cohesion ``Seek`` towards a flock's
  center plus ``Separation`` plus ``VelocityMatch`` (alignment) — the
  classic three boids rules, none of which needs to fully override the
  others.
- ``PrioritySteering``: tries each group (itself blended) in order and
  returns the first one that produces a meaningful output. Good for an
  urgent behavior that should override lower-priority ones outright,
  e.g. ``WallAvoidance`` first, a movement blend second.
- ``CooperativeArbitration``: evaluates *every* group instead of
  stopping at the first meaningful one, and returns whichever scores
  highest (by squared magnitude, or a custom ``score`` callable) — for
  when the "right" behavior isn't simply the highest-priority one that
  happens to fire, but whichever actually addresses the situation the
  most.

.. code-block:: python

   from gale.ai.steering import BlendedSteering, PrioritySteering, Seek, Separation, VelocityMatch, WallAvoidance

   flock_steering = BlendedSteering(
       character,
       [
           (Seek(character, flock_center), 0.5),
           (Separation(character, flock_mates), 1.0),
           (VelocityMatch(character, flock_average_velocity), 0.5),
       ],
   )

   guard_steering = PrioritySteering(
       character,
       [
           [(WallAvoidance(character, walls), 1.0)],
           [(Seek(character, patrol_point), 1.0)],
       ],
   )

Motor control
-------------

- ``OutputFilter``: wraps another behavior and smooths its output over
  time (exponential smoothing), so a noisy underlying behavior doesn't
  produce jittery, frame-to-frame-inconsistent motion.
- ``CapabilityFilter``: wraps another behavior and reclamps its output
  to a set of capabilities that may be more restrictive than the
  character's own ``Kinematic`` limits — useful to reuse the same
  targeting logic across characters with different physical
  capabilities (a fast scout vs. a slow, heavy tank).

.. code-block:: python

   from gale.ai.steering import CapabilityFilter, OutputFilter, Pursue

   smoothed = OutputFilter(Pursue(character, target), smoothing=0.2)
   heavy_tank_turret = CapabilityFilter(
       Pursue(character, target), max_acceleration=50, max_angular_acceleration=0.5
   )

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

Blackboard
----------

Every ``Agent`` owns a ``Blackboard``: a shared key-value store, the
same role a Blackboard plays alongside Behavior Trees in engines such
as Unreal Engine. It lets a behavior tree's (or decision tree's) nodes,
an agent's steering behaviors, and any external system (a perception
system, a quest system, another agent) read and write data about the
agent without needing direct references to one another — they only
need to agree on a key.

Continuing the chase-or-patrol example above, a perception system
could set ``"has_target"`` whenever it spots the player, and the
behavior tree would just check the blackboard instead of computing the
distance to the player itself:

.. code-block:: python

   from gale.ai.behavior_tree import Action, BehaviorTree, Condition, Selector, Status


   def has_target(agent) -> bool:
       return agent.blackboard.get("has_target", False)


   def chase(agent, dt) -> Status:
       agent.set_steering_behavior(Pursue(agent.kinematic, player))
       return Status.RUNNING


   agent.set_brain(
       BehaviorTree(Selector([Sequence([Condition(has_target), Action(chase)]), Action(patrol)]))
   )

   # Somewhere in a perception system, unrelated to the behavior tree:
   agent.blackboard.set("has_target", True)

You can also react immediately to a value changing, instead of waiting
for the next tick to notice it, by registering an observer:

.. code-block:: python

   def on_target_spotted(key, old_value, new_value):
       if new_value:
           print("Spotted!")

   agent.blackboard.observe("has_target", on_target_spotted)

Pass a ``Blackboard`` explicitly to ``Agent`` (instead of letting it
create its own) to share one across several agents, for instance so an
entire guard squad reacts together to ``"team_alerted"``:

.. code-block:: python

   from gale.ai.blackboard import Blackboard

   squad_blackboard = Blackboard({"team_alerted": False})
   guard1 = Agent(x=0, y=0, blackboard=squad_blackboard)
   guard2 = Agent(x=50, y=0, blackboard=squad_blackboard)

   guard1.blackboard.set("team_alerted", True)
   guard2.blackboard.get("team_alerted")  # True: same blackboard instance

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
  Each transition can optionally carry an action label (for instance, a
  description of the move that produced it), recoverable afterwards
  with ``get_action``/``actions_for_path`` — the states along a path
  don't always make it obvious what to actually do to go from one to
  the next.

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
       # from bottom to top. Each transition is labeled with the
       # (source_peg, target_peg) move that produces it.
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
               yield tuple(next_state), 1, (source, target)


   n = 3
   start = (tuple(range(n, 0, -1)), (), ())
   goal = ((), (), tuple(range(n, 0, -1)))

   graph = StateGraph.expand(start, hanoi_successors)
   solution = breadth_first_search(start, goal, graph)
   print(len(solution) - 1)  # 7 moves: optimal for 3 disks (2**n - 1)

   # The states alone don't spell out what to actually do; recover the
   # (source_peg, target_peg) move behind each step of the solution:
   moves = graph.actions_for_path(solution)

Pathfinding: hierarchical, interruptible, and open-goal
---------------------------------------------------------

``gale.ai.pathfinding`` builds on ``gale.ai.search`` for larger or
trickier pathfinding needs:

- ``a_star_to_predicate``: an "open goal" search — instead of one
  fixed goal node, any node satisfying a predicate is acceptable (e.g.
  the nearest node tagged as cover, whichever one that turns out to
  be).
- ``incremental_a_star``: a generator version of ``a_star`` that
  yields ``None`` after every node expansion instead of running to
  completion in one call, so it can be advanced a limited number of
  steps per frame instead of spiking the frame that requested it.
  ``PathfindingRequest`` wraps one search, and ``PlannerPool`` manages
  several concurrent ones, sharing a fixed per-update iteration budget
  round-robin across whichever are still pending.
- ``HierarchicalGraph``: groups a graph's nodes into clusters (you
  supply the assignment) and automatically derives an abstract graph
  of cluster "entrances", so ``find_path`` searches the much smaller
  abstract graph first, then refines each segment within its cluster —
  cheaper than a flat search over a very large graph.

.. code-block:: python

   from gale.ai.pathfinding import PlannerPool, incremental_a_star

   pool = PlannerPool(iterations_per_update=200)
   request = pool.request(incremental_a_star(start, goal, nav_graph, heuristic))

   # In the game loop:
   pool.update()
   if request.done:
       path = request.result  # None if unreachable

Fuzzy logic
-----------

``gale.ai.fuzzy`` lets a decision change gradually instead of snapping
between states — for instance, a guard's alertness rising smoothly as
a player gets closer and stays visible longer, instead of jumping
straight from "unaware" to "alerted".

.. code-block:: python

   from gale.ai.fuzzy import FuzzyRule, FuzzyRuleSet, FuzzyVariable, LeftShoulderSet, RightShoulderSet, TriangularSet, fuzzy_and

   distance = FuzzyVariable("distance", domain=(0, 500), sets={
       "near": LeftShoulderSet(50, 200),
       "far": RightShoulderSet(150, 400),
   })
   visible = FuzzyVariable("visible", domain=(0, 1), sets={
       "yes": RightShoulderSet(0, 1),
   })
   alertness = FuzzyVariable("alertness", domain=(0, 1), sets={
       "low": LeftShoulderSet(0.2, 0.5),
       "high": RightShoulderSet(0.5, 0.8),
   })

   rules = FuzzyRuleSet([
       FuzzyRule(
           lambda d: fuzzy_and(d["distance"]["near"], d["visible"]["yes"]),
           "alertness", "high",
       ),
       FuzzyRule(lambda d: d["distance"]["far"], "alertness", "low"),
   ])

   fuzzified = {"distance": distance.fuzzify(120), "visible": visible.fuzzify(1)}
   output = rules.evaluate(fuzzified)
   alert_level = alertness.defuzzify(output["alertness"])  # a single crisp number

Learning models
---------------

``gale.ai.learning`` models an opponent's behavior from what's been
observed so far, instead of reacting to only the current frame:

- ``NaiveBayesClassifier``: learns which discrete features tend to go
  with which label (e.g. "aggressive" vs. "defensive" play style) and
  predicts a label for new features.
- ``NGramPredictor``: predicts the next action in a sequence from how
  often it has followed the same recent actions before — anticipating,
  say, whether the player is about to dodge left, dodge right, or
  attack.

.. code-block:: python

   from gale.ai.learning import NGramPredictor

   predictor = NGramPredictor(n=3)

   # Every time the player acts:
   predictor.observe(player_action)

   # Before the enemy reacts:
   likely_next = predictor.predict_next()  # None until this exact context repeats

Targeting
---------

``gale.ai.targeting`` helps aim a projectile at a moving target:

.. code-block:: python

   import pygame

   from gale.ai.targeting import iterative_targeting_angle, predict_intercept_time

   # No gravity/drag: solve directly for when a constant-speed shot
   # would meet a linearly-moving target.
   time_to_hit = predict_intercept_time(
       shooter.position, target.position, target.velocity, projectile_speed=400
   )

   # With gravity (and optionally drag, for which there's no closed-form
   # solution): search for the launch angle that lands on target.
   gravity = pygame.Vector2(0, 300)
   angle = iterative_targeting_angle(
       shooter.position, target.position, speed=400, gravity=gravity
   )

Formations
----------

``gale.ai.formation`` moves a group as a unit: an anchor ``Kinematic``
represents the group's overall position (steer it yourself, e.g. with
``Arrive``), and ``FormationManager`` gives each member a per-slot
target ``Kinematic`` to steer towards in turn — "two-level" steering,
since a member only ever needs to follow its own slot, not the whole
group's plan.

.. code-block:: python

   from gale.ai.formation import FormationManager, WedgeFormation
   from gale.ai.steering import Arrive, Kinematic

   anchor = Kinematic(x=0, y=0)
   manager = FormationManager(anchor, WedgeFormation(spacing=40, depth=40))
   manager.add_member(soldier_1.kinematic, role="left_flank")
   manager.add_member(soldier_2.kinematic, role="right_flank")

   # In the game loop, after steering the anchor towards its destination:
   manager.update()
   for member in manager.members:
       steering = Arrive(member, manager.slot_kinematic(member)).get_steering()

``LineFormation``, ``WedgeFormation``, and ``CircleFormation`` are the
built-in fixed patterns; wrap one in ``ScalableFormationPattern`` to
keep the formation's footprint roughly constant regardless of how many
members currently occupy it. "Emergent" (boids-like) formations need
none of this: ``Separation`` + a cohesion ``Seek`` + ``VelocityMatch``
combined with ``BlendedSteering`` (see "Combining steering" above) is
enough.

Markov chains and state machines
----------------------------------

``gale.ai.markov`` varies a character's idle/patrol behavior without
scripting a fixed sequence: ``MarkovState`` is a ``gale.sequence.Step``
(the same lifecycle ``gale.quest``/``gale.cutscene`` already use), and
``MarkovStateMachine`` picks the next one probabilistically, through a
``MarkovChain``, whenever the current one completes.

.. code-block:: python

   from gale.ai.markov import MarkovChain, MarkovState, MarkovStateMachine

   chain = MarkovChain()
   chain.add_transition("idle", "patrol", 0.7)
   chain.add_transition("idle", "investigate", 0.3)
   chain.add_transition("patrol", "idle", 1.0)
   chain.add_transition("investigate", "idle", 1.0)

   machine = MarkovStateMachine(
       chain,
       {
           "idle": MarkovState("idle", duration=2.0),
           "patrol": PatrolState("patrol", duration=5.0),  # your own MarkovState subclass
           "investigate": InvestigateState("investigate", duration=3.0),
       },
       start="idle",
   )

   # In the game loop:
   machine.update(dt)

Goal-oriented action planning (GOAP)
---------------------------------------

``gale.ai.goap`` finds the cheapest sequence of ``GoapAction`` s that
turns a starting world state into one satisfying a goal, reusing
``gale.ai.pathfinding.a_star_to_predicate`` over the space of possible
world states instead of a bespoke planner.

.. code-block:: python

   from gale.ai.goap import GoapAction, plan

   get_axe = GoapAction("get_axe", preconditions={}, effects={"has_axe": True})
   chop_wood = GoapAction(
       "chop_wood", preconditions={"has_axe": True}, effects={"has_wood": True}, cost=2.0
   )

   steps = plan(
       world_state={"has_axe": False, "has_wood": False},
       goal={"has_wood": True},
       actions=[get_axe, chop_wood],
   )  # [get_axe, chop_wood]

Rule-based systems
------------------

``gale.ai.rules`` forward-chains a set of ``Rule`` s against a shared
working memory: each call to ``run`` fires the highest-priority
applicable rule and repeats until none applies or a steady state is
reached.

.. code-block:: python

   from gale.ai.rules import Rule, RuleEngine

   engine = RuleEngine([
       Rule("flee", lambda m: m["health"] < 20, lambda m: m.update(goal="flee"), priority=10),
       Rule("attack", lambda m: m["enemy_visible"], lambda m: m.update(goal="attack"), priority=5),
       Rule("patrol", lambda m: True, lambda m: m.update(goal="patrol"), priority=0),
   ])
   engine.working_memory.update(health=100, enemy_visible=True)
   engine.run()
   engine.working_memory["goal"]  # "attack"

Scripting: building trees from data
---------------------------------------

``gale.ai.scripting`` turns a plain, JSON-friendly dict into a
``BehaviorTree``/``DecisionTree``, so an agent's logic can be described
as data (hand-written, generated, or loaded from a file) instead of
Python subclasses for every leaf:

.. code-block:: python

   from gale.ai.behavior_tree import BehaviorTree
   from gale.ai.scripting import Registry, build_behavior_tree

   registry = Registry()
   registry.register_condition("enemy_visible", lambda agent: agent.can_see_enemy())
   registry.register_action("attack", lambda agent, dt: agent.attack(dt))
   registry.register_action("patrol", lambda agent, dt: agent.patrol(dt))

   spec = {
       "type": "selector",
       "children": [
           {"type": "sequence", "children": [
               {"type": "condition", "name": "enemy_visible"},
               {"type": "action", "name": "attack"},
           ]},
           {"type": "action", "name": "patrol"},
       ],
   }
   tree = BehaviorTree(build_behavior_tree(spec, registry))

``build_decision_tree`` works the same way for ``DecisionTree`` specs
(``"type": "decision"``/``"random"``/``"action"``).

Tactical AI: influence maps
----------------------------

``gale.ai.tactical`` tracks, over a grid, how much presence each side
has across an area, so an agent can query "who controls this spot" or
pick the best of several candidate positions instead of only reacting
to what's immediately visible.

.. code-block:: python

   from gale.ai.tactical import InfluenceMap, best_position

   influence_map = InfluenceMap(width=800, height=600, cell_size=40)

   for enemy in enemies:
       influence_map.add_influence(enemy.position, strength=1.0, radius=150, team="enemy")

   for ally in allies:
       influence_map.add_influence(ally.position, strength=1.0, radius=150, team="ally")

   influence_map.propagate()

   safest_spot = best_position(
       candidate_positions,
       score=lambda p: influence_map.dominance_at(p),
   )

Minimax
-------

``gale.ai.minimax`` provides ``minimax`` (and ``best_move``, a thin
wrapper that just returns the chosen move) for turn-based adversarial
games -- tic-tac-toe, a tactical hacking minigame, or anything else
with a clear "my turn, their turn" structure. It works over any state
exposing ``(move, next_state)`` transitions and a leaf evaluation, with
alpha-beta pruning to skip branches that can't affect the result.

.. code-block:: python

   from gale.ai.minimax import best_move


   def get_children(board):
       return [(i, board[:i] + "X" + board[i + 1 :]) for i in range(9) if board[i] == "."]


   def is_terminal(board):
       return "." not in board  # a full game would also check for three in a row


   def evaluate(board):
       return board.count("X") - board.count("O")


   move = best_move("....O....", depth=4, maximizing=True, get_children=get_children, evaluate=evaluate, is_terminal=is_terminal)

Since a ``gale.ai.graph.StateGraph``'s edges already carry a move
label (see "Graphs" above), one built with ``StateGraph.expand`` plugs
directly into ``get_children`` via ``weighted_neighbors``/
``get_action``, instead of writing a bespoke one.

Perception
----------

``gale.ai.perception`` turns raw vision-cone sightings into a single
0..1 "awareness" value and an ``AlertLevel`` (``UNAWARE`` /
``SUSPICIOUS`` / ``ALERTED``), posted onto a ``Blackboard`` so a
behavior tree's ``Condition``/``Action`` nodes can react to it without
knowing anything about vision cones themselves.

.. code-block:: python

   import math

   from gale.ai.blackboard import Blackboard
   from gale.ai.perception import AlertLevel, Perception, VisionCone

   blackboard = Blackboard()
   cone = VisionCone(
       guard.kinematic, range_near=80, range_far=250, half_angle=math.radians(30)
   )
   perception = Perception([cone], blackboard)

   # In the game loop:
   perception.update(dt, player.position, obstacles=walls)

   if blackboard.get("alert_level") == AlertLevel.ALERTED:
       last_seen = blackboard.get("last_known_target_position")

A guard can watch through several cones at once (e.g. a wide, dim
peripheral cone plus a narrow, sharp forward one) by passing more than
one ``VisionCone`` to the same ``Perception`` -- awareness accumulates
from whichever cone currently sees the most.
