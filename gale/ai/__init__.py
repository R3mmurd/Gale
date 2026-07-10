"""
gale.ai: a modular toolkit to build autonomous characters — Kinematic
bodies and steering behaviors, a behavior tree, a decision tree, a
shared Blackboard, generic graphs with search algorithms, and the
Agent class that ties them together.

See docs/examples/gale_ai.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .steering import (
    SteeringOutput,
    Kinematic,
    SteeringBehavior,
    Seek,
    Flee,
    Arrive,
    Align,
    Face,
    VelocityMatch,
    Pursue,
    Evade,
    Wander,
    Separation,
    Obstacle,
    ObstacleAvoidance,
    BlendedSteering,
    PrioritySteering,
)
from .behavior_tree import (
    Status,
    Node,
    Action,
    Condition,
    Composite,
    Sequence,
    Selector,
    Parallel,
    Decorator,
    Inverter,
    Succeeder,
    Failer,
    Repeater,
    UntilSuccess,
    UntilFailure,
    Cooldown,
    BehaviorTree,
)
from .decision_tree import (
    DecisionTreeNode,
    ActionNode,
    DecisionNode,
    RandomDecisionNode,
    DecisionTree,
)
from .graph import (
    CycleError,
    Graph,
    NavGraph,
    DependencyGraph,
    StateGraph,
)
from .search import (
    depth_first_search,
    breadth_first_search,
    dijkstra,
    a_star,
    path_cost,
)
from .blackboard import Blackboard
from .agent import Agent
