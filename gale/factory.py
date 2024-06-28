"""
This file contains the class Factory that allows you to build
new object given a prototype. This also contains the class
Abstract factory to create factory of classes belonging to a module.

Author: Alejandro Mujica
"""

import sys

from typing import Any, Dict, Optional, Type, TypeVar, Generic

T = TypeVar("T")


class Factory(Generic[T]):
    def __init__(self, prototype: T) -> None:
        """
        :param prototype: The data type that will be created by the factory.
        """
        if type(prototype) is not type:
            raise ValueError("Argument prototype it not a data type")
        self._prototype = prototype

    def create(
        self, x: float, y: float, properties: Optional[Dict[str, any]] = None
    ) -> T:
        """
        Create a new object from the prototype.

        :param x: The x component for the position of the object.
        :param y: The y component for the position of the object.
        :param properties: A dictionary with the properties that will be set to the new object.
        :returns: A new instance of the prototype.
        :raises RuntimeError: If the stack is empty
        """
        if properties is None:
            properties = {}

        if type(properties) is not dict:
            raise TypeError("Argument properties is not a dict")

        properties.update(dict(x=x, y=y))
        return self._prototype(**properties)


class AbstractFactory:
    def __init__(self, module_name: str) -> None:
        """
        :param module_name: The name of the module that contains the data types that should be created for any factory.
        :raises ValueError: If the given name is not an existing module.
        """
        if module_name not in sys.modules:
            raise ValueError(f"{module_name} is not a module.")

        self.module_name = module_name

    def get_factory(self, prototype_name: str) -> Factory:
        """
        Build a new factory for the given data type name.

        :param prototype_name: The name of the data type that will be created by the generated factory.
        :returns: The new factory.
        :raises ValueError: if there is no existing class with the given name.
        """
        prototype = getattr(sys.modules[self.module_name], prototype_name, None)

        if prototype is None:
            raise ValueError(f"There is no class called {prototype_name}")

        return Factory(prototype)
