"""
This file contains a small fuzzy logic toolkit: fuzzy sets (membership
functions), FuzzyVariable (a named collection of linguistic values
over a domain), FuzzyRule/FuzzyRuleSet (antecedent/consequent rules and
their evaluation), and defuzzify (turning an aggregated fuzzy output
back into a single crisp number). Useful for AI decisions that should
change gradually instead of snapping between states -- for instance, a
guard's alertness rising smoothly as a player gets closer and stays
visible longer, instead of jumping straight from "unaware" to
"alerted".

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, Dict, List, Tuple

Antecedent = Callable[[Dict[str, float]], float]


class FuzzySet:
    """
    Base class for a fuzzy set: a function from a crisp value to a
    degree of membership between 0 (not in the set at all) and 1
    (fully in the set).
    """

    def membership(self, x: float) -> float:
        """
        :param x: The crisp value to compute the membership degree of.
        :returns: The degree, between 0 and 1, to which x belongs to this set.
        """
        raise NotImplementedError()


class TriangularSet(FuzzySet):
    """
    A fuzzy set shaped like a triangle: membership is 0 at and beyond
    left/right, rises linearly to 1 at peak, then falls linearly back
    to 0.
    """

    def __init__(self, left: float, peak: float, right: float) -> None:
        """
        :param left: Value at and below which membership is 0.
        :param peak: Value at which membership is 1.
        :param right: Value at and beyond which membership is 0.
        """
        self.left: float = left
        self.peak: float = peak
        self.right: float = right

    def membership(self, x: float) -> float:
        if x <= self.left or x >= self.right:
            return 0.0

        if x <= self.peak:
            return (x - self.left) / (self.peak - self.left)

        return (self.right - x) / (self.right - self.peak)


class TrapezoidalSet(FuzzySet):
    """
    A fuzzy set shaped like a trapezoid: membership is 0 at and beyond
    left/right, rises linearly to 1 at left_peak, stays 1 until
    right_peak, then falls linearly back to 0.
    """

    def __init__(
        self, left: float, left_peak: float, right_peak: float, right: float
    ) -> None:
        """
        :param left: Value at and below which membership is 0.
        :param left_peak: Value at and above which membership reaches 1.
        :param right_peak: Value at and below which membership is still 1.
        :param right: Value at and beyond which membership is 0.
        """
        self.left: float = left
        self.left_peak: float = left_peak
        self.right_peak: float = right_peak
        self.right: float = right

    def membership(self, x: float) -> float:
        if x <= self.left or x >= self.right:
            return 0.0

        if x < self.left_peak:
            return (x - self.left) / (self.left_peak - self.left)

        if x <= self.right_peak:
            return 1.0

        return (self.right - x) / (self.right - self.right_peak)


class LeftShoulderSet(FuzzySet):
    """
    A fuzzy set that is fully true (1) at and below peak, then falls
    linearly to 0 at and beyond right. Useful for the lowest linguistic
    value of a variable (e.g. "near"), where anything below the
    interesting range should be fully in the set.
    """

    def __init__(self, peak: float, right: float) -> None:
        """
        :param peak: Value at and below which membership is 1.
        :param right: Value at and beyond which membership is 0.
        """
        self.peak: float = peak
        self.right: float = right

    def membership(self, x: float) -> float:
        if x <= self.peak:
            return 1.0

        if x >= self.right:
            return 0.0

        return (self.right - x) / (self.right - self.peak)


class RightShoulderSet(FuzzySet):
    """
    A fuzzy set that is 0 at and below left, rises linearly to 1 at
    peak, and stays fully true (1) beyond it. Useful for the highest
    linguistic value of a variable (e.g. "far"), where anything beyond
    the interesting range should be fully in the set.
    """

    def __init__(self, left: float, peak: float) -> None:
        """
        :param left: Value at and below which membership is 0.
        :param peak: Value at and above which membership is 1.
        """
        self.left: float = left
        self.peak: float = peak

    def membership(self, x: float) -> float:
        if x <= self.left:
            return 0.0

        if x >= self.peak:
            return 1.0

        return (x - self.left) / (self.peak - self.left)


def fuzzy_and(*degrees: float) -> float:
    """
    :param degrees: Membership degrees to combine.
    :returns: The fuzzy AND (minimum) of degrees.
    """
    return min(degrees)


def fuzzy_or(*degrees: float) -> float:
    """
    :param degrees: Membership degrees to combine.
    :returns: The fuzzy OR (maximum) of degrees.
    """
    return max(degrees)


class FuzzyVariable:
    """
    A named collection of fuzzy sets (linguistic values, such as
    "near"/"medium"/"far") sharing a single domain. Used both to
    fuzzify a crisp input (turn a number into a dict of membership
    degrees, one per linguistic value) and, as a consequent, to
    defuzzify a rule set's aggregated output back into a single crisp
    number.

    Usage example:

        distance = FuzzyVariable(
            "distance",
            domain=(0, 100),
            sets={
                "near": LeftShoulderSet(10, 30),
                "medium": TriangularSet(10, 40, 70),
                "far": RightShoulderSet(50, 90),
            },
        )
        distance.fuzzify(25)  # {"near": 0.25, "medium": 0.5, "far": 0.0}
    """

    def __init__(
        self,
        name: str,
        domain: Tuple[float, float],
        sets: Dict[str, FuzzySet],
        resolution: int = 100,
    ) -> None:
        """
        :param name: Name of this variable.
        :param domain: (min, max) crisp values this variable ranges over.
        :param sets: Linguistic values (name -> FuzzySet) defined over domain.
        :param resolution: Number of samples taken across domain when defuzzifying by centroid. The default value is 100.
        """
        self.name: str = name
        self.domain: Tuple[float, float] = domain
        self.sets: Dict[str, FuzzySet] = sets
        self.resolution: int = resolution

    def fuzzify(self, x: float) -> Dict[str, float]:
        """
        :param x: The crisp value to fuzzify.
        :returns: The membership degree of x in each of this variable's linguistic values.
        """
        return {name: fuzzy_set.membership(x) for name, fuzzy_set in self.sets.items()}

    def defuzzify(self, degrees: Dict[str, float]) -> float:
        """
        Turn an aggregated set of output degrees (one per linguistic
        value of this variable, as produced by FuzzyRuleSet.evaluate)
        back into a single crisp number, using the centroid method:
        sample the domain, clip each linguistic value's membership at
        its degree, and average the samples weighted by their clipped
        membership.

        :param degrees: Aggregated membership degree of each of this variable's linguistic values.
        :returns: The crisp value at the centroid of the aggregated, clipped membership curve, or the midpoint of domain if every sample has zero membership.
        """
        low, high = self.domain

        if not degrees:
            return (low + high) / 2

        step = (high - low) / (self.resolution - 1) if self.resolution > 1 else 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for i in range(self.resolution):
            x = low + step * i
            clipped = max(
                min(self.sets[name].membership(x), degree)
                for name, degree in degrees.items()
            )
            weighted_sum += x * clipped
            total_weight += clipped

        if total_weight == 0:
            return (low + high) / 2

        return weighted_sum / total_weight


class FuzzyRule:
    """
    A single fuzzy rule: an antecedent that computes a firing degree
    from a dict of fuzzified inputs (build it with fuzzy_and/fuzzy_or
    over the values fuzzify() produced), and a consequent -- the
    linguistic value of an output FuzzyVariable that this rule votes
    for, weighted by how strongly it fires.
    """

    def __init__(
        self, antecedent: Antecedent, consequent_variable: str, consequent_set: str
    ) -> None:
        """
        :param antecedent: Callable that, given a dict of fuzzified input degrees (name -> {linguistic_value: degree}), returns this rule's firing degree.
        :param consequent_variable: Name of the output FuzzyVariable this rule affects.
        :param consequent_set: Name of the linguistic value of consequent_variable this rule votes for.
        """
        self.antecedent: Antecedent = antecedent
        self.consequent_variable: str = consequent_variable
        self.consequent_set: str = consequent_set


class FuzzyRuleSet:
    """
    A collection of FuzzyRule evaluated together: each rule's firing
    degree is computed from the fuzzified inputs, then rules voting for
    the same (variable, linguistic value) pair are aggregated by
    fuzzy_or (max), producing one degree per output linguistic value
    per variable -- ready to hand to FuzzyVariable.defuzzify.

    Usage example:

        alertness = FuzzyVariable("alertness", (0, 1), {
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
        fuzzified = {
            "distance": distance.fuzzify(25),
            "visible": visible.fuzzify(1),
        }
        output_degrees = rules.evaluate(fuzzified)
        alertness.defuzzify(output_degrees["alertness"])
    """

    def __init__(self, rules: List[FuzzyRule]) -> None:
        """
        :param rules: The rules to evaluate together.
        """
        self.rules: List[FuzzyRule] = rules

    def evaluate(
        self, fuzzified_inputs: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        :param fuzzified_inputs: Fuzzified input variables, as name -> FuzzyVariable.fuzzify(x) result.
        :returns: For each consequent variable name affected by at least one rule, a dict of linguistic_value -> aggregated firing degree.
        """
        output: Dict[str, Dict[str, float]] = {}

        for rule in self.rules:
            degree = rule.antecedent(fuzzified_inputs)
            variable_output = output.setdefault(rule.consequent_variable, {})
            variable_output[rule.consequent_set] = fuzzy_or(
                variable_output.get(rule.consequent_set, 0.0), degree
            )

        return output
