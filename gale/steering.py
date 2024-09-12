"""
This module contains steering behaviors for agents.
"""
import math
import pygame


class Steering:
    """
    This is the base class to implement steering behaviors.
    """
    def calculate(self) -> pygame.Vector2:
        """
        This method should be implemented by the child classes.
        """
        raise NotImplementedError


class Seek(Steering):
    """
    This class implements the seek steering behavior.
    """
    def __init__(self, agent, target) -> None:
        """
        :param agent: The agent that will seek the target.
        :param target: The target to seek.
        """
        self.agent = agent
        self.target = target

    def calculate(self) -> pygame.Vector2:
        desired = self.target.position - self.agent.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Flee(Steering):
    """
    This class implements the flee steering behavior.
    """
    def __init__(self, agent, target) -> None:
        """
        :param agent: The agent that will flee from the target.
        :param target: The target to flee.
        """
        self.agent = agent
        self.target = target

    def calculate(self) -> pygame.Vector2:
        desired = self.agent.position - self.target.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Arrival(Steering):
    """
    This class implements the arrival steering behavior.
    """
    def __init__(self, agent, target, radius) -> None:
        """
        :param agent: The agent that will arrive at the target.
        :param target: The target to arrive.
        :param radius: The radius to start slowing down.
        """
        self.agent = agent
        self.target = target
        self.radius = radius

    def calculate(self) -> pygame.Vector2:
        desired = self.target.position - self.agent.position
        distance = desired.length()
        desired.normalize_ip()
        if distance < self.radius:
            desired *= self.agent.max_speed * distance / self.radius
        else:
            desired *= self.agent.max_speed
        return desired


class Wander(Steering):
    """
    This class implements the wander steering behavior.
    """
    def __init__(self, agent, wander_distance, wander_radius, wander_jitter) -> None:
        """
        :param agent: The agent that will wander.
        :param wander_distance: The distance from the agent to the wander circle.
        :param wander_radius: The radius of the wander circle.
        :param wander_jitter: The jitter value to add to the wander target.
        """
        self.agent = agent
        self.wander_distance = wander_distance
        self.wander_radius = wander_radius
        self.wander_jitter = wander_jitter
        self.wander_target = pygame.Vector2(1, 0)

    def calculate(self) -> pygame.Vector2:
        self.wander_target += pygame.Vector2(
            (2 * math.pi * self.wander_jitter * (2 * math.pi * math.pi)),
            (2 * math.pi * self.wander_jitter * (2 * math.pi * math.pi)),
        )
        self.wander_target.normalize_ip()
        self.wander_target *= self.wander_radius
        target = self.wander_target + pygame.Vector2(self.wander_distance, 0)
        target = target.rotate(self.agent.angle)
        desired = target - self.agent.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Pursue(Steering):
    """
    This class implements the pursue steering behavior.
    """
    def __init__(self, agent, target) -> None:
        """
        :param agent: The agent that will pursue the target.
        :param target: The target to pursue.
        """
        self.agent = agent
        self.target = target

    def calculate(self) -> pygame.Vector2:
        distance = self.target.position - self.agent.position
        updates = distance.length() / self.agent.max_speed
        future_position = self.target.position + self.target.velocity * updates
        desired = future_position - self.agent.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Evade(Steering):
    """
    This class implements the evade steering behavior.
    """
    def __init__(self, agent, target) -> None:
        """
        :param agent: The agent that will evade the target.
        :param target: The target to evade.
        """
        self.agent = agent
        self.target = target

    def calculate(self) -> pygame.Vector2:
        distance = self.target.position - self.agent.position
        updates = distance.length() / self.agent.max_speed
        future_position = self.target.position + self.target.velocity * updates
        desired = self.agent.position - future_position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Avoid(Steering):
    """
    This class implements the avoid steering behavior.
    """
    def __init__(self, agent, obstacles) -> None:
        """
        :param agent: The agent that will avoid the obstacles.
        :param obstacles: The obstacles to avoid.
        """
        self.agent = agent
        self.obstacles = obstacles

    def calculate(self) -> pygame.Vector2:
        closest = None
        distance = float("inf")
        for obstacle in self.obstacles:
            vector = obstacle.position - self.agent.position
            if vector.length() < distance:
                distance = vector.length()
                closest = obstacle
        desired = self.agent.position - closest.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class FollowPath(Steering):
    """
    This class implements the follow path steering behavior.
    """
    def __init__(self, agent, path) -> None:
        """
        :param agent: The agent that will follow the path.
        :param path: The path to follow.
        """
        self.agent = agent
        self.path = path
        self.current = 0

    def calculate(self) -> pygame.Vector2:
        target = self.path[self.current]
        distance = target - self.agent.position
        if distance.length() < 10:
            self.current += 1
            if self.current >= len(self.path):
                self.current = 0
        desired = target - self.agent.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Separate(Steering):
    """
    This class implements the separate steering behavior.
    """
    def __init__(self, agent, neighbors) -> None:
        """
        :param agent: The agent that will separate from the neighbors.
        :param neighbors: The neighbors to separate from.
        """
        self.agent = agent
        self.neighbors = neighbors

    def calculate(self) -> pygame.Vector2:
        desired = pygame.Vector2(0, 0)
        for neighbor in self.neighbors:
            distance = self.agent.position - neighbor.position
            if distance.length() < self.agent.radius * 2:
                desired += distance
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Align(Steering):
    """
    This class implements the align steering behavior.
    """
    def __init__(self, agent, neighbors) -> None:
        """
        :param agent: The agent that will align with the neighbors.
        :param neighbors: The neighbors to align with.
        """
        self.agent = agent
        self.neighbors = neighbors

    def calculate(self) -> pygame.Vector2:
        average = pygame.Vector2(0, 0)
        for neighbor in self.neighbors:
            average += neighbor.velocity
        average /= len(self.neighbors)
        desired = average - self.agent.velocity
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Cohesion(Steering):
    """
    This class implements the cohesion steering behavior.
    """
    def __init__(self, agent, neighbors) -> None:
        """
        :param agent: The agent that will move towards the center of mass of the neighbors.
        :param neighbors: The neighbors to move towards.
        """
        self.agent = agent
        self.neighbors = neighbors

    def calculate(self) -> pygame.Vector2:
        center = pygame.Vector2(0, 0)
        for neighbor in self.neighbors:
            center += neighbor.position
        center /= len(self.neighbors)
        desired = center - self.agent.position
        desired.normalize_ip()
        desired *= self.agent.max_speed
        return desired


class Flock(Steering):
    """
    This class implements the flock steering behavior.
    """
    def __init__(self, agent, neighbors) -> None:
        """
        :param agent: The agent that will flock with the neighbors.
        :param neighbors: The neighbors to flock with.
        """
        self.agent = agent
        self.neighbors = neighbors

    def calculate(self) -> pygame.Vector2:
        separation = Separate(self.agent, self.neighbors).calculate()
        alignment = Align(self.agent, self.neighbors).calculate()
        cohesion = Cohesion(self.agent, self.neighbors).calculate()
        return separation + alignment + cohesion
