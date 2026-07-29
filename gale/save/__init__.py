"""
gale.save: a general-purpose save-game system. SaveManager persists
whatever JSON-serializable dict a game gives it into named slots on
disk, so the same class works for any game; everything a specific game
is likely to need to customize -- where saves live, the file format, a
schema version with migrations for evolving what a save contains,
and arbitrary per-save metadata for a save-select screen -- is a
constructor parameter or a gale.conf setting.

See docs/examples/save.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .manager import SaveError, SaveManager, SaveMetadata
from .serialization import Deserializer, Serializer, json_deserialize, json_serialize

__all__ = [
    "Deserializer",
    "SaveError",
    "SaveManager",
    "SaveMetadata",
    "Serializer",
    "json_deserialize",
    "json_serialize",
]
