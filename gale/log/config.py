"""
This file contains the functions to configure and obtain gale's
loggers.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import logging
from typing import Optional

from .level import LogLevel

_ROOT_LOGGER_NAME: str = "gale"
_DEFAULT_LOG_FILE: str = "gale.log"
_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

_configured: bool = False


def configure(
    level: int = LogLevel.INFO,
    log_file: Optional[str] = _DEFAULT_LOG_FILE,
    console: bool = True,
) -> None:
    """
    Set up gale's default logging: a console handler and/or a
    plain-text file handler. Call this once, as early as convenient
    (get_logger auto-configures with these same defaults on first use
    if you never call this explicitly, so calling it is only needed to
    override the defaults).

    Extra "strategies" — where else records should go, such as a
    Graylog server — are added on top of whatever this sets up, with
    add_handler; calling configure again replaces the console/file
    handlers but leaves any handler added through add_handler alone.

    :param level: The minimum severity to emit, one of the LogLevel constants. The default value is LogLevel.INFO.
    :param log_file: Path to the plain-text log file to write to. The default value is "gale.log". Pass None to disable file logging.
    :param console: Whether to also print log records to the terminal. The default value is True.
    """
    logger = _root_logger()
    logger.setLevel(level)
    # Otherwise, if the embedding application also configures
    # Python's root logger (e.g. via logging.basicConfig()), every
    # record would be emitted twice: once by our own handlers, once
    # by the root's.
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "_gale_default", False):
            logger.removeHandler(handler)

    formatter = logging.Formatter(_FORMAT)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._gale_default = True
        logger.addHandler(console_handler)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler._gale_default = True
        logger.addHandler(file_handler)

    global _configured
    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    :param name: A dotted name for the logger, nested under gale's own (e.g. "space_trip.player" becomes "gale.space_trip.player"). The default value is None, returning gale's own top-level logger.
    :returns: A standard library Logger, so it composes with anything else that already understands logging.Logger. Auto-configures with configure()'s defaults on first use if configure() was never called explicitly.
    """
    if not _configured:
        configure()

    if name is None:
        return _root_logger()

    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")


def add_handler(handler: logging.Handler) -> None:
    """
    Attach an additional handler — a strategy for where log records
    should also go, such as a GraylogHandler — to gale's logger, on
    top of whatever configure() set up.

    :param handler: The handler to add.
    """
    get_logger().addHandler(handler)


def remove_handler(handler: logging.Handler) -> None:
    """
    :param handler: The handler to remove, previously passed to add_handler.
    """
    get_logger().removeHandler(handler)


def _root_logger() -> logging.Logger:
    return logging.getLogger(_ROOT_LOGGER_NAME)
