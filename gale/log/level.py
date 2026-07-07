"""
This file contains the implementation of the class LogLevel.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import logging


class LogLevel:
    """
    The severities a log record can have, in increasing order of
    severity. These are exactly Python's own logging levels — kept
    under gale's own name so a game never has to import the standard
    library's logging module just to pick a level.
    """

    DEBUG: int = logging.DEBUG
    INFO: int = logging.INFO
    WARNING: int = logging.WARNING
    ERROR: int = logging.ERROR
    CRITICAL: int = logging.CRITICAL
