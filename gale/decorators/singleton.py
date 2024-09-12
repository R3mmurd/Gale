"""
Thios module contains the Singleton class decorator.
"""
from functools import wraps


def singleton(cls):
    """
    This is a decorator to make a class a Singleton
    """
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
