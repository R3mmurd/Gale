"""
gale.ai: a modular toolkit to build autonomous characters — Kinematic
bodies and steering behaviors (including combination/motor-control
variants), a behavior tree, a decision tree, data-driven scripting for
both, a shared Blackboard, generic graphs with search/pathfinding
algorithms (flat, hierarchical, interruptible, open-goal), the Agent
class that ties them together, a vision-cone Perception system, fuzzy
logic, naive-Bayes/n-gram learning models, projectile aiming/targeting,
coordinated-movement formations, Markov chains/state machines,
goal-oriented action planning (GOAP), a forward-chaining rule engine,
tactical influence maps, and a minimax search with alpha-beta pruning
for turn-based adversarial decisions.

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
    LookWhereYoureGoing,
    VelocityMatch,
    Pursue,
    Evade,
    Wander,
    Separation,
    CollisionAvoidance,
    Wall,
    WallAvoidance,
    PathFollow,
    Obstacle,
    ObstacleAvoidance,
    BlendedSteering,
    PrioritySteering,
    CooperativeArbitration,
    OutputFilter,
    CapabilityFilter,
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
from .scripting import Registry, build_behavior_tree, build_decision_tree
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
from .pathfinding import (
    incremental_a_star,
    a_star_to_predicate,
    PathfindingRequest,
    PlannerPool,
    HierarchicalGraph,
)
from .blackboard import Blackboard
from .agent import Agent
from .minimax import minimax, best_move
from .perception import (
    has_line_of_sight,
    VisionCone,
    AlertLevel,
    Perception,
)
from .fuzzy import (
    FuzzySet,
    TriangularSet,
    TrapezoidalSet,
    LeftShoulderSet,
    RightShoulderSet,
    fuzzy_and,
    fuzzy_or,
    FuzzyVariable,
    FuzzyRule,
    FuzzyRuleSet,
)
from .learning import NaiveBayesClassifier, NGramPredictor
from .targeting import (
    predict_intercept_time,
    ballistic_position,
    simulate_drag_trajectory,
    iterative_targeting_angle,
)
from .formation import (
    FormationPattern,
    LineFormation,
    WedgeFormation,
    CircleFormation,
    ScalableFormationPattern,
    SlotAssignment,
    FormationManager,
)
from .markov import MarkovChain, MarkovState, MarkovStateMachine
from .goap import GoapAction, plan as goap_plan
from .rules import Rule, RuleEngine
from .tactical import InfluenceMap, best_position
