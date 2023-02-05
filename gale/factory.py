"""
This file contains the class Factory that allows you to build
new object given a prototype.

Author: Alejandro Mujica
"""
from typing import Any, Dict, Optional, Type


class Factory:
    def __init__(self, prototype: Type) -> None:
        if type(prototype) is not type:
            raise ValueError("Argument prototype it not a data type")
        self._prototype = prototype

    def create(
        self, x: float, y: float, properties: Optional[Dict[str, any]] = None
    ) -> None:
        """
        Create a new object from the prototype.

        :param dt: Time elapsed of the game loop.
        :returns: A new instance of the prototype.
        :raises RuntimeError: If the stack is empty
        """
        if properties is None:
            properties = {}

        if type(properties) is not dict:
            raise TypeError("Argument properties is not a dict")

        properties.update(dict(x=x, y=y))
        return self._prototype(**properties)
