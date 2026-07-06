"""
This file contains a behavior tree implementation to model the decision
making of autonomous characters through a hierarchy of composable nodes.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class Status(Enum):
    """
    Result of ticking a behavior tree node.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class Node:
    """
    Base class for any node of a behavior tree.
    """

    def tick(self, agent: Any, dt: float) -> Status:
        """
        Execute this node.

        :param agent: The agent this behavior tree belongs to. It is passed down to every node so that leaves can inspect/modify it.
        :param dt: Time elapsed (in seconds) since the last tick.
        :returns: The status of this node after this tick.
        """
        raise NotImplementedError()

    def reset(self) -> None:
        """
        Reset any internal state kept by this node. It is called whenever
        this node stops being run, either because it finished or because
        its parent moved on to another child, so that the next tick
        starts fresh.
        """
        pass


class Action(Node):
    """
    Leaf node that executes a function and reports its result as the
    node status.
    """

    def __init__(self, function: Callable[[Any, float], Status]) -> None:
        """
        :param function: Callable that receives (agent, dt) and returns a Status.
        """
        self.function: Callable[[Any, float], Status] = function

    def tick(self, agent: Any, dt: float) -> Status:
        return self.function(agent, dt)


class Condition(Node):
    """
    Leaf node that evaluates a predicate and succeeds or fails depending
    on its result.
    """

    def __init__(self, predicate: Callable[[Any], bool]) -> None:
        """
        :param predicate: Callable that receives the agent and returns a bool.
        """
        self.predicate: Callable[[Any], bool] = predicate

    def tick(self, agent: Any, dt: float) -> Status:
        return Status.SUCCESS if self.predicate(agent) else Status.FAILURE


class Composite(Node):
    """
    Base class for nodes that group several children nodes.
    """

    def __init__(self, children: List[Node]) -> None:
        """
        :param children: The children nodes of this composite.
        """
        self.children: List[Node] = children

    def reset(self) -> None:
        for child in self.children:
            child.reset()


class Sequence(Composite):
    """
    Runs its children in order and succeeds only if all of them succeed.
    It stops (and fails) as soon as one of them fails, and reports
    RUNNING while the current child is still running, resuming from it
    on the next tick.
    """

    def __init__(self, children: List[Node]) -> None:
        super().__init__(children)
        self._current_index: int = 0

    def tick(self, agent: Any, dt: float) -> Status:
        while self._current_index < len(self.children):
            status = self.children[self._current_index].tick(agent, dt)

            if status == Status.RUNNING:
                return Status.RUNNING

            if status == Status.FAILURE:
                self.reset()
                return Status.FAILURE

            self._current_index += 1

        self.reset()
        return Status.SUCCESS

    def reset(self) -> None:
        super().reset()
        self._current_index = 0


class Selector(Composite):
    """
    Runs its children in order and succeeds as soon as one of them
    succeeds. It only fails if all of them fail, and reports RUNNING
    while the current child is still running, resuming from it on the
    next tick.
    """

    def __init__(self, children: List[Node]) -> None:
        super().__init__(children)
        self._current_index: int = 0

    def tick(self, agent: Any, dt: float) -> Status:
        while self._current_index < len(self.children):
            status = self.children[self._current_index].tick(agent, dt)

            if status == Status.RUNNING:
                return Status.RUNNING

            if status == Status.SUCCESS:
                self.reset()
                return Status.SUCCESS

            self._current_index += 1

        self.reset()
        return Status.FAILURE

    def reset(self) -> None:
        super().reset()
        self._current_index = 0


class Parallel(Composite):
    """
    Runs all of its children on every tick and succeeds or fails
    according to how many of them succeeded or failed on this tick.
    Children that already reached SUCCESS or FAILURE are latched and no
    longer ticked on subsequent calls, so their side effects only run
    once, until this node itself finishes and resets.
    """

    def __init__(
        self,
        children: List[Node],
        success_threshold: Optional[int] = None,
        failure_threshold: Optional[int] = None,
    ) -> None:
        """
        :param children: The children nodes to run concurrently.
        :param success_threshold: Minimum number of children that must succeed for this node to succeed. The default value is the number of children (all of them).
        :param failure_threshold: Minimum number of children that must fail for this node to fail. The default value is 1 (any of them).
        """
        super().__init__(children)
        self.success_threshold: int = (
            len(children) if success_threshold is None else success_threshold
        )
        self.failure_threshold: int = (
            1 if failure_threshold is None else failure_threshold
        )
        self._latched: Dict[int, Status] = {}

    def tick(self, agent: Any, dt: float) -> Status:
        successes = 0
        failures = 0

        for index, child in enumerate(self.children):
            status = self._latched.get(index)

            if status is None:
                status = child.tick(agent, dt)

                if status != Status.RUNNING:
                    self._latched[index] = status

            if status == Status.SUCCESS:
                successes += 1
            elif status == Status.FAILURE:
                failures += 1

        if successes >= self.success_threshold:
            self.reset()
            return Status.SUCCESS

        if failures >= self.failure_threshold:
            self.reset()
            return Status.FAILURE

        return Status.RUNNING

    def reset(self) -> None:
        super().reset()
        self._latched = {}


class Decorator(Node):
    """
    Base class for nodes that wrap and alter the behavior of a single
    child node.
    """

    def __init__(self, child: Node) -> None:
        """
        :param child: The node whose result will be transformed.
        """
        self.child: Node = child

    def reset(self) -> None:
        self.child.reset()


class Inverter(Decorator):
    """
    Inverts the result of its child: SUCCESS becomes FAILURE and vice
    versa. RUNNING is left untouched.
    """

    def tick(self, agent: Any, dt: float) -> Status:
        status = self.child.tick(agent, dt)

        if status == Status.SUCCESS:
            return Status.FAILURE

        if status == Status.FAILURE:
            return Status.SUCCESS

        return Status.RUNNING


class Succeeder(Decorator):
    """
    Always reports SUCCESS once its child finishes, regardless of its
    actual result.
    """

    def tick(self, agent: Any, dt: float) -> Status:
        status = self.child.tick(agent, dt)
        return Status.RUNNING if status == Status.RUNNING else Status.SUCCESS


class Failer(Decorator):
    """
    Always reports FAILURE once its child finishes, regardless of its
    actual result.
    """

    def tick(self, agent: Any, dt: float) -> Status:
        status = self.child.tick(agent, dt)
        return Status.RUNNING if status == Status.RUNNING else Status.FAILURE


class Repeater(Decorator):
    """
    Runs its child a fixed number of times (or forever), reporting
    RUNNING until it has finished all the repetitions.
    """

    def __init__(self, child: Node, times: Optional[int] = None) -> None:
        """
        :param child: The node to repeat.
        :param times: Number of times to repeat the child. The default value is None to repeat forever.
        """
        super().__init__(child)
        self.times: Optional[int] = times
        self._count: int = 0

    def tick(self, agent: Any, dt: float) -> Status:
        status = self.child.tick(agent, dt)

        if status == Status.RUNNING:
            return Status.RUNNING

        self._count += 1

        if self.times is not None and self._count >= self.times:
            self.reset()
            return Status.SUCCESS

        return Status.RUNNING

    def reset(self) -> None:
        super().reset()
        self._count = 0


class UntilSuccess(Decorator):
    """
    Keeps running its child until it succeeds.
    """

    def tick(self, agent: Any, dt: float) -> Status:
        status = self.child.tick(agent, dt)

        if status == Status.SUCCESS:
            self.reset()
            return Status.SUCCESS

        return Status.RUNNING


class UntilFailure(Decorator):
    """
    Keeps running its child until it fails.
    """

    def tick(self, agent: Any, dt: float) -> Status:
        status = self.child.tick(agent, dt)

        if status == Status.FAILURE:
            self.reset()
            return Status.FAILURE

        return Status.RUNNING


class Cooldown(Decorator):
    """
    Prevents its child from being run again until a given amount of time
    has passed since the last time it finished, either by success or
    failure. While in cooldown, this node fails immediately.
    """

    def __init__(self, child: Node, duration: float) -> None:
        """
        :param child: The node to guard with a cooldown.
        :param duration: Time (in seconds) to wait before the child can run again.
        """
        super().__init__(child)
        self.duration: float = duration
        self._timer: float = duration

    def tick(self, agent: Any, dt: float) -> Status:
        if self._timer < self.duration:
            self._timer += dt
            return Status.FAILURE

        status = self.child.tick(agent, dt)

        if status != Status.RUNNING:
            self._timer = 0

        return status

    def reset(self) -> None:
        super().reset()
        self._timer = self.duration


class BehaviorTree:
    """
    Wraps a root node so that it can be conveniently ticked as a whole.

    Usage example:

        tree = BehaviorTree(
            Selector([
                Sequence([
                    Condition(lambda agent: agent.can_see_enemy()),
                    Action(lambda agent, dt: agent.attack(dt)),
                ]),
                Action(lambda agent, dt: agent.patrol(dt)),
            ])
        )
        tree.tick(agent, dt)
    """

    def __init__(self, root: Node) -> None:
        """
        :param root: The root node of the tree.
        """
        self.root: Node = root

    def tick(self, agent: Any, dt: float) -> Status:
        """
        Tick the tree from its root.

        :param agent: The agent this tree belongs to.
        :param dt: Time elapsed (in seconds) since the last tick.
        :returns: The status of the root node after this tick.
        """
        return self.root.tick(agent, dt)
